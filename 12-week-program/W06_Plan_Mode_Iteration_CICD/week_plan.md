# W06 — Plan Mode, Iteration & CI/CD

**Domain:** Applied Knowledge · 3.4–3.6
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W05 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1 — plan mode vs direct execution decision criteria (single-file fix → direct; 45-file migration → plan); Explore subagent for verbose discovery |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §2 — iterative refinement: concrete references (file/function/behavior), TDD red/green/refactor, interview/clarifying-questions pattern |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §3–4 — headless CI (`-p`, `--output-format json`, `--json-schema`); generator and reviewer in **separate** fresh sessions |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Add a second CI invocation with separate reviewer session (context isolation) |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §5 — Message Batches API (50% cheaper, up to 24 h, `custom_id`, single-turn only); sync for blocking pre-merge checks vs batch for overnight bulk; SLA-window calculation |
| 1:00–1:45 | Test | **Practice Test 6** — 10 Q on plan mode & CI/CD → solve [practice_test/test6_questions.md](practice_test/test6_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test6_answers.md](practice_test/test6_answers.md); wrong-answer review → [practice_test/test6_review.md](practice_test/test6_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** working CI invocation script in `exercises/`, test-6 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test6_questions.md](practice_test/test6_questions.md) (the table at the bottom) against [practice_test/test6_answers.md](practice_test/test6_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test6_review.md`.
