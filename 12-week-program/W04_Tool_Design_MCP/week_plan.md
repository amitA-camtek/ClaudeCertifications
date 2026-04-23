# W04 — Tool Design & MCP

**Domain:** Foundations · 2.1–2.5
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W03 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — descriptions are the selector; input/output formats, positive + negative boundaries; split vs consolidate for near-similar tools |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3 — structured errors (`isError`, `errorCategory`, `isRetryable`, `message`); retry branches on `isRetryable`, not string parsing |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §4–5 — 4–5 tools per agent max, scoped access per role, `tool_choice` modes — then follow [exercises/build.md](exercises/build.md) step by step to sketch the tool set |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Wire a local MCP server using `.mcp.json` |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §6–8 — `.mcp.json` (project, committed) vs `~/.claude.json` (user, personal), `${ENV_VAR}` expansion for secrets, MCP tools vs resources, built-in tool selection (Read/Grep/Glob/Edit/Write/Bash) |
| 1:00–1:45 | Test | **Practice Test 4** — 10 Q on tool design & MCP → solve [practice_test/test4_questions.md](practice_test/test4_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test4_answers.md](practice_test/test4_answers.md); wrong-answer review → [practice_test/test4_review.md](practice_test/test4_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** MCP config sample in `exercises/`, test-4 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test4_questions.md](practice_test/test4_questions.md) (the table at the bottom) against [practice_test/test4_answers.md](practice_test/test4_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test4_review.md`.

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
/harvest-scratch 12-week-program/W04_Tool_Design_MCP/notes/session_YYYY-MM-DD.md
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
