# W02 Reference — Multi-Agent Orchestration (Domain 1.2–1.3)

Complete, self-contained study material for Week 2. Read this end-to-end.

Prerequisites: W01 (you must understand the agentic loop and `stop_reason` before multi-agent makes sense — a multi-agent system is just multiple agentic loops talking through structured messages).

---

## 1. Why multi-agent?

A single agent running in one context window breaks down when:
- **Context bloat** — too many tool descriptions, too much history, attention degrades.
- **Role conflict** — the same prompt has to be a strict code reviewer AND a lenient refactor assistant AND a SQL expert; compromises everywhere.
- **Parallelism lost** — independent subtasks run sequentially because one loop can only do one thing at a time.
- **Context pollution** — a failed exploratory branch (bad file reads, wrong rabbit hole) poisons the remaining session.

Multi-agent fixes all four: each agent has a narrow role, a short prompt, a scoped tool set, and its own isolated context. A **coordinator** decomposes the problem and dispatches to **subagents**.

---

## 2. The hub-and-spoke pattern (this is THE pattern the exam tests)

```
                 ┌──────────────────┐
                 │   COORDINATOR    │
                 │  (hub / router)  │
                 └────┬────┬────┬───┘
                      │    │    │
              ┌───────┘    │    └────────┐
              ▼            ▼             ▼
         ┌────────┐   ┌────────┐    ┌────────┐
         │ Sub A  │   │ Sub B  │    │ Sub C  │
         │isolated│   │isolated│    │isolated│
         │context │   │context │    │context │
         └────────┘   └────────┘    └────────┘
```

**Rules:**

1. **Coordinator is the only agent that knows the whole task.** It decomposes, dispatches, aggregates, synthesizes.
2. **Subagents have isolated contexts.** They see *only* the task the coordinator handed them, plus whatever tool results they gather. They do **not** see the user's original message, the coordinator's reasoning, or other subagents' work.
3. **Inter-agent communication is explicit and structured.** Coordinator → subagent = a task-description prompt. Subagent → coordinator = a structured return value (text or JSON). Never shared memory.
4. **Subagents get scoped tools**, not everything. A research subagent gets `web_search`; a refund subagent gets `issue_refund`. Cross-scoping leaks responsibilities and degrades tool selection (see W04).

### Why *isolated* contexts matter

If a subagent's 40-turn exploration (with 30 tool calls and 50 kB of intermediate results) all landed in the coordinator's context, the coordinator would drown. Isolation is what makes the pattern scale. The subagent returns a **compact synthesis** — the coordinator never sees the raw trace.

---

## 3. The `Task` tool (Agent SDK)

In the Claude Agent SDK and Claude Code, subagent spawning is done through a built-in tool named **`Task`**. The coordinator agent calls `Task(subagent_type="researcher", prompt="...")` just like any other tool call. Under the hood the SDK:

1. Spins up a fresh agent with the specified `subagent_type` definition (system prompt, tool set).
2. Runs that agent's own loop until *it* emits `end_turn`.
3. Returns the subagent's final message as the `tool_result` for the coordinator's `Task` call.

**The coordinator's loop doesn't know or care** whether `Task` took 1 turn or 50 turns internally — to it, `Task` is just a tool that returned a string.

### The `allowedTools` rule

For a coordinator to be *able* to spawn subagents, its tool allow-list **must include `"Task"`**. If you forget this, the coordinator has no way to delegate — it'll try to do everything itself, blow up its own context, and fail.

```python
# Coordinator definition — MUST include "Task"
COORDINATOR_TOOLS = ["Task", "Read", "Write"]   # ✓ can delegate

# Subagent definition — typically does NOT include "Task"
# (subagents generally don't spawn further subagents)
RESEARCHER_TOOLS = ["WebSearch", "WebFetch"]    # ✓ scoped to research
```

**Exam distractor pattern:** "Add instructions to the coordinator prompt telling it to delegate." — wrong. If `"Task"` isn't in `allowedTools`, the coordinator *cannot* delegate no matter what the prompt says. Deterministic mechanism beats prompt instruction (again — this theme repeats across every domain).

---

## 4. `AgentDefinition`

An `AgentDefinition` (in the Agent SDK / Claude Code) declaratively describes a subagent type:

```python
AgentDefinition(
    description="Fetches and summarizes technical documentation",
    prompt="You are a technical research specialist. Given a question, ...",
    tools=["WebSearch", "WebFetch"],
    model="claude-sonnet-4-6",      # optional model override
)
```

Fields to know:

| Field | Purpose |
|---|---|
| `description` | Short summary — how the coordinator *selects* this subagent type. Treat it the same way you'd treat a tool description: be specific about when to use it. |
| `prompt` | The system prompt for that subagent's loop. |
| `tools` | Scoped tool list for this subagent. Explicit subset, not "all". |
| `model` | Optional — different subagents can use different models (small model for triage, big model for synthesis). |

You register a set of `AgentDefinition`s with the SDK/Claude Code, and the coordinator picks among them when calling `Task`.

---

## 5. Parallel subagent execution

A coordinator can call `Task` multiple times in **one assistant turn** — that is parallel subagent dispatch. The mechanics are identical to parallel tool use from W01:

- One `assistant` turn with N `Task` tool_use blocks.
- Your runtime (the SDK) runs the N subagents in parallel.
- One `user` turn back to the coordinator with N `tool_result` blocks, each with matching `tool_use_id`.

### When to parallelize

Parallelize when subtasks are **independent**: research three risk domains, summarize five documents, check four services' health. The wall-clock speedup is huge — three 30-second subagents in parallel ≈ 30 seconds, not 90.

### When NOT to parallelize

Don't parallelize when subtask B's input *depends on* subtask A's output. Doing them in parallel means B runs without the information it needs. If there's a dependency, dispatch sequentially: turn 1 dispatches A, turn 2 (after A returns) dispatches B with A's results embedded in B's prompt.

### Exam distractor pattern

"Always run subagents sequentially to preserve order." — wrong. Order is preserved by task decomposition, not execution mode. Independent tasks should be parallel; the coordinator is the one imposing order where needed.

---

## 6. `fork_session` — branched exploration

`fork_session` splits the current session into an independent branch so the agent can explore a hypothesis without polluting the main context. If the branch turns out to be a dead end, the main session keeps going clean.

Typical uses:
- "Try migrating this file to the new API; if it works, I'll apply the same pattern to the other 20." The trial migration goes in a forked session; if it fails, the main session never sees the mess.
- Branched research: fork per hypothesis, each explores independently, coordinator compares final outputs.

Contrast with `--resume <name>` (covered in W03): `--resume` continues an existing named session; `fork_session` creates a divergent copy.

---

## 7. Task decomposition — the pitfalls

The hardest part of multi-agent is decomposition. The exam tests two failure modes heavily:

### Pitfall A — Overly narrow decomposition → coverage gaps

Splitting a task too finely means no single subagent sees enough to notice missing pieces.

- **Bad:** 10 subagents, each summarizing one paragraph of a report. No one has context to spot inconsistencies across paragraphs.
- **Good:** 2–3 subagents with overlapping or hierarchical roles — e.g., one per thematic section, plus a coordinator doing the cross-section integration pass.

### Pitfall B — Overly broad decomposition → subagent drowning

Giving one subagent a sprawling task ("research everything about this company") reproduces all the single-agent problems inside the subagent. Break it down further.

### Decomposition rule of thumb

- Each subagent should have a **scope a human could describe in one sentence**.
- There should be a **clear synthesis step** in the coordinator that integrates outputs — not just a concatenation.
- If you can't articulate what the coordinator does *after* all subagents return, you've decomposed badly.

---

## 7b. Iterative refinement loops — coordinator re-delegation

Decomposition rarely lands right on the first pass. The exam-critical pattern is that the coordinator doesn't just run subagents once and ship — it **evaluates the synthesized output, identifies gaps, and re-delegates with targeted queries until coverage is sufficient.**

The loop (at the coordinator level — this is NOT a subagent's inner loop):

1. Dispatch initial subagents in parallel.
2. Collect results, synthesize.
3. Inspect the synthesis against the original goal. Ask: *"Are there domains, subtopics, or angles the initial decomposition missed?"*
4. If gaps exist → dispatch follow-up subagents with **narrow, targeted queries** aimed at those specific gaps. Not a full redo.
5. Re-synthesize with the new findings merged in.
6. Terminate when coverage is sufficient (or a bounded refinement-cap is hit so the loop can't run forever).

### Why this matters for the exam

The canonical failing scenario: a coordinator decomposes *"impact of AI on creative industries"* into `digital art`, `graphic design`, `photography` — three visual-arts subtasks. Each subagent performs correctly. The final report looks polished but silently omits **music, writing, film**. The failure is not in the subagents; it's that the coordinator never re-examined its own decomposition for gaps.

The fix is NOT *"give the subagents more autonomy"* or *"add a coverage-check inside the synthesis agent"* — it's that the **coordinator** must run a gap-detection step and re-delegate. The synthesis agent is not positioned to know what was never researched.

### Targeted queries vs full redo

When the coordinator re-delegates, the follow-up subagent prompts should be narrow:

> *"Research AI's impact on music production specifically, focusing on generative composition, vocal synthesis, and DAW integration."*

Not:

> *"Re-research creative industries."*

Narrow targeting is what makes the loop convergent and efficient.

### Exam distractor pattern

"Have the synthesis agent identify its own coverage gaps and fetch additional sources." — **wrong**. The synthesis agent only sees what the prior decomposition surfaced; it has a blind spot for whole missing branches. The coordinator is the only agent positioned to notice what *wasn't asked*.

---

## 8. Fixed prompt chains vs adaptive decomposition

Two strategies for decomposition:

| Strategy | When right | When wrong |
|---|---|---|
| **Fixed prompt chain** — predefined sequence of steps (e.g., "always do: classify → look-up → respond") | Well-understood tasks where the steps don't change per input. Predictable latency, easy to debug. | Ambiguous or open-ended tasks where the right decomposition depends on the input. |
| **Adaptive decomposition** — coordinator inspects the input and decides which subagents to call and how many | Open-ended / multi-concern inputs (the classic "refund + address change + loyalty question" message). | Simple, single-concern tasks. Adaptive is overkill and adds a reasoning turn for no benefit. |

**Exam-critical:** a multi-concern customer message is the canonical scenario for adaptive decomposition. The coordinator spots the three concerns, dispatches three specialist subagents in parallel, synthesizes one unified reply.

---

## 9. Anti-patterns (exam distractors)

| Wrong answer | Why it's wrong |
|---|---|
| "Give every subagent access to every tool" | 18 tools >> 4–5 tools degrades tool selection. Scope per role. |
| "Let subagents share memory / directly see each other's context" | Breaks isolation. Re-introduces all single-agent problems at higher cost. |
| "Add a rule to the coordinator's prompt that it must delegate" | Can't delegate without `"Task"` in `allowedTools`. Add the tool, don't just nag in prompt. |
| "Have the coordinator review its own reasoning" | Self-review retains bias. Use an independent subagent (W08 theme). |
| "Run all subagents sequentially for safety" | Wastes latency when tasks are independent. Parallelize unless there's a data dependency. |
| "Let one big subagent handle everything open-ended" | Reproduces the problems you spawned it to solve. Decompose further. |
| "Pass shared state through a global variable" | Breaks context isolation. Inter-agent data must go through prompts and structured returns. |
| "Spawn unbounded subagents from subagents" | Subagents generally should NOT have `"Task"`. Keep the tree shallow; only coordinators delegate. |
| "Coordinator dispatches subagents once and ships the synthesis" | No gap-detection step. Whole missing branches (music/writing/film when decomposition only hit digital-art) never surface. Coordinator must evaluate coverage and re-delegate. |
| "Have the synthesis agent fetch more sources when it spots gaps" | Synthesis agent only sees what was decomposed — it has a blind spot for whole missing branches. Only the coordinator can re-examine its own decomposition. |

---

## 10. Hub-and-spoke in code (conceptual)

The Agent SDK hides the mechanics, but conceptually a coordinator's loop looks like this (compare to the W01 loop skeleton):

```python
# Coordinator loop — same shape as W01's agentic loop
while True:
    resp = client.messages.create(
        model=...,
        system=COORDINATOR_SYSTEM_PROMPT,
        tools=[TASK_TOOL, ...other_tools...],   # Task MUST be here
        messages=messages,
    )
    messages.append({"role": "assistant", "content": resp.content})

    if resp.stop_reason == "end_turn":
        return final_text(resp)

    if resp.stop_reason == "tool_use":
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                if block.name == "Task":
                    # Run the named subagent in an ISOLATED context — a whole
                    # inner agentic loop, with its own messages[], its own tools,
                    # its own system prompt.
                    result = run_subagent(
                        subagent_type=block.input["subagent_type"],
                        prompt=block.input["prompt"],
                    )
                else:
                    result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})
```

The key insight: **`Task` is just a tool from the coordinator's perspective.** The coordinator doesn't manage the subagent's turn-by-turn execution — it dispatches, waits, receives a synthesized result, and continues. That's the isolation boundary.

---

## 11. What the exam will probe

- Scenarios where one big agent is failing; pick the multi-agent decomposition.
- Broken coordinator missing `"Task"` in `allowedTools`.
- Distractors that confuse adaptive decomposition with fixed chains.
- "Should these subagents run parallel or sequential?" given a dependency description.
- "What's the correct inter-agent communication pattern?" — explicit prompts + structured returns, not shared state.
- Task decomposition questions: over-narrow vs over-broad splits.

---

## 12. Fast recap

- **Hub-and-spoke:** coordinator dispatches, subagents execute in isolated contexts, coordinator synthesizes.
- **`Task` tool** is the mechanism. Coordinator's `allowedTools` **must** include `"Task"`.
- **AgentDefinition** declares subagent type (description, prompt, tools, optional model).
- **Parallel** when independent, **sequential** when there's a data dependency.
- **`fork_session`** for branched exploration; keeps main context clean.
- **Decomposition pitfalls:** too narrow → coverage gaps; too broad → subagent drowns.
- **Fixed chain** vs **adaptive decomposition** — adaptive for multi-concern / ambiguous inputs.
- Inter-agent data = structured prompts and returns. Never shared memory.

When you can explain each of those eight bullets out loud in ~20 seconds each, you're ready for the W02 test.
