# W05 — Claude Code Configuration

**Domain:** Applied Knowledge · 3.1–3.3
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** Put every rule in root `CLAUDE.md`; or keep team-wide config in `~/.claude/CLAUDE.md` (user scope).
**Correct:** Scope path-specific rules in `.claude/rules/*.md` with `paths:` frontmatter. Team config goes in `<repo>/CLAUDE.md` or `<repo>/.claude/CLAUDE.md` — committed to git so teammates stay in sync.
**Why it's a trap:** Every line in root `CLAUDE.md` is paid for on every turn, diluting attention with irrelevant rules. User scope isn't shared — teammates drift out of sync and behavior becomes per-machine. Scope and commit. See [reference.md](reference.md) §9.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Cold-recall drill per [../spaced_repetition_schedule.md](../spaced_repetition_schedule.md) — today: [W04 weak_spots](../W04_Tool_Design_MCP/notes/weak_spots.md), [W02 weak_spots](../W02_Multi_Agent_Orchestration/notes/weak_spots.md) |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — three scopes (user / project / subdirectory), merge semantics, CLAUDE.md hierarchy and precedence, `/memory` for diagnostics |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3–4 — `@import` modular configs, `.claude/rules/*.md` with YAML `paths:` frontmatter for conditional loading |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §5–6 — `.claude/commands/` (user-invoked saved prompts) vs `.claude/skills/<name>/SKILL.md` (multi-step capability, `allowed-tools`, `context: fork`) — then follow [exercises/build.md](exercises/build.md) step by step |
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

## Placeholder note — `.claude/commands/` and `.claude/skills/`

The command + skill placeholders live under [exercises/.claude/](exercises/.claude/) inside the week folder — this subdirectory is **not** picked up by Claude Code (Claude Code only reads `.claude/` at the project root or `~/.claude/`). When you want to test your slash command and skill live, copy the folder contents into your project's real `.claude/`:

```
cp -r exercises/.claude/* <project-root>/.claude/
```

Keeping the practice copy inside the week folder means each week's experiments stay self-contained and don't collide with other weeks' skills.

## Validation prompt

Paste this at the start of the Review block to have Claude grade your attempt and write the review file:

> Grade my answers in [practice_test/test5_questions.md](practice_test/test5_questions.md) (the table at the bottom) against [practice_test/test5_answers.md](practice_test/test5_answers.md). For each wrong answer: state my pick, the correct pick, why mine was wrong, and why the correct one is right — citing the relevant § of [reference.md](reference.md). Write the review to `practice_test/test5_review.md`.

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
/harvest-scratch 12-week-program/W05_Claude_Code_Config/notes/session_YYYY-MM-DD.md
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
