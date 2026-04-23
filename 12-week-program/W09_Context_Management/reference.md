# W09 Reference — Context Management & Reliability (Domain 5.1–5.3)

Complete, self-contained study material for Week 9. Read this end-to-end. Every concept the exam tests for task statements 5.1–5.3 is included here.

Prerequisites: W01 (agentic loop), W02 (coordinator/subagent pattern), W04 (structured tool errors). This week is about keeping long-running agents reliable — preserving facts across many turns, deciding when to escalate, and propagating errors between agents without silent failures.

---

## 1. Why context management is its own domain

The agentic loop from W01 assumes you keep *all* history. That works for 5 turns. It does not work for 50.

Long sessions hit three failure modes:

1. **Context bloat** — tool outputs, intermediate reasoning, old user messages all accumulate. Eventually you hit the window cap, or the model starts paying attention to the wrong things.
2. **Progressive summarization loss** — if you ask the model to summarize older turns to save tokens, it keeps the *gist* and silently drops the *numbers*. Order IDs, dollar amounts, dates, SKU codes, policy references — gone.
3. **Attention degradation in the middle** — long windows don't mean uniform attention. Content in the middle of the context gets less weight than content near the top or bottom. This is the "lost in the middle" effect and it is empirical, not theoretical.

Context management is the set of techniques that keep the agent usable across long interactions without quietly losing critical data.

---

## 2. Progressive summarization — why it loses the things that matter

The naive token-saving strategy is: every N turns, ask the model to summarize the conversation so far and replace the raw history with the summary.

This saves tokens. It also deletes precisely the information a support agent needs to act:

- "Refund $149.00 on ORD-1001 delivered 2026-04-15" → summarized to "customer asked about a refund for their headphones".
- "Policy override applies for LTV > $1,000" → summarized to "we discussed the policy".
- "Customer confirmed shipping address 221B Baker St" → dropped entirely.

The model doesn't summarize *identifiers* and *amounts* because those aren't where the semantic content is. It summarizes the *meaning*. The numbers are the thing you cannot afford to lose.

### The fix: a persistent `case_facts` block

Keep a separate, structured block of durable values outside the summarizable conversation. Update it per turn. Re-inject it at the top of every turn. Summarization affects the dialogue; the `case_facts` block survives intact.

```python
case_facts = {
    "order_id": "ORD-1001",
    "customer_id": "C-77",
    "issue_type": "defective_product",
    "amount_usd": 149.00,
    "purchase_date": "2026-04-11",
    "delivery_date": "2026-04-15",
    "policy_references": ["refund_window_30d", "loyalty_override_60d"],
    "agreed_actions": ["full_refund_approved"],
}
```

This is the structure the exam refers to when it says "extract case facts". It is not a prompt technique — it is a data structure you maintain in your agent code and inject every turn.

**Rule:** if a field could be lost if a human paraphrased the transcript, it belongs in `case_facts`.

---

## 3. Lost-in-the-middle — position-aware ordering

When you stuff 50 turns of history plus a 2 kB system prompt into a single request, the model's effective attention is not uniform. Empirically:

- Content at the **start** of the context is well-attended.
- Content at the **end** of the context is well-attended.
- Content in the **middle** is the most likely to be skipped or under-weighted.

### What to do about it

1. **Put the `case_facts` at the start of the system message** — above the role description, above the tool instructions. Use a clear section header like `## CURRENT CASE FACTS`.
2. **Repeat the `case_facts` at the end of the conversation** as part of the latest user turn, or as a trailing system reminder. Yes, literally twice. Start and end.
3. **Use section headers** (`## POLICY`, `## CASE FACTS`, `## CUSTOMER MESSAGE`) so the model can locate content by structure, not by reading linearly.
4. **Do not assume the model will "find" a fact buried in turn 17 of a 40-turn history.** If it matters, surface it.

### Exam distractor

"Increase the context window to fix attention degradation" — **wrong**. A bigger window gives you more room, not better attention quality. Degradation in the middle is a property of how the model attends, not of how much it can hold. The fix is positional (start/end) and structural (headers), not capacity.

---

## 4. Trimming verbose tool outputs

A `get_order` call might return a 40-field JSON blob: line items, tax breakdown, shipping events, tracking history, internal flags, fulfillment timestamps, warehouse codes. For deciding a refund, you need 5 of those fields. The other 35 are noise that:

- Eats tokens (each reappears every turn, forever, because you append history).
- Dilutes attention across irrelevant content.
- Makes the case harder to reason about — for the model *and* for a human reading the trace.

### The pattern

In your tool-execution wrapper, trim the tool output to the fields the agent actually needs *before* appending it as `tool_result`:

```python
RELEVANT_ORDER_FIELDS = {"order_id", "amount_usd", "status", "delivered_at", "item"}

def run_get_order(order_id):
    raw = backend.fetch_order(order_id)       # 40 fields
    return {k: raw[k] for k in RELEVANT_ORDER_FIELDS if k in raw}  # 5 fields
```

The model never sees the other 35 fields. The history stays small. If a later turn needs one of the dropped fields, you add it to the trim set — an explicit, reviewable change.

**Rule of thumb:** if you wouldn't put it in a case summary you'd hand to a supervisor, don't put it in the context.

### Exam distractor

"Dump the full raw tool output into history for completeness" — **wrong**. The cost is paid every turn, the benefit is zero, and attention gets worse. Trim at the boundary.

---

## 5. Escalation triggers — the correct ones

When a support agent can't resolve a case, it escalates to a human. The exam probes *which signals should trigger escalation* and consistently rewards the same three:

1. **Explicit customer request.** The customer said "I'd like to speak to a human" (or equivalent). Non-negotiable; route them.
2. **Identified policy gap.** The customer's situation is not covered by existing policy. Not "the model doesn't know" — the *policy itself* has no provision. Example: the refund policy covers defective products and wrong items but not "changed my mind after 45 days"; a 45-day change-of-mind request is a policy gap.
3. **Inability to progress after concrete attempts.** The agent has tried at least two specific actions (alternative query, different identifier, clarifying question) and is still blocked. Not "I feel stuck" — "I called these tools, got these structured errors, and have no other route."

These are the reliable triggers because each one can be observed from the conversation and the tool trace without relying on vibes.

---

## 6. Escalation NON-triggers — the distractors

The exam deliberately tempts you with escalation signals that *feel* right but are unreliable:

| Wrong trigger | Why it's wrong |
|---|---|
| **Sentiment analysis** — "the customer sounds frustrated" | Sentiment ≠ case complexity. Frustrated customers often have simple cases. Calm customers sometimes have hard ones. Sentiment is noise for escalation. |
| **Model self-reported confidence (1–10 scale)** | LLM self-confidence is **miscalibrated**, especially on hard cases. Often the model is most confident exactly where it's wrong. Asking "rate your confidence 1–10" returns a number with no predictive value. |
| **"The model said it was unsure"** | The phrasing "I think" or "I'm not sure" in the response is probabilistic output, not a reliable signal. |
| **Response length** ("long replies mean the agent is struggling") | Correlation is too weak to be a trigger. |
| **Number of tool calls** ("too many calls = stuck") | Legitimate multi-tool tasks take many calls. This signal fires on healthy behavior. |

**The principle:** escalation triggers must be **observable, deterministic, and tied to concrete failure**. Customer said it, policy has no rule, or N attempts failed. Everything else is a distractor.

---

## 7. Multiple matches — never heuristically pick one

A lookup tool returns 3 candidate orders for an ambiguous query ("my recent order"). The wrong moves:

- Pick the first one. (You don't know it's the right one.)
- Pick the one with the largest amount. (Heuristic, not evidence.)
- Pick the most recent. (Same — a guess.)
- Pick one and ask the customer to confirm *after* taking an action on it. (Confirmation is too late if you've already initiated a refund on the wrong order.)

The correct move: **surface the ambiguity, ask the customer for a distinguishing identifier** — order ID, exact date, last four digits of the card, item name — and re-query with the narrower criteria.

This generalizes: whenever a tool returns N > 1 candidates for an entity that must be uniquely identified before an action, ask the user to disambiguate. Don't guess.

### Exam distractor

"Have the agent pick the most likely match based on a heuristic" — **wrong**. Heuristic resolution of identity ambiguity is exactly the place silent failures compound.

---

## 8. Error propagation — structured context, not generic strings

When a tool fails (timeout, not found, rate limited, invalid input), what comes back into the agent's context determines whether it can recover.

### Anti-pattern A — generic "operation failed"

```json
{"error": "operation failed"}
```

This kills recovery. The agent has no information to act on. It cannot tell whether to retry, try an alternative, ask the user, or escalate.

### Anti-pattern B — silent suppression / empty result

```json
{"results": []}
```

On a timeout, returning an empty result set *looks* like a successful "no matches" response. The caller cannot distinguish "there are no matching orders" from "I failed to reach the database." Silent failures here propagate into wrong decisions (e.g., "no orders found → maybe the customer is lying").

### The correct shape

Return structured context the caller can reason about:

```python
{
    "failure_type": "timeout",              # categorical, actionable
    "attempted_query": {"order_id": "ORD-?"},   # what you tried
    "partial_results": [],                  # anything you did get before failing
    "alternatives": ["retry", "ask_user_for_date"],  # suggested next moves
}
```

Now the agent (or the coordinator) can decide: retry the same call? Try an alternative identifier? Ask the user? Escalate? All three questions need the structured context to answer.

The exam consistently rewards the structured shape and punishes both generic errors and silent suppression.

---

## 9. Coordinator vs subagent error flow

In a multi-agent system (W02), error propagation has an extra hop.

A subagent hits an error. It does **not** decide for itself whether to escalate, retry indefinitely, or abandon the task. It reports a **structured error upward** to the coordinator:

```
Subagent → Coordinator:
{
    "status": "failed",
    "failure_type": "source_unavailable",
    "attempted_query": "...",
    "partial_results": [...],
    "alternatives": ["retry_different_source", "proceed_without_this_data"],
}
```

The coordinator then decides:
- **Try an alternative** — dispatch the subagent again with a different approach.
- **Annotate a coverage gap** in the final report — proceed with what was gathered, mark the gap explicitly.
- **Escalate** — if the coordinator-level criteria are met (explicit request, policy gap, inability to progress after attempts).

### Rules for this flow

1. **Subagents never swallow errors.** Silent failures look like success and mislead the coordinator.
2. **Subagents don't escalate directly to humans.** They report upward; the coordinator has the scope to decide.
3. **Coordinators never treat an empty result as success** without checking the structured status.
4. **Partial results are valuable** — a subagent that got 7 of 10 items and then failed should return the 7, flagged as partial, not throw everything away.

### Exam distractor

"If a subagent fails, the coordinator should retry forever until it succeeds." — **wrong**. Retry is a local recovery move (see §10), and only for certain `failure_type`s (transient like timeout). Non-transient failures (e.g., "source returned 404") don't improve by retrying.

---

## 10. Local recovery before coordinator escalation

Before the coordinator escalates, the subagent (and the agent loop itself) should try local recovery:

1. **Retry transient failures** — timeout, rate limit. Once or twice, with backoff. Then stop.
2. **Try an alternative query** — different identifier, different tool, different phrasing of the request.
3. **Ask the user for clarification** — if the ambiguity is on the user side (missing order ID, which account).

Only after these concrete local attempts fail does the path go: subagent → coordinator → (escalate or annotate gap).

The anti-pattern here is jumping straight to escalation on the first hiccup. Real production agents recover from most failures locally; escalation should be the last resort, not the first reflex.

The opposite anti-pattern is retrying forever: once you've tried two alternatives, stop. Unbounded retries turn a recoverable error into a hung session.

---

## 11. Anti-patterns table (exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| "Increase the context window to fix attention degradation" | Attention quality doesn't scale with window size | Use position-aware ordering (start/end) + section headers |
| "Summarize history aggressively to save tokens" | Loses numbers, dates, identifiers silently | Extract durable values into a persistent `case_facts` block |
| "Use sentiment analysis to trigger escalation" | Sentiment ≠ case complexity; frustrated ≠ hard | Trigger on explicit request, policy gap, or failure-to-progress |
| "Ask the model to self-rate confidence 1–10" | LLM self-confidence is miscalibrated, especially when wrong | Use deterministic signals: tool errors, policy coverage, attempt count |
| "Heuristically pick the most likely match out of N candidates" | Guessing identity ambiguity silently corrupts actions | Ask the user for a distinguishing identifier |
| "Return a generic 'operation failed' error" | Kills recovery — caller has no information | Return `{failure_type, attempted_query, partial_results, alternatives}` |
| "On timeout, return empty results as if successful" | Caller can't tell "no matches" from "I failed" | Structured error with `failure_type: "timeout"` |
| "Dump the full raw tool output (40 fields) into history" | Eats tokens every turn, dilutes attention | Trim to the 5 relevant fields at the boundary |
| "Subagent decides on its own whether to escalate to a human" | Subagent doesn't have full task scope | Subagent reports structured error up; coordinator decides |
| "Retry a failing tool forever with exponential backoff" | Doesn't help when the info is absent | Bounded retries for transient errors only; escalate after |
| "Escalate immediately on the first tool failure" | Skips cheap local recovery | Try alternative query, different identifier, clarify with user first |

The top three rows recur every exam. The bottom rows are scenario-specific but hit reliably in support-agent and multi-agent questions.

---

## 12. What the exam will probe

- A long support conversation drops an order ID / dollar amount after summarization; pick the fix (`case_facts` block, not a bigger window).
- Key fact buried in turn 20 of a 40-turn context; the model "forgets" it; pick the fix (surface it at the start AND end, with a header).
- Tool returns 40 fields; pick the right thing to do (trim at the boundary, not ask the model to "ignore" extra fields).
- Scenario: "customer sounds frustrated, escalate?" — correct answer is **no**, sentiment is not a trigger; escalate on explicit request / policy gap / failure-to-progress.
- Scenario: "the model rated its confidence as 3/10, escalate?" — correct answer is **no**, self-reported confidence is miscalibrated.
- Multiple-match scenario: 3 candidate orders; correct move is **ask for identifiers**, not heuristically pick.
- Tool timeout scenario: what does the tool return? Structured `{failure_type, ...}`, not generic or empty.
- Subagent fails partway through: who decides next step? **Coordinator**, via structured error, not the subagent by itself.
- Distinguishing local recovery (retry once, alternative query, ask user) from escalation (after local recovery exhausted).

---

## 13. Fast recap

- **Case facts block.** Persistent JSON of durable values (IDs, amounts, dates, agreed actions). Update per turn. Re-inject every turn. Survives summarization.
- **Lost in the middle.** Put critical facts at the start AND end of context. Use section headers. Do not rely on the model finding facts buried mid-history. A bigger window does not fix this.
- **Trim tool outputs.** Keep the 5 fields the agent needs, not the 40 the backend returns. Trim at the boundary, before the result enters history.
- **Escalate on real signals:** explicit customer request, policy gap, inability to progress after concrete attempts. Never on sentiment, self-reported confidence, or vibes.
- **Multiple matches → ask for identifiers.** Never heuristically resolve identity.
- **Errors are structured.** `{failure_type, attempted_query, partial_results, alternatives}`. Never generic "operation failed"; never silent empty-result-on-timeout.
- **Coordinator decides, subagent reports.** Subagents never swallow errors and never escalate directly. Structured error goes up; coordinator chooses to retry / try alternative / annotate gap / escalate.
- **Local recovery first.** Retry (bounded) → alternative query → ask user → then escalate.

When you can explain each of those eight bullets out loud in ~20 seconds each, you're ready for the W09 test.
