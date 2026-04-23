# W05 — Claude Code Configuration

**Domain:** Applied Knowledge · 3.1–3.3
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W04 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — three scopes (user / project / subdirectory), merge semantics, CLAUDE.md hierarchy and precedence, `/memory` for diagnostics |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3–4 — `@import` modular configs, `.claude/rules/*.md` with YAML `paths:` frontmatter for conditional loading |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §5–6 — `.claude/commands/` (user-invoked saved prompts) vs `.claude/skills/<name>/SKILL.md` (multi-step capability, `allowed-tools`, `context: fork`) |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Add `SKILL.md` with frontmatter: `context: fork`, `allowed-tools`, `argument-hint` |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §4, §8 — path-scoped rules via `paths:` glob patterns; worked scope-resolution scenarios (rule vs subdirectory CLAUDE.md vs skill invocation) |
| 1:00–1:45 | Test | **Practice Test 5** — 10 Q on Claude Code config → solve [practice_test/test5_questions.md](practice_test/test5_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test5_answers.md](practice_test/test5_answers.md); wrong-answer review → [practice_test/test5_review.md](practice_test/test5_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** working skill + slash command in `exercises/`, test-5 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test5_questions.md](practice_test/test5_questions.md) (the table at the bottom) against [practice_test/test5_answers.md](practice_test/test5_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test5_review.md`.
