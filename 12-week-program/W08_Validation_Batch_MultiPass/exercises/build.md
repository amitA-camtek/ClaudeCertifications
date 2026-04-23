# Build — Validation, Batch & Multi-Pass

**Time:** 40 min · **Goal:** Build a bounded validation-retry loop that feeds specific errors back to the model, plus a paper sketch of a Batches API submission with SLA-window math.

## What you'll have at the end
- `exercises/my_retry.py` — extractor + strict validator + 2–3 attempt retry loop with absent-data detection
- A 6-line Batches sketch (custom_id, submit, poll, 24h) with the SLA-cadence formula written next to it

## Prereqs
- `ANTHROPIC_API_KEY` exported; `anthropic` + `pydantic` installed
- Finished reading [reference.md](../reference.md) §1–§5
- Target: `exercises/my_retry.py` (peek at [minimal_validation_retry.py](minimal_validation_retry.py) if stuck)

## Steps

### 1. Define the extractor + strict schema (~6 min)
One tool (`emit_invoice`) with `tool_choice={"type":"tool","name":"emit_invoice"}`. Pydantic model with a **strict** ISO-date validator and `tax_id: Optional[str]`.
- [ ] Define `Invoice` with `vendor`, `invoice_date` (regex `\d{4}-\d{2}-\d{2}`), `amount_usd > 0`, `tax_id: Optional[str]`
- [ ] Declare `emit_invoice` tool; force it with `tool_choice`
**Why:** §1 — tool_use enforces *shape*; Pydantic enforces *semantics* the schema can't express. §3 — nullable fields are the upstream fix for legitimately-absent data.
**Checkpoint:** Instantiating `Invoice(invoice_date="Q3 2024", ...)` raises `ValidationError`; `tax_id=None` validates fine.

### 2. Validator returns field-specific errors (~5 min)
A generic "Invalid" string is useless to the model. Pull `loc`, `msg`, `type` from the `ValidationError` and format `field 'X': <msg> (type=Y)`.
- [ ] On catch, extract `e.errors()[0]` into `{field, msg, category}`
- [ ] Include an excerpt from the source that contained the offending value when available
**Why:** §2 — without specific error signal, the model has no gradient and emits the same bad value again. Target shape: `{'field': 'invoice_date', 'error': "not ISO-8601, got 'Q3 2024'", 'excerpt_from_source': 'Date: Q3 2024'}`.
**Checkpoint:** Printed error names the exact field and the bad value, not "validation failed".

### 3. Retry loop bounded to 2–3 attempts (~7 min)
`MAX_RETRIES = 2` → three total attempts. On each validation fail, append source + prior output + specific error and re-call. On success, return immediately.
- [ ] Loop `for attempt in range(1, MAX_RETRIES + 2)`
- [ ] Return `{status: "failed_validation", attempts, last_error}` when budget exhausts — never loop forever
**Why:** §2 — 2–3 attempts max; beyond that you're either stuck in an impossible case or chasing a semantic problem through a structural door. §8 — "retry 10 times" is the canonical distractor.
**Checkpoint:** Doc with "Q3 2024" date succeeds by attempt 2, **not** attempt 10.

### 4. Append prior output + specific error + source to next call (~6 min)
The retry user turn must contain all three. Also pair the previous `tool_use` block with a `tool_result` (`is_error: true`) so the API accepts the history.
- [ ] Retry prompt shape (three-liner):

```
ORIGINAL SOURCE: <unchanged>   YOUR PREVIOUS OUTPUT: <exact JSON>
VALIDATION ERROR: field 'invoice_date': not ISO-8601, got 'Q3 2024'
Fix ONLY the flagged field. If source lacks it, pass null — do not invent.
```
**Why:** §2 — model needs (a) what it wrote, (b) why it was rejected, (c) source to re-read. Missing any of the three = same output again.
**Checkpoint:** Retry turn contains all three sections; `tool_result.is_error == true`.

### 5. Detect absent-source case — stop, don't retry (~6 min)
Before consuming the next attempt, check if the same field failed with the same category twice AND the source lacks any mention of it (keyword heuristic on `tax id`, `ein`, `vat`, etc.). If so, return `status: "absent_data"` with a `detected_pattern` record.
- [ ] Track `last_error_field`, `last_error_category`, `repeated_same_failure`
- [ ] `_field_absent_in_source(field, text)` — returns True when no hint keywords found
- [ ] On repeat + absent → return early with `detected_pattern: {field, error_category, occurrences, source_lacks_field: true}`
**Why:** §3 — retries on absent data produce hallucinations, not corrections. §4 — `detected_pattern` beats "model will self-correct". §8 — "raise retry budget when a field keeps failing" is the wrong fix; the right fix is nullable + skip.
**Checkpoint:** Doc with no Tax ID line returns `absent_data` on attempt 2 without burning attempt 3.

### 6. Sketch Batches invocation + SLA math (~6 min)
No code — write a 6-line pseudocode block in a docstring at the bottom of `my_retry.py`. Cover: build `requests=[{"custom_id": doc_id, "params": {...}}, ...]`; `client.messages.batches.create(requests=...)`; poll `batches.retrieve(id)` until `processing_status == "ended"`; download; map results back by `custom_id`; note the 24h ceiling.
- [ ] Write the cadence formula next to it: **`submit every (S − B)` hours**, where S = SLA, B = batch ceiling (24h). Worked example: S=30h, B=24h → submit every 4h → worst case = 4h wait + 24h process = 28h < 30h.
- [ ] Add one comment: "single-turn per request → no agentic tool loops inside Batches"
**Why:** §5 — `custom_id` is the only way to correlate; polling (not push); 50% cheaper; single-turn constraint. §5 SLA trap — naive check "24h > SLA?" rules Batches out when cadence scheduling would fit.
**Checkpoint:** You can answer out loud: "SLA is 20h, can I use Batches?" → No, because S − B = −4h. "SLA is 36h?" → Yes, submit every 12h.

## Verify
Run against the three-doc sample (complete / "Q3 2024" date / missing Tax ID). Expected:
- INV-001: `status=ok`, `attempts=1`
- INV-002: fixes on **attempt 2**, not attempt 10 — `status=ok`, `attempts=2`
- INV-003: `status=absent_data` with `detected_pattern.source_lacks_field=true`, attempts ≤ 2 — retry loop does **not** burn attempt 3

**Common mistakes:**
- Unbounded retries / `while True` → §2, §8
- Generic "please try again" instead of field-specific error + excerpt → §2, §8
- Reaching for Batches for pre-merge CI or a real-time UI → §5 mis-assignment table
- Forgetting `custom_id` and correlating by list order → §5, §8
- Raising retry budget when tax_id keeps failing instead of making it nullable → §3, §8

## Stretch — Polish block (30 min on Practice Day)
Self-review limitation demo: same session retains reasoning context, so it rubber-stamps its own output.
- [ ] Pick one ambiguous doc (e.g., vendor/buyer swap risk). Run extraction.
- [ ] **Same-session review:** append "Is this extraction correct? Explain." to the same `messages[]`. Record the verdict.
- [ ] **Independent-instance review:** new API call, fresh `messages[]`, new system prompt ("You are a reviewer. Compare source vs candidate output. Flag every discrepancy."). Pass source + candidate JSON as two labeled chunks.
- [ ] Compare outputs. Write 3 bullets in `notes/study_day.md`: what same-session missed, what independent caught, why (§6 reasoning bias).

## If stuck
Compare with [minimal_validation_retry.py](minimal_validation_retry.py). Read → close → rewrite from memory.
