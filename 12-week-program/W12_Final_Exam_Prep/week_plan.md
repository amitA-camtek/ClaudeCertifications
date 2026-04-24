# W12 — Final Exam Prep

**Domain:** Exam Prep · Review & Practice (All Domains)
**Budget:** 2 days × 2.5 h = 5 h
**Goal:** walk into exam day with ≥ 720/1000 readiness.

## Anti-pattern to avoid vs correct

**Avoid:** Cram new content in the final days — read fresh reference material, attempt new exercises, or pick up a new topic "to close the gap".
**Correct:** Only review previously-studied material: `notes/weak_spots.md` across W01–W11, the wrong-answer table in [reference.md](reference.md) §4, and [exercises/anti_patterns_master_list.md](exercises/anti_patterns_master_list.md) end-to-end. For each anti-pattern, generate the exam question that would make the distractor tempting — saying the trap out loud is the drill.
**Why it's a trap:** New content this late doesn't consolidate; it displaces retrieval of already-mastered material and raises exam-day anxiety. The master list IS the distractor catalog — the exam tests the exact traps it documents. Reject-on-sight recognition beats fresh study.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Pull 2 weakest domains from [W11 notes/weak_spots.md](../W11_Integration_Hands_On/notes/weak_spots.md) |
| 0:10–1:00 | Targeted review | Weakest domain — re-read task statements in [reference.md](reference.md) §3 and [exercises/domain_cheatsheet.md](exercises/domain_cheatsheet.md); re-do missed Q's |
| 1:00–1:50 | Targeted review | 2nd-weakest domain — same drill against [reference.md](reference.md) §3 and [exercises/domain_cheatsheet.md](exercises/domain_cheatsheet.md) |
| 1:50–2:30 | Exam | **Full Practice Exam 2** (50 Q) — use [exercises/scenario_drills.md](exercises/scenario_drills.md) as scenario warm-up; start the exam; finish in buffer if needed |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review Exam 2 results |
| 0:10–1:40 | Exam | **Full Practice Exam 3** (50 Q, **timed**) — walk through [exercises/exam_day_playbook.md](exercises/exam_day_playbook.md) beforehand to set pacing |
| 1:40–2:15 | Review | Wrong answers, focus on anti-patterns and gotchas — cross-reference [exercises/anti_patterns_master_list.md](exercises/anti_patterns_master_list.md) |
| 2:15–2:30 | Final | Light review of key concepts — [reference.md](reference.md) fast-recap sections + [exercises/domain_cheatsheet.md](exercises/domain_cheatsheet.md); write final `notes/exam_day_cheatsheet.md` |

**Exam day follows immediately after this week.**

**Deliverables:** Practice Exams 2 & 3 reviews in `practice_test/`, final cheatsheet in `notes/exam_day_cheatsheet.md`.

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
/harvest-scratch 12-week-program/W12_Final_Exam_Prep/notes/session_YYYY-MM-DD.md
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
