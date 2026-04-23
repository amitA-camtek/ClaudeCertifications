# W02 Study Day — Multi-Agent Orchestration (Domain 1.2–1.3)

## The one thing to internalize

**Multi-agent = multiple agentic loops connected through a single tool (`Task`).** The coordinator's loop is a normal W01 loop. The subagent's loop is a normal W01 loop. What's new is the boundary between them: explicit prompt in, compact structured result out. No shared state.

## Hub-and-spoke, in one sentence

One coordinator, many isolated subagents, inter-agent data passes through `Task` tool calls — nothing else.

## The four rules

1. **Coordinator is the only agent that sees the full task.** Subagents see only the slice they're handed.
2. **Subagent contexts are isolated.** They don't see the user's original message, the coordinator's reasoning, or peer subagents' work.
3. **`"Task"` must be in the coordinator's `allowedTools`** or it physically cannot delegate. No prompt rule substitutes for this.
4. **Subagents get scoped tools** (research subagent gets search tools; refund subagent gets refund tools). Not everything.

## The loop, conceptually

The coordinator's loop is identical to the W01 agentic loop. When the coordinator calls `Task(subagent_type=..., prompt=...)`:

- The runtime spins up a fresh agent with that subagent's `AgentDefinition`.
- That agent runs its **own** agentic loop to completion.
- Its final message comes back as a single `tool_result` to the coordinator.

From the coordinator's perspective, `Task` is just a tool that takes a while and returns a string. The subagent's 40 intermediate turns are never visible.

## AgentDefinition fields

| Field | What it's for |
|---|---|
| `description` | Selection signal — how the coordinator picks this subagent type |
| `prompt` | System prompt for the subagent's loop |
| `tools` | Scoped tool allow-list for this subagent |
| `model` | Optional per-subagent model override |

## Parallel vs sequential subagent calls

- **Parallel** when subtasks are independent → coordinator emits multiple `Task` tool_use blocks in one turn, runtime runs them concurrently, all tool_results come back in one `user` turn (same invariant as W01 parallel tool use).
- **Sequential** when subtask B needs subtask A's output → dispatch A first, wait, embed A's result in B's prompt, dispatch B.

Order is decided by **dependency**, not by default safety.

## `fork_session`

Branches the current session into an independent copy for speculative exploration. If the branch is a dead end, the main session is untouched. Different from `--resume` (continues an existing session) — `fork_session` **diverges** from one.

## Decomposition pitfalls

- **Too narrow** → coverage gaps. 10 tiny subagents, each too small to notice inconsistencies.
- **Too broad** → subagent drowns. One subagent doing "research the whole company" has every single-agent problem you spawned it to fix.
- **Rule of thumb:** each subagent's scope fits in one sentence; coordinator has a clear synthesis step, not just concatenation.

## Fixed chain vs adaptive decomposition

- **Fixed chain** — predictable sequence, right for well-understood tasks.
- **Adaptive decomposition** — coordinator inspects input, chooses subagents and count. Right for open-ended or multi-concern inputs (classic: "refund + address change + loyalty question" in one message → three specialist subagents in parallel, unified reply).

## 3-bullet recap

- Coordinator dispatches via `Task`, subagents run in isolated contexts, coordinator synthesizes — inter-agent data is only prompts and structured returns, never shared state.
- `"Task"` in `allowedTools` is mandatory; subagents get scoped tool sets; subagents generally do NOT get `"Task"` themselves (keep the tree shallow).
- Parallelize independent subtasks; decompose with just enough granularity — each subagent's job must be explainable in one sentence, and the coordinator must have a real synthesis step after.
