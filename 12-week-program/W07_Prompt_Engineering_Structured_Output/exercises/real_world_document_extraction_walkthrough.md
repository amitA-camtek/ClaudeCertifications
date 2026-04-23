# W07 Walkthrough — `real_world_document_extraction.py`

This file explains every design choice in `real_world_document_extraction.py`. Each choice maps to an exam-relevant concept. After the design-choice section, there's a "variations to try" section with small edits you can make to watch each guardrail fail — the fastest way to internalize why each piece is there.

---

## 1. Why a `tool_use` + JSON Schema at all, and not "return JSON in text"?

Natural-language JSON is an anti-pattern. The model will intermittently:

- Wrap the JSON in ```` ```json ```` fences when it wasn't asked to.
- Prepend "Sure, here's the extracted data:" or similar prose.
- Emit trailing commas, unquoted keys, or single-quoted strings (valid-looking JavaScript, invalid JSON).
- Drop a "required" field if it thinks the field isn't relevant.
- Produce a subtly wrong type (e.g., `"140.00"` as a string instead of `140.00` as a number).

Every one of those is a **syntax / shape** error that a JSON Schema, enforced through `tool_use`, eliminates.

The shape of the call is:

```python
client.messages.create(
    tools=[EXTRACT_TOOL],
    tool_choice={"type": "tool", "name": "extract_invoice"},
    ...
)
```

The `input_schema` on the tool is the output schema. The `.input` of the returned `tool_use` block is guaranteed to conform to that schema (right shape, right types, all required fields present, enum values inside the enum).

Exam-critical caveat: **the schema guarantees shape, not semantics.** See section 7.

---

## 2. Why `tool_choice={"type": "tool", "name": "extract_invoice"}`?

This is forced-specific `tool_choice`. It says: "the model MUST call this exact tool on this turn." Our task is structured extraction — there is no scenario where the right response is prose, or a different tool.

Compare the alternatives:

- `{"type": "auto"}` — the model decides. For mandatory extraction, this is wrong: the model will sometimes reply in text ("Here's the invoice data: …") and skip the tool entirely. Non-deterministic compliance.
- `{"type": "any"}` — the model must call *some* tool. Useful when you have multiple extraction tools (e.g., `extract_invoice`, `extract_receipt`, `extract_purchase_order`) and want the model to route. Here we only have one, so forced-specific is cleaner.
- `{"type": "none"}` — no tools. Wrong for extraction.

**Exam rule:** for mandatory structured output, `tool_choice` forced-specific (or `any` when there are multiple extraction tools). A prompt instruction like "you must always call the tool" is probabilistic and therefore wrong.

---

## 3. Required vs nullable — why `due_date` is required AND `["string", "null"]`

`due_date` and `po_number` are in the `required` list **and** typed as `["string", "null"]`. That combination means: the key is always present in the output, and its value is either a string or `null`.

This is deliberate. Three alternatives we rejected:

- **Non-nullable required** (`type: "string"`). The model is forced to produce a string. If the source doesn't have a due date (receipt case), the model has no legal "absent" answer and will **fabricate** one — often a plausible-looking future date. This is the canonical hallucination trigger in extraction pipelines.
- **Non-required, not nullable** (key optional, type string). The model may omit the key. Downstream code has to handle both "key absent" and "key present with value" as two different states — more surface area, more bugs.
- **Non-required, nullable.** Same problem — two absent states (missing key, null value) that behave identically but need different handling paths.

**Required + nullable = one consistent shape (key always present), one explicit "absent" answer (null).** This is the exam-correct design for "a field that might not exist in the source but must be recorded as absent."

### The anti-hallucination instruction in the system prompt

The schema opens the legal null path. The system prompt ("If a field is NOT PRESENT in the source document, return null. Do not infer, guess, or fabricate values.") tells the model to *use* that path. Both are required — schema alone is not enough if the prompt doesn't say "null is fine."

---

## 4. Why `payment_terms` uses an enum **with `"other"`** instead of a closed enum

A closed enum (`["net_30", "net_60", "due_on_receipt"]`) is brittle. The moment an input says "Net 45" or "50% upfront" or "due by month-end":

- If the enum is strict, the model either schema-violates or tries to coerce — most likely picking the closest enum value (`net_30` wins by proximity), silently miscategorizing the row.
- If the enum is open (non-enum string type), we lose the canonicalization benefit — downstream can't trust the value to be normalized.

The `enum` + `"other"` + separate detail string threads the needle:

- Common cases canonicalize to `net_30` / `net_60` / `due_on_receipt`. Downstream can treat these as known tokens.
- Novel cases route to `"other"`, preserving the verbatim phrase in `payment_terms_detail`. Downstream knows to special-case these.
- Over time, you can add new canonical values (`net_45`) once you see the "other" detail frequencies justify it — schema evolution without breakage.

### The pairing contract

We require `payment_terms_detail` to be non-null when `payment_terms == "other"` and null otherwise. The schema can't enforce this cross-field invariant (JSON Schema's conditional-required support is not guaranteed to be applied by the model). So we:

1. Describe the contract in the field descriptions and the system prompt.
2. Add a **semantic sanity check** in Python (`semantic_sanity()`) that catches violations.

The semantic checks are intentionally there to model the shape of real production code: **schema for shape, Python validators for meaning.**

---

## 5. Why **2–3 few-shot examples**, and why those specific three

Few-shot is a concentrated budget. You want each example to teach the model something it would otherwise get wrong. We picked three:

- **Example A — "Net 30" → `net_30`, detail=null.** Canonical case. You might think this is wasted budget (the model should get this right anyway), but it's necessary as a *counter*-example to Example B. Without it, the model tends to over-use `"other"` for anything that isn't dead-canonical.
- **Example B — "Net 45" → `other`, detail="Net 45".** The extensibility case. Without this example, the model frequently coerces "Net 45" to `net_30` to match the enum — a silent semantic error.
- **Example C — Absent fields → null.** The hallucination case. Without this example (and the system-prompt rule), the model often fabricates a plausible due date rather than returning null.

Each example shows the **reasoning** ("Net 45 is not in the enum, so …"), not just the answer. That's what generalizes: the model learns the decision rule, not three specific inputs.

### Why not 1 example, or 10?

- **One example** isn't a pattern. You need at least two points to define a rule, and ideally a canonical example plus the edge case so the model sees the boundary.
- **Ten examples** is bloat: diminishing returns past ~4, context cost grows, and the model can over-fit to surface features of the examples. The exam-aligned sweet spot is **2–4**.

### Placement

These examples are in the system prompt because they're short and text-only. For longer multi-turn examples, we'd put them as `user` / `assistant` message pairs before the real input. The exam doesn't prescribe placement; it cares that you **recognize few-shot as the right lever for ambiguous cases.**

---

## 6. Why the categorical rules in the system prompt, not "do a good job"

The SYSTEM prompt is a numbered list of checkable rules:

1. Null when absent.
2. `total_usd` is a number, no symbols.
3. `payment_terms` enum handling + `other` + detail pairing.
4. Call the tool exactly once.

This is intentional. Compare to the vague version: "extract the invoice accurately and cleanly." The model has no shared definition of "accurately" — it drifts per input. Numbered, categorical, checkable rules are what make behavior consistent across invoices.

**Exam rule:** vague adjectives ("accurate", "confident", "important") are distractors; concrete thresholds and feature checks are the right answer.

---

## 7. What this pipeline still can NOT guarantee — semantic errors

The schema plus forced `tool_choice` plus nullable types plus the enum pattern eliminate **syntax and shape** errors. They do not catch:

- The model extracts the **customer** name into `vendor_name`. Shape is fine (it's a string); the value is wrong.
- The model picks the **subtotal** as `total_usd` instead of the grand total. Type is fine; value is wrong.
- The model returns `"2026-06-30"` for `due_date` when the invoice actually says `"2026-06-03"` (OCR or confusion error). String, ISO-formatted — but wrong.
- The model decides the invoice currency is USD when it's actually EUR and there's no conversion. Number, non-negative — but wrong.

These are **semantic** errors. The only defenses are:

- **Downstream validators.** Cross-field consistency checks (the `semantic_sanity` function here); business rules (total > 0; date in the future for due dates); comparison to ground-truth fields elsewhere.
- **Human review.** Stratified sampling, field-level accuracy tracking (covered in W10).
- **Second-pass model review.** Independent instance, different prompt, compare outputs — covered in W08.

The exam repeatedly reinforces this: "enforce a JSON Schema to eliminate extraction errors" is the tempting-but-wrong distractor. The correct characterization is "eliminate *syntax* errors; semantic errors need other defenses."

---

## 8. Variations to try (learn by breaking things)

Run the script as-is first. Then make each of these edits in turn and observe the behavior — each one isolates a single design decision.

### Variation A — remove nullable, watch hallucination

In `EXTRACT_TOOL.input_schema.properties`, change:

```python
"due_date": {"type": ["string", "null"], ...}
```

to:

```python
"due_date": {"type": "string", ...}
```

Run against invoice 2 (the receipt with no due date). The model now has no legal "absent" answer and will typically fabricate a due date — often a plausible-looking one two weeks after the sale date. The schema accepts it; the value is a hallucination. This is the exam's canonical "no nullable fields → hallucination pressure" demonstration.

### Variation B — remove the null-when-absent rule from the system prompt

Keep the nullable schema, but delete rule #1 from SYSTEM:

```
1. If a field is NOT PRESENT in the source document, return null. ...
```

Run against invoice 2. You'll often see the model still fabricate values, because the *schema* allows null but the *prompt* didn't tell it null is the right answer. Takeaway: schema and prompt must cooperate. Nullable schema without a null-when-absent rule is only half the fix.

### Variation C — remove `"other"` from the enum, watch silent miscategorization

Change:

```python
"enum": ["net_30", "net_60", "due_on_receipt", "other"]
```

to:

```python
"enum": ["net_30", "net_60", "due_on_receipt"]
```

Also remove the `payment_terms_detail` field. Run against invoice 3 ("Net 45"). You'll see one of two failure modes:
- The model coerces to `net_30` (closest semantic neighbor) — silent miscategorization, the worst outcome because downstream has no signal that anything was wrong.
- The model violates the schema and the API call errors.

Takeaway: closed enums are brittle. `"other"` + detail is how you design for the inputs you haven't seen yet.

### Variation D — remove the few-shot examples, watch ambiguous cases degrade

Keep the schema intact (with `"other"` and nullable). Delete the "FEW-SHOT EXAMPLES" section from SYSTEM.

Run all three invoices multiple times. Invoice 1 (canonical) stays stable. Invoice 2 (receipt) often still works — rule #1 is explicit. **Invoice 3 (Net 45)** becomes the flaky one: sometimes the model picks `"other"` correctly, sometimes it picks `net_30` (coercing to the closest enum value because the rule didn't show it an example of the "other" path being the right choice).

Takeaway: few-shot on the ambiguous cases is where few-shot earns its keep. Without it, categorical rules alone are often not enough for the 10% of inputs that live in the gray area.

### Variation E — switch `tool_choice` to `"auto"`, watch the model skip

Change:

```python
tool_choice={"type": "tool", "name": "extract_invoice"}
```

to:

```python
tool_choice={"type": "auto"}
```

Run several times. On some runs, the model will respond in prose ("Here are the extracted fields for the Acme invoice: …") instead of calling the tool. `extract_one()` will then raise `"extract_invoice was not called"`. Takeaway: for mandatory extraction, `tool_choice` must be forced — a prompt instruction is not enough.

### Variation F — replace the categorical rules with vague language

Change the SYSTEM rules section to:

> "Extract the fields carefully and accurately. Be conservative and only include values you are confident about."

Run all three invoices. You'll see more drift: sometimes null is used on present fields ("conservative"), sometimes fabricated values appear ("confident" about the guess). Takeaway: "conservative", "confident", "accurate" are vague. Categorical rules (null when absent; enum membership; exact contracts) produce consistent output.

### Variation G — add a second extraction tool, try `tool_choice: "any"`

Add a second tool — say, `extract_receipt` with a slightly different schema (`receipt_id` instead of `po_number`). Change `tool_choice` to `{"type": "any"}`. Now the model must call *one* of the two tools, and picks based on the input (invoice 2 being a receipt should route to `extract_receipt`).

Takeaway: `"any"` is the right `tool_choice` when you have multiple extraction schemas and want the model to route among them. Forced-specific is still right when you have one target schema.

---

## 9. Summary — how each design choice maps to the exam

| Choice | Exam concept |
|---|---|
| `tool_use` + `input_schema` instead of text JSON | Structured output eliminates SYNTAX errors. |
| Forced `tool_choice` specific tool | Deterministic compliance; not a prompt instruction. |
| `required` + `["string", "null"]` | Anti-hallucination: legitimate "absent" answer. |
| Enum + `"other"` + detail | Extensibility; no brittle closed enums. |
| 2–3 few-shot on ambiguous cases | Few-shot earns its keep on the edges, not the canonical cases. Show reasoning. |
| Categorical rules in system prompt | Beats vague adjectives like "accurately" / "confidently". |
| Python semantic sanity checks | Schema doesn't catch semantic errors — validators do. |

If you can map each row of that table back to a specific line in `real_world_document_extraction.py`, you're fluent in W07.
