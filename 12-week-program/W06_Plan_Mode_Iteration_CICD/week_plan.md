# W06 — Plan Mode, Iteration & CI/CD

**Domain:** Applied Knowledge · 3.4–3.6
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Same Claude session generates **and** reviews code in CI (`--resume` the same context); regex-parse the natural-language `claude -p` output.
**Correct:** Separate fresh sessions for generator and reviewer — artifacts-only, no `--resume`. Use `--output-format json --json-schema` for a stable, machine-parseable contract.
**Why it's a trap:** Self-review retains reasoning bias: the reviewer already "knows" why each choice was made and will rationalize its own mistakes instead of catching them. Natural-language output phrasing drifts across model updates; regex that passes today fails silently next month. See [reference.md](reference.md) §6.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W05 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1 — plan mode vs direct execution decision criteria (single-file fix → direct; 45-file migration → plan); Explore subagent for verbose discovery |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §2 — iterative refinement: concrete references (file/function/behavior), TDD red/green/refactor, interview/clarifying-questions pattern |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §3–4 — headless CI (`-p`, `--output-format json`, `--json-schema`); generator and reviewer in **separate** fresh sessions — then follow [exercises/build.md](exercises/build.md) step by step |
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

---

## Note-taking while you read → auto-harvest to `weak_spots.md`

Capture weak spots without breaking reading flow. The flow:

**1. During reading — dump rough bullets into a session scratch file.**

Open (or create) `notes/session_YYYY-MM-DD.md` in a split pane. No format required — just free-form lines:

```markdown
- when does stop_reason=max_tokens happen vs end_turn?
- fork_session vs --resume — fuzzy on the poisoned-context case
- why can't Message Batches do multi-turn tool use?
- TODO: re-do exercise step 3 after reading section 5
- aha: PostToolUse is too late for gates — always PreToolUse
```

**2. End of session — run the slash command** from the repo root:

```
/harvest-scratch 12-week-program/W06_Plan_Mode_Iteration_CICD/notes/session_YYYY-MM-DD.md
```

**3. What it does automatically:**

- Classifies every line as **weak-spot** / **insight** / **todo** / **skip**
- Rewrites weak spots as exam flashcards (`**Q:** ... **A:** ...`) grounded in this week's `reference.md`
- Deduplicates against existing `notes/weak_spots.md` (merges overlapping cards instead of piling up duplicates)
- Appends new flashcards under a `## Harvested from session_YYYY-MM-DD` section
- Appends todos under a `## Todos` section as `- [ ]` checkboxes
- Asks you one clarifying question if a bullet is too vague to flashcard cleanly
- Renames the scratch file to `session_YYYY-MM-DD_harvested.md` so you can tell it's been processed
- Prints a one-line summary (e.g. "4 new flashcards, 2 merged, 1 todo")

**4. Why this setup:**

- Zero format friction while reading (just dump bullets).
- `reference.md` and other study files stay clean — no inline annotations.
- `weak_spots.md` grows as exam-ready flashcards, not raw thoughts — feeds W12 targeted review directly.
- The slash command lives at `.claude/commands/harvest-scratch.md` at the repo root — inspect or tweak it there.
