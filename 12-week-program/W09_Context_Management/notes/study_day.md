# W09 Study Day — Context Management & Reliability (Domain 5.1–5.3)

## The one thing to internalize

**Long sessions silently lose the things that matter most — numbers, dates, identifiers — unless you hold them outside the summarizable conversation.** The `case_facts` block is not a prompt technique; it is a data structure your agent code maintains and re-injects every turn. Everything else in this week (position-aware ordering, trimmed tool outputs, structured errors, real escalation triggers) is downstream of this same principle: keep the critical stuff where attention actually looks, and make failure legible.

## Progressive summarization, in one sentence

Summarizing history keeps the gist and drops the numbers — which is precisely backwards for support work. Use `case_facts` for durable values, let summarization touch only the dialogue.

## Case facts block — what goes in it

A JSON structure maintained by your agent code, updated every turn, re-injected at the top of every context:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "C-77",
  "issue_type": "defective_product",
  "amount_usd": 149.00,
  "purchase_date": "2026-04-11",
  "delivery_date": "2026-04-15",
  "policy_references": ["refund_window_30d", "loyalty_override_60d"],
  "agreed_actions": ["full_refund_approved"]
}
```

Rule: if a field would be lost if a human paraphrased the transcript, it belongs here.

## Lost in the middle — position-aware ordering

Attention on long contexts is not uniform. Best attention sits at the **start** and the **end**. Content buried in the middle is the most likely to be under-weighted.

The fixes:
1. Put `case_facts` at the top of the system message, under a `## CURRENT CASE FACTS` header.
2. Repeat `case_facts` at the end (trailing user message or system reminder).
3. Use section headers the model can locate content by.

**Wrong fix:** a bigger context window. Degradation in the middle is about how attention works, not capacity.

## Trim verbose tool outputs

Backend returns 40 fields. The agent needs 5. Trim at the tool wrapper, *before* appending to history. Dumping full raw JSON into context is paid every turn (because history is append-only) and dilutes attention for no benefit.

## Escalation — the three correct triggers

1. **Explicit customer request.**
2. **Identified policy gap** — not "I don't know", but "policy has no rule for this".
3. **Inability to progress after concrete attempts** — two+ specific actions tried and blocked.

Each is observable from the conversation and tool trace.

## Escalation — the distractors

- Sentiment ("customer sounds frustrated") — sentiment ≠ complexity.
- Self-reported confidence 1–10 — miscalibrated, worst exactly when it matters.
- "The model hedged in its reply" — probabilistic output, not a signal.
- Response length or tool-call count — too weakly correlated.

**Principle:** escalation triggers must be observable, deterministic, tied to concrete failure. Everything else is noise.

## Multiple matches — ask, don't guess

Tool returns 3 candidate orders for an ambiguous query → ask the customer for a distinguishing identifier (exact date, last 4 of card, item name) and re-query. Never heuristically pick one. Heuristic resolution of identity ambiguity is where silent failures compound.

## Error propagation — the shape that works

```python
{
    "failure_type": "timeout",               # categorical
    "attempted_query": {"order_id": "..."},  # what was tried
    "partial_results": [...],                # whatever was gathered
    "alternatives": ["retry", "ask_user"],   # recovery options
}
```

Two anti-patterns:
- **Generic `"operation failed"`** — kills recovery, no information to act on.
- **Empty result on timeout** — indistinguishable from "no matches"; silent failure.

## Coordinator vs subagent error flow

- Subagent hits an error → reports structured error upward. Never swallows. Never escalates directly.
- Coordinator sees the structured error and decides: retry / try alternative / annotate coverage gap / escalate.
- Partial results are valuable — return the 7 you got, flagged partial, don't drop everything.

## Local recovery before escalation

Order of moves when something fails:
1. Retry transient errors (timeout, rate limit) — bounded, 1–2 tries.
2. Try an alternative query / identifier / tool.
3. Ask the user for clarification if the ambiguity is on their side.
4. **Then** escalate, if none of the above resolved it.

Escalating on the first hiccup is as wrong as retrying forever.

## 3-bullet recap

- `case_facts` block is the durable-values store: updated per turn, re-injected every turn, survives summarization; numbers/dates/IDs live here, not in the dialogue history.
- Position-aware ordering (start + end, section headers) plus trimming tool outputs to 5 relevant fields are how you keep attention on what matters — bigger windows don't fix middle-of-context degradation.
- Escalate only on explicit customer request, identified policy gap, or inability-to-progress after concrete attempts; never on sentiment or self-reported confidence. Errors travel as structured `{failure_type, attempted_query, partial_results, alternatives}` blocks — subagents report up, coordinators decide.
