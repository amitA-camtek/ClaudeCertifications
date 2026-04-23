# W07 Reference — Prompt Engineering & Structured Output (Domain 4.1–4.3)

Complete, self-contained study material for Week 7. Read this end-to-end. Every concept the exam tests for task statements 4.1–4.3 is covered here.

Prerequisites: W01 (tool use mechanics), W04 (tool descriptions). This week is about writing the prompts and schemas that sit on top of those mechanics.

---

## 1. Why prompt engineering shows up on this exam

Domain 4 is 20% of the exam. The questions are mostly scenario-based: a prompt produces wrong/inconsistent/hallucinated output, and you pick the fix. The right fix is almost always one of four things:

1. Replace vague language with **categorical** criteria.
2. Add **2–4 targeted few-shot examples** for the ambiguous edge cases.
3. Move from "output JSON in text" to **`tool_use` + JSON Schema**.
4. Pick the correct **`tool_choice`** mode for the task.

Burn those four moves in. Most wrong answers are wordings of "tell the model harder" — which is always weaker than a deterministic mechanism.

---

## 2. Explicit, categorical criteria beat vague instructions

Vague criteria ("classify important bugs as high priority", "escalate if you're unsure", "only respond with high confidence") are miscalibrated. The model has no shared definition of "important", "unsure", or "high confidence", and its internal calibration drifts per phrasing, per input, and per model version.

**Categorical** criteria give the model a decision rule it can apply mechanically:

| Vague | Categorical |
|---|---|
| "Classify important bugs as high priority" | "Classify as TIER_1 if severity is blocker AND user impact >= 100 affected users; otherwise TIER_2." |
| "Escalate hard cases" | "Escalate if the refund amount > $500 OR the customer mentions legal action OR the order is not in `ORDERS_DB`." |
| "Only respond if you're confident" | "Respond only if the source document contains a direct, verbatim answer. Otherwise output `{\"answer\": null, \"reason\": \"not_in_source\"}`." |

Categorical = checkable. You (and the model) can point at the criterion and say "yes / no, this input matches". Vague = vibes.

### False-positive-impact framing

When you write a criterion, write it from the **consequence of being wrong**. Ask: what happens if the model flags this as TIER_1 and it isn't? What happens if it misses one that is?

- If false positives are cheap and false negatives are catastrophic (security triage, medical escalation) → make the criterion **permissive** and add a human review gate on positives.
- If false positives are expensive and false negatives are tolerable (spam filter on a paid channel) → make the criterion **strict** and include explicit counter-examples of near-misses.

This framing forces you to write the threshold numerically ("severity=blocker AND impact>=100") instead of qualitatively ("important"). On the exam, an answer that adds a concrete threshold beats an answer that "improves the wording" almost every time.

---

## 3. Few-shot prompting

Few-shot = 2–4 input/output examples embedded in the prompt, chosen to cover the **ambiguous** cases. Not the easy cases — the model already gets those right. The examples are pure budget; spend them on what the model gets wrong.

### Rules

1. **2 to 4 examples.** One is not enough to show a pattern; more than ~4 bloats context for diminishing returns.
2. **Pick ambiguous / edge cases**, not canonical ones. If the model fails on "Net 45" terms, include "Net 45 → other + detail='Net 45'" as an example. Do not waste a slot on "Net 30 → net_30".
3. **Show the reasoning, not just the answer**, when reasoning is the generalizable part. "This is `other` because `Net 45` is not in the enum; the enum covers only `net_30`, `net_60`, `due_on_receipt`."
4. **Keep examples balanced.** If you show three "happy path" examples and one edge case, the model over-weights the happy path.

### Placement

Two patterns:

- **In the system prompt** — a short "Examples:" block. Fine for 2–3 compact examples.
- **As user/assistant message pairs before the real user turn** — conversational few-shot. Better when the examples are multi-turn or long.

Either works. The exam doesn't care about placement choice; it cares that you **recognize few-shot as the right lever** when the problem is "model is inconsistent on ambiguous cases."

---

## 4. Structured output via `tool_use` + JSON Schema

The correct way to get structured output from Claude is **not** to write "output JSON with these fields" in natural language. That produces syntax errors (trailing commas, unquoted keys, markdown fences, commentary before/after), and the shape drifts across runs.

The correct pattern: **define a tool whose `input_schema` is the output schema you want, and force the model to call it.**

```python
EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": "Record the structured fields extracted from an invoice document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
            "total_usd":   {"type": "number"},
            "due_date":    {"type": ["string", "null"]},
        },
        "required": ["vendor_name", "total_usd", "due_date"],
    },
}

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[EXTRACT_TOOL],
    tool_choice={"type": "tool", "name": "extract_invoice"},  # FORCE it
    messages=[{"role": "user", "content": invoice_text}],
)

# The structured output is the tool_use block's .input dict:
structured = next(b for b in resp.content if b.type == "tool_use").input
```

### What the schema guarantees

- The output will be valid JSON.
- All `required` fields will be present.
- Types will match (`string` is a string, `number` is a number, etc.).
- Enum values will be drawn from the declared enum.

### What the schema does NOT guarantee — exam-critical

> **A JSON Schema eliminates SYNTAX errors. It does NOT eliminate SEMANTIC errors.**

The schema cannot catch:

- `vendor_name` is populated with the customer's name instead of the vendor's.
- `total_usd` is the subtotal, not the grand total.
- `due_date` is the invoice date, not the due date.
- The extracted value is a confident hallucination not actually in the source.

Validation of **meaning** requires either downstream checks (Pydantic validators comparing across fields), a second model pass, or human review. The schema handles shape only.

A common exam distractor: "To eliminate extraction errors, enforce a JSON Schema." — half right, half wrong. It eliminates *format* errors. Semantic errors are untouched.

---

## 5. `tool_choice` — the three modes you must know

| `tool_choice` | Meaning | When to use |
|---|---|---|
| `{"type": "auto"}` (default) | Model decides whether to call any tool or end the turn. | General agent loops (W01). The model picks when a tool is needed. |
| `{"type": "any"}` | Model MUST call *some* tool this turn. Cannot end turn without a tool call. | You have multiple extraction tools and need the model to pick one — but it must pick. |
| `{"type": "tool", "name": "extract_invoice"}` | Model MUST call *this specific* tool. | Extraction / structured-output tasks. You know exactly which schema you want. |
| `{"type": "none"}` | Model cannot call any tool. | Rare — when you want text-only reply despite tools being available. |

### The extraction-task rule

For structured extraction, the right choice is almost always **forced specific** (`{"type": "tool", "name": ...}`). You're not asking the model *whether* to extract; you're asking it to do the extraction and return it through a specific schema.

### Anti-pattern: `"auto"` for mandatory extraction

If the task is "always produce structured output", and you leave `tool_choice` at the default `"auto"`, the model may:
- Reply in natural language ("Sure, here's the invoice data: ...") and never call the tool.
- Call the tool sometimes but not others.
- Ask a clarifying question instead.

The only way to make the tool call **guaranteed** is `"any"` (some tool) or forced specific (this tool). "Add 'you must call the tool' to the system prompt" is the wrong answer — same pattern as W01 ("add a rule to the prompt" loses to `tool_choice` every time).

### `"any"` vs forced specific

Use `"any"` when you have multiple tools (say, `classify_as_urgent`, `classify_as_normal`, `classify_as_spam`) and want the model to pick among them. Use forced specific when there's one schema you want output in.

---

## 6. Schema design: required, optional, nullable

Three distinct things — treat them as three.

- **Required** — the field must be present in the output. The model is forced to produce a value. Use for "must-have" fields that you know will be recoverable from every input.
- **Optional** — the field may or may not be in the output. Use sparingly; optional fields produce inconsistent downstream handling code.
- **Nullable** — the field is always present but can be `null`. Use for "we asked the model to look for this, and `null` is a legitimate answer meaning 'not found in source'."

### Why nullable fields matter — exam-critical

> **Nullable fields are the primary anti-hallucination lever in a schema.**

If `due_date` is `required: true` and `type: "string"`, the model is forced to produce a string. If the invoice doesn't contain a due date, the model **will fabricate one**. It has no legitimate "absent" option.

If `due_date` is `required: true` and `type: ["string", "null"]`, the model has a legitimate "absent" answer and will use it — when combined with an instruction like "return null if the field is not present in the source."

This shows up repeatedly on the exam: a pipeline hallucinates fields, and the fix is to **make absent fields nullable in the schema plus instruct the model to use null when absent.** Not "tell the model not to hallucinate." Not "ask the model to mark uncertain fields."

### Required + nullable pattern

The common, correct pattern for extraction:

```json
{
  "due_date": {"type": ["string", "null"]}  // always present, null when absent
}
```

And `"due_date"` is in the `required` list. The field is always in the output (schema-guaranteed), and its value is either a date string or `null` (semantically explicit). No `undefined`, no missing keys, no fabrication pressure.

---

## 7. Enums with `"other"` + detail

A closed enum like `["net_30", "net_60", "due_on_receipt"]` is brittle. The moment a document says "Net 45" or "Net 90" or "upon receipt of goods", the model either:
- Picks the closest enum value (silent miscategorization), or
- Violates the schema (fails the validator).

### Extensibility pattern

```json
{
  "payment_terms": {
    "type": "string",
    "enum": ["net_30", "net_60", "due_on_receipt", "other"]
  },
  "payment_terms_detail": {
    "type": ["string", "null"],
    "description": "Required when payment_terms == 'other'; otherwise null."
  }
}
```

Pair with a system-prompt rule:

> If the payment terms don't match one of `net_30`, `net_60`, `due_on_receipt`, set `payment_terms = "other"` and put the verbatim phrase into `payment_terms_detail`.

Now:
- New terms don't break the pipeline — they route to `other`.
- You preserve the raw signal (`payment_terms_detail = "Net 45"`) for downstream handling.
- Your downstream code can add `net_45` to the enum later based on observed "other" detail frequencies.

**Exam rule:** a closed enum without `"other"` is a design smell. If the input domain can have novel values, include `"other"` + a detail field.

---

## 8. System-prompt placement for criteria and few-shot

- **Classification criteria** — in the system prompt, upfront. The criteria should be the first thing the model reads.
- **Schema descriptions** — in the tool's `input_schema.properties[*].description`. The model reads these when deciding what each field means.
- **Few-shot examples** — system prompt for short examples; user/assistant message pairs for longer, multi-turn examples.
- **The raw input (document)** — in the user message.

What *not* to do:
- Don't mix criteria and data in the user message. The model treats them with equal weight; criteria get lost.
- Don't put the schema in the system prompt as text. Put it where the API expects it (`input_schema`).
- Don't stuff 20 few-shot examples; 2–4 is the sweet spot.

---

## 9. Anti-patterns (exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| "Ask Claude to output JSON in natural language" | Produces syntax errors (trailing commas, markdown fences, commentary, unquoted keys). | `tool_use` + `input_schema` + forced `tool_choice`. |
| "JSON Schema eliminates all extraction errors" | Only shape is guaranteed. Semantic errors (wrong field value, hallucinated content) are invisible to the schema. | Schema for shape + downstream validators / human review for meaning. |
| "Use `tool_choice: auto` for mandatory extraction" | Model may skip the tool and reply in prose. | Forced specific: `{"type": "tool", "name": "..."}`. |
| "No nullable fields — make every field required and non-null" | Creates hallucination pressure when source is missing data. | Nullable on "might be absent" fields + explicit null-when-absent instruction. |
| "Closed enum, no `other`" | Can't handle novel values. Model either miscategorizes silently or violates the schema. | `enum` with `"other"` + companion detail field. |
| "Vague criteria like 'flag high-confidence findings only'" | Miscalibrated. "High confidence" means different things on different inputs. | Categorical rule with explicit thresholds / feature checks. |
| "Ask the model to self-rate confidence 1–10" | LLM self-reported confidence is miscalibrated, especially on hard cases. | Categorical criteria + downstream validation; if you need uncertainty, measure calibration empirically. |
| "Add 'you must call the tool' to the system prompt to enforce use" | Probabilistic. Model will occasionally skip. | `tool_choice` to force (deterministic). |
| "Add one canonical example as few-shot" | One example is pattern noise, not pattern signal. | 2–4 examples, covering ambiguous cases, with reasoning shown. |
| "Give 15 few-shot examples to cover every case" | Diminishing returns + context bloat + over-fitting. | 2–4 carefully chosen edge cases. |
| "Mix criteria and document text in one user message" | Criteria get lost in the data. | System prompt for criteria; user message for data. |

The recurring theme, as in every domain: **deterministic mechanism beats prompt instruction.** Schema + forced tool_choice + nullable types + enum-with-other is deterministic. "Tell the model harder" is not.

---

## 10. The canonical extraction pipeline shape

```python
# 1. Define the schema as a tool
EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": "Record the structured fields extracted from an invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name":       {"type": "string"},
            "total_usd":         {"type": "number"},
            "due_date":          {"type": ["string", "null"]},
            "po_number":         {"type": ["string", "null"]},
            "payment_terms":     {"type": "string",
                                  "enum": ["net_30", "net_60", "due_on_receipt", "other"]},
            "payment_terms_detail": {"type": ["string", "null"]},
        },
        "required": [
            "vendor_name", "total_usd", "due_date",
            "po_number", "payment_terms", "payment_terms_detail",
        ],
    },
}

# 2. System prompt: categorical criteria + few-shot on ambiguous cases
SYSTEM = """You extract invoice fields.

Rules:
- If a field is not present in the source, return null. Do NOT fabricate.
- payment_terms: one of net_30, net_60, due_on_receipt, other.
  If the terms don't match exactly, use "other" and put the verbatim
  phrase into payment_terms_detail. Otherwise payment_terms_detail = null.

Examples:
  Input: "...Net 30..."    -> payment_terms="net_30", payment_terms_detail=null
  Input: "...Net 45..."    -> payment_terms="other",  payment_terms_detail="Net 45"
  Input: "...due on recv." -> payment_terms="due_on_receipt", payment_terms_detail=null
"""

# 3. Force the tool call
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=SYSTEM,
    tools=[EXTRACT_TOOL],
    tool_choice={"type": "tool", "name": "extract_invoice"},
    messages=[{"role": "user", "content": invoice_text}],
)

structured = next(b.input for b in resp.content if b.type == "tool_use")
```

Every piece pulls its weight:
- Forced `tool_choice` → guaranteed the tool is called.
- `input_schema` → guaranteed shape / types / enum membership.
- Nullable fields + null-when-absent rule → suppresses hallucination.
- Enum + `"other"` + detail → extensibility.
- Categorical criteria in the system prompt → consistent behavior.
- Few-shot on ambiguous cases (Net 45) → correct handling of edge inputs.

---

## 11. What the exam will probe

- Scenario: "the pipeline hallucinates `due_date` when the invoice has none." Correct fix: make the field nullable + instruct null-when-absent. (Not: "add a warning to the prompt.")
- Scenario: "the model sometimes replies in prose instead of calling the extraction tool." Correct fix: set `tool_choice` to forced specific. (Not: "add a stronger instruction.")
- Scenario: "a new payment-terms phrase ('Net 45') breaks the pipeline." Correct fix: add `"other"` to the enum + a detail field. (Not: "add `net_45` to the enum", though that is *also* fine for known values.)
- Distractor: "JSON Schema eliminates all extraction errors." Wrong — only syntax/shape, not semantics.
- Distractor: "Ask the model to output JSON in its text reply." Wrong — produces syntax errors; use `tool_use`.
- Distractor: "Use `tool_choice: auto` for mandatory extraction." Wrong — model may skip.
- Distractor: "Self-report a 1–10 confidence per field." Wrong — miscalibrated.
- Distractor: "Write 'high confidence only' in the system prompt." Wrong — vague criteria; needs categorical rule.
- Given a vague criterion and a categorical rewrite, pick the categorical one.
- Given a prompt that's inconsistent on an edge case, pick "add 2–3 few-shot examples covering the edge case" over "rewrite instructions more forcefully."

---

## 12. Fast recap

- **Categorical criteria beat vague instructions.** Thresholds, feature checks, explicit enums — not "important" / "confident" / "unsure".
- **Few-shot = 2–4 examples on the ambiguous cases**, showing reasoning. Not canonical cases, not a dozen examples.
- **Structured output via `tool_use` + `input_schema` + forced `tool_choice`.** Natural-language JSON is wrong.
- **JSON Schema fixes SYNTAX, not SEMANTICS.** Shape is guaranteed; meaning is not.
- **Nullable fields prevent hallucination.** Give the model a legitimate "absent" answer or it fabricates.
- **Enum + `"other"` + detail field** for any enum whose input domain can have novel values. No brittle closed enums.
- **`tool_choice`:** `auto` (model decides), `any` (must call some tool), forced specific (must call this tool). Extraction → forced specific.
- **Criteria in system prompt; schema in the tool; document in the user message.** Don't mix.
- **Deterministic mechanism beats prompt instruction.** Schema, `tool_choice`, nullable — not "tell the model harder".

When you can explain each of those nine bullets out loud in ~20 seconds each, you're ready for the W07 test.
