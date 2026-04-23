# Practice Test 6 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | C |
| 2 | B |
| 3 | B |
| 4 | C |
| 5 | A |
| 6 | B |
| 7 | C |
| 8 | C |
| 9 | B |
| 10 | B |

## Detailed explanations

### Q1 — Answer: C

**Why C is correct:** The reference's decision table lists "Single-file, well-specified, small diff" as direct execution, and the worked exam scenario is literally "a 3-line null check needs to be added to `user.py` → Direct. Plan mode adds a round-trip with zero information gain" (§1).

**Why the others are wrong:**
- A. "Every code change should be reviewed as a plan" contradicts the reference; plan mode is for scope uncertainty, not trivial edits (§1, §6).
- B. Plan mode is "not 'Claude thinks harder'" — it is a read-only + written plan + approval protocol (§1).
- D. The Batches API is unrelated to this interactive edit; cost is not the decision criterion here (§5).

**Reference:** §1 (decision criterion, two exam scenarios) and §6 (anti-patterns row 1).

### Q2 — Answer: B

**Why B is correct:** The reference's worked example states: "Migrate all 45 test files from Jest to Vitest → Plan mode. You need an explicit, reviewable file-by-file plan before anything is modified, or you'll lose the plot somewhere in the middle and end up with half-migrated files" (§1). The anti-patterns table also flags "Skip plan mode for a 45-file migration" as wrong because there is no reviewable checklist (§6).

**Why the others are wrong:**
- A. Multi-file migrations still benefit from a plan — cross-file coverage is what you lose without it (§1).
- C. Plan mode is explicitly recommended for multi-file migrations and refactors touching >3 modules (§1 decision table).
- D. The Batches API is for async bulk classification-style work with no multi-turn loop; it is not a substitute for a plan (§5).

**Reference:** §1 and §6 of reference.md

### Q3 — Answer: B

**Why B is correct:** §4 is explicit: "Self-review retains reasoning bias. If the same session that generated the code also reviews it, the reviewer already 'knows' why the generator made each choice — it shares the generator's mental model, including its mistakes. It will rationalize its own output." The concrete "WRONG" example in §4 is `claude -p "... review what you wrote" --resume gen-42`.

**Why the others are wrong:**
- A. `--resume` does not disable `--output-format json`; that is fabricated (§3, §4).
- C. `-p` is the non-interactive form; `--resume` does not re-enable interactivity (§3a).
- D. Batches cost is unrelated to why self-review is wrong (§4, §5).

**Reference:** §4 (session context isolation) and §6 (anti-patterns row on `--resume`).

### Q4 — Answer: C

**Why C is correct:** §3 establishes the three-flag CI chain: `-p` for determinism, `--output-format json` for parseability, and `--json-schema` for contract enforcement. §6 lists "Parse Claude's natural-language output with regex in CI" as an anti-pattern whose correct fix is "`--output-format json --json-schema review.schema.json` — shape is contract." The reference explicitly says "Never regex natural-language output."

**Why the others are wrong:**
- A. Prompt instructions like "always format as markdown" are probabilistic; the reference says deterministic mechanisms beat prompt instructions (§6, §3c).
- B. Retry does not fix format drift; the regex will still be wrong next run (§6).
- C is correct.
- D. Batches do not solve format drift and are inappropriate for a blocking CI check (§5, §6).

**Reference:** §3 and §6 of reference.md

### Q5 — Answer: A

**Why A is correct:** §5's properties table lists exactly these four facts: "50% cheaper," "up to 24 hours," `custom_id` correlation, and "Single-turn tool use per request only. No multi-turn agentic loop inside a batched request."

**Why the others are wrong:**
- B. There is no 1-hour SLA and batches do not support multi-turn tool use in one request (§5).
- C. Batches are 50% cheaper, not same-priced; ordering is via `custom_id`, not submission order (§5).
- D. The reference explicitly names "blocking pre-merge CI check" as a WRONG use of batches (§5, §6).

**Reference:** §5 (Message Batches API properties).

### Q6 — Answer: B

**Why B is correct:** §5's "When batches are WRONG" list includes "Blocking CI checks — a PR sitting in 'checks pending' for up to 24h is not a product" and "Pre-merge review: the whole point of pre-merge review is that it runs before merge, fast enough to block the PR. Batch doesn't meet that bar." The exam rule in §5 says if the scenario includes "blocking," "pre-merge," or "pipeline check," it is not batches — use synchronous headless `claude -p`.

**Why the others are wrong:**
- A. Directly contradicts §5's exam rule.
- C. `custom_id` does not solve the 24h latency problem for a blocking gate (§5).
- D. `--resume` is itself an anti-pattern between generator and reviewer (§4, §6); it does not rescue batches for pre-merge checks.

**Reference:** §5 and §6 of reference.md

### Q7 — Answer: C

**Why C is correct:** §2a says "if your feedback doesn't reference a file, function, identifier, or expected behavior, it's too vague," and §2b recommends the TDD red/green/refactor loop because each step has a "deterministic success signal." §6 explicitly maps "'Make it better' feedback for iterative refinement" to "Concrete references: file, function, behavior, example" as the fix, and "Iterate until the model says 'I'm confident this is correct'" is listed as an anti-pattern because self-reported confidence is miscalibrated.

**Why the others are wrong:**
- A. §6 lists "Add 'be thorough' to the prompt" as an anti-pattern — it is probabilistic, not deterministic.
- B. §6 explicitly says self-reported confidence is miscalibrated; iterate against deterministic checks instead.
- D. Batches do not give "more time to think"; they are a bulk async endpoint with no multi-turn loop (§5).

**Reference:** §2a, §2b, and §6 of reference.md

### Q8 — Answer: C

**Why C is correct:** §7's canonical CI shape shows exactly: `claude -p "implement X per spec.md" --output-format json --json-schema generator.schema.json`. §3 explains why all three flags are required: determinism (`-p`), parseability (`--output-format json`), and contract enforcement (`--json-schema`).

**Why the others are wrong:**
- A. The interactive REPL is for humans; §3a says `-p` is "the only form you should use in CI pipelines."
- B. Regexing stdout is explicitly called out as an anti-pattern (§6).
- D. `--resume` in CI is the isolation anti-pattern from §4/§6.

**Reference:** §3 and §7 of reference.md

### Q9 — Answer: B

**Why B is correct:** §2c describes the interview pattern — Claude asks 3–5 clarifying questions before coding — as the fix for ambiguous requirements, and notes the exam distractor: "'Add explicit criteria in the system prompt and then run direct execution' is often a trap when the scenario is ambiguous requirements. The correct answer is usually 'have Claude ask clarifying questions first' or 'plan mode.'" §1's decision table also lists "Ambiguous scope, open-ended feature" as plan mode.

**Why the others are wrong:**
- A. §2c explicitly flags this as the distractor pattern.
- C. Batches are unrelated and do not handle multi-turn disambiguation (§5).
- D. Generating-then-picking inside one session adds no independence and is not a pattern the reference endorses; the reference's recipe is clarifying questions or plan mode (§2c, §1).

**Reference:** §1 and §2c of reference.md

### Q10 — Answer: B

**Why B is correct:** §5's "When batches are RIGHT" list names exactly this shape: "Overnight data-processing jobs (classify 100k support tickets)... latency-tolerant... cost-sensitive," with `custom_id` correlation, and single-turn tool use per request fits a per-ticket classification. The §5 exam rule confirms: "nightly," "overnight bulk," "cost-sensitive," "100k records," "latency-tolerant" → batches.

**Why the others are wrong:**
- A. Synchronous `claude -p` is correct for blocking/SLA work, not cost-sensitive overnight bulk; it forgoes the 50% discount (§5).
- C. Interactive sessions are for humans at a terminal, not CI/bulk (§3a). `--resume` would share context across unrelated tickets (§4).
- D. Stuffing 100k tickets into one prompt is not a pattern the reference supports; batches correlate results via `custom_id`, one request per ticket (§5).

**Reference:** §5 of reference.md
