# W01 — Agentic Loops & Core API

**Domain:** Foundations · 1.1
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Parsing `resp.content` text for "done" / "finished" to terminate the loop, or exiting after a tight iteration cap (3–5 turns).
**Correct:** Terminate only on `stop_reason == "end_turn"`. Keep a high `safety_fuse` (25/50/100) as a crash guard, not a task-level cap.
**Why it's a trap:** Text matching is probabilistic — model phrasing drifts across runs and versions. Tight caps truncate valid multi-step tasks (10+ turns is normal). The API already provides a deterministic termination signal; use it. See [reference.md](reference.md) §7.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Skim [exam_guide_summary.md](exam_guide_summary.md) — 5 domains table + 6 scenario headlines |
| 0:10–1:00 | Theory | Read [exam_guide_summary.md](exam_guide_summary.md) end-to-end; memorize domain weights and which scenarios hit which domains |
| 1:00–1:40 | Theory | Read [reference.md](reference.md) §1–4 — agentic loop lifecycle, `stop_reason` (`tool_use` vs `end_turn`), message-history contract, canonical loop |
| 1:40–2:20 | Build | Minimal agentic loop with the Agent SDK (single tool, until `end_turn`) — follow [exercises/build.md](exercises/build.md) step by step |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Finish the agentic loop, add a second tool |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §7 — anti-patterns (parsing NL for termination, arbitrary iteration caps, `role: "tool"`, silent `max_tokens` → `end_turn`) |
| 1:00–1:45 | Test | **Practice Test 1** — 10 Q on agentic loops → solve [practice_test/test1_questions.md](practice_test/test1_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test1_answers.md](practice_test/test1_answers.md); wrong-answer review → [practice_test/test1_review.md](practice_test/test1_review.md); re-read task statement 1.1 for any miss |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** working loop in `exercises/`, test-1 review in `practice_test/`, updated `notes/weak_spots.md`.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test1_questions.md](practice_test/test1_questions.md) (the table at the bottom) against [practice_test/test1_answers.md](practice_test/test1_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test1_review.md`.

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
/harvest-scratch 12-week-program/W01_Agentic_Loops/notes/session_YYYY-MM-DD.md
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
