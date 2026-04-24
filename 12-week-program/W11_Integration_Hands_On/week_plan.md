# W11 — Integration & Hands-On Exercises

**Domain:** Exam Prep · All Domains
**Budget:** 2 days × 2.5 h = 5 h

## Anti-pattern to avoid vs correct

**Avoid:** "Add it to the system prompt" as the fix for *any* compliance, correctness, or reliability problem — whether it's forcing tool choice, enforcing a policy, shaping output, or scoping a rule.
**Correct:** Reach for the deterministic mechanism — `tool_choice` for forced calls, a `PreToolUse` hook for policy gates, `input_schema` for output shape, `allowedTools` / `paths:` / `.mcp.json` for scope, a separate reviewer session for independence.
**Why it's a trap:** This is the single recurring theme across all 5 exam domains. Prompts are probabilistic; mechanisms are enforced by code. When two distractors differ on *prompt-vs-mechanism*, the mechanism answer is almost always correct. See [integration_notes.md](integration_notes.md) for cross-domain examples.

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Cold-recall drill per [../spaced_repetition_schedule.md](../spaced_repetition_schedule.md) — today: [W10 weak_spots](../W10_Advanced_Context_Provenance/notes/weak_spots.md), [W08 weak_spots](../W08_Validation_Batch_MultiPass/notes/weak_spots.md), [W05 weak_spots](../W05_Claude_Code_Config/notes/weak_spots.md), [W02 weak_spots](../W02_Multi_Agent_Orchestration/notes/weak_spots.md) |
| 0:10–1:15 | Exercise | **Exercise 1 — Multi-Tool Agent with Escalation Logic** · Read [reference.md](reference.md) §2 (week mapping) · Work through [exercises/exercise_1_multi_tool_agent_with_escalation.py](exercises/exercise_1_multi_tool_agent_with_escalation.py) |
| 1:15–2:10 | Exercise | **Exercise 2 — Claude Code Team Workflow Configuration** · Read [reference.md](reference.md) §3 · Work through [exercises/exercise_2_claude_code_team_workflow.md](exercises/exercise_2_claude_code_team_workflow.md) |
| 2:10–2:30 | Operational | Read [operational_topics.md](operational_topics.md) end-to-end — prompt caching, extended thinking, model selection, cost economics. Jot 3-bullet recap + integration pain points → [notes/study_day.md](notes/study_day.md) |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:45 | Exercise | **Exercise 3 — Structured Data Extraction Pipeline** · Read [reference.md](reference.md) §4 · Work through [exercises/exercise_3_structured_extraction_pipeline.py](exercises/exercise_3_structured_extraction_pipeline.py) |
| 0:45–1:30 | Exercise | **Exercise 4 — Multi-Agent Research Pipeline** · Read [reference.md](reference.md) §5 · Work through [exercises/exercise_4_multi_agent_research_pipeline.py](exercises/exercise_4_multi_agent_research_pipeline.py) |
| 1:30–1:50 | Scenario warmup | Skim both non-exercise scenario walkthroughs — [exercises/scenario_4_developer_productivity_walkthrough.md](exercises/scenario_4_developer_productivity_walkthrough.md) and [exercises/scenario_5_ci_cd_walkthrough.md](exercises/scenario_5_ci_cd_walkthrough.md). These fill the 2-of-6 scenario gap not covered by Exercises 1–4 |
| 1:50–2:10 | Drill | **Adjacent-concept discrimination drill** — run [../W12_Final_Exam_Prep/exercises/adjacent_concepts_drill.md](../W12_Final_Exam_Prep/exercises/adjacent_concepts_drill.md) cold: cover the discriminator column, self-test 2–3 pairs per domain. Pairs you can't state the discriminator on → flashcard with `⭐` |
| 2:10–2:25 | Exam | Start **Full Practice Exam 1** (50 Q, all 6 scenarios) — carry over to W12 if needed |
| 2:25–2:30 | Weak spots | Identify 2 weakest domains → [notes/weak_spots.md](notes/weak_spots.md) (feeds W12) |

**Deliverables:** Exercises 1–4 in `exercises/`, Practice Exam 1 score + wrong-answer review in `practice_test/full_exam_1.md`, 2 weakest domains identified.

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
/harvest-scratch 12-week-program/W11_Integration_Hands_On/notes/session_YYYY-MM-DD.md
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
