# W03 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** PreToolUse vs PostToolUse hooks, deterministic vs probabilistic controls, `--resume` vs `fork_session`, `/compact`, crash recovery.

---

## Talk 1 — Hooks in Claude Code (deterministic gates)

- **The key distinction: deterministic vs probabilistic.**
  - *Probabilistic:* "Please never refund over $500 without manager approval" in the system prompt. Works most of the time. Non-zero failure rate. **Will fail the exam distractor test.**
  - *Deterministic:* a PreToolUse hook intercepts the `tool_use` block, inspects the arguments, and blocks the call. Zero probability of bypass.
- **Hook contract:** a hook is a script wired in `.claude/settings.json`. Claude Code pipes a JSON event to stdin; the script writes JSON to stdout. The critical field is `decision`: `"block"`, `"approve"`, or omit for pass-through. `"block"` returns a reason to the model, which then chooses a different path.
- **PreToolUse vs PostToolUse:**
  - **PreToolUse** fires before the tool executes. Use for gates — auth checks, dollar thresholds, path-allowlist validation.
  - **PostToolUse** fires after. Use for *shaping* the result — redacting secrets, trimming verbose output, adding audit log entries. It cannot prevent the call from happening; the side effect is already done.
- **Canonical exam scenario — the refund gate:** a PreToolUse hook on the `issue_refund` tool that checks `amount > 500` and blocks with `decision: "block"`, `reason: "Refunds over $500 require manager approval"`. The model receives the reason and routes the conversation to escalation.
- **Anti-pattern:** using PostToolUse to "undo" a destructive action. By then the refund has been issued. Gates belong in PreToolUse.

---

## Talk 2 — Sessions: `--resume`, `fork_session`, `/compact`

- **`--resume <name>`** is for coherent continuation. Same context, same tools, same history. Right for "same task, picked up tomorrow."
- **`fork_session`** is for *branched* work. From a known-good checkpoint, spawn a divergent path to try something risky. Two use cases:
  1. **Exploration:** test approach A and approach B without each seeing the other's context.
  2. **Poisoned-context recovery:** the session has gone off the rails (bad intermediate result, irrelevant tangent). Fork from the last good checkpoint, skip the poison.
- **`/compact`** collapses long history into a summary to free up tokens. Lossy — numbers, dates, and IDs are the first things to disappear. Pair with an explicit scratchpad file if precision matters.
- **Resume-after-crash trap:** if a session crashed mid-tool-call, naive `--resume` may retry a non-idempotent action (double refund, duplicate email). Always checkpoint "intended action" before calling the tool, and "action completed" after. Recovery reads the manifest and skips completed steps.

---

## Talk 3 — Fixed chains vs adaptive decomposition (again, from a workflow angle)

- **Fixed prompt chains** are just a sequence of LLM calls you hard-code. No agentic loop, no tool dynamism. Best for stable pipelines — data extraction, known reviews, compliance checks.
- **Adaptive decomposition** requires an agentic loop with `stop_reason == "tool_use"` branching, and usually `Task` for subagents. Right for open-ended / multi-concern problems.
- **Distractor alert:** "use adaptive decomposition for a 3-step customer audit that always runs the same way." Wrong — a fixed chain is cheaper, more predictable, easier to debug, and adequate.

---

## Exam-relevance one-liners

- "Add a strict instruction to the system prompt" → **probabilistic, insufficient** — prefer a hook.
- "Use PostToolUse to block a refund" → **too late** — gates belong in PreToolUse.
- "Resume the crashed session directly" → risk of duplicate side effects; use a manifest + idempotency key.
- "Fork the session to keep the main thread alive while trying something risky" → correct use of `fork_session`.

---

## Optional external viewing

- Search — Claude Code hooks: https://www.youtube.com/results?search_query=claude+code+hooks+tutorial
- Search — Claude Agent SDK tutorial: https://www.youtube.com/results?search_query=claude+agent+sdk+tutorial
- Anthropic YouTube channel: https://www.youtube.com/@anthropic-ai/videos
