# W09 Walkthrough — `real_world_long_support_session.py`

This companion doc walks through the scripted 15+ turn support session turn by turn and maps each decision to the W09 exam concepts. Read it alongside the Python file.

The run goes through a complete defective-headphones refund case that deliberately hits every Domain 5.1–5.3 decision point:

- multiple-match disambiguation,
- tool timeout recovery,
- policy-gap escalation,
- structured error shapes,
- case-facts preservation,
- and rejection of the two biggest distractor signals (sentiment, self-reported confidence).

---

## Turn-by-turn

### Turn 0 — Customer message contains "frustrated"

> *"Hi, my headphones stopped working after a week. I'm really frustrated — this is the second time..."*

**Agent behavior:** asks for customer ID and order. Does **not** escalate.

**Exam mapping:**
- "Customer sounds frustrated" is **not** a valid escalation trigger. Sentiment ≠ case complexity. The word `frustrated` is in the transcript precisely so you can verify the agent ignores it under the default (correct) flags. Flip `bad_use_sentiment=True` to see the distractor path fire.
- `case_facts.issue_type` is tentatively updated to `defective_product` from the "stopped working" phrasing (see `agent_step`, later turn).

### Turn 2 — Customer says "my recent order"

> *"I'm customer C-77. It was my recent order — the wireless headphones I think."*

**Agent behavior:** Populates `case_facts.customer_id = "C-77"`. Calls `search_orders(customer_id="C-77", hint="recent")`.

**Exam mapping:**
- Durable values (`customer_id`) go into the case_facts block as soon as they're known. They're re-injected at the top AND the bottom of every subsequent context (`render_context`).
- The tool returns **trimmed** records (5 fields) even though the backend carries 40+. The trimming happens in `tool_search_orders`, not downstream. The model never sees the 35 noise fields.

### Turn 3 — Tool returns 3 candidate orders

**Agent behavior:** Does **not** pick one. Asks the customer for a distinguishing identifier (order ID, item name, or exact purchase date).

**Exam mapping:**
- The "multiple matches → ask for identifier" rule. Heuristically picking one (e.g., the most recent, or the highest-value) is an exam distractor that corrupts action silently.

### Turn 5 — Customer supplies ORD-1001

**Agent behavior:** Calls `get_order` with a simulated timeout flag on (`get_order_with_timeout`). The tool returns a **structured error**:

```json
{
  "failure_type": "timeout",
  "attempted_query": {"order_id": "ORD-1001"},
  "partial_results": [],
  "alternatives": ["retry_same_call", "search_orders_by_customer_id", "ask_user_for_alternate_identifier"]
}
```

**Exam mapping:**
- Not `{"error": "operation failed"}` (generic), not `{"results": []}` (silent empty). The shape itself is the answer the exam rewards.
- Crucial: an empty `results: []` on a successful call would be indistinguishable from "no matches". The `failure_type: "timeout"` field is the signal that makes the two cases distinguishable.

### Turn 6 — Local recovery (retry once)

**Agent behavior:** Retries the same call (this time `get_order` without the timeout flag). Appends `"get_order:timeout"` to `escalation.failed_attempts`.

**Exam mapping:**
- **Local recovery before escalation.** The agent does not jump straight to escalation on the first hiccup. It tries a bounded retry first. If the retry had also failed, the next move would be an alternative query (e.g., re-search by customer_id), then ask the user, *then* escalate.
- Counting attempts in `failed_attempts` is what makes "inability to progress after 2+ concrete attempts" an observable, deterministic trigger — not a vibe.

### Turn 7 — Successful fetch, populate case facts

`case_facts` now carries:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "C-77",
  "issue_type": "defective_product",
  "amount_usd": 149.00,
  "purchase_date": "2026-04-11",
  "delivery_date": "2026-04-15"
}
```

**Exam mapping:**
- The order amount (`149.00`) and the dates are the exact kind of values naive progressive summarization loses. Held in `case_facts`, they survive every turn — and thanks to `render_context`, they appear at the **start** *and* the **end** of the prompt every single turn ("lost in the middle" mitigation).

Agent then calls `check_policy(reason="defective_product", days_since_purchase=12)`.

### Turn 8 — Policy confirms eligibility

Agent appends `refund_window_30d` to `case_facts.policy_references` and `full_refund_approved` to `case_facts.agreed_actions`. Replies with a warm confirmation to the customer.

**Exam mapping:**
- Policy references and agreed actions are both case-facts fields because they're the kind of thing a follow-up turn must know verbatim.

### Turn 10 — Policy gap

> *"Also — can you waive the restocking fee on a different old order from last year too?"*

This reason isn't in `POLICY["covered_reasons"]`. The agent sets `escalation.policy_gap_detected = True` and escalates.

**Exam mapping:**
- **Policy gap** is a valid escalation trigger — distinct from "I don't know" or "I'm unsure". The *policy* has no rule for this, which is observable.
- The primary refund for ORD-1001 ($149.00) is **not** rolled back on escalation. The resolved part of the case stays resolved; only the un-covered part is handed off. Preserves progress; avoids the "all-or-nothing" anti-pattern.

### Turn 12 — Confirmation and clean handoff

Agent sets `case_facts.confirmation_id = "RF-1001"` and sends a final reply that:
- References the exact amount ($149.00) and order ID (ORD-1001) — these come from `case_facts`, not from recall of turn 7.
- Notes the human handoff for the uncovered request.

**Exam mapping:**
- Because `case_facts` is re-injected every turn, the agent's *final* message can still cite specific values from turn 5 without relying on those values surviving somewhere in the middle of history. This is the whole point of the case-facts pattern.

---

## The escalation decision, summarized

```python
class EscalationState:
    explicit_customer_request: bool   # VALID
    policy_gap_detected: bool         # VALID
    failed_attempts: list[str]        # VALID when len >= 2
```

Three triggers. All observable. All deterministic.

**Deliberately absent:**
- `customer_sentiment_score` — *wrong*, sentiment ≠ complexity.
- `model_self_confidence` — *wrong*, miscalibrated.
- `response_length`, `tool_call_count` — too weakly correlated.

The `bad_use_sentiment` and `bad_use_self_confidence` flags in the code exist so you can turn on the wrong triggers and watch the agent escalate on turn 0 (just because the customer typed "frustrated") or on every turn where the dice roll a low number (simulating self-rated confidence). That's the distractor behavior the exam asks you to reject.

---

## Structured error propagation

Every tool wrapper in this file returns the same shape, even on success:

```python
{
    "failure_type": None | "timeout" | "not_found" | "policy_gap",
    "attempted_query": { ... },
    "partial_results": [ ... ],
    "alternatives": [ ... ],
}
```

This means:

- The caller checks `failure_type is None` to decide success, not the length of `partial_results`. (A legitimate zero-result response would have `failure_type: None` and `partial_results: []`; a failure would have a non-null `failure_type`.)
- On failure, the caller has a categorical `failure_type` and a concrete `alternatives` list — it can route to retry, alternative query, or escalation without guessing.
- Partial results are preserved when available, not discarded. A subagent that got 7 of 10 items and then failed returns the 7.

In a multi-agent system this same shape travels from subagent to coordinator. The coordinator inspects `failure_type` and decides whether to retry, try an alternative subagent, annotate a coverage gap, or escalate. **The subagent never escalates directly to a human**, and never swallows an error into a silent success.

---

## Variations to try

These modifications take seconds and make the exam-critical rules vivid:

1. **Enable sentiment-triggered escalation.** In `__main__`, uncomment the BAD-MODE block and re-run. The agent will escalate on turn 0 because "frustrated" appears in the first message. Contrast with the default run, where the same word is correctly ignored.

2. **Enable self-confidence-triggered escalation.** Pass `bad_use_self_confidence=True` to `run_session`. The agent will escalate on whatever turn the random confidence roll lands below 5. Random, unrelated to actual case progress — exactly what the "confidence is miscalibrated" distractor warns against.

3. **Remove the `case_facts` block.** Comment out the two `case_facts.render_block()` calls in `render_context`. The turn-by-turn trace still prints, but if you imagine a real LLM reading that context, the order IDs, amounts, and dates are now only visible inside tool-result history lines that pile up in the *middle* of the context — the worst place. Position-aware ordering exists for exactly this reason.

4. **Stop trimming tool outputs.** In `tool_get_order`, replace the `trimmed = {...}` line with `trimmed = raw`. Every turn now appends a 40-field bloat to history. Token cost compounds linearly; the model has to skim past warehouse codes, carrier events, analytics tags, and A/B cohort assignments every iteration. Attention quality suffers even if nothing visibly breaks. This is what the "dump full output into history" anti-pattern actually looks like.

5. **Change a tool failure to a generic error.** Replace the structured timeout response with `{"error": "operation failed"}`. Observe that the agent has nothing to act on — no `failure_type` to branch on, no `alternatives` to try. Recovery logic dies at this boundary. This is the single most punished error-propagation anti-pattern on the exam.

6. **Make the "multiple matches" branch pick one.** At turn 3, replace the "ask for distinguishing identifier" reply with "I'll work on your most recent order." See how silently this corrupts everything downstream if the customer's intent was a different order.

Each variation is a one-line change that produces a distinct failure mode the exam asks about explicitly.

---

## Concept-to-code index

| Exam concept | Where in the file |
|---|---|
| Case facts block (durable values) | `CaseFacts` dataclass + `render_block()` |
| Position-aware ordering (start + end) | `render_context` — `render_block()` appears twice |
| Section headers | `render_context` — `## ROLE`, `## POLICY`, `## CONVERSATION HISTORY`, `## LATEST CUSTOMER MESSAGE`, `## CURRENT CASE FACTS` |
| Trimmed tool outputs | `RELEVANT_ORDER_FIELDS` + `tool_get_order` / `tool_search_orders` |
| Structured error shape | every tool wrapper returns `{failure_type, attempted_query, partial_results, alternatives}` |
| Valid escalation triggers | `EscalationState.should_escalate()` |
| Distractor triggers (rejected) | `bad_use_sentiment` and `bad_use_self_confidence` flags |
| Multiple-match → ask for identifier | turn 3 in `agent_step` |
| Local recovery before escalation | turn 6 — retry after timeout; `failed_attempts` tracked |
| Policy gap → escalate | turn 10 in `agent_step` + `tool_check_policy`'s `"policy_gap"` failure type |
| Case facts drive the final customer reply | turn 12 — message cites `$149.00` and `ORD-1001` from `case_facts` |
