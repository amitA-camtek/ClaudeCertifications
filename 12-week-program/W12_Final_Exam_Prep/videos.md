# W12 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** final review; pattern recognition for exam distractors; exam-day rhythm.

---

## Talk 1 — The "wrong answer patterns" you must reflex-recognize

Restated from the `LEARNING_PROGRAM.md` master list, plus context for each:

| Anti-pattern | Why it's wrong | Right answer involves |
|---|---|---|
| "Add to the system prompt that X is mandatory" | Probabilistic; non-zero failure rate | PreToolUse hook / `tool_choice` / `allowedTools` |
| "Have the model self-report confidence 1–10" | Miscalibrated, especially on hard cases | Field-level structured confidence + stratified eval |
| "Use sentiment analysis to trigger escalation" | Sentiment ≠ complexity | Explicit-request / policy-gap / inability-to-progress triggers |
| "Switch to a bigger context window" | Attention quality doesn't scale | Split into passes; scratchpad + manifest |
| "Return generic 'operation failed' on error" | Kills caller recovery | Structured error with failure_type, attempted_query, partial_results, alternatives |
| "Empty result set on timeout (mark as success)" | Silent suppression | `isError: true, errorCategory: "timeout", isRetryable: true` |
| "Retry with exponential backoff forever" | Useless when info is absent from source | Map to `null`; route to human review |
| "Give every agent every tool" | Selection degrades past ~7 tools | Scope 4–5 tools per role |
| "Same session writes and reviews the code" | Self-review bias | Independent reviewer session, fresh `messages[]` |
| "Use Message Batches for pre-merge checks" | 24 h window, no SLA | Sync; batches are for overnight bulk |
| "Use adaptive decomposition for a known 3-step process" | Overhead without benefit | Fixed prompt chain |
| "Parse response text for 'done' to terminate loop" | Fragile, wrong abstraction | `stop_reason == "end_turn"` |
| "Use `role: 'tool'` messages" | Not Anthropic schema; that's OpenAI | `tool_use` / `tool_result` blocks |
| "Synthesize by picking the most recent source" | Loses contested evidence | Annotate conflicts with attribution + dates |

Drill this table until you can answer "what's the right answer" for each row in under 15 seconds.

---

## Talk 2 — The six exam scenarios (framing)

The exam shows 4 of 6 scenarios. Know the *type* each one is testing so you can prime the right mental model:

1. **Customer support agent** — deterministic gates (hooks), escalation triggers, structured errors, multiple-match disambiguation. Domains 1, 5.
2. **Code generation / refactor** — plan mode, generator/reviewer isolation, iterative refinement. Domain 3.
3. **Multi-agent research** — hub-and-spoke, parallel subagents, provenance, conflict annotation. Domains 1, 5.
4. **Developer productivity / team workflow** — CLAUDE.md hierarchy, rules, skills vs commands, MCP team vs user. Domain 3.
5. **CI/CD integration** — headless mode, JSON schema, exit codes, sync vs batch. Domains 3, 4.
6. **Structured extraction** — `tool_use` + schema, nullable, enums, validation-retry, stratified eval. Domain 4.

For each, ask: *what's the failure mode distractor likely to dangle, and what's the real fix?*

---

## Talk 3 — Exam-day rhythm

- **First pass: flag and move.** Read each scenario's first sub-question, answer if obvious, flag and skip if not. Don't burn 10 minutes on one question.
- **Second pass: anti-pattern scan.** For each flagged question, look for the anti-pattern distractor first (any of the 14 rows above). Eliminate those options; your answer is usually one of the remaining 1–2.
- **Third pass: gut-check the remaining.** If two options look right, ask "which one is *deterministic*?" or "which one *preserves recovery information*?" The exam rewards those properties.
- **Time budget:** if the exam is ~100 min for ~50 questions, that's ~2 min/Q. You will finish first-pass in ~60 min and have ~40 min for flagged + final review. Don't let early scenarios eat your review budget.
- **Don't second-guess.** On the third pass, only change an answer if you have a *specific* new reason. Revising on gut feel tends to lose points.

---

## Exam-day cheatsheet (one screen)

- Stop reasons: `end_turn` (done), `tool_use` (run tool), `max_tokens` (re-check, don't treat as success).
- Messages schema: `assistant` with `tool_use` block, `user` with `tool_result` block. No `role: "tool"`.
- Deterministic ≻ probabilistic for gates.
- Fresh session for reviewer.
- 4–5 tools per agent, rich descriptions with boundaries.
- Structured errors: `isError`, `errorCategory`, `isRetryable`, `message`.
- `.mcp.json` = team/committed; `~/.claude.json` = personal.
- Nullable fields prevent hallucination.
- Few-shot on edge cases, 2–4 examples, show reasoning.
- Batches: 50% off, 24 h, single-turn, `custom_id`.
- Stratify eval by type × field.
- Scratchpad + manifest > bigger context.
- Annotate conflicts with dates; don't resolve arbitrarily.
- Valid escalation: explicit request / policy gap / inability to progress. Not sentiment.

---

## Optional external viewing

- Anthropic YouTube channel: https://www.youtube.com/@anthropic-ai/videos
- "Building effective agents": https://www.anthropic.com/research/building-effective-agents
- "How we built our multi-agent research system": https://www.anthropic.com/engineering/built-multi-agent-research-system
