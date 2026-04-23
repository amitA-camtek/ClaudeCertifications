# Exam Day Playbook

How to actually take the exam. Read this Friday evening and again Sunday morning before you sit.

The test is 60 questions across 5 domains, scenario-based multiple choice, passing score 720/1000. Most questions follow a predictable structure; recognizing the structure is worth more than cramming content at this point.

---

## 1. How a scenario-based question is built

Every question has the same four parts, in the same order. Train yourself to parse them mechanically.

1. **Scenario frame (1–3 sentences).** Sets the context: the system (agent, pipeline, skill), the tools/config in play, and what's gone wrong or what's being designed.
2. **The failure mode or design goal (1 sentence).** This is the crux. "Refunds over $500 are being issued despite the policy." "The extraction pipeline hallucinates due dates." "The coordinator's context is filling up with raw fetch content."
3. **The question stem.** Usually some variant of: "What is the best fix?", "Which approach addresses this correctly?", "What should the architect do?"
4. **Four options.** Three distractors, one correct answer. Distractors are deliberately plausible.

### How to parse each part fast

- Read the frame once. Identify the domain in your head. (27/18/20/20/15 mental map from the cheat sheet.)
- Read the failure mode. **State it to yourself in one sentence.** "This is a probabilistic-vs-deterministic question." "This is a plan-vs-direct question." "This is a sentiment-escalation distractor."
- Read the stem to confirm the question type (fix vs design vs classify).
- Now read the options with a hypothesis already in mind — don't let the options seed your analysis.

---

## 2. The distractor families — how to eliminate them

Roughly 80% of distractors fall into one of these families. If you can name the family, you can reject the option in seconds without re-reading it.

### Family A — "Add a rule to the system prompt"

Look for phrases like:
- "Add an instruction to the prompt that…"
- "Specify in the system prompt that…"
- "Tell the model to…"
- "Include in the instructions that…"

**When there's a deterministic mechanism available (hook, `tool_choice`, schema, config flag, separate session, `context: fork`, scoped tool list), the prompt-only answer is wrong.** Every time.

Exception: Family A is correct when the question is specifically about **prompt quality** (few-shot examples, categorical vs vague criteria, writing explicit thresholds). Prompts ARE the mechanism for style, tone, criteria phrasing.

### Family B — "Check the text / parse for keywords"

Look for phrases like:
- "Check if the model's response contains 'done'…"
- "Parse the output for the word 'error'…"
- "Read the model's text to decide whether to…"

**Almost always wrong.** Deterministic signals exist: `stop_reason`, `isError` field, `--output-format json`, JSON Schema-validated output. Text parsing is the fallback of last resort and never the right exam answer.

### Family C — "Give every agent every tool / maximize flexibility"

Look for phrases like:
- "Give the coordinator access to all tools so it can handle any case…"
- "Include all MCP tools in the agent's allow-list…"
- "Maximum flexibility by consolidating tools into one agent…"

**Wrong.** Selection accuracy degrades past ~5–7 tools. Scope per role; delegate cross-domain work. The correct answer is always the one that scopes.

### Family D — "Use self-review / the same session reviews itself"

Look for phrases like:
- "Use `--resume` to continue in the same session for the review step…"
- "Have the coordinator review its own output…"
- "Run the reviewer with the generator's context for continuity…"

**Wrong.** Self-review retains reasoning bias. Independent, fresh session — artifacts only.

### Family E — "Bigger context window / more tokens"

Look for phrases like:
- "Upgrade to a larger context window…"
- "Increase max_tokens…"
- "Use a model with more context to hold more history…"

**Almost always wrong** as a solution to stale session, lost-in-the-middle, context pollution, or summarization loss. Attention does not scale with window size. Structural fixes (`/compact`, fork, scratchpad, start fresh, hub-and-spoke decomposition) are the answer.

### Family F — "Retry with exponential backoff / retry until success"

Look for phrases like:
- "Retry the call with exponential backoff…"
- "Retry until the model succeeds…"
- "Loop retries until the validation passes…"

Often wrong for `validation`, `not_found`, `policy` errors (which will never succeed on retry). Correct only for `timeout` / transient `internal` errors — and only when `isRetryable: true`. When the source info is absent, retry is pure waste.

### Family G — "Resume the session after a crash"

Look for phrases like:
- "Resume the session to pick up where it left off…"
- "`--resume` to recover the failed work…"

**Wrong when the last turn was destructive or the history is poisoned.** The broken state is in the history and will mis-steer the next turn. Fork from a clean point, or start fresh.

### Family H — "Use sentiment / self-reported confidence as a trigger"

Look for phrases like:
- "Trigger escalation when sentiment is negative…"
- "Escalate when the model reports low confidence…"
- "Route to human review when the customer seems upset…"

**Wrong.** Sentiment ≠ complexity; LLM self-confidence is miscalibrated. Use categorical triggers.

### Family I — "Use Message Batches for a blocking / SLA path"

Look for phrases with:
- "blocking", "pre-merge", "user-facing", "SLA", "must complete before X"

Paired with "Use the Message Batches API for cost savings…" — **wrong**. Batches are for latency-tolerant bulk. Blocking paths want synchronous `claude -p`.

---

## 3. The decision procedure for every question

Run this in your head on every question. Should take 20–40 seconds per question on the easy ones, 60–90 on the hard ones.

1. **Read frame. Identify domain.**
2. **State the failure/goal in one sentence.**
3. **Scan options. For each, name the distractor family if it fits one of A–I above.**
4. **Eliminate the Family A–I options.** You'll often be down to two choices.
5. **Of the survivors, pick the more deterministic and more specific one.** If both are deterministic, pick the one whose mechanism matches the failure mode most tightly (hook for side-effect prevention, schema for output shape, `tool_choice` for forcing a call, `context: fork` for isolation, etc.).
6. **Sanity check:** does the chosen answer describe a mechanism that runs outside the model's reasoning? If yes, you're probably right. If it relies on the model choosing to comply, you've probably picked a distractor.
7. **Commit unless you see an obvious error.** Move on.

---

## 4. Time management

60 questions. Assume a 90-minute exam (confirm on your actual portal; if different, scale proportionally).

- **Target pace: 1 minute per question average.** Leaves 30 minutes of buffer.
- **First pass (0:00–0:45):** answer everything you're confident on in ≤ 60 seconds. **Flag anything that takes longer or you're genuinely unsure about; do not stall.** Pick your best guess, flag, move on.
- **Second pass (0:45–1:15):** revisit flagged questions. You'll often find the answer comes easier the second time because fatigue has cleared and you've seen related scenarios.
- **Third pass (1:15–1:30):** final review. Sanity-check any flagged questions where you're still torn; prefer your first instinct unless you find a concrete reason to change.

### The 90-second rule

If you've spent 90 seconds on a question and you're not converging, **flag it, guess, move on**. Time is more valuable than marginal accuracy on one hard question.

### Don't grind the first hard question

The first hard question is the trap most test-takers fall into. You sink 5 minutes, get flustered, and answer the next 15 questions too fast to compensate. Flag and move on — you'll probably solve it on pass two with better pattern recognition from the other 59 questions in your head.

---

## 5. When two answers both look plausible

This is the central tiebreaker. Internalize it.

**The more deterministic answer wins.**

If option A involves code / configuration / API contract / runtime mechanism, and option B involves prompt wording / instructions / guidance, pick A.

Concrete tiebreakers, from strongest to weakest:
1. A uses a hook / `tool_choice` / schema / `context: fork` / separate session / scoped tool list. B uses a prompt instruction.
2. A specifies an exact threshold or categorical rule. B uses vague language ("conservative", "high confidence", "important").
3. A scopes tools/context. B maximizes flexibility/access.
4. A reads a structured field (`isError`, `stop_reason`). B parses text.
5. A runs in a fresh/isolated session. B resumes/shares a session.
6. A uses synchronous sync path. B uses batches for a blocking flow.

If none of these resolve the tie, re-read the **failure mode** sentence. The right answer addresses the specific failure mode; the almost-right answer addresses a related-but-not-identical mode. Sharpen on the exact failure.

---

## 6. When to flag and revisit vs commit

**Commit immediately when:**
- You recognized the distractor family within 10 seconds and eliminated three options.
- You can name the task statement the question maps to.
- The remaining answer is an obvious deterministic mechanism.

**Flag and revisit when:**
- Two options survive elimination and you're torn.
- The question mixes two domains and you're unsure which lens matters more.
- You find yourself second-guessing after initial choice.
- The phrasing is unusual and you want fresh eyes.

**Never:**
- Grind a single question past 90 seconds on pass one.
- Change an answer on pass three without a concrete reason — first instincts under pattern recognition are usually right.
- Leave a question blank. Guess on the deterministic option, flag, move on. A guess has positive expected value.

---

## 7. Mental reset cues during the exam

- **Between questions**, take a one-breath pause before reading the next frame. Clears the previous question's framing.
- **Every 10 questions**, scan the time remaining. Recalibrate pace if you're slow; slow down if you're rushing.
- **If you notice you're rattled** (spiraled on one question, energy low, seeing distractors everywhere), flag the current question, close your eyes for 10 seconds, and resume on the next one. Don't fight through a dip — reset.
- **If you catch yourself re-reading distractors three times**, you're overthinking. Apply the elimination procedure (section 2), commit, move on. You can flag it for pass two.

---

## 8. Fast checklist for each question (copy of the procedure, condensed)

1. Domain?
2. Failure mode in one sentence?
3. Eliminate Family A–I distractors.
4. Survivors: pick more deterministic, more specific.
5. Commit, or flag and move on.

---

## 9. The night before

- **No new studying.** If you don't know it now, you won't learn it in the next 8 hours.
- Read `reference.md` section 5 (the deterministic meta-theme).
- Read the 60-row wrong-answer table in `reference.md` once more — just skim.
- Read this playbook once more.
- **Sleep.** Rested recall beats tired cramming by a wide margin.

## 10. The morning of

- Eat. Hydrate. Arrive early.
- In the last 15 minutes before the exam starts, read:
  - The "single sentence to memorize" at the bottom of `domain_cheatsheet.md`.
  - The distractor-family list (section 2 of this playbook).
- Walk in with one sentence in your head: **"Deterministic mechanism beats prompt instruction."**
- First question: take a beat, follow the procedure, answer. Momentum builds from there.
