# W09 — Context Management

**Domain:** Exam Prep · 5.1–5.3
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W08 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–3 — long-session failure modes (context bloat, summarization loss, lost-in-the-middle); bigger window does NOT fix attention quality |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §2–4 — persistent `case_facts` block (IDs / amounts / dates / agreed actions), position-aware ordering (start + end, section headers), trimming verbose tool output at the boundary |
| 1:40–2:20 | Theory+Sketch | Read [reference.md](reference.md) §5–7 — valid escalation triggers (explicit request, policy gap, inability to progress); non-triggers (sentiment, self-rated confidence); multiple-match → ask for identifiers |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Demo error propagation: structured context vs generic errors |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §8–10 — structured errors (`failure_type`, `attempted_query`, `partial_results`, `alternatives`) vs generic/empty; coordinator decides, subagent reports; local recovery (bounded retry → alternative query → ask user) before escalation |
| 1:00–1:45 | Test | **Practice Test 9** — 10 Q on context & reliability → solve [practice_test/test9_questions.md](practice_test/test9_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test9_answers.md](practice_test/test9_answers.md); wrong-answer review → [practice_test/test9_review.md](practice_test/test9_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** context-trimming + error-propagation demos in `exercises/`, test-9 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test9_questions.md](practice_test/test9_questions.md) (the table at the bottom) against [practice_test/test9_answers.md](practice_test/test9_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test9_review.md`.
