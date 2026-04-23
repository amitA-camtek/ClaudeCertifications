# Build — Plan Mode, Iteration & CI/CD

**Time:** 40 min · **Goal:** Produce a headless CI invocation that runs a schema-constrained generator session, then a separate fresh reviewer session, and fails the check on blocking issues.

## What you'll have at the end
- `exercises/ci_invoke.sh` — two `claude -p` calls (generator + reviewer), non-zero exit on review fail
- `exercises/review_schema.json` — JSON Schema pinning the reviewer's output shape

## Prereqs
- Env: Claude Code CLI on `PATH`, `jq` installed, a JSON Schema validator available (the CLI enforces with `--json-schema`)
- Finished reading [reference.md](../reference.md) §3–§4
- Target: `exercises/ci_invoke.sh` + `exercises/review_schema.json` (peek at [minimal_headless_claude.md](minimal_headless_claude.md) if stuck)

## Steps

### 1. Identify CI inputs and outputs (~5 min)
Write down, on paper, what goes in and what comes out of the pipeline. Inputs: PR diff path, spec path. Outputs: generator artifact + a reviewer JSON with `issues[]`, `approved`, `blocking_count`.
- [ ] List inputs in a comment at the top of `ci_invoke.sh`
- [ ] Decide exit rule: `blocking_count > 0` → exit 1

**Why:** §7 canonical CI shape — two independent invocations, one deterministic decision at the end.
**Checkpoint:** You can state in one sentence what makes the build fail.

### 2. Write `review_schema.json` (~8 min)
Draft-07 object with `required: ["issues","approved","blocking_count"]`, `additionalProperties: false`. Each issue has `severity` (`enum: ["blocking","warn","nit"]`), `file`, `line`, `message`.
- [ ] Create `exercises/review_schema.json` with the three required fields
- [ ] Constrain `severity` via `enum` (syntactic — semantic correctness is still the model's job)

**Why:** §3c — `--json-schema` guarantees shape; §6 "natural-language stdout as contract" is an anti-pattern. The schema IS the pipeline contract.
**Checkpoint:** `jq type exercises/review_schema.json` returns `"object"`.

### 3. Headless generator invocation (~6 min)
First call: fresh session, writes code/artifact. Pipeline-friendly form is `-p` + `--output-format json` — no interactive prompts, stable envelope.
- [ ] In `ci_invoke.sh` add: `claude -p "implement per ./spec.md, write to ./out.py" --output-format json > gen.json`
- [ ] Parse with `jq -r '.result'` — do NOT regex natural language

**Why:** §3a–§3b — `-p` is the only CI-safe form; `--output-format json` gives a parseable envelope. §6 warns against regexing stdout.
**Checkpoint:** `jq -e '.session_id' gen.json` succeeds.

### 4. Separate fresh reviewer invocation (~8 min)
Second call: **no `--resume`, no shared `--session-id`**. Reviewer sees only artifacts (the diff and spec paths), not the generator's reasoning trace.

Snippet (the one code block for this file):
```bash
claude -p "Review ./out.py against ./spec.md. Output JSON per ./review_schema.json." \
  --output-format json --json-schema ./exercises/review_schema.json > review.json
```
- [ ] Confirm no `--resume` flag anywhere in the reviewer call
- [ ] Reviewer prompt references artifacts by path only

**Why:** §4 — self-review retains generator bias; fresh session recreates the independence a human reviewer has. §6 anti-pattern "Use `--resume` to have the reviewer pick up from the generator."
**Checkpoint:** `grep -c -- '--resume' ci_invoke.sh` returns `0`.

### 5. Schema-constrain the reviewer output (~4 min)
Add `--json-schema ./exercises/review_schema.json` to the reviewer call. Runtime rejects off-schema output; your script can trust `.result.blocking_count` exists.
- [ ] `.result` is now a JSON object (not a free-form string)
- [ ] Parse: `jq '.result.blocking_count' review.json`

**Why:** §3c + §7 — contract enforcement is the third leg of the CI tripod (`-p` + `json` + `schema`). Missing any one makes the pipeline flaky.
**Checkpoint:** `jq -e '.result.issues | type == "array"' review.json` is `true`.

### 6. Exit non-zero on blocking issues (~5 min)
Decision step at the end of `ci_invoke.sh`: read `blocking_count`, exit 1 if > 0, else 0. This is the gate CI uses.
- [ ] `count=$(jq '.result.blocking_count' review.json); [ "$count" -eq 0 ] || exit 1`
- [ ] `chmod +x exercises/ci_invoke.sh`

**Why:** §7 flow — `blocking_count > 0 → fail the check`. §6 anti-pattern "retry with no structured error context" — the schema already carries `issues[]` for the retry context.
**Checkpoint:** Force `blocking_count=1` in a stub `review.json` and confirm the script exits 1.

### 7. Smoke-test end-to-end (~4 min)
Run `./exercises/ci_invoke.sh` against a tiny sample diff and spec. Confirm two distinct `session_id`s in `gen.json` and `review.json`.
- [ ] `jq -r '.session_id' gen.json review.json` — two different IDs
- [ ] Script exit code matches `blocking_count` rule

**Why:** §4 "what separate session means concretely" — different `session_id`s are the observable proof of isolation.
**Checkpoint:** Two distinct IDs, exit code aligns with the count.

## Verify
Run the script against a sample PR diff. Expected:
- Generator returns a schema-conforming JSON envelope on stdout; `.result` is a JSON object, not a markdown string
- Reviewer session starts fresh: distinct `session_id` from the generator, no `--resume`, no context leak
- Script exits 1 when `blocking_count > 0`, exits 0 otherwise — CI can consume it directly

**Common mistakes:**
- Reviewer reuses generator session via `--resume` or shared `--session-id` → §4, §6 (self-review bias)
- Treating `--json-schema` as a semantic guarantee (right values) instead of a syntactic one (right shape) → §3c
- Regexing natural-language `result` because `--output-format json` was added but `--json-schema` was skipped → §3b vs §3c
- Picking Message Batches API for this pre-merge check — 24 h window kills the gate → §5

## Stretch — Polish block (30 min on Practice Day)
From the Polish row: add a second CI invocation with a separate reviewer session (context isolation) wired as its own shell function, and prove isolation observably.
- [ ] Extract `run_generator` and `run_reviewer` into two shell functions in `ci_invoke.sh`
- [ ] Add a third call: a "meta-reviewer" that reads only `review.json` (not `gen.json`) and flags reviewer hallucinations — again, fresh session, own schema
- [ ] Log all three `session_id`s to `ci.log` and assert all three differ
- [ ] Add a `generator.schema.json` so the generator's `files_changed`/`summary` is also schema-shaped (§7 canonical shape)

## If stuck
Compare with [minimal_headless_claude.md](minimal_headless_claude.md). Read → close → rewrite.
