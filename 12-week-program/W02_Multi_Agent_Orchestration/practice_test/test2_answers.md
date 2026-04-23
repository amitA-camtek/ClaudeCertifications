# Practice Test 2 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | B |
| 2 | C |
| 3 | B |
| 4 | C |
| 5 | B |
| 6 | B |
| 7 | B |
| 8 | B |
| 9 | B |
| 10 | B |

## Detailed explanations

### Q1 — Answer: B

**Why B is correct:** Subagents have isolated contexts. They see only the task prompt handed to them by the coordinator plus tool results they gather themselves. They do not see the user's original message, the coordinator's reasoning, or other subagents' work (§2, "Rules" #2).

**Why the others are wrong:**
- A. The user's original message and coordinator reasoning are explicitly hidden from subagents — that's the whole point of isolation (§2).
- C. Shared memory across subagents is an anti-pattern; it breaks isolation and re-introduces all single-agent problems (§9).
- D. There is no read-only window into the coordinator's messages[]; inter-agent communication is via explicit prompts and structured returns only (§2 rule 3).

**Reference:** §2 of reference.md

---

### Q2 — Answer: C

**Why C is correct:** Delegation is a deterministic mechanism gated by `"Task"` in `allowedTools`. If it's missing, the coordinator has no way to call `Task` regardless of what the prompt says. "Deterministic mechanism beats prompt instruction" (§3, "The `allowedTools` rule").

**Why the others are wrong:**
- A. Prompt instructions cannot create a tool that doesn't exist in `allowedTools` (§3 exam distractor).
- B. The SDK does not silently upgrade `allowedTools`; the developer must include `"Task"` explicitly (§3).
- D. Tool availability is not model-dependent — it's a configuration concern (§3).

**Reference:** §3 of reference.md

---

### Q3 — Answer: B

**Why B is correct:** A multi-concern customer message is the canonical scenario for adaptive decomposition: the coordinator inspects the input, spots N concerns, dispatches N specialist subagents in parallel, then synthesizes one unified reply (§8, "Exam-critical").

**Why the others are wrong:**
- A. Fixed prompt chains fit well-understood tasks with input-independent steps; open-ended multi-concern messages defeat them (§8 table).
- C. "One big subagent handles everything open-ended" reproduces all single-agent problems (§9 anti-pattern).
- D. The three concerns are independent; forcing sequential dispatch wastes latency (§5, "When NOT to parallelize" only applies when there's a data dependency).

**Reference:** §8 of reference.md

---

### Q4 — Answer: C

**Why C is correct:** The coordinator is the only agent positioned to notice what was never asked. The canonical failure is that the coordinator did not run a gap-detection step against the original goal and re-delegate targeted follow-up subagents (§7b, "Why this matters for the exam").

**Why the others are wrong:**
- A. Broadening subagent prompts reproduces the "subagent drowning" pitfall (§7 Pitfall B) and doesn't solve the missing-branch problem.
- B. The synthesis agent only sees what the prior decomposition surfaced; it has a blind spot for whole missing branches. This is an explicit exam distractor (§7b, "Exam distractor pattern").
- D. Shared memory between subagents is an anti-pattern (§9) and still wouldn't surface a branch no one researched.

**Reference:** §7b of reference.md

---

### Q5 — Answer: B

**Why B is correct:** The `description` field is how the coordinator selects among registered subagent types — treat it the same way you'd treat a tool description; be specific about when to use it. Generic descriptions degrade selection (§4 table, "description" row).

**Why the others are wrong:**
- A. `description` is functional, not cosmetic — it drives coordinator routing (§4).
- C. Nothing in §4 indicates the SDK validates uniqueness of descriptions.
- D. `description` and `prompt` are separate fields with distinct purposes; `prompt` is the subagent's system prompt (§4 table).

**Reference:** §4 of reference.md

---

### Q6 — Answer: B

**Why B is correct:** The three fetches are independent subtasks, so they should be dispatched in parallel: one assistant turn with three `Task` tool_use blocks, then synthesize after all return. Wall-clock speedup is substantial (§5, "When to parallelize").

**Why the others are wrong:**
- A. "Always run subagents sequentially to preserve order" is an explicit exam distractor; order is preserved by task decomposition, not execution mode (§5 exam distractor).
- C. One subagent holding all three tools reproduces the single-agent problems and loses parallelism (§9 anti-patterns).
- D. `fork_session` is for branched exploration of hypotheses, not for independent data fetches (§6).

**Reference:** §5 of reference.md

---

### Q7 — Answer: B

**Why B is correct:** When B's input depends on A's output, parallel dispatch means B's prompt is constructed before A has returned, so B runs without the information it needs. Dependencies require sequential dispatch: turn 1 dispatches A, turn 2 dispatches B with A's results embedded (§5, "When NOT to parallelize").

**Why the others are wrong:**
- A. The SDK does not auto-serialize dependent tasks — the coordinator imposes ordering (§5).
- C. Context pollution isn't the failure mode here; missing input is.
- D. The model will happily emit multiple `Task` blocks in one turn; the SDK does not detect semantic dependencies (§5).

**Reference:** §5 of reference.md

---

### Q8 — Answer: B

**Why B is correct:** `fork_session` splits the current session into an independent branch for hypothesis exploration. If the branch dead-ends, the main session keeps going clean — exactly the trial-migration use case described (§6).

**Why the others are wrong:**
- A. `--resume <name>` continues an existing named session; it does not create a divergent copy (§6, contrast paragraph).
- C. Spawning a subagent creates an isolated execution but isn't the mechanism for branched session exploration of the main context (§6 is specifically about fork_session).
- D. `allowedTools` controls tool access, not session branching (§3).

**Reference:** §6 of reference.md

---

### Q9 — Answer: B

**Why B is correct:** Subagents generally should NOT include `"Task"`. Keep the tree shallow — only coordinators delegate. "Spawn unbounded subagents from subagents" is listed as an explicit anti-pattern (§9 table; also §3 code comment "Subagent definition — typically does NOT include `Task`").

**Why the others are wrong:**
- A. Deep recursive delegation is not the recommended pattern; it's an anti-pattern (§9).
- C. Shared memory between agents is itself an anti-pattern (§9) and doesn't fix the depth problem.
- D. Model choice is independent of tool scoping; `model` is an optional per-subagent override (§4).

**Reference:** §9 and §3 of reference.md

---

### Q10 — Answer: B

**Why B is correct:** This is Pitfall A — overly narrow decomposition causes coverage gaps because no single subagent sees enough to notice cross-page inconsistencies. The fix is 2–3 subagents with overlapping or hierarchical roles (e.g., one per thematic section) plus a coordinator cross-section integration pass (§7 Pitfall A).

**Why the others are wrong:**
- A. Going back to one big subagent is Pitfall B (subagent drowning) — the opposite extreme (§7 Pitfall B).
- C. Tool scoping is unrelated; each page-summary subagent has the tools it needs (§2 rule 4 is about scoping, not this failure).
- D. Sequential execution doesn't fix coverage gaps; it just wastes latency (§5 exam distractor).

**Reference:** §7 of reference.md
