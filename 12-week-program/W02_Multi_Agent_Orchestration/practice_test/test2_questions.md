# Practice Test 2 — Multi-Agent Orchestration

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 1.2–1.3

## Instructions
Solve all 10 questions before opening `test2_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. In the hub-and-spoke pattern, which statement is true about what a subagent can see during its execution?
- A. The subagent sees the user's original message plus the coordinator's decomposition reasoning.
- B. The subagent sees only the task prompt handed to it by the coordinator plus whatever tool results it gathers itself.
- C. The subagent shares a common memory region with its sibling subagents so they can coordinate.
- D. The subagent sees the coordinator's full messages[] list via a read-only reference.

### Q2. An architect adds the following line to the coordinator's system prompt: *"You must delegate research tasks to the researcher subagent rather than doing them yourself."* The coordinator's `allowedTools` list is `["Read", "Write", "WebSearch"]`. What will happen at runtime?
- A. The coordinator will delegate correctly because the instruction is explicit.
- B. The coordinator will attempt delegation but the SDK will silently upgrade `allowedTools` to include `"Task"`.
- C. The coordinator cannot delegate — without `"Task"` in `allowedTools`, the mechanism doesn't exist regardless of prompt instructions.
- D. The coordinator will delegate only if the model is Opus; Sonnet will ignore the instruction.

### Q3. A coordinator receives: *"I want a refund for order #123, please also update my shipping address to 42 Oak St, and remind me how loyalty points work."* Which decomposition strategy fits best?
- A. A fixed prompt chain: classify → look-up → respond, run in that order for every message.
- B. Adaptive decomposition: coordinator spots the three concerns and dispatches three specialist subagents in parallel, then synthesizes a unified reply.
- C. One broad subagent called "customer-service-generalist" that handles the whole message.
- D. A sequential chain where the refund subagent runs first, then passes its result as input to the address-change subagent.

### Q4. A coordinator is asked to research *"the impact of AI on creative industries"*. It decomposes into three subagents: `digital_art`, `graphic_design`, `photography`. All three subagents execute correctly and return high-quality summaries. The synthesis agent produces a polished report. Music, writing, and film are never mentioned. Where is the defect?
- A. The subagents needed broader prompts so each could cover adjacent domains.
- B. The synthesis agent should have inspected its own output for coverage gaps and fetched more sources.
- C. The coordinator never ran a gap-detection step on its own decomposition and re-delegated targeted follow-ups.
- D. The subagents should have been given shared memory so they could notice each other's scope and fill gaps.

### Q5. A developer registers `AgentDefinition` entries for five subagent types. The `description` field on three of them is `"helpful agent"`. What is the practical consequence?
- A. None — `description` is cosmetic metadata used only in logging.
- B. The coordinator's subagent selection degrades because `description` is how the coordinator picks which subagent type to call (treat it like a tool description).
- C. The SDK refuses to register duplicate descriptions and throws an error.
- D. Each subagent's own system prompt is overridden by its `description`.

### Q6. A coordinator must: (1) fetch current pricing from service A, (2) fetch inventory from service B, (3) fetch shipping ETA from service C, then (4) write a combined quote. Services A, B, C are independent APIs. What is the correct dispatch pattern?
- A. Dispatch A, B, C sequentially to preserve ordering, then synthesize.
- B. Dispatch A, B, C in parallel in one assistant turn (three `Task` tool_use blocks), then synthesize after all three return.
- C. Give one subagent all three tools and let it handle everything.
- D. Fork a session for each service to keep their contexts isolated.

### Q7. Subtask B's prompt requires the output of subtask A. An engineer dispatches A and B in parallel from the same assistant turn to save latency. What goes wrong?
- A. Nothing — the SDK automatically serializes dependent tasks.
- B. B runs without the information it needs because its prompt is constructed before A has returned; parallel dispatch is only valid for independent subtasks.
- C. The coordinator's context gets polluted because both results arrive together.
- D. The model refuses to emit two `Task` blocks in one turn when a dependency exists.

### Q8. A team wants to try migrating one file to a new API as a trial. If the trial fails, they want the main exploratory session to continue untouched by the failed attempt. Which mechanism fits?
- A. `--resume <name>` — resumes the main session so the trial can continue it.
- B. `fork_session` — creates an independent branch; if the branch dead-ends, the main session stays clean.
- C. Spawn a subagent with `Task` — subagents are the only way to branch.
- D. Use `allowedTools` to disable writes during the trial.

### Q9. An architect proposes: *"Each subagent should have `Task` in its `allowedTools` so it can spawn its own helpers whenever it needs to. This will make the system flexible and recursive."* What is the correct critique?
- A. Correct design — deep recursion through `Task` is the recommended pattern for flexibility.
- B. Subagents generally should NOT include `"Task"`; the tree should be kept shallow with only the coordinator delegating. Unbounded subagent-from-subagent spawning is an anti-pattern.
- C. Fine, as long as each subagent also shares memory with its parent so state is consistent.
- D. Only valid if every subagent uses the same model as the coordinator.

### Q10. A coordinator decomposes a 30-page report into 30 subagents, each summarizing exactly one page. Each subagent's summary is accurate. The final aggregated document contains contradictions between pages that no subagent noticed. Which decomposition pitfall is this, and what is the fix?
- A. Overly broad decomposition; fix by giving one subagent the whole report.
- B. Overly narrow decomposition; fix by using 2–3 subagents with overlapping or hierarchical scopes (e.g., one per thematic section) plus a coordinator cross-section integration pass.
- C. Tool scoping problem; fix by giving each subagent more tools.
- D. Parallelism problem; fix by running the 30 subagents sequentially instead.

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
