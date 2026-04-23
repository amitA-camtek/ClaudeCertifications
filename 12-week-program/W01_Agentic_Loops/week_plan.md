# W01 — Agentic Loops & Core API

**Domain:** Foundations · 1.1
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Skim [exam_guide_summary.md](exam_guide_summary.md) — 5 domains table + 6 scenario headlines |
| 0:10–1:00 | Theory | Read [exam_guide_summary.md](exam_guide_summary.md) end-to-end; memorize domain weights and which scenarios hit which domains |
| 1:00–1:40 | Theory | Read [reference.md](reference.md) §1–4 — agentic loop lifecycle, `stop_reason` (`tool_use` vs `end_turn`), message-history contract, canonical loop |
| 1:40–2:20 | Build | Minimal agentic loop with the Agent SDK (single tool, until `end_turn`) |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Finish the agentic loop, add a second tool |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §7 — anti-patterns (parsing NL for termination, arbitrary iteration caps, `role: "tool"`, silent `max_tokens` → `end_turn`) |
| 1:00–1:45 | Test | **Practice Test 1** — 10 Q on agentic loops |
| 1:45–2:20 | Review | Wrong answers, re-read task statement 1.1 → `practice_test/test1_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** working loop in `exercises/`, test-1 review in `practice_test/`, updated `notes/weak_spots.md`.
