# W03 — Hooks, Workflows & Sessions

**Domain:** Foundations · 1.4–1.7
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Put a policy rule ("NEVER refund over $500") in the system prompt; use **PostToolUse** to prevent a destructive action.
**Correct:** **PreToolUse** hook that inspects `tool_input` in code and blocks the call before it runs (e.g. `amount_usd > 500`). PostToolUse is for shaping what the model sees next — redaction, normalization, logging — never for prevention.
**Why it's a trap:** Prompts are probabilistic — the model mostly complies, then fails silently under injection or long conversations. PostToolUse fires *after* the side effect (refund issued, file deleted). The deterministic code gate is the mechanism; the prompt is hope. See [reference.md](reference.md) §11.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Cold-recall drill per [../spaced_repetition_schedule.md](../spaced_repetition_schedule.md) — today: [W02 weak_spots](../W02_Multi_Agent_Orchestration/notes/weak_spots.md), [W01 weak_spots](../W01_Agentic_Loops/notes/weak_spots.md) |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §2–4, §6 — PreToolUse vs PostToolUse, hook script interface (stdin/stdout JSON, `decision: block/approve`), wiring in `settings.json`, PostToolUse shaping |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §1, §5, §10 — deterministic (hooks/`tool_choice`/`allowedTools`) vs probabilistic (prompt rules); canonical refund-gate scenario |
| 1:40–2:20 | Build | Hook that blocks refunds > $500 and redirects to escalation — follow [exercises/build.md](exercises/build.md) step by step |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Finish refund hook, verify trigger conditions |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §7–8 — `--resume` (coherent continuation) vs `fork_session` (risky exploration / poisoned recovery); `/compact` for staleness; resume-after-crash trap |
| 1:00–1:15 | Theory | Read [reference.md](reference.md) §9 — fixed prompt chain (known steps) vs adaptive decomposition (open-ended / multi-concern); adaptive-for-fixed-task distractor |
| 1:15–2:00 | Test | **Practice Test 3** — 10 Q on hooks, workflows, sessions → solve [practice_test/test3_questions.md](practice_test/test3_questions.md) (table at bottom) |
| 2:00–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test3_answers.md](practice_test/test3_answers.md); wrong-answer review → [practice_test/test3_review.md](practice_test/test3_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** working refund-blocking hook in `exercises/`, test-3 review, updated weak spots.

## Placeholder note — `.claude/settings.json`

The hook-wiring placeholder is provided as [exercises/settings_snippet.json](exercises/settings_snippet.json) inside the week folder — it is **not** a real `.claude/settings.json`. When you want to test the hook end-to-end in Claude Code, copy the contents of your completed `settings_snippet.json` into your project's actual `.claude/settings.json` at the project root.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test3_questions.md](practice_test/test3_questions.md) (the table at the bottom) against [practice_test/test3_answers.md](practice_test/test3_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test3_review.md`.

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
/harvest-scratch 12-week-program/W03_Hooks_Workflows_Sessions/notes/session_YYYY-MM-DD.md
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
