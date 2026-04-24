# Scenario 5 walkthrough — Claude Code for Continuous Integration

Scenario 5 from the exam guide covers Claude Code running inside **CI/CD pipelines** — automated code review on pull requests, test generation for new code paths, and structured PR feedback to engineers. The scenario emphasizes **actionable feedback that minimizes false positives** and **machine-parseable output** that downstream tooling can route, gate, or display.

Primary domains tested: **Claude Code Configuration & Workflows** (Domain 3), **Prompt Engineering & Structured Output** (Domain 4). Supporting: Domain 1 (session isolation) and Domain 5 (error propagation when the CI step itself fails).

This walkthrough maps the scenario to W05–W08 concepts and the exam-critical judgment calls a candidate must make. It matches `scenario_4_developer_productivity_walkthrough.md` in shape — no runnable code, just the decision landscape.

---

## The setup

A team runs Claude Code on every pull request via GitHub Actions. The pipeline needs to:

1. **Review** the diff for bugs, style violations, and policy breaches.
2. **Generate** tests for new or modified functions that lack coverage.
3. **Emit feedback** to engineers as inline PR comments, formatted so reviewers can triage fast.
4. **Gate** the merge on critical findings (e.g., added secrets, broken migrations).

Pipeline is expected to complete in **under 5 minutes** for a typical PR (blocking path — engineers are waiting).

---

## Task 1 — Structure the CI invocation

**Wrong instinct:** call `claude` interactively in the Actions step and regex the natural-language output for "LGTM" or "BLOCKER".

**Why it's wrong (W06 §5):**
- Interactive mode doesn't exist in headless CI.
- Natural-language phrasing drifts across model versions — a regex that passes today fails silently next month when the model rephrases "blocker" as "critical issue".

**Right approach (W06 §3–4):**

```yaml
- name: Claude review
  run: |
    claude -p \
      --output-format json \
      --json-schema schemas/review.schema.json \
      --max-turns 15 \
      < pr_review_prompt.md
```

- **`-p` / `--print`** — headless mode, single completion, exits after output.
- **`--output-format json`** — machine-parseable envelope.
- **`--json-schema`** — validates the response shape. Downstream steps can rely on the contract; schema drift fails the step immediately instead of leaking malformed data to the next job.
- **`--max-turns`** — safety fuse for agent loops inside CI. If the loop trips the fuse, the step fails loudly; better than silently returning a partial review.

---

## Task 2 — Isolate generation from review

**Wrong instinct:** one Claude Code session generates test code and then reviews it in the same `--resume`-d context to save on spin-up.

**Why it's wrong (W06 §4, W08 §5):**
- Self-review retains the reasoning trail. The reviewer already "knows" why each choice was made and rationalizes its own mistakes instead of catching them.
- The model is at its weakest spotting errors it *just committed*.

**Right approach:**

- **Two separate sessions**, both **fresh** (no `--resume`):
  - Session A (generator): produces the test file as an artifact.
  - Session B (reviewer): reads only the *artifact* + diff + test file; has no memory of A's reasoning.
- Cross-job data passes as a file in `actions/upload-artifact` / `download-artifact`, not as shared session state.

This is the same principle as multi-pass review at a smaller scale: **independence is the property you're buying by separating sessions.**

---

## Task 3 — Prompt for actionable, low-false-positive feedback

**Wrong instinct:** "Review this PR and point out anything that could be improved."

**Why it's wrong (W07 §1):**
- "Anything that could be improved" is unbounded — the model will pad with nits to look thorough.
- No false-positive budget → reviewers learn to ignore the bot.

**Right approach — explicit categorical criteria:**

```
Review the diff for the following categories only:
1. BLOCKER — the change introduces a bug that will break production or leak secrets.
2. POLICY — the change violates a documented rule in CLAUDE.md.
3. TEST_GAP — a modified public function has no test covering the new behavior.

Do NOT comment on:
- Style / formatting (handled by linter).
- Speculative refactors.
- Preferences without a documented rule.

For each finding, emit:
{ "category": "BLOCKER|POLICY|TEST_GAP", "file": "...", "line": 123, "issue": "<one line>", "fix": "<one line suggestion>" }

If no findings in any category, emit an empty array.
```

Why this works:
- **Categorical** triggers, not vibes (W09 §3).
- **Explicit exclusions** prevent nit-padding.
- **Schema-shaped output** (W07 §3) pairs with `--json-schema` on the CLI — downstream parsers never guess.

---

## Task 4 — Gate the merge on critical findings

**Wrong instinct:** an LLM decides "should this PR merge?" by inspecting the whole diff and returning a yes/no.

**Why it's wrong:**
- The merge gate is a **policy decision**, not a judgment call. LLMs are probabilistic; merge gating should be deterministic.
- A yes/no from the model masks *which* criterion failed.

**Right approach — mechanism on top of model output:**

1. The model emits the structured findings array from Task 3.
2. A **shell step** (not Claude) counts findings by category:
   ```bash
   blockers=$(jq '[.[] | select(.category=="BLOCKER")] | length' findings.json)
   if [ "$blockers" -gt 0 ]; then exit 1; fi
   ```
3. The shell gate, not the model, owns pass/fail. The model owns *what was found*; policy code owns *what to do about it*.

This is the **prompt-vs-mechanism** discriminator from W11 again: the model produces data; code enforces rules.

---

## Task 5 — Handle CI step failures gracefully

**Wrong instinct:** if Claude Code exits non-zero, fail the whole pipeline.

**Why it's wrong (W09 §11):**
- The model hitting `--max-turns` isn't the same as finding a blocker. Treating them identically punishes the team for CI infrastructure issues.
- Engineers lose trust in the check and start `skip ci`-ing past it.

**Right approach — structured error propagation:**

- The Claude step emits one of three exit codes:
  - `0` — ran cleanly (with or without findings).
  - `1` — findings were emitted; gate job will decide based on category.
  - `2` — infrastructure failure (rate limit, network, schema-violation, max-turns). PR gets a neutral status + a "retry" suggestion, **not** a blocker comment.
- Downstream jobs `select` on category, not on exit code.

This mirrors W09 §11's **structured error envelope** pattern at the CI level — callers (the merge gate) can distinguish "I found a problem" from "I failed to check".

---

## Task 6 — Cost shape

**Wrong instinct:** route all PR reviews through **Message Batches** to get 50% off.

**Why it's wrong (W08 §3):**
- Batches have up to a 24 h window with no SLA.
- A blocking PR check must complete in minutes. An unpredictable queue kills engineer velocity.

**Right approach:**
- **Synchronous `claude -p`** for the blocking review.
- **Enable prompt caching** on the system prompt + review criteria (large, stable) — cache hits at ~10% of input cost pay for themselves the 2nd PR of the day (see [../operational_topics.md](../operational_topics.md) §1).
- **Model selection:** Sonnet is the default. Upgrade to Opus only if Sonnet demonstrably misses blockers on your codebase (validate with a held-out set first). Haiku is usually too weak for nuanced code review.
- Reserve Batches for *overnight* passes: weekly security scan, bulk test generation across the repo, etc.

---

## Exam-shaped traps tied to this scenario

Common distractors the exam likes to plant when Scenario 5 lands:

| Distractor | Why wrong | Correct |
|---|---|---|
| "Use the same session to both write and review test code" | Self-review retains reasoning bias | Separate fresh sessions; artifacts-only |
| "Regex the natural-language output for 'error' or 'fail'" | Phrasing drifts across model versions | `--output-format json --json-schema` |
| "Ask the model to return a single overall score 1–10" | Vague + self-reported confidence miscalibrated | Categorical findings with schema |
| "Use Message Batches for cost savings" | 24 h window, no SLA — blocks PR velocity | Synchronous `claude -p` |
| "Have the model decide whether to merge" | Merge gate is a policy decision, not a judgment call | Model emits findings; shell gate enforces policy |
| "Enable plan mode for every PR review" | Plan-mode overhead on every PR doesn't pay off | Direct execution; plan mode is for scope-ambiguous work, not per-PR |
| "Fail CI on any non-zero exit from the Claude step" | Conflates findings with infra failures | Distinguish findings exit from infra exit; neutral status on infra |

---

## How this scenario composes with the others

- **If Scenario 5 appears alongside Scenario 2 (Code Gen):** the exam may test whether you correctly split *generation* (Scenario 2 pattern) from *review* (Scenario 5 pattern) across separate sessions.
- **If alongside Scenario 6 (Structured Extraction):** the `--json-schema` output contract is the shared mechanism — both scenarios rely on it.
- **If standalone:** expect questions on `--output-format`, session isolation in CI, batch-vs-sync, and categorical review criteria.

---

## Drill

Before Practice Exam 1, self-test on these prompts:

1. Why is `--resume` in CI a mistake?
2. What does `--json-schema` buy you that natural-language output doesn't?
3. Why is "ask the model if the PR should merge" wrong, and what's the right split of responsibilities?
4. When would you use Message Batches in a CI context (if ever)?
5. What's the exit-code contract for the Claude step, and why does it have three codes instead of two?

If you can answer all five in one sentence each, Scenario 5 is solid.
