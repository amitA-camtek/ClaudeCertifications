# Build — Prompt Engineering & Structured Output

**Time:** 40 min · **Goal:** Build an extractor that uses `tool_use` + `input_schema` + forced `tool_choice` to return strict JSON from an invoice string, with nullable fields that suppress hallucination when data is missing.

## What you'll have at the end
- `exercises/my_extract.py` that extracts `vendor_name`, `total_usd`, `due_date` from an invoice blob via a forced tool call
- A run that returns `due_date: null` (not fabricated) when the invoice lacks a due date

## Prereqs
- `ANTHROPIC_API_KEY` set; `anthropic` SDK installed
- Finished reading [reference.md](../reference.md) §4–§7
- Target: `exercises/my_extract.py` that extracts fields from an invoice string (peek at [minimal_structured_output.py](minimal_structured_output.py) if stuck)

## Steps

### 1. Pick the extraction target & sample inputs (~4 min)
Write two invoice blobs as module constants: one complete, one missing the due date. The second one is the real test — it's where a naive pipeline hallucinates.
- [ ] `INVOICE_FULL` — vendor, total, Net 30, due date present
- [ ] `INVOICE_NO_DUE` — vendor, total, Net 30, **no** due-date line

**Why:** §6 — nullable fields only prove their worth on inputs where the field is absent. Without the missing-data case you can't observe anti-hallucination behavior.
**Checkpoint:** Both strings exist; `INVOICE_NO_DUE` genuinely contains no parseable date.

### 2. Design the `input_schema` with required + nullable (~7 min)
Define `EXTRACT_TOOL` with three properties. Mark `due_date` as `{"type": ["string", "null"]}` and put it in `required` alongside the others.
- [ ] `vendor_name: string` (required)
- [ ] `total_usd: number` (required)
- [ ] `due_date: string | null` (required, nullable)

```python
"due_date": {"type": ["string", "null"],
             "description": "ISO 8601 date (YYYY-MM-DD) or null if not present."}
```

**Why:** §6 — required+nullable is the canonical anti-hallucination pattern. Required alone forces fabrication; nullable alone without `required` produces inconsistent downstream handling.
**Checkpoint:** `due_date` is in `required` AND its type is the two-element array `["string", "null"]`.

### 3. Write categorical null-when-absent system prompt (~5 min)
Put the rule in the system prompt, not the user message. Be mechanical — no "try to" or "if you're confident".
- [ ] System prompt states: "If the invoice has no due date, set `due_date` to null — never guess."
- [ ] No vague words (`important`, `confident`, `best-guess`) anywhere

**Why:** §2 — categorical ("set due_date=null") beats vague ("be careful about dates"). §8 — criteria belong in the system prompt, document in the user message.
**Checkpoint:** Read the prompt aloud; every instruction is a mechanically checkable rule.

### 4. Force the tool call via `tool_choice` (~4 min)
In `client.messages.create`, pass `tools=[EXTRACT_TOOL]` and `tool_choice={"type": "tool", "name": "extract_invoice"}`.
- [ ] Forced-specific `tool_choice`, not `"auto"` and not `"any"`
- [ ] `tools` list contains exactly the one tool

**Why:** §5 — for mandatory extraction, forced-specific is the only deterministic option. `"auto"` lets the model reply in prose; "add 'you must call the tool' to the prompt" is the anti-pattern (§9).
**Checkpoint:** Removing `tool_choice` would allow a prose reply; your code wouldn't.

### 5. Parse `tool_use.input` & handle the schema-violation retry (~8 min)
Iterate `resp.content`, grab the first block where `block.type == "tool_use"` and `block.name == "extract_invoice"`, return `block.input`. Wrap in a bounded retry (max 1 retry) for the extremely rare case of missing tool_use.
- [ ] Return `block.input` directly — it's already a dict
- [ ] If no `tool_use` block found, retry ONCE, then raise
- [ ] Do NOT parse JSON from text; do NOT strip markdown fences

**Why:** §4 — `.input` is the structured output; the schema guarantees shape/types/required fields. Bounded retry (not infinite) because forced `tool_choice` should make failure impossible — repeated failure means something is genuinely wrong, not transient.
**Checkpoint:** No `json.loads`, no regex, no `.text` access anywhere in the extraction path.

### 6. Wire the CLI demo (~4 min)
`if __name__ == "__main__":` run extraction against both invoices and print both results.
- [ ] Print result for `INVOICE_FULL`
- [ ] Print result for `INVOICE_NO_DUE`

**Why:** §4 — observing both cases side-by-side makes the null-vs-hallucinated distinction visible.
**Checkpoint:** Two JSON objects printed to stdout.

### 7. Run & verify (~8 min)
`python exercises/my_extract.py`. Inspect the second output.
- [ ] `INVOICE_FULL` → `due_date` is the actual date string
- [ ] `INVOICE_NO_DUE` → `due_date` is literally `None`/`null`, not a guessed date

**Why:** §6 — this is the exam-critical behavior; the schema+prompt combination must produce null, not a fabricated date.
**Checkpoint:** If the second run produces any date string, your prompt or schema is wrong — fix before moving on.

## Verify
Run against a sample invoice with a missing date. Expected:
- `due_date` is `None` in the Python dict (not a hallucinated date like "2026-05-15")
- The response contains exactly one `tool_use` block with `name == "extract_invoice"` (forced `tool_choice` guarantees this)
- `vendor_name` and `total_usd` are populated with correct types (string, number)
- No JSON parsing code ran — `.input` was used directly

**Common mistakes:**
- Making `due_date` optional (missing key) vs nullable (present, value null) — §6: these are distinct; nullable is what you want
- Wording like "only include due_date if confident" → vague; fix to "set due_date=null if absent" — §2
- Leaving `tool_choice` at default `"auto"` → model may reply in prose — §5 / §9
- Closed enum on `payment_terms` without `"other"` — §7 (will bite on Net 45 in the Stretch)
- Writing `json.loads(response.text)` — you're back in the BEFORE anti-pattern — §4

## Stretch — Polish block (30 min on Practice Day)
Exercise `tool_choice` modes: `auto` vs `any` vs forced specific.
- [ ] Add a second tool `classify_invoice` with an enum `{"urgent","normal"}`
- [ ] Run the same invoice three times: `tool_choice={"type":"auto"}`, `{"type":"any"}`, `{"type":"tool","name":"extract_invoice"}`
- [ ] Log which tool (if any) was called in each mode; confirm `auto` sometimes returns prose, `any` always calls *some* tool, forced-specific always calls that exact tool
- [ ] Extend the schema with `payment_terms` enum `["net_30","net_60","due_on_receipt","other"]` + nullable `payment_terms_detail`; feed an invoice with "Net 45" and verify it routes to `other` with detail="Net 45" (§7)

## If stuck
Compare with [minimal_structured_output.py](minimal_structured_output.py). Read → close → rewrite.
