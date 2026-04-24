# W09 — Context Management

**Domain:** Exam Prep · 5.1–5.3
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Return `[]` (empty result set) on a tool timeout, or return a generic `"operation failed"` string on any error.
**Correct:** Structured error envelope — `{isError: true, errorCategory: "timeout", isRetryable: true, message: "<user-friendly>"}` — so the caller can retry, escalate, or explain the real failure.
**Why it's a trap:** The caller cannot distinguish "no matches" from "I failed". The agent confidently tells the user "no orders found" when actually the warehouse API was down. Silent failures mask outages and turn operational bugs into user-visible data lies. See [reference.md](reference.md) §11.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Cold-recall drill per [../spaced_repetition_schedule.md](../spaced_repetition_schedule.md) — today: [W08 weak_spots](../W08_Validation_Batch_MultiPass/notes/weak_spots.md), [W06 weak_spots](../W06_Plan_Mode_Iteration_CICD/notes/weak_spots.md), [W03 weak_spots](../W03_Hooks_Workflows_Sessions/notes/weak_spots.md) |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–3 — long-session failure modes (context bloat, summarization loss, lost-in-the-middle); bigger window does NOT fix attention quality |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §2–4 — persistent `case_facts` block (IDs / amounts / dates / agreed actions), position-aware ordering (start + end, section headers), trimming verbose tool output at the boundary |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §5–7 — valid escalation triggers (explicit request, policy gap, inability to progress); non-triggers (sentiment, self-rated confidence); multiple-match → ask for identifiers — then follow [exercises/build.md](exercises/build.md) step by step |
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
/harvest-scratch 12-week-program/W09_Context_Management/notes/session_YYYY-MM-DD.md
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
