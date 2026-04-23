# Build — Multi-Agent Orchestration

**Time:** 40 min · **Goal:** Stand up a hub-and-spoke coordinator that dispatches a multi-concern task to two scoped subagents and synthesizes one answer.

## What you'll have at the end
- `exercises/my_orchestrator.py` — runnable coordinator + 2 `AgentDefinition`s with isolated contexts
- A run trace showing the coordinator calling `Task` and receiving only each subagent's final synthesis (never the raw tool turns)

## Prereqs
- `ANTHROPIC_API_KEY` exported, `anthropic` SDK installed, Python 3.10+
- Finished reading [reference.md](../reference.md) §1–§4
- Target file: `exercises/my_orchestrator.py` (peek at [minimal_multi_agent.py](minimal_multi_agent.py) only if stuck)

## Steps

### 1. Scaffold the agentic loop (~5 min)
Reuse the W01 loop shape — you need the same `while stop_reason != "end_turn"` skeleton for *both* the coordinator and each subagent. One function, two callers.
- [ ] Create `my_orchestrator.py`, import `anthropic`, set `MODEL`, write a `run_agent_loop(system, tools, tool_dispatch, user_input, label)` that handles `tool_use` → `tool_result` → next turn.
- [ ] Add a `safety_fuse` counter so a runaway loop can't burn your key.

**Why:** §10 — the coordinator's loop is the same shape as a single agent's; `Task` is just another tool from its perspective.
**Checkpoint:** Calling `run_agent_loop` with zero tools on "say hi" returns a text answer and exits cleanly.

### 2. Define the two subagents as `AgentDefinition` analogues (~7 min)
Pick two clearly distinct specialists so role separation is obvious. Use `researcher` (public info lookup) and `calculator` (arithmetic), or any pair you like — the point is scoped tools + a one-sentence role.
- [ ] Build a `SUBAGENTS` dict with two entries. Each entry needs `description` (how the coordinator selects it), `system` (short role prompt), `tools` (scoped — researcher gets a mock `web_search`, calculator gets `calculate`).
- [ ] Implement each tool as a plain Python function and register them in a `SUBAGENT_TOOL_DISPATCH` map keyed by subagent_type.

**Why:** §4 — `AgentDefinition` fields are `description` / `prompt` / `tools`; §2 rule 4 — subagents get **scoped** tools, not everything. §9 anti-pattern: "give every subagent every tool" degrades selection.
**Checkpoint:** `SUBAGENTS["calculator"]["tools"]` contains `calculate` and does NOT contain `web_search`.

### 3. Write the coordinator system prompt (~5 min)
The coordinator is the only agent that sees the whole user task. Its prompt must name the subagent types, describe when to use each, and demand a *synthesis* step — not a dump.
- [ ] Write `COORDINATOR_SYSTEM` that lists both subagents by name with one-line "use when" rules and ends with "After all subagent results are in, synthesize ONE final answer."
- [ ] Do NOT give the coordinator domain tools (no `calculate`, no `web_search`) — force it to delegate.

**Why:** §2 rule 1 — coordinator decomposes + dispatches + synthesizes; §7 decomposition rule of thumb — if you can't describe the synthesis step, you decomposed badly.
**Checkpoint:** Reading your prompt aloud, a stranger could name the two subagents and when each fires.

### 4. Give the coordinator the `Task` tool in `allowedTools` (~7 min)
This is the single most exam-tested mechanic. Without `Task` in the tool list, no amount of prompt nagging makes the coordinator delegate.
- [ ] Define a `Task`-analogue tool (call it `Task` or `spawn_subagent`) with input schema `{subagent_type: enum[...], prompt: string}`. The prompt field's description must say "self-contained — subagent sees nothing else."
- [ ] Put ONLY this tool in `COORDINATOR_TOOLS`. The one non-obvious shape to get right is the tool_use input:

```python
{"subagent_type": "researcher", "prompt": "<fully self-contained task>"}
```

**Why:** §3 — `allowedTools` **must** include `"Task"`; §9 anti-pattern — "add a rule to the prompt" is a distractor, the mechanism is the tool list.
**Checkpoint:** Remove `Task` from the list, rerun — coordinator tries to answer directly or hallucinates. Put it back.

### 5. Wire `Task` to spawn an isolated subagent loop (~7 min)
When the coordinator calls `Task`, you run a **fresh** `run_agent_loop` with a brand-new `messages=[]`, the subagent's own system prompt, and its scoped tools. Only the final text string goes back as the `tool_result`.
- [ ] In your coordinator's tool dispatch, map `Task` → a function that looks up `SUBAGENTS[subagent_type]`, calls `run_agent_loop` with fresh messages, and returns the final text.
- [ ] Log a banner before/after each subagent run so you can *see* the isolation boundary in the trace.

**Why:** §2 rule 2 — subagents have isolated contexts; §3 — `Task` returns the subagent's final message as a `tool_result`, not its raw trace.
**Checkpoint:** Your print log shows subagent messages NEVER include the original user question unless you explicitly put it in the `prompt` field.

### 6. Dispatch a multi-concern task and observe parallel vs sequential (~7 min)
Send one user message that needs **both** subagents. Pick whether the two subtasks are independent (parallel) or dependent (sequential), and predict before you run.
- [ ] Example independent prompt: "Look up the population of Tokyo, and separately compute 17 * 23." → coordinator should emit two `Task` tool_use blocks in one assistant turn.
- [ ] Example dependent prompt: "Find the population of Tokyo, then compute that number divided by 1000." → coordinator must dispatch sequentially (turn 1 researcher, turn 2 calculator with result embedded).
- [ ] Run both. In the trace, count how many `Task` tool_use blocks appear per assistant turn.

**Why:** §5 — parallel when independent, sequential when there's a data dependency. §5 exam distractor: "always sequential for safety" is wrong.
**Checkpoint:** Independent run shows 2 tool_use blocks in one turn; dependent run shows 1 block per turn across two turns.

## Verify
Run the independent-concern prompt. Expected:
- Final answer integrates both subagent outputs in a single synthesized reply (not two stitched paragraphs).
- Trace shows each subagent's internal tool calls stay inside its own loop; only final text bubbles up to the coordinator's `tool_result`.
- Coordinator never calls `calculate` or `web_search` directly — only `Task`.

**Common mistakes:**
- Forgot `Task` in `COORDINATOR_TOOLS` → coordinator improvises answers → §3
- Passed the original user message into the subagent's `messages` → isolation breached → §2 rule 2
- Gave both subagents every tool "to be safe" → tool-selection degraded → §9 row 1
- Wrote a prompt-rule "you must delegate" but no `Task` tool → §3 distractor + §9 row 3
- Subagent prompt references "the user's question" without including the data → subagent sees nothing else → §2 rule 3

## Stretch — Polish block (30 min on Practice Day)
From the Polish row: add parallel subagent execution + `fork_session`.
- [ ] Construct a prompt with three genuinely independent subtasks; confirm the coordinator emits 3 `Task` tool_use blocks in one assistant turn and your runner processes all 3 `tool_result`s in the matching `user` turn with correct `tool_use_id`s (§5).
- [ ] Wrap the dispatcher in an async `gather` so the 3 subagent loops run concurrently; compare wall-clock vs the sequential version.
- [ ] Add a `fork_session`-style branch: before committing a risky action (e.g., a speculative multi-step plan), spawn a forked subagent to trial it; if it fails, the main coordinator context is untouched (§6).
- [ ] Add a gap-detection pass: after synthesis, have the coordinator re-inspect coverage vs the original ask and re-delegate one narrow follow-up if something was missed (§7b).

## If stuck
Compare with [minimal_multi_agent.py](minimal_multi_agent.py). Read → close → rewrite.
