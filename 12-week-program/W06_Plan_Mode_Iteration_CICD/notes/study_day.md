# W06 Study Day — Plan Mode, Iteration & CI/CD (Domain 3.4–3.6)

## The one thing to internalize

**Deterministic mechanisms beat prompt instructions — again.** For W06 specifically:

- Plan mode vs direct is a **scope decision**, not a "Claude thinks harder" toggle.
- CI pipelines speak **JSON Schema**, not natural language.
- The reviewer runs in a **fresh session**, not the generator's session.

All three are mechanical guarantees. None of them are "add instructions to the prompt."

## Plan mode vs direct — the decision table

| Task | Mode | Why |
|---|---|---|
| 3-line null-check fix | **Direct** | Plan-mode overhead > the change itself |
| 45-file framework migration | **Plan** | Plan is your coverage checklist |
| Open-ended "make the API nicer" | **Plan** | Converge on scope before code exists |
| Bug with a failing repro test | **Direct** | Scope is already pinned |
| Schema migration in prod | **Plan** | Hard-to-reverse → cheap review gate pays off |

Exam trap: "add explicit criteria in the prompt and run direct" is often wrong when the scenario is ambiguous scope. The correct answer is usually **plan mode** or **interview pattern**.

## Iterative refinement — three patterns

1. **Concrete feedback** — reference a file, function, or behavior. Never "make it better."
2. **TDD loop** — red (failing test) → green (minimal impl) → refactor. Each step has a deterministic success signal.
3. **Interview pattern** — Claude asks clarifying questions before coding. Enable via prompt, CLAUDE.md rule, or plan mode.

If a scenario says "the model keeps over-building," the fix is usually TDD or interview, not a longer system prompt.

## Headless CI — the three flags you memorize

```bash
claude -p "..." --output-format json --json-schema ./schema.json
```

- `-p` / `--print` — single-shot, non-interactive, machine-safe.
- `--output-format json` — envelope your script can parse with `jq`.
- `--json-schema <file>` — shape is a contract; syntax correctness guaranteed.

Missing any one of these → your CI parses natural-language text with regex and breaks silently on the next model update.

## Session isolation in CI — the rule

The **generator** and the **reviewer** run in **separate** headless sessions.

- No `--resume` between them.
- Reviewer sees only the **artifacts** (diff, spec, test output) — not the generator's reasoning trace.
- Self-review retains the generator's biases. An independent reviewer catches what self-review misses. Same principle as W02 subagent isolation.

```bash
# WRONG
claude -p "write X" --session-id gen
claude -p "review what you wrote" --resume gen

# RIGHT
claude -p "write X" --session-id gen
claude -p "review ./out.py against ./spec.md" \
  --output-format json --json-schema ./review.schema.json
```

## Message Batches API — when it's right, when it's wrong

| Property | Value |
|---|---|
| Price | 50% cheaper |
| Latency | Up to 24h (no SLA) |
| Tool use | Single-turn only (no multi-turn loop inside one request) |
| Correlation | `custom_id` — your scheme, returned in results |

- **Right:** overnight bulk, latency-tolerant, cost-sensitive, 100k+ records.
- **Wrong:** pre-merge CI checks, blocking gates, anything with a user-visible SLA, anything needing multi-turn tool conversation.

Exam keywords → batches: "nightly," "overnight," "backfill," "cost-sensitive."
Exam keywords → NOT batches: "blocking," "pre-merge," "SLA," "must complete before merge."

## Anti-patterns that appear as distractors

| Wrong answer | Why it's wrong |
|---|---|
| Plan mode for a 3-line null check | Overhead outweighs the change |
| Direct mode for a 45-file migration | No coverage checklist; you lose the plot |
| Same session generates and reviews | Self-review retains reasoning bias |
| Batches API for a blocking pre-merge check | 24h window, no SLA |
| Regex on natural-language stdout in CI | Silent drift between model updates |
| "Iterate until the model says it's confident" | Self-reported confidence is miscalibrated |
| "Add 'be thorough' to the prompt" to fix reviewer misses | Probabilistic; won't hit zero miss rate |

## 3-bullet recap

- **Plan mode for ambiguous / multi-file / irreversible work; direct for small well-specified edits.** 3 lines → direct; 45 files → plan.
- **Headless CI is three flags together:** `-p --output-format json --json-schema`. Natural-language output is never the contract.
- **Generator and reviewer run in separate sessions.** Self-review inherits bias; an isolated reviewer is the equivalent of a W02 subagent for QA.
