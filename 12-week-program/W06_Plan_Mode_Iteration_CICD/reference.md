# W06 Reference — Plan Mode, Iteration & CI/CD (Domain 3.4–3.6)

Complete, self-contained study material for Week 6. Read this end-to-end. Every concept the exam tests for task statements 3.4, 3.5, and 3.6 is included here.

Prerequisites: W01 (agentic loop, `stop_reason`), W02 (subagents / context isolation), W05 (CLAUDE.md, slash commands, skills). W06 builds on isolation ideas from W02 and applies them to the CI/CD pipeline.

---

## 1. Plan mode vs direct execution

Claude Code has two top-level execution modes for a user request:

- **Direct execution** — Claude reads files, edits them, runs tools, and reports back. No explicit plan produced first.
- **Plan mode** — Claude explores the repo and returns a written plan (ordered steps, files to touch, risks). You review, approve or reject, and only then does execution begin.

Plan mode is *not* "Claude thinks harder." It's a protocol: read-only exploration + written plan + explicit user approval → execution.

### The decision criterion (memorize this)

| Task shape | Mode | Why |
|---|---|---|
| Single-file, well-specified, small diff | **Direct** | Plan-mode overhead outweighs the benefit. The plan would be "edit this one line." |
| Ambiguous scope, open-ended feature | **Plan** | Forces you to converge on requirements before code exists. Catches misunderstandings cheaply. |
| Multi-file migration (e.g., 45 files) | **Plan** | Without a plan you lose track of coverage. The plan is your checklist. |
| Refactor touching >3 modules | **Plan** | Cross-file dependencies need to be mapped before changes, not during. |
| Bug fix with a known reproduction | **Direct** | Scope is pinned by the failing test. |
| "Make this codebase faster / better" | **Plan** | Scope undefined. You need Claude to propose a scope you can accept or narrow. |

### Two exam scenarios, two answers

- *"A 3-line null check needs to be added to `user.py`."* → **Direct.** Plan mode adds a round-trip with zero information gain.
- *"Migrate all 45 test files from Jest to Vitest."* → **Plan mode.** You need an explicit, reviewable file-by-file plan before anything is modified, or you'll lose the plot somewhere in the middle and end up with half-migrated files.

### Why plan mode matters for expensive or irreversible work

Plan mode is also the correct mode when the wrong change is hard to undo: schema migrations, config changes that affect production, cross-service contract changes. The review gate is cheap; the failed execution is not.

### The Explore subagent (brief — relate to W02)

For verbose discovery phases, Claude Code may spawn an **Explore** subagent. Mechanically this is the same hub-and-spoke pattern from W02: the coordinator calls `Task(subagent_type="explore", ...)`, the explore subagent reads widely in an isolated context, and returns a compact synthesis — the coordinator never sees the raw file contents, only the summary. This keeps the main context clean during planning. You don't need to configure this by hand for the exam; you need to recognize the pattern and know *why* it's isolated.

---

## 2. Iterative refinement patterns

"First pass is rarely the final pass." The exam tests three specific iteration patterns.

### 2a. Concrete examples, not vague instructions

Vague feedback wastes a turn. Each iteration should add *specific* signal.

| Wrong | Right |
|---|---|
| "Make it better." | "The function returns `None` on empty input; change it to raise `ValueError('input is empty')` to match the convention in `utils.py:parse_ids`." |
| "Clean this up." | "Extract the nested try/except into a helper `_safe_parse(row) -> Optional[Row]`. Keep the outer loop to 10 lines." |
| "Handle edge cases." | "Add tests for: empty list, single item, list with one None, list with duplicates." |

**Rule of thumb:** if your feedback doesn't reference a file, function, identifier, or expected behavior, it's too vague.

### 2b. TDD iteration loop (red / green / refactor)

TDD is iterative refinement applied to code generation:

1. **Red** — write (or ask Claude to write) a failing test that pins down the desired behavior.
2. **Green** — ask Claude to make the test pass. Minimal implementation, no extras.
3. **Refactor** — ask Claude to clean up while keeping tests green.

This works well with Claude because each step has a **deterministic success signal** (the test passes or doesn't). Compare to "make the function good," where there's no signal at all.

On the exam, if a scenario describes "ambiguous spec, model keeps over-building," the correct fix is usually "pin behavior with a failing test first, then ask for the implementation" — not "write a longer system prompt."

### 2c. Interview pattern — Claude asks before coding

Also called the *clarifying-questions* pattern. Instead of coding immediately, Claude asks 3–5 targeted questions, gets answers, *then* writes code.

When to use:
- Ambiguous requirements.
- User intent could be satisfied by several incompatible implementations.
- High-cost or hard-to-revert work.

You enable this by (a) asking for it directly — "Ask me any clarifying questions before writing code" — or (b) putting it into a CLAUDE.md rule for the relevant path, or (c) using plan mode (which naturally surfaces ambiguities in the plan).

**Exam distractor pattern:** "Add explicit criteria in the system prompt and then run direct execution" is often a trap when the scenario is *ambiguous requirements*. The correct answer is usually "have Claude ask clarifying questions first" or "plan mode."

---

## 3. Headless / CI mode

Interactive Claude Code is for humans at a terminal. In CI you need **headless** invocation: single-shot, non-interactive, machine-parseable output.

### 3a. `-p` / `--print` — non-interactive single-shot

```bash
claude -p "List every TODO comment in src/ as a markdown table."
```

- Runs one prompt, prints the final assistant message to stdout, exits.
- No interactive REPL, no approval prompts.
- Exit code is non-zero on failure.
- This is the **only** form you should use in CI pipelines.

### 3b. `--output-format json` — machine parseable

```bash
claude -p "..." --output-format json
```

Instead of natural-language text on stdout, Claude emits a JSON envelope with fields like `result`, `session_id`, `stop_reason`, and (depending on flags) tool-call traces. Your CI script parses this with `jq` or the language-native JSON library. Never regex natural-language output.

### 3c. `--json-schema <file>` — schema-constrained output

```bash
claude -p "Review this diff and emit a review object." \
  --output-format json \
  --json-schema ./review.schema.json
```

Claude is constrained to produce output that conforms to the JSON Schema you pass. Syntax correctness is guaranteed; semantic correctness is not (the model can still pick the wrong `severity` value, but it cannot emit malformed JSON or omit required fields). This is the CI/CD equivalent of the W04/W07 `tool_use` structured-output trick.

### Why this chain matters

In CI you need:
1. **Determinism** — no surprise interactive prompts (`-p`).
2. **Parseability** — a stable shape your script can consume (`--output-format json`).
3. **Contract enforcement** — the shape doesn't drift between runs (`--json-schema`).

Missing any one of these turns your pipeline into a flaky, regex-scraping nightmare.

---

## 4. Session context isolation in CI — the generator must NOT review itself

This is the single most tested W06 concept. Internalize it.

**Self-review retains reasoning bias.** If the same session that generated the code also reviews it, the reviewer already "knows" why the generator made each choice — it shares the generator's mental model, including its mistakes. It will rationalize its own output instead of catching flaws.

### The rule

In a CI pipeline:
- The code-generation step runs in its own headless session.
- The review step runs in a **separate headless session** — no `--resume`, no shared transcript, no shared scratchpad.
- The reviewer receives only the **artifacts** (the diff, the requirements, the test output). Not the generator's reasoning trace.

### Why a fresh session works

The reviewer starts with the same blind spot a human code reviewer has: it hasn't seen the thought process, only the result. That's exactly the independence property you want.

### Connection to W02

This is the same principle as subagent isolation (W02): a reviewer with its own isolated context will catch things that a shared-context reviewer won't. The CI pipeline is just the production form of that pattern, split across two CLI invocations instead of two subagents.

### What "separate session" means concretely

```bash
# WRONG — reviewer resumes the generator's session
claude -p "Write the migration script" --session-id gen-42
claude -p "Now review what you wrote" --resume gen-42   # <— shares bias

# RIGHT — reviewer runs in a fresh session, sees only artifacts
claude -p "Write the migration script. Write to ./out.py" --session-id gen-42
claude -p "Review the diff at ./out.py against ./requirements.md. \
  Output JSON per ./review.schema.json." \
  --output-format json \
  --json-schema ./review.schema.json
# no --resume, no --session-id → fresh session
```

---

## 5. Message Batches API

A separate Anthropic API endpoint for bulk asynchronous processing. **Not** the same as headless `claude -p`.

### Properties

| Property | Value |
|---|---|
| Price | **50% cheaper** than the standard Messages API |
| Latency | Up to **24 hours** to complete (usually much faster, but no SLA) |
| Throughput | Very high — built for bulk |
| Tool use | Single-turn tool use per request only. **No multi-turn agentic loop** inside a batched request. |
| Correlation | Each request has a `custom_id` you set; results come back keyed by `custom_id`. |

### When batches are RIGHT

- Overnight data-processing jobs (classify 100k support tickets).
- Weekly reports (summarize 5,000 PRs).
- Backfills and re-scoring of historical data.
- Any task where you can wait, want the discount, and don't need mid-request tool conversations.

### When batches are WRONG

- **Blocking CI checks** — a PR sitting in "checks pending" for up to 24h is not a product.
- Anything with a user-visible SLA (chat, search, live review).
- Multi-turn agentic work where the model needs to call tool → read result → call another tool inside one "request." Batches don't support the full loop.
- Pre-merge review: the whole point of pre-merge review is that it runs *before* merge, fast enough to block the PR. Batch doesn't meet that bar.

### Exam rule

If the scenario has any of the words "blocking," "pre-merge," "SLA," "pipeline check," or "must finish before X can proceed" → **not batches**. Use synchronous headless `claude -p`.

If the scenario says "nightly," "overnight bulk," "cost-sensitive," "100k records," "latency-tolerant" → **batches**, with `custom_id` correlation.

---

## 6. Anti-patterns (these ARE the exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| Use plan mode for a 3-line null-check fix | Overhead (approval round-trip, exploration phase) dwarfs the actual change | Direct execution. Plan mode is for scope uncertainty, not trivial edits. |
| Skip plan mode for a 45-file migration | No reviewable checklist → you lose track of coverage halfway, ship half-migrated code | Plan mode. The plan IS your migration checklist. |
| Review your own generated code in the same session | Self-review retains the generator's reasoning bias — it rationalizes its own mistakes | Fresh headless session for review; reviewer sees artifacts, not the generation trace |
| Use the Message Batches API for a blocking pre-merge CI check | Up to 24h window, no SLA. Your PR gate will stall for a day. | Synchronous `claude -p --output-format json --json-schema` |
| Parse Claude's natural-language output with regex in CI | Natural language varies run to run; regex breaks silently | `--output-format json --json-schema review.schema.json` — shape is contract |
| Retry a failing CI step with no structured error context | Retry has the same information the first call did; you've lost why it failed | Emit structured errors (`errorCategory`, failure details) from the schema and feed them back on retry |
| "Make it better" feedback for iterative refinement | Not actionable, model guesses at your intent | Concrete references: file, function, behavior, example |
| Same system prompt used to generate AND review | Inherits generator's biases and blindspots | Separate reviewer prompt, separate session, separate schema |
| Use natural-language stdout as the pipeline contract | Silent format drift on every model update | JSON Schema-constrained output is the contract |
| Add "be thorough" to the prompt to fix reviewer misses | Probabilistic; the miss-rate doesn't go to zero | Separate review pass in isolated session + explicit categorical criteria |
| Iterate until the model says "I'm confident this is correct" | Self-reported confidence is miscalibrated | Iterate against a deterministic check: tests pass, schema validates, lint clean |
| Use `--resume` to have the reviewer pick up from the generator | Defeats isolation; reviewer inherits generator's context | Fresh session (no `--resume`), reviewer reads only the artifacts |

The pattern across rows: **deterministic signals (schemas, tests, isolated sessions) beat prompt instructions.** Same theme as every other week.

---

## 7. Putting it all together — the canonical CI shape

```
┌────────────────────────────────────────────────────────────┐
│  Generator (session A, fresh)                              │
│    claude -p "implement X per spec.md"                     │
│      --output-format json                                  │
│      --json-schema generator.schema.json                   │
│    → writes code + emits {files_changed, summary}          │
└────────────────────────────────────────────────────────────┘
                             │
                             ▼ (artifacts only: diff + spec)
┌────────────────────────────────────────────────────────────┐
│  Reviewer (session B, fresh — NO --resume)                 │
│    claude -p "review diff against spec.md"                 │
│      --output-format json                                  │
│      --json-schema review.schema.json                      │
│    → emits {issues[], approved, blocking_count}            │
└────────────────────────────────────────────────────────────┘
                             │
                             ▼
                       CI decides:
                       blocking_count > 0  →  fail the check
                       blocking_count == 0 →  post review comments,
                                              allow merge
```

Two independent invocations. Two independent sessions. Two independent schemas. One pipeline that isn't a regex nightmare.

---

## 8. What the exam will probe

- "Claude Code: which mode for task X?" — you pick plan vs direct based on scope/ambiguity/reversibility.
- Broken CI script that regexes natural-language output → fix is `--output-format json --json-schema`.
- Scenario where the same session generates and reviews → fix is a separate, fresh session for the reviewer.
- "Should this run as batch or sync?" given a latency/SLA description.
- "The iteration is going in circles" → fix is concrete feedback or TDD loop, not a longer system prompt.
- Distractors that add rules to the prompt where a deterministic mechanism is the real fix.
- Batches API property questions: 50%, 24h, `custom_id`, no multi-turn inside one request.

---

## 9. Fast recap

- **Plan mode** for ambiguous / multi-file / hard-to-reverse work. **Direct** for small well-specified fixes. 45-file migration → plan. 3-line null check → direct.
- **Iterative refinement** works when feedback is concrete (file/function/behavior) or deterministic (TDD red/green/refactor). Vague "make it better" wastes turns. The interview pattern (Claude asks clarifying questions) is the fix for ambiguous specs.
- **Headless CI** = `-p` + `--output-format json` + `--json-schema`. All three. Natural-language output is never the CI contract.
- **Session isolation** in CI: the generator and reviewer run in **separate** sessions. Self-review inherits generator bias. No `--resume` between them.
- **Message Batches API** = 50% cheaper, up to 24h, `custom_id` correlation, no multi-turn tool loop inside one request. Right for overnight bulk; wrong for blocking pre-merge checks.
- **Deterministic mechanisms** (schemas, tests, isolated sessions) beat prompt instructions. Every time.

When you can explain each of those six bullets out loud in ~20 seconds each, you're ready for the W06 test.
