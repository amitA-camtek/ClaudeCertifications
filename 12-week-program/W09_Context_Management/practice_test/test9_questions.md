# Practice Test 9 — Context Management

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 5.1–5.3

## Instructions
Solve all 10 questions before opening `test9_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A support agent runs for 50 turns. Every 10 turns, the developer asks the model to summarize prior history and replaces the raw turns with that summary to save tokens. After 40 turns, the agent recommends a refund for the wrong order amount. What is the root cause and the correct fix?
- A. The context window was too small; migrate to a model with a larger window.
- B. Progressive summarization silently dropped identifiers and amounts; extract durable values into a persistent `case_facts` block and re-inject every turn.
- C. The system prompt was too short; add more role instructions to anchor the agent.
- D. The model's temperature was too high; lower it to reduce hallucination of amounts.

### Q2. In a 40-turn conversation, a critical policy override was mentioned in turn 17. The agent now ignores it when producing the final action. Which explanation and fix best match the reference?
- A. The model forgot because it has no memory across turns; enable memory retention via a vector DB.
- B. "Lost in the middle" — attention is weakest for mid-context content; surface the fact at the start AND end of the context with section headers.
- C. The response was truncated; increase the max output tokens.
- D. Any long history is unreliable; summarize every turn aggressively so nothing gets buried.

### Q3. Which of the following is NOT a reliable escalation trigger per the reference?
- A. The customer explicitly asks to speak with a human.
- B. The customer's situation is not covered by any existing policy (policy gap).
- C. The model self-reports its confidence as 3/10.
- D. The agent has tried two concrete alternative actions and is still blocked.

### Q4. A `get_order` tool returns a 40-field JSON blob. The agent only needs 5 fields (order_id, amount_usd, status, delivered_at, item) to decide a refund. What is the correct pattern?
- A. Append the full 40-field blob to history for completeness; instruct the model to ignore irrelevant fields.
- B. Ask the model to summarize the blob before appending it.
- C. Trim the output to the 5 relevant fields in the tool-execution wrapper, before appending it as `tool_result`.
- D. Store the blob in a separate file and reference it by path.

### Q5. A customer query "my recent order" returns 3 candidate orders from the lookup tool. Which move matches the reference-endorsed pattern?
- A. Pick the most recent order — it is the most likely match.
- B. Pick the order with the largest amount, since refunds usually target higher values.
- C. Initiate a refund on the top candidate, then ask the customer to confirm.
- D. Surface the ambiguity and ask the customer for a distinguishing identifier (order ID, date, last four of card, item name), then re-query.

### Q6. A subagent hits a timeout fetching one of several data sources. According to §9, what should happen next?
- A. The subagent escalates directly to a human operator.
- B. The subagent returns a structured error (`failure_type`, `attempted_query`, `partial_results`, `alternatives`) to the coordinator, which decides whether to retry, try an alternative, annotate a gap, or escalate.
- C. The subagent silently returns an empty result so the coordinator can continue.
- D. The subagent retries forever with exponential backoff until the source responds.

### Q7. A tool encounters a database timeout. Which return shape does the reference endorse?
- A. `{"error": "operation failed"}`
- B. `{"results": []}` so the caller can treat it as "no matches found"
- C. `{"failure_type": "timeout", "attempted_query": {...}, "partial_results": [], "alternatives": ["retry", "ask_user_for_date"]}`
- D. Raise an exception and let the agent loop crash so the user sees a hard error.

### Q8. An engineer proposes: "If we double the context window from 200k to 400k tokens, the model will stop forgetting mid-conversation facts." Per §3 and §11, this reasoning is:
- A. Correct — attention quality scales linearly with window size.
- B. Correct — more room means the facts are never evicted.
- C. Wrong — attention degradation in the middle is a property of how the model attends, not of capacity; fix is positional (start/end) + section headers.
- D. Wrong — a bigger window increases latency, which is the real problem.

### Q9. A customer says "I'm really frustrated with this whole process." The agent's sentiment classifier flags HIGH negative sentiment. The case itself is a straightforward 30-day-window refund the policy clearly covers. What should the agent do?
- A. Escalate immediately — frustrated customers always need a human.
- B. Do not escalate on sentiment; process the refund per policy. Sentiment is not an escalation trigger.
- C. Lower the agent's temperature to sound more empathetic, then escalate.
- D. Ask the customer to rate their frustration 1–10 and escalate if above 7.

### Q10. An agent's first `search_orders` call hits a 500 error. Which sequence best matches the reference's guidance on local recovery vs. escalation?
- A. Escalate to a human immediately — one tool failure proves the session is broken.
- B. Retry the exact same call in an unbounded loop with exponential backoff until it succeeds.
- C. Try bounded local recovery (retry once or twice for transient errors, then try an alternative query or different identifier, then ask the user to clarify); escalate only after concrete local attempts are exhausted.
- D. Return an empty result set and continue as if no orders exist.

## Your answers
| Q  | Answer |
|----|--------|
| 1  |        |
| 2  |        |
| 3  |        |
| 4  |        |
| 5  |        |
| 6  |        |
| 7  |        |
| 8  |        |
| 9  |        |
| 10 |        |
