# W08 — Validation, Batch & Multi-Pass

**Domain:** Applied Knowledge · 4.4–4.6
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Use Message Batches for a blocking pre-merge check (because they're 50% cheaper); treat schema-validation success as "extraction is correct".
**Correct:** Synchronous `claude -p` for blocking paths; reserve Batches for latency-tolerant bulk (overnight scoring of 10k docs). For correctness, pair schema validation (shape) with a second-pass semantic validator (meaning).
**Why it's a trap:** Batches have up to a 24 h window with no SLA — a PR sitting in "checks pending" that long is unacceptable. And a schema guarantees **shape**, not **meaning**: the model can fill `vendor_name` with the customer, pick the wrong enum, or fabricate a plausible date. See [reference.md](reference.md) §8.

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
/harvest-scratch 12-week-program/W08_Validation_Batch_MultiPass/notes/session_YYYY-MM-DD.md
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
