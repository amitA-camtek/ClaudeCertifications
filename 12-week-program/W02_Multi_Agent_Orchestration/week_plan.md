# W02 — Multi-Agent Orchestration

**Domain:** Foundations · 1.2–1.3
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Give every subagent every tool "for maximum flexibility", or let subagents share memory / see each other's context.
**Correct:** Scope each subagent to ~4–5 role-relevant tools; isolate context per subagent; coordinator delegates via structured prompts and receives compact return values (hub-and-spoke).
**Why it's a trap:** Tool-selection quality degrades past ~5–7 tools as near-similar descriptions blur. Shared memory re-creates single-agent problems (context bloat, poisoned trails from failed branches) at higher cost. Isolation is the *whole point* of the pattern. See [reference.md](reference.md) §9.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Cold-recall drill per [../spaced_repetition_schedule.md](../spaced_repetition_schedule.md) — today: [W01 weak_spots](../W01_Agentic_Loops/notes/weak_spots.md) |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — why multi-agent, hub-and-spoke pattern, coordinator role, subagent context isolation |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3–4 — `Task` tool for subagent spawning, `allowedTools` must include `"Task"`, `AgentDefinition` fields |
| 1:40–2:20 | Build | Coordinator + 2 subagents, explicit context passing — follow [exercises/build.md](exercises/build.md) step by step |
| 2:20–2:30 | Summary | 3-bullet recap → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Add parallel subagent execution + `fork_session` for branched exploration |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §7–8 — decomposition pitfalls (narrow → coverage gaps, broad → subagent drowning), iterative refinement, fixed chains vs adaptive |
| 1:00–1:45 | Test | **Practice Test 2** — 10 Q on multi-agent systems → solve [practice_test/test2_questions.md](practice_test/test2_questions.md) (table at bottom) |
| 1:45–2:20 | Review | Paste the validation prompt below; grade against [practice_test/test2_answers.md](practice_test/test2_answers.md); wrong-answer review → [practice_test/test2_review.md](practice_test/test2_review.md) |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** coordinator + subagent demo in `exercises/`, test-2 review, updated weak spots.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test2_questions.md](practice_test/test2_questions.md) (the table at the bottom) against [practice_test/test2_answers.md](practice_test/test2_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test2_review.md`.

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
/harvest-scratch 12-week-program/W02_Multi_Agent_Orchestration/notes/session_YYYY-MM-DD.md
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
