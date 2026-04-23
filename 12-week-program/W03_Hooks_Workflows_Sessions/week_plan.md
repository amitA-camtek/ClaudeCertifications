# W03 — Hooks, Workflows & Sessions

**Domain:** Foundations · 1.4–1.7
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W02 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §2–4, §6 — PreToolUse vs PostToolUse, hook script interface (stdin/stdout JSON, `decision: block/approve`), wiring in `settings.json`, PostToolUse shaping |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §1, §5, §10 — deterministic (hooks/`tool_choice`/`allowedTools`) vs probabilistic (prompt rules); canonical refund-gate scenario |
| 1:40–2:20 | Build | Hook that blocks refunds > $500 and redirects to escalation |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Finish refund hook, verify trigger conditions |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §7–8 — `--resume` (coherent continuation) vs `fork_session` (risky exploration / poisoned recovery); `/compact` for staleness; resume-after-crash trap |
| 1:00–1:15 | Theory | Read [reference.md](reference.md) §9 — fixed prompt chain (known steps) vs adaptive decomposition (open-ended / multi-concern); adaptive-for-fixed-task distractor |
| 1:15–2:00 | Test | **Practice Test 3** — 10 Q on hooks, workflows, sessions |
| 2:00–2:20 | Review | Wrong answers → `practice_test/test3_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** working refund-blocking hook in `exercises/`, test-3 review, updated weak spots.
