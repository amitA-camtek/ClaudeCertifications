# Practice Test 6 — Plan Mode, Iteration & CI/CD

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 3.4–3.6

## Instructions
Solve all 10 questions before opening `test6_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A developer asks Claude Code to add a 3-line null check to `user.py` at a specific spot they already identified. Which mode should be used and why?
- A. Plan mode, because every code change should be reviewed as a plan before execution.
- B. Plan mode, because it lets Claude "think harder" about edge cases.
- C. Direct execution, because the scope is pinned and plan-mode overhead outweighs the benefit.
- D. Message Batches API, because it is 50% cheaper than interactive sessions.

### Q2. A team is migrating all 45 test files from Jest to Vitest. One engineer says "just let Claude do it directly — plan mode is extra ceremony." What is the correct mode and the main reason?
- A. Direct execution — the task is deterministic once you know the source and target frameworks.
- B. Plan mode — without a reviewable, file-by-file plan you lose track of coverage mid-migration and ship half-migrated code.
- C. Direct execution — plan mode is only useful for single-file refactors.
- D. Message Batches API — 45 files is exactly the bulk workload batches are designed for.

### Q3. In a CI pipeline, a reviewer step is invoked as `claude -p "Review what you just wrote" --resume gen-42`, resuming the generator's session. Why is this an anti-pattern?
- A. `--resume` disables `--output-format json`, so output cannot be parsed.
- B. The reviewer session inherits the generator's reasoning and rationalizes its own mistakes, defeating review independence.
- C. `--resume` forces interactive mode, which hangs CI runners.
- D. Batches API is cheaper, so `--resume` is wasteful.

### Q4. A CI script runs `claude -p "List TODO comments..."` and parses the natural-language stdout with a regex. Occasionally the format drifts after a model update and the script breaks silently. What is the correct fix per the reference?
- A. Add "always format as a markdown table" to the prompt.
- B. Wrap the regex in a retry loop with exponential backoff.
- C. Use `--output-format json` together with `--json-schema <file>` so the output shape is contractually enforced.
- D. Switch the job to the Message Batches API for determinism.

### Q5. Which statement about the Message Batches API is correct according to the reference?
- A. It is ~50% cheaper, may take up to 24h, correlates results via a `custom_id` you set, and does not support a multi-turn agentic tool loop inside one request.
- B. It is ~50% cheaper, completes within an SLA of 1 hour, and supports multi-turn tool use per request.
- C. It is the same price as the Messages API but runs asynchronously and returns results in order of submission.
- D. It is ~50% cheaper and is the recommended default for blocking pre-merge CI checks.

### Q6. A team is considering moving their blocking pre-merge code-review CI check onto the Message Batches API "for the 50% cost savings." What does the reference say about this?
- A. It is the recommended approach because pre-merge reviews are naturally bulk workloads.
- B. It is wrong: batches have up to a 24h window and no SLA, so the PR gate would stall. Pre-merge review should use synchronous `claude -p`.
- C. It is fine as long as `custom_id` is set per PR.
- D. It is fine if the batch job is configured with `--resume` between generator and reviewer.

### Q7. A user is iterating with Claude on a function and keeps giving feedback like "clean this up" and "make it better." The loop is going in circles. Per the reference, which fix is best?
- A. Add "be thorough and produce high-quality code" to the system prompt.
- B. Iterate until Claude reports "I'm confident this is correct."
- C. Give concrete feedback that references a file, function, identifier, or expected behavior — or pin the behavior with a failing test and use the TDD red/green/refactor loop.
- D. Switch to the Message Batches API so Claude has more time to think.

### Q8. A new CI job runs Claude Code to implement a feature from `spec.md` and needs machine-parseable output. Which invocation matches the canonical headless CI shape from the reference?
- A. `claude "implement X per spec.md"` (interactive REPL, then copy stdout into the next step)
- B. `claude -p "implement X per spec.md"` and regex the stdout
- C. `claude -p "implement X per spec.md" --output-format json --json-schema ./generator.schema.json`
- D. `claude --resume last-session "implement X per spec.md"` to reuse prior context

### Q9. The spec for a new feature is ambiguous and could be satisfied by several incompatible implementations. A candidate answer says "add explicit criteria to the system prompt and run direct execution." Per the reference, what is the preferred approach and why?
- A. That candidate answer is correct — a more detailed system prompt removes ambiguity.
- B. Use plan mode, or have Claude ask 3–5 clarifying questions before coding; ambiguity should be resolved by interview or a reviewable plan, not by longer prompts.
- C. Run the Message Batches API so the model has more compute budget to guess.
- D. Generate multiple implementations in one session and have Claude pick the best one.

### Q10. A nightly job must classify 100,000 support tickets. Latency is tolerant (overnight is fine), cost matters, and each ticket is a single-turn classification with no mid-request tool loop. Which option is correct?
- A. Synchronous `claude -p` in a loop — that's the only supported pattern in CI.
- B. Message Batches API with a `custom_id` per ticket — 50% cheaper, up to 24h is acceptable, single-turn tool use fits the constraint.
- C. Interactive Claude Code sessions, one per ticket, resumed with `--resume`.
- D. A single `claude -p` call that takes all 100k tickets in one prompt.

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
