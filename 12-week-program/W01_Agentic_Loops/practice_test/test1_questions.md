# Practice Test 1 — Agentic Loops & Core API

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 1.1

## Instructions
Solve all 10 questions before opening `test1_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A developer writes an agent loop that inspects each response with `if "I'm done" in resp.content[0].text: break`. The loop sometimes exits mid-task and sometimes never exits at all. What is the fundamental problem?
- A. The check should look for the string "finished" instead of "I'm done".
- B. Termination must be driven by `stop_reason == "end_turn"`, not by parsing model text.
- C. The developer should also break when the model calls no tools that turn.
- D. `resp.content[0]` should be `resp.content[-1]` to look at the last block.

### Q2. An assistant turn returns three `tool_use` blocks with ids `t1`, `t2`, `t3`. Which next message is correctly shaped per the API contract?
- A. Three separate messages with `role: "tool"`, one per `tool_use_id`.
- B. Three separate `user` messages, each containing one `tool_result` block.
- C. One `user` message whose `content` is a list of three `tool_result` blocks, each with its matching `tool_use_id`.
- D. One `assistant` message containing three `tool_result` blocks that reference the ids.

### Q3. A developer wants to guarantee that, on a given turn, the model calls the `extract_invoice_fields` tool and nothing else. Which setting accomplishes this deterministically?
- A. Add "You must always call extract_invoice_fields" to the system prompt.
- B. Set `tool_choice = {"type": "any"}`.
- C. Set `tool_choice = {"type": "tool", "name": "extract_invoice_fields"}`.
- D. Set `tool_choice = {"type": "auto"}` and list only that tool in `tools`.

### Q4. A loop returns `stop_reason == "max_tokens"`. The developer's code treats this the same as `end_turn` and returns the text to the user. Per the reference, what is wrong?
- A. Nothing — `max_tokens` is a valid natural terminator.
- B. The output is truncated; code should raise or retry with a larger cap, not silently return it as complete.
- C. The developer should re-prompt the model with "please continue" as a `user` message.
- D. `max_tokens` only occurs for tool calls, so the code should execute tools instead.

### Q5. Which statement about the `safety_fuse` in the canonical loop is correct?
- A. It is the normal termination mechanism for the loop.
- B. It should be set to 3–5 to prevent runaway costs.
- C. It is a high crash-prevention cap (e.g., 25/50/100) — not a task-level iteration limit.
- D. It should match the exact number of tools the model is expected to call.

### Q6. A developer notices that when the model calls a tool, the very next API request includes a `user` message whose content is the `tool_result` blocks. They ask "shouldn't this be `role: tool`?" What is the correct response grounded in the reference?
- A. Yes — `"role": "tool"` is the modern replacement for stuffing results in `user`.
- B. No — the API has no `"tool"` role; tool results are sent in a `user` message by convention.
- C. Only when there is one tool call — for multiple calls, use `"role": "tool"`.
- D. Either role works; the API normalizes them internally.

### Q7. An agent is supposed to complete a 12-step data-reconciliation task but keeps exiting after step 5. Inspection shows the loop has `for _ in range(5): ...`. Which fix aligns with the reference's guidance?
- A. Change to `range(3)` and have the model batch more work per turn.
- B. Remove the loop entirely and let the SDK handle iteration.
- C. Raise the cap to a high safety fuse (e.g., 50) and rely on `end_turn` for termination.
- D. Parse the last response text for "task complete" and break on that.

### Q8. A developer's loop overwrites `messages` each iteration with only the latest tool result, thinking this saves tokens. What problem does the reference identify with this approach?
- A. It's optimal — the model only needs the latest state.
- B. It breaks history; the model loses context and cannot reason over prior turns.
- C. It's fine as long as `stop_reason` is still checked.
- D. It only matters when `tool_choice` is set to `"any"`.

### Q9. Which row correctly maps the `tool_choice` value to its behavior?
- A. `{"type": "auto"}` — model must call some tool this turn.
- B. `{"type": "any"}` — model decides whether to call a tool or end the turn.
- C. `{"type": "none"}` — model cannot call any tool this turn, even if tools are listed.
- D. `{"type": "tool", "name": "X"}` — model is encouraged but not required to call tool X.

### Q10. A loop code reviewer sees this pattern: *"If the response contains no `tool_use` block, re-prompt the model with 'are you sure you're done?' before exiting."* According to the reference, what is wrong with this?
- A. Nothing — it's a useful safety check.
- B. `end_turn` with no tool call is a valid completion; the loop should trust it and exit.
- C. The re-prompt should be sent as an `assistant` message, not a `user` message.
- D. The check should only fire when `stop_reason == "max_tokens"`.

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
