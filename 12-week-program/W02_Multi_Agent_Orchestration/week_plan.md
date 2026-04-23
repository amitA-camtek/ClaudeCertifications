# W02 — Multi-Agent Orchestration

**Domain:** Foundations · 1.2–1.3
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W01 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — why multi-agent, hub-and-spoke pattern, coordinator role, subagent context isolation |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3–4 — `Task` tool for subagent spawning, `allowedTools` must include `"Task"`, `AgentDefinition` fields |
| 1:40–2:20 | Build | Coordinator + 2 subagents, explicit context passing |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Add parallel subagent execution + `fork_session` for branched exploration |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §7–8 — decomposition pitfalls (narrow → coverage gaps, broad → subagent drowning), iterative refinement, fixed chains vs adaptive |
| 1:00–1:45 | Test | **Practice Test 2** — 10 Q on multi-agent systems |
| 1:45–2:20 | Review | Wrong answers → `practice_test/test2_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** coordinator + subagent demo in `exercises/`, test-2 review, updated weak spots.
