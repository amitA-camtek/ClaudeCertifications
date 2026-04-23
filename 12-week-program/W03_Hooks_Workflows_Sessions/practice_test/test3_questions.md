# Practice Test 3 — Hooks, Workflows & Sessions

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 1.4–1.7

## Instructions
Solve all 10 questions before opening `test3_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A hook script finishes processing a `PreToolUse` event and prints nothing to stdout before exiting with code 0. What does the harness do next?
- A. Block the tool call defensively and surface an error to the model.
- B. Retry the hook up to three times before giving up.
- C. Pass through — the tool runs as if no hook were registered.
- D. Prompt the user interactively to approve or block the call.

### Q2. A PHI-handling tool returns patient records that contain names and SSNs. The team wants raw PHI to never enter the model's context window, but the model still needs a sanitized view of the data to reason over. Which mechanism fits best?
- A. A `PreToolUse` hook that blocks the tool whenever PHI is detected in `tool_input`.
- B. A `PostToolUse` hook that scans `tool_response`, replaces SSN/name patterns with `[REDACTED]`, and returns the sanitized version.
- C. A `SessionStart` hook that adds "Do not reveal PHI" to the system prompt.
- D. Increase the context window so the model can tolerate larger unredacted payloads.

### Q3. A developer registers a hook under `PostToolUse` with `matcher: "issue_refund"` whose script returns `decision: "block"` whenever `amount_usd > 500`. In production, a $742 refund still gets issued and the block message then appears in the model's transcript. Why?
- A. The `matcher` field must be a regex — an exact name silently fails.
- B. `decision: "block"` is only honored when the exit code is non-zero.
- C. `PostToolUse` fires after the tool already ran; it cannot prevent the side effect.
- D. Hooks registered in project `settings.json` are overridden by `~/.claude/settings.json`.

### Q4. Yesterday's session named `api-migration` ended when a file write corrupted a config and the model spent the final turns rationalizing the broken state. You need to continue the migration work today. What is the correct move?
- A. `claude --resume api-migration` — the model will self-correct now that it has slept on it.
- B. Fork from a clean point before the corruption (or start fresh with a hand-written summary); do not resume into the poisoned history.
- C. Resume the session and immediately run `/compact` to erase the bad turns.
- D. Increase the context window and resume — a larger window will dilute the poisoned turns.

### Q5. Which statement about the `decision` field in hook stdout is correct?
- A. `decision: "approve"` on a `PostToolUse` hook causes the tool to re-run.
- B. Omitting `decision` and exiting 0 means pass-through (default harness behavior).
- C. `decision: "block"` discards the `reason` string silently.
- D. `decision` is only read on non-zero exit codes.

### Q6. An engineer's "fix" for a runaway Bash-tool loop is to raise the system prompt temperature and add "Please stop after 5 iterations" to CLAUDE.md. A week later, a different prompt talks the model past 5 iterations again. What is the reference's prescribed fix?
- A. Lower the temperature to 0 so the instruction is always followed.
- B. Rely on a global "max iterations" cap that truncates any tool loop at a fixed number.
- C. Register a hook that blocks the specific abusive pattern, and keep a high safety fuse as backup.
- D. Move the "stop after 5 iterations" rule from CLAUDE.md into the user-level system prompt.

### Q7. A customer-support pipeline runs four known steps every time: classify intent → look up order → draft response → confirm with customer. The architect proposes adaptive decomposition with a coordinator that spawns subagents per request. According to the reference, why is this the wrong call?
- A. Adaptive decomposition cannot integrate with hooks.
- B. Subagents cannot call tools that use a `matcher` pattern.
- C. When the steps are fixed, adaptive decomposition adds a reasoning turn and a failure mode for no benefit; a fixed prompt chain is simpler.
- D. Fixed chains cannot log audit data, so compliance will fail.

### Q8. A session has ballooned to hundreds of turns on a long-running refactor. The model now contradicts decisions it helped make 80 turns ago and latency is creeping up, but the work is still coherent and the developer wants to keep the relevant state. What should they try first?
- A. Start a new session every turn to prevent any staleness from accumulating.
- B. Request a larger-context model — bigger windows fix stale context.
- C. Run `/compact` to summarize the history and continue with the summary as the new baseline.
- D. Use `fork_session` and abandon the original — the history is irrecoverable.

### Q9. A team wants "one uniform refund policy that applies no matter which subagent tries to issue a refund." Which setup correctly enforces that?
- A. Copy the refund-gate hook command into each subagent's `AgentDefinition` tool list.
- B. Register a single `PreToolUse` hook with `matcher: "issue_refund"` in `.claude/settings.json`; it applies harness-wide wherever the tool is called.
- C. Duplicate the rule "NEVER refund over $500" in every subagent's system prompt.
- D. Register the hook under `UserPromptSubmit` so it is checked before any subagent runs.

### Q10. A senior engineer says, "Hooks and prompt rules are basically the same thing — pick whichever is convenient." Which rebuttal matches the reference?
- A. Correct in practice; the exam only distinguishes them pedagogically.
- B. Prompts are deterministic and hooks are probabilistic, so prompts are preferred for safety.
- C. Hooks are deterministic runtime code that cannot be talked out of it; prompt rules are probabilistic guidance the model obeys ~98% of the time. For policy/safety/compliance, pick the hook.
- D. Both are probabilistic, but hooks have lower latency so they are preferred.

## Your answers
| Q  | Answer |
|----|--------|
| 1  |        |
| 2  |        |
| 3  |        |
| 4  |        |
| 5  |        |
| 6  |        |
| 7  |        |
| 8  |        |
| 9  |        |
| 10 |        |
