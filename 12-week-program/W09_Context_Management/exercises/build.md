# Build — Context Management

**Time:** 40 min · **Goal:** Build a support-loop skeleton that maintains a persistent `case_facts` dict, trims tool output at the boundary, and escalates only on valid triggers (explicit request / policy gap / inability to progress).

## What you'll have at the end
- `exercises/my_support_loop.py` — runnable loop with `case_facts` injected start + end of context, trimmed `get_order` output, and a `should_escalate()` gate keyed on valid triggers only.
- A 15-turn simulated session trace showing IDs/amounts surviving a summarize-style drop and escalation firing on a policy gap (not on sentiment).

## Prereqs
- Python 3.10+, no API key needed (summarizer and tools are local stubs).
- Finished reading [reference.md](../reference.md) §2–§7
- Target: `exercises/my_support_loop.py` (peek at [minimal_case_facts.py](minimal_case_facts.py) if stuck)

## Steps

### 1. Define the `case_facts` shape (~5 min)
Create the durable-values dict *before* writing any loop logic. If a human paraphrasing the transcript would lose it, it goes here.
- [ ] Define `case_facts = {'customer_id': None, 'order_id': None, 'amount_usd': None, 'purchase_date': None, 'delivery_date': None, 'policy_references': [], 'agreed_actions': [], 'confirmation_id': None}`
- [ ] Write a `render_case_facts(facts) -> str` that returns a `## Case facts (do not lose)` section with the JSON dump underneath.

**Why:** §2 — summarization drops identifiers and amounts; `case_facts` sits outside the summarizable dialogue.
**Checkpoint:** `render_case_facts({})` returns a string starting with `## Case facts (do not lose)`.

### 2. Build the context assembler with start + end injection (~5 min)
The assembler is the one place that builds the model-facing context each turn. Facts go at the top *and* the bottom.
- [ ] Write `build_context(system, facts, history_summary, latest_user_msg)` that concatenates: `case_facts block` → `system` → `## Policy` → `history_summary` → `## Customer message` → `latest_user_msg` → `case_facts block` (again).
- [ ] Use explicit section headers so the model locates content by structure.

**Why:** §3 — lost-in-the-middle is positional; surface critical facts at start AND end, with headers. A bigger window does not fix it.
**Checkpoint:** Print a context; the `case_facts` string appears twice and section headers are visible.

### 3. Trim tool output at the boundary (~6 min)
Write one tool wrapper that reduces a 40-field payload to the 5 the loop needs. The history never sees the other 35.
- [ ] Stub `backend_fetch_order(order_id)` returning a dict with ~10 keys (order_id, amount_usd, status, delivered_at, item, tax, warehouse_code, shipping_events, internal_flags, fulfillment_ts).
- [ ] In `run_get_order(order_id)`, define `RELEVANT = {"order_id","amount_usd","status","delivered_at","item"}` and return only those keys.
- [ ] Have the loop call `run_get_order`, never the backend directly.

**Why:** §4 — trimmed output shrinks per-turn cost, stops attention dilution, and keeps the trace readable. Asking the model to "ignore" extra fields is the wrong fix.
**Checkpoint:** `run_get_order("ORD-1001")` returns exactly 5 keys.

### 4. Update `case_facts` after every tool call and user turn (~5 min)
The block is only useful if it's current. Update it each loop iteration, before building the next context.
- [ ] After each `run_get_order` result, merge its fields into `case_facts` (order_id, amount_usd, delivery_date from `delivered_at`).
- [ ] After each customer/agent turn, extract IDs/dates/policy refs and write them in (regex is fine for the demo).
- [ ] Append entries to `agreed_actions` when a refund/replacement/credit is approved.

**Why:** §2, §13 — the block must reflect the latest turn; stale facts are worse than none.
**Checkpoint:** After turn 5 of your simulated session, `case_facts['order_id']` and `amount_usd` are both populated.

### 5. Implement `should_escalate(trace)` with valid triggers only (~7 min)
Three signals, nothing else. Each must be observable from the conversation or tool trace.
- [ ] Trigger 1 — explicit request: regex on user text for `speak to (a )?human|agent|manager|representative`.
- [ ] Trigger 2 — policy gap: a flag `trace['policy_gap'] = True` set when no policy rule in `case_facts['policy_references']` covers the request (e.g. 45-day change-of-mind against a 30-day window).
- [ ] Trigger 3 — inability to progress: counter of distinct concrete attempts (alternative query, different identifier, clarifying question); fire when `attempts >= 2` and still blocked.
- [ ] Explicitly reject non-triggers: do NOT read sentiment, do NOT ask the model "rate your confidence 1–10", do NOT count tool calls or response length.

**Why:** §5–§6 — valid triggers are observable and deterministic; sentiment and self-rated confidence are miscalibrated distractors the exam repeatedly tests.
**Checkpoint:** A turn with the text "I'm SO frustrated!!" alone does not escalate; a turn declaring a 45-day change-of-mind request does.

### 6. Handle multiple matches by asking for an identifier (~5 min)
When a lookup returns N > 1 candidates, never heuristically pick one. Ask the user to disambiguate and re-query.
- [ ] Stub `search_orders(customer_id)` returning 3 candidates for an ambiguous query.
- [ ] In the loop, if `len(results) > 1`, emit a turn asking for order ID / exact date / last-4 of card, and do NOT take any action yet.
- [ ] Re-query with the narrower criterion on the next user turn.

**Why:** §7 — heuristic resolution of identity ambiguity silently corrupts downstream actions; asking is the only safe move.
**Checkpoint:** Running the loop on an ambiguous query produces a clarifying question, not a refund initiation.

### 7. Run a 15-turn simulated session (~7 min)
Script a scenario that exercises the three mechanisms in one run.
- [ ] Turns 1–6: normal refund flow populating `case_facts` (ORD-1001, $149.00, delivered 2026-04-15, `refund_window_30d`).
- [ ] Turns 7–10: pass history through a lossy summarizer (strip IDs/amounts from the dialogue); assert `case_facts` still has `order_id` and `amount_usd`.
- [ ] Turns 11–13: customer raises a 45-day change-of-mind request; set `policy_gap=True`; assert `should_escalate()` returns True.
- [ ] Turns 14–15: control — customer sounds frustrated but no policy gap; assert `should_escalate()` returns False.

**Why:** §12 — these are the exam-probe shapes (summarization drop, policy-gap escalation, sentiment non-trigger) in one trace.
**Checkpoint:** Session prints 4 `assert` passes and a final `case_facts` JSON with all values intact.

## Verify
Run a 15-turn simulated session that includes a policy-gap case. Expected:
- `case_facts['order_id'] == 'ORD-1001'` and `amount_usd == 149.00` *after* the summarizer has wiped them from the dialogue text.
- `should_escalate()` returns True on the 45-day change-of-mind turn; returns False on the "sounds frustrated" turn.
- `run_get_order("ORD-1001")` output has exactly 5 keys in the trace.
- The assembled context string contains the `## Case facts (do not lose)` header twice.

**Common mistakes:**
- Summarizing away identifiers because you only keep history, not `case_facts` → §2.
- Putting `case_facts` only at the top, not the bottom → §3.
- Escalating when the customer "sounds frustrated" → §6.
- Asking the model to self-rate confidence 1–10 and branching on it → §6.
- Heuristically picking the most recent of 3 candidate orders → §7.
- Dumping the full 40-field order payload into history → §4.

## Stretch — Polish block (30 min on Practice Day)
Demo error propagation: structured context vs generic errors.
- [ ] Add `run_get_order_with_timeout(order_id, simulate="timeout")` that returns `{"failure_type":"timeout","attempted_query":{"order_id":order_id},"partial_results":[],"alternatives":["retry","ask_user_for_date"]}` instead of raising or returning `{}`.
- [ ] Show the caller branching on `failure_type`: `timeout` → bounded retry (once), then alternative query; `not_found` → ask user for a different identifier; `policy_gap` → escalate.
- [ ] Add a second variant that returns `{"error":"operation failed"}` and a third that returns `{"results":[]}` on timeout. Show both kill recovery (no branch has enough info to act) — this is the distractor the exam rewards you for rejecting.
- [ ] Write 3 lines of output per variant: input → tool return → caller decision.

## If stuck
Compare with [minimal_case_facts.py](minimal_case_facts.py). Read → close → rewrite.
