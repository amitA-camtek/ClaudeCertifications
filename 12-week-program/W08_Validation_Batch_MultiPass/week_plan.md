# W08 — Validation, Batch & Multi-Pass

**Domain:** Applied Knowledge · 4.4–4.6
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W07 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — structure vs semantics split; validation-retry loop (append **specific** validator error + source + prior output, bounded to 2–3 attempts) |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3–4 — when retries can't help (absent source info); `detected_pattern` fields for pattern-aware early termination |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §5 — sync vs Message Batches (50% cheaper, up to 24 h, single-turn, `custom_id`); SLA-window scheduling — then follow [exercises/build.md](exercises/build.md) step by step |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Self-review limitation demo: same session retains reasoning context |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §6–7 — self-review bias; independent reviewer instance (fresh `messages[]`, new system prompt); per-record pass + cross-record integration pass |
| 1:00–1:45 | Test | **Practice Test 8** — 10 Q on validation & multi-pass → solve [practice_test/test8_questions.md](practice_test/test8_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test8_answers.md](practice_test/test8_answers.md); wrong-answer review → [practice_test/test8_review.md](practice_test/test8_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** validation-retry example + multi-pass script in `exercises/`, test-8 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test8_questions.md](practice_test/test8_questions.md) (the table at the bottom) against [practice_test/test8_answers.md](practice_test/test8_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test8_review.md`.
