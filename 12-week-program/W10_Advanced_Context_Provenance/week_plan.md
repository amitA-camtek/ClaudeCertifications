# W10 — Advanced Context & Provenance

**Domain:** Exam Prep · 5.4–5.6
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W09 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1 — long-session degradation (attention fade, retrieval drift, reasoning drift); scratchpad files as durable state (survives `/compact` and crashes) |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §1 (mitigations B & C), §2 — `/compact` as lossy compression (pair with scratchpad), subagent delegation as context-management tool, crash-recovery manifests (step index + scratchpad, resume by `step_index + 1`) |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §6–7 — aggregate-accuracy trap; stratified sampling by (document_type × field × confidence bucket); source characterization (primary vs derivative, dates, credibility) — then follow [exercises/build.md](exercises/build.md) step by step |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Build a claim-source mapping with temporal data |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §3–5, §8, §8b — per-claim provenance (`claim`, `source_url`, `publication_date`), publication dates disambiguate old-vs-new from real conflict, conflict annotation (not resolution), well-established / contested / single-source tags, content-type-aware rendering (tables for quantitative, prose for narrative) |
| 1:00–1:45 | Test | **Practice Test 10** — 10 Q on advanced context → solve [practice_test/test10_questions.md](practice_test/test10_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test10_answers.md](practice_test/test10_answers.md); wrong-answer review → [practice_test/test10_review.md](practice_test/test10_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** provenance mapping demo in `exercises/`, test-10 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test10_questions.md](practice_test/test10_questions.md) (the table at the bottom) against [practice_test/test10_answers.md](practice_test/test10_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test10_review.md`.
