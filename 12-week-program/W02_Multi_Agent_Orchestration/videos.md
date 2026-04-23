# W02 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** hub-and-spoke orchestration, coordinator role, subagent context isolation, `Task` tool, `AgentDefinition`, parallel execution, decomposition pitfalls.

---

## Talk 1 — "How we built our multi-agent research system" (Anthropic engineering)

The definitive source for exam distractors on multi-agent patterns.

- **Hub-and-spoke, not a chatroom.** One LeadResearcher (coordinator) spawns N subagents in parallel. Subagents do **not** talk to each other — all context they need is handed to them in the spawning prompt. Any answer choice where "subagents coordinate amongst themselves" is wrong.
- **Context isolation is the point.** Each subagent gets its own fresh context window. This is how you scale: instead of one 200k-token monster session, you get N × 50k-token focused sessions. Bigger context windows do **not** replace this — attention quality drops faster than the window grows.
- **Parallelism matters more than you think.** Sequential subagent calls is a common anti-pattern. Running 4 searches in parallel in a single coordinator turn is typically ~3× faster than sequential and barely more expensive (each subagent pays for its own context, but wall-clock wins).
- **15× token cost vs a single agent is realistic.** The team explicitly called this out. Multi-agent is for *research-grade* tasks where quality matters more than cost — not for every problem.
- **Failure mode: subagent drowning.** If the coordinator hands a subagent 40 pages of context "just in case," you've lost the isolation benefit. Pass only what that subagent needs to do its job.

**Exam relevance:** "the coordinator should pass all accumulated history to every subagent" is a distractor. The correct pattern is minimal, task-specific context per subagent.

---

## Talk 2 — Agent SDK: `Task` tool and `AgentDefinition`

- **`Task` is the spawn primitive.** To spawn a subagent, the coordinator must have `"Task"` in its `allowedTools`. Forgetting this is a common "why isn't my coordinator working" bug and a frequent exam distractor.
- **`AgentDefinition` fields:** name, description, system prompt, allowed tools, model. The description is used by the coordinator to decide *which* subagent to spawn — treat it like a tool description (same rigor: examples, boundaries).
- **`fork_session` vs `--resume`:**
  - `--resume <name>` continues a session coherently (same context, same history). Right for "pick up where we left off."
  - `fork_session` creates a divergent branch from a checkpoint. Right for *exploratory* work where you want to try two approaches without polluting each other, or to recover from a poisoned context without losing prior good work.
- **Coordinator pattern in code:** the coordinator's loop runs `Task` calls like any other tool. Each `Task` call returns a synthesized result; the coordinator integrates results into its own context. The subagent's raw transcript does not come back — only its final output.

**Exam relevance:** if a scenario says "one agent needs to try three different strategies without contaminating its main thread," the answer is `fork_session`, not `--resume`.

---

## Talk 3 — Decomposition: fixed chains vs adaptive

- **Fixed prompt chain** = you know the steps in advance ("summarize → extract entities → classify"). Use when the workflow is stable. Cheaper, more predictable, easier to debug.
- **Adaptive decomposition** = the agent itself decides what to do next based on intermediate findings. Use for open-ended research, multi-concern customer messages, debugging sessions where the next step depends on what you just found.
- **Pitfalls both directions:**
  - Narrow decomposition on an open-ended task → coverage gaps. ("Only researched the 2020 data; missed the 2024 context.")
  - Broad decomposition on a fixed task → subagent drowning. ("Spawned 7 subagents for a 3-step extraction.")
- **Iterative refinement loop.** For adaptive tasks, the coordinator often runs: decompose → spawn → integrate → *reassess gaps* → spawn more. Stopping after one round is usually premature.

**Exam relevance:** when a scenario describes a fixed 3-step audit, the answer is a fixed chain (or single agent); adaptive decomposition is a distractor.

---

## Optional external viewing

- "How we built our multi-agent research system": https://www.anthropic.com/engineering/built-multi-agent-research-system
- Search — multi-agent research system: https://www.youtube.com/results?search_query=anthropic+multi+agent+research+system
- Search — Claude Agent SDK tutorial: https://www.youtube.com/results?search_query=claude+agent+sdk+tutorial
