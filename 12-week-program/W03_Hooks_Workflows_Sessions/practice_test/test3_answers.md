# Practice Test 3 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | C |
| 2 | B |
| 3 | C |
| 4 | B |
| 5 | B |
| 6 | C |
| 7 | C |
| 8 | C |
| 9 | B |
| 10 | C |

## Detailed explanations

### Q1 — Answer: C

**Why C is correct:** The reference's exit-code table states: "Exit 0, no `decision` field → pass-through." The harness treats silence-plus-success as "no opinion, let the tool run." (§3)

**Why the others are wrong:**
- A. Defensive blocking is what happens on *non-zero* exit, not on exit 0 with empty stdout.
- B. There is no retry semantics described in the reference; hooks are a single-shot JSON contract.
- D. Hooks are non-interactive; the harness does not escalate to the user on silent success.

**Reference:** §3 of reference.md (stdin/stdout JSON contract, exit codes)

### Q2 — Answer: B

**Why B is correct:** The reference's PostToolUse use-case table lists "Redaction — scan the tool result for SSN / email / credit-card patterns; replace with `[REDACTED]` before it enters the model's context." PostToolUse is precisely the shaping hook for sanitizing a result before the model sees it. (§6)

**Why the others are wrong:**
- A. Blocking the tool denies the model the sanitized data it needs to do its job; the goal is to let the tool run and then redact.
- C. A SessionStart prompt rule is probabilistic guidance — the model can still leak PHI and raw PHI still hits context. The reference says deterministic redaction beats prompt rules (§5, §11).
- D. "Increase context window" is explicitly flagged as the wrong answer to staleness/noise problems; it does not redact anything (§8, §11).

**Reference:** §6 of reference.md (PostToolUse as a shaping tool)

### Q3 — Answer: C

**Why C is correct:** The reference's "Exam distractor pattern" in §4 nails this exact case: "a config where the hook is registered under `PostToolUse` but the stated goal is 'prevent refunds over $500 from executing.' Wrong — PostToolUse fires after the refund already ran. The money is out. Move it to `PreToolUse`." The block message still reaches the model, but the refund has already been issued. (§2, §4, §11)

**Why the others are wrong:**
- A. `matcher` accepts exact tool names, regex, or `"*"` — exact names work fine (§4).
- B. Non-zero exit is treated as a *hook failure*, not as the trigger for honoring `decision: "block"` (§3).
- D. The reference does not describe project settings being overridden silently by user-global settings in a way that changes hook semantics.

**Reference:** §2, §4, §11 of reference.md (PreToolUse vs PostToolUse distinction)

### Q4 — Answer: B

**Why B is correct:** The reference's resume-vs-fork decision rule states: "Last turn crashed / wrote bad data / model got confused → **Fork** from a clean point (or start fresh) — **never resume**." The poisoned history will mis-steer the next turn. (§7, §11)

**Why the others are wrong:**
- A. The model does not "self-correct" — the broken state and rationale sit in the history and poison future turns. This is called out as a canonical distractor (§7).
- C. `/compact` summarizes but still carries the rationale forward; the reference prescribes fork for poisoned sessions, not compact.
- D. "Increase the context window" is explicitly rejected — attention degrades regardless of cap; bigger windows do not dilute poison (§8, §11).

**Reference:** §7, §11 of reference.md (sessions, resume-vs-fork decision rule)

### Q5 — Answer: B

**Why B is correct:** The exit-code table states: "Exit 0, no `decision` field → pass-through. Harness uses its default (usually pass-through)." Omitting `decision` with a clean exit is the explicit pass-through contract. (§3)

**Why the others are wrong:**
- A. `PostToolUse` fires *after* the tool already ran; `approve` there means pass the result through unmodified, not re-execute the tool (§3 table).
- C. `decision: "block"` feeds the `reason` string back to the model as the tool_result — it is not discarded; it is how the model learns why and recovers (§3).
- D. `decision` is read on exit 0; non-zero exits are treated as hook failures, not as the vehicle for `decision` semantics (§3).

**Reference:** §3 of reference.md (Output stdout, decision values, exit codes)

### Q6 — Answer: C

**Why C is correct:** The anti-patterns table lists "Rely on 'max iterations' to stop runaway tool use — Truncates legitimate work" and prescribes "Hook that blocks the specific abusive pattern + high safety fuse." Temperature tweaks and prompt additions are probabilistic; the fix is deterministic. (§11)

**Why the others are wrong:**
- A. Temperature 0 does not make a probabilistic instruction deterministic against prompt-injection-style talk-outs; the reference's central theme is that prompt rules are obeyed ~98% of the time regardless (§1, §5).
- B. The reference explicitly calls out a blanket "max iterations" cap as the wrong answer because it also truncates legitimate work (§11).
- D. Moving a probabilistic rule from CLAUDE.md to the system prompt keeps it probabilistic; the fix is structural (§5, §11).

**Reference:** §11 of reference.md (anti-patterns table, runaway tool use)

### Q7 — Answer: C

**Why C is correct:** §9's "Exam-critical gotcha" states: "If the steps are fixed, adaptive is overkill — it adds a reasoning turn (and a failure mode) for no benefit. Prefer the simpler pattern." The anti-patterns table reinforces this. (§9, §11)

**Why the others are wrong:**
- A. Adaptive decomposition integrates with hooks just fine — "One hook, uniform policy" (§9). This is not the reason.
- B. Subagents calling tools that match a `matcher` is exactly what harness-level hooks support (§11 row on subagent tool lists).
- C is correct.
- D. Fixed chains can absolutely log audit data — PostToolUse audit logging is hook-based and works with either pattern (§6).

**Reference:** §9, §11 of reference.md (fixed chain vs adaptive decomposition)

### Q8 — Answer: C

**Why C is correct:** §8 ranks mitigation options "roughly in order of preference" with `/compact` first: "asks Claude to produce a compact summary of the session so far, then continues with that summary as the new history. Cheapest, usually sufficient." The work is still coherent, so compact fits before fork or fresh. (§7, §8)

**Why the others are wrong:**
- A. The anti-patterns table lists "Start a new session every turn to avoid staleness — Throws away all useful context" (§11).
- B. Explicitly rejected: "Bigger windows don't fix stale context; attention degrades regardless of cap" (§8, §11).
- D. Fork-and-abandon is for poisoned sessions or risky exploration, not for a coherent session that just needs compression (§7).

**Reference:** §7, §8, §11 of reference.md (stale context and /compact)

### Q9 — Answer: B

**Why B is correct:** The anti-patterns table row "Register the hook only on the subagent's tool list" says the correct approach is "Register in `settings.json`, applies wherever the tool is called." §9 reinforces: "In adaptive decomposition, the hook enforces the same policy regardless of which subagent tries to call the guarded tool. One hook, uniform policy." (§4, §9, §11)

**Why the others are wrong:**
- A. Hooks are not part of `AgentDefinition`; they are harness-level and registered in `settings.json` (§11).
- C. Duplicating a prompt rule is still probabilistic across every subagent — the central anti-pattern (§1, §5).
- D. `UserPromptSubmit` fires on user input, not on tool calls; it cannot inspect `tool_input` for `issue_refund` (§2).

**Reference:** §4, §9, §11 of reference.md (wiring hooks; uniform policy across subagents)

### Q10 — Answer: C

**Why C is correct:** This is the central theme of §1 and §5: "Deterministic enforcement (hooks) beats probabilistic guidance (prompt instructions). Every single time." Hooks run outside the model and cannot be talked out of it; prompt rules are obeyed ~98% of the time — unacceptable for policy/safety/compliance. (§1, §5, §11)

**Why the others are wrong:**
- A. Directly contradicts the reference's central thesis — they are not interchangeable (§1, §11).
- B. Inverted: prompts are probabilistic, hooks are deterministic. Safety belongs to hooks (§5).
- D. Latency is not the distinguishing factor the reference cites; determinism is (§1, §5).

**Reference:** §1, §5, §11 of reference.md (deterministic vs probabilistic, the central idea)
