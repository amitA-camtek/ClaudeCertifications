# W01 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** agentic loop lifecycle, `stop_reason` (`tool_use` vs `end_turn`), message-history contract, canonical loop, anti-patterns.

---

## Talk 1 — "Building Effective Agents" (Schluntz & Zhang, Anthropic)

The canonical framing you'll see echoed throughout the exam.

- **Workflow vs agent.** A *workflow* is a predefined graph of LLM calls; an *agent* is an LLM running in a loop that decides its own next step based on tool results. Use agents only when you genuinely need dynamic control flow — otherwise prefer workflows for predictability and cost.
- **Agent = LLM + tools + loop.** That's it. The "loop" is not a Python `while True` wrapping NL parsing. It's: send messages → inspect `stop_reason` → if `tool_use`, execute tool → append `tool_result` → resend. Terminate when `stop_reason == "end_turn"`.
- **Five workflow patterns** (useful distractors on the exam): prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer. None of these are "an agent" — they're deterministic scaffolds around an LLM.
- **Failure modes they emphasize:** agents burn tokens on exploration. Always set a token ceiling and a cost alarm. Tool errors should be *visible to the model* so it can recover — swallowing errors is the #1 cause of silent failure.

**Exam relevance:** the "is this really an agent or a workflow?" reframing appears in distractors. When a scenario says "3 known steps always run in order," the right answer is almost always a fixed chain, not an adaptive agent.

---

## Talk 2 — Agent SDK / Claude Code overview (concepts)

- **Stop reasons are the contract.** `stop_reason` is the only correct termination signal. Parsing the model's natural language for words like "done" or "finished" is an anti-pattern — the model may narrate completion while still wanting a tool call, or vice versa.
- **`max_tokens` can silently end a turn.** If the model is mid-generation and hits the token limit, you'll see `stop_reason: "max_tokens"`, **not** `end_turn`. Treating this as successful completion is a classic bug — always branch on `max_tokens` explicitly and either resume or fail loudly.
- **Message history is append-only during a loop.** Each tool call becomes an `assistant` message with a `tool_use` block; each result becomes a `user` message with a `tool_result` block. There is **no `role: "tool"`** in Claude's API (that's the OpenAI schema — a common distractor).
- **Iteration caps are guardrails, not termination.** A cap of 10 loops is a circuit breaker, not a success condition. Hitting the cap should raise, not silently return partial output as if it were done.

**Exam relevance:** any answer choice that says "parse the response text to decide when to stop," uses `role: "tool"`, or treats `max_tokens` as success is wrong.

---

## Talk 3 — Getting started with the Anthropic API

- **Minimum viable loop:** system prompt → user message → messages.create → check `stop_reason` → if `tool_use`, run tool and resend. Four operations, no framework needed.
- **Tool definitions travel with every request.** They're not a server-side config; they're part of the request payload. This is why tool descriptions are the *primary* selector — the model re-reads them every turn.
- **Temperature for agents:** keep it low (0–0.3) for tool selection and high only for creative generation turns. A common bug is a single high temperature across an agent loop, causing tool-pick instability.

---

## Optional external viewing

These are the *same* search URLs already listed in `LEARNING_PROGRAM.md`. Kept here so you can watch the originals if a concept above feels thin — not required.

- Anthropic YouTube channel: https://www.youtube.com/@anthropic-ai/videos
- "Building effective agents" blog post (the talk is based on this): https://www.anthropic.com/research/building-effective-agents
- Search — Claude Agent SDK tutorial: https://www.youtube.com/results?search_query=claude+agent+sdk+tutorial
- Search — Building effective agents: https://www.youtube.com/results?search_query=anthropic+building+effective+agents
