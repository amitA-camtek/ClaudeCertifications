# W11 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** integration across all domains — multi-tool agent with escalation, Claude Code team workflow, structured extraction pipeline, multi-agent research pipeline.

---

## Talk 1 — "Putting it all together" themes

This week re-uses content from W01–W10. Instead of new videos, use this as a *re-skim guide* — return to the earlier `videos.md` files with a specific question in mind.

### Re-skim for Exercise 1 (Multi-Tool Agent with Escalation)
- W01 `videos.md` — agentic loop, stop_reason handling.
- W03 `videos.md` — PreToolUse hook for deterministic gates (the refund-gate pattern).
- W04 `videos.md` — tool descriptions and structured errors.
- **Key integration idea:** the loop, the tools, and the hook are three independent components. If any one is probabilistic (NL termination, weak description, prompt-only gate), the system is probabilistic.

### Re-skim for Exercise 2 (Claude Code Team Workflow)
- W05 `videos.md` — CLAUDE.md hierarchy, rules with `paths:`, slash commands vs skills.
- W06 `videos.md` — plan mode, headless CI, generator/reviewer isolation.
- **Key integration idea:** team config is *committed*; personal config is *local*. The test is "can a new hire clone the repo and have everything work?"

### Re-skim for Exercise 3 (Structured Extraction Pipeline)
- W07 `videos.md` — categorical criteria, few-shot, `tool_use` + schema, nullable fields.
- W08 `videos.md` — validation-retry, batch for bulk, self-review trap.
- **Key integration idea:** the LLM extracts; a validator verifies; low-confidence goes to human review. Three stages, three different failure modes.

### Re-skim for Exercise 4 (Multi-Agent Research Pipeline)
- W02 `videos.md` — hub-and-spoke, parallel spawning, context isolation.
- W09 `videos.md` — structured errors, valid escalation triggers.
- W10 `videos.md` — provenance, conflict annotation, stratified sampling.
- **Key integration idea:** the value of multi-agent is *isolated subagent contexts* + *preserved provenance through synthesis*. Lose either and it's just expensive prompt chaining.

---

## Talk 2 — Common integration mistakes (watch for these in the exercises)

- **Mixing deterministic and probabilistic controls for the same concern.** If you have a hook blocking refunds over $500 *and* a system-prompt line saying "be careful with refunds," you have one real control (the hook) and a placebo. Remove the placebo.
- **Letting session identity leak between roles.** Generator and reviewer share a session — self-review bias. Coordinator passes its own history to subagents — kills isolation. Each role gets its own context.
- **Schemas + vague prompts.** Schema guarantees shape; prompt guarantees content. Both are needed. `tool_use` + schema + a vague prompt produces well-formed garbage.
- **Retry loops on absent-info cases.** If the document doesn't contain the field, more retries don't help — the info isn't there. Map to `null`, route to human review.
- **Aggregate evaluation.** 95% overall hides the 60% bucket. Stratify.

---

## Talk 3 — Exam-scenario rhythm

On the exam, every scenario has the same rhythm: *a plausible-sounding wrong answer using a known anti-pattern*. The correct answer is usually the less obvious one that addresses the actual failure mode.

Common patterns, re-stated:
- Deterministic gate (hook / `tool_choice` / `allowedTools`) beats prompt-only control.
- Independent reviewer beats same-session review.
- Structured error beats generic "failed."
- Stratified eval beats aggregate.
- Schema + example beats "please respond in JSON."
- Scratchpad + manifest beats bigger context window.

Internalize these five and you have most of the exam.

---

## Optional external viewing

- "Building effective agents" (foundational): https://www.anthropic.com/research/building-effective-agents
- "How we built our multi-agent research system": https://www.anthropic.com/engineering/built-multi-agent-research-system
- Anthropic YouTube channel: https://www.youtube.com/@anthropic-ai/videos
