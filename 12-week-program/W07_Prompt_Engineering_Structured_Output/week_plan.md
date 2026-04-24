# W07 — Prompt Engineering & Structured Output

**Domain:** Applied Knowledge · 4.1–4.3
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Ask for JSON in natural language ("output JSON with these fields: ..."); use `tool_choice: auto` for mandatory extraction.
**Correct:** Declare a tool with `input_schema`, then force the call with `tool_choice: {"type": "tool", "name": "..."}`. Read the JSON off the `tool_use` block.
**Why it's a trap:** NL JSON requests produce trailing commas, markdown fences, commentary around the JSON, unquoted keys, and shape drift across runs. `auto` lets the model skip the extraction entirely and reply in prose. Tool-use gives you SDK-guaranteed syntactic validity. See [reference.md](reference.md) §9.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W06 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §2 — categorical criteria (explicit thresholds, feature checks) vs vague wording (`important`, `confident`); false-positive-impact framing |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3 — few-shot = 2–4 examples on ambiguous edge cases (not canonical ones), show reasoning, placement in system prompt vs message pairs |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §4 — `tool_use` + `input_schema` + forced `tool_choice` for structured output; schemas fix **syntax**, not semantics — then follow [exercises/build.md](exercises/build.md) step by step |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Exercise `tool_choice` modes: `auto` vs `any` vs forced specific tool |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §6–7 — required / optional / nullable (nullable is the anti-hallucination lever); enums with `"other"` + detail field for extensibility |
| 1:00–1:45 | Test | **Practice Test 7** — 10 Q on prompt engineering → solve [practice_test/test7_questions.md](practice_test/test7_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test7_answers.md](practice_test/test7_answers.md); wrong-answer review → [practice_test/test7_review.md](practice_test/test7_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** JSON-schema tool call in `exercises/`, test-7 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test7_questions.md](practice_test/test7_questions.md) (the table at the bottom) against [practice_test/test7_answers.md](practice_test/test7_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test7_review.md`.

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
/harvest-scratch 12-week-program/W07_Prompt_Engineering_Structured_Output/notes/session_YYYY-MM-DD.md
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
