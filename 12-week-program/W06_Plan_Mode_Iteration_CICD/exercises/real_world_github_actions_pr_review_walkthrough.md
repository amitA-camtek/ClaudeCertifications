# Walkthrough — GitHub Actions PR review pipeline

Companion to `real_world_github_actions_pr_review.md`. This walkthrough steps through the pipeline and maps each decision to a W06 exam concept. At the end, two variations you can try to watch the failure modes emerge.

---

## Step-by-step, with exam-concept callouts

### Step 1 — Trigger: `on: pull_request`

The workflow runs on `opened`, `synchronize`, `reopened`. That makes this a **pre-merge, blocking check** — the PR cannot merge until the workflow returns.

- **Exam concept: Message Batches API would be WRONG here.** Batches have up to a 24-hour window and no SLA. A pre-merge check that can stall for a day is not a product. Synchronous headless `claude -p` is the only right answer.

### Step 2 — `timeout-minutes: 10`

Hard ceiling on the whole job.

- **Exam concept:** pre-merge checks need an SLA. A hung Claude invocation that eats your runner forever is worse than a "review unavailable" message. Always bound pre-merge calls by wall-clock time.

### Step 3 — Checkout + build diff

Compute `pr.diff` from `base.sha` to `head.sha`, excluding lockfiles and vendored code.

- **Exam concept: trim inputs before they hit the model.** Connects to W05/W09 context-management hygiene — don't feed the reviewer 50k lines of lockfile churn. You're paying in tokens for every irrelevant line, and you're burying real findings in noise.

### Step 4 — Install `@anthropic-ai/claude-code`

Standard package install. Nothing clever here.

### Step 5 — Run the reviewer: `claude -p --output-format json --json-schema ./review.schema.json`

This is the heart of the pipeline. Every flag matters.

- **`-p` / `--print`** → single-shot, non-interactive. No REPL, no approval prompts, no interactive tool gates. **Exam concept: headless mode is the ONLY form for CI.**
- **`--output-format json`** → a stable envelope (`session_id`, `stop_reason`, `result`). Your script parses it with `jq`, never with regex on free text. **Exam concept: natural-language output is never the CI contract.**
- **`--json-schema ./review.schema.json`** → the `result` field is shape-guaranteed. **Exam concept: structured output eliminates syntax errors; semantic errors (wrong severity, wrong file) are still on the model.** Same idea as `tool_use` with JSON Schema in W04/W07.
- **No `--resume`, no `--session-id` linking to a prior Claude step** → the reviewer runs in its own fresh session.

#### Session isolation — the load-bearing decision

- **Exam concept: generator session ≠ reviewer session.** Self-review retains reasoning bias. The reviewer here sees only the diff, PR title/body, and schema — no prior Claude scratchpad. This is exactly the W02 isolation principle applied to CI: the reviewer is a QA "subagent" isolated by being a different CLI invocation.

If an earlier step used Claude to generate or auto-fix code, that step would run with `--session-id writer-$RUNID` and the reviewer would still NOT use `--resume`. Two sessions, two contexts, one clean handoff via artifacts.

### Step 6 — Parse, post comments, fail on blocking

```bash
BLOCKING=$(jq '[.result.issues[] | select(.severity == "blocking")] | length' review.json)
```

- **Exam concept: deterministic mechanism for pipeline control.** The gate is "blocking count > 0 → fail the check." Not "ask Claude if it thinks this should block" — that would be self-reported confidence, which is miscalibrated. You defined `blocking` categorically in the schema enum, so the model has to pick it deliberately, and your CI logic is simple, deterministic, testable.

- The `gh api` POST to `/issues/<N>/comments` posts the consolidated comment. `exit 1` on blocking findings fails the check and blocks merge.

---

## Mapping decisions to exam concepts — one-line summary

| Decision | W06 concept |
|---|---|
| Synchronous `claude -p` (not Batches API) | Pre-merge check needs SLA; Batches = 24h, no SLA |
| `--output-format json --json-schema` | Structured output is the CI contract |
| No `--resume` between writer and reviewer | Session isolation — self-review retains bias |
| Reviewer sees only artifacts (diff, spec, schema) | Isolation pattern (W02) applied to CI |
| `timeout-minutes: 10` | Pre-merge checks need bounded latency |
| Categorical `severity` enum + `BLOCKING=` from `jq` | Deterministic gate, not self-reported confidence |
| Lockfiles excluded from diff | Context-hygiene: trim input noise |
| Explicit `"blocking"` / `"warn"` / `"info"` vs free-text severity | Enum-constrained = deterministic parsing |

---

## When Batches API would be WRONG here (and when it's right)

The Message Batches API is 50% cheaper than the standard Messages API and supports up to a 24-hour completion window. It sounds attractive for "a bunch of reviews," but it's **wrong for this pipeline** for three reasons.

1. **No SLA.** A batch may complete in minutes or may take 23 hours. A PR check that might stall for a day isn't a check — developers will merge with `[skip ci]` out of frustration.
2. **Blocking gate.** The whole premise of pre-merge review is that it blocks the merge until it returns. Batches are asynchronous; by the time the result comes back, the PR is long merged.
3. **Single-turn tool use.** Batches don't support multi-turn agentic loops inside a single request. If your reviewer needs to call a tool, read a result, call another tool — that won't work in a batch.

**Where Batches would be right** — a weekly code-health report: "review every PR merged in the last 7 days and generate a trends summary." Latency-tolerant (runs Sunday night, read Monday morning), cost-sensitive (hundreds of PRs × 50% discount = real savings), single-turn-friendly (one diff → one review object per `custom_id`). That's the canonical batch use case; this pre-merge workflow is its opposite.

**Exam phrasing that flags "not batch":** "blocking," "pre-merge," "SLA," "must complete before merge," "PR gate."
**Exam phrasing that flags "yes batch":** "nightly," "weekly," "overnight bulk," "backfill," "cost-sensitive," "latency-tolerant."

---

## Variations to try

Run these to see the failure modes first-hand. Each one teaches a W06 lesson by breaking the pipeline in a specific, exam-relevant way.

### Variation A — Reuse the session (watch bias emerge)

Modify Step 5 to resume a writer session:

```yaml
- name: Auto-fix lint first
  run: |
    claude -p "Auto-fix lint in src/" \
      --session-id shared-${{ github.run_id }}

- name: Review (WRONG — shares session)
  run: |
    claude -p "Review the diff at pr.diff" \
      --resume shared-${{ github.run_id }} \
      --output-format json \
      --json-schema ./review.schema.json \
      > review.json
```

Run this on a PR where the auto-fix introduced a subtle bug (e.g., changed `==` to `===` in a place where loose equality was intentional). The shared-session reviewer will approve it — it "remembers" that it made that change deliberately, so it defends the change instead of flagging it.

**Lesson:** self-review retains the generator's reasoning bias. The reviewer rationalizes its own output. Isolation is enforced by *not sharing the session*, not by prompt instructions.

**Then fix it:** delete `--resume shared-${{ github.run_id }}`. Re-run. Watch the (now isolated) reviewer flag the equality change.

### Variation B — Switch to the Batches API (watch it be the wrong tool)

Replace Step 5 with a Batches API submission:

```yaml
- name: Submit review to Batches API (WRONG for pre-merge)
  run: |
    # Submit the review as a batch job with custom_id=pr-<N>
    curl https://api.anthropic.com/v1/messages/batches \
      -H "x-api-key: ${ANTHROPIC_API_KEY}" \
      -d @batch_request.json
    # ... and now what?  We can't wait up to 24h; the PR is waiting.
```

Two things go wrong:

1. **No SLA.** Your workflow either has to poll for up to 24h (violating its own `timeout-minutes: 10`), or mark the check as "pending" and return — at which point the developer can't tell whether the review is coming or is lost.
2. **The developer workflow breaks.** Pre-merge is a gate; the gate only works if it returns fast enough to shape the developer's feedback loop. Batches don't do that.

**Lesson:** Batches API is 50% cheaper and up to 24h — great for overnight bulk, wrong for any synchronous pre-merge gate. Match the API to the latency envelope, not to the discount.

**Then fix it:** go back to synchronous `claude -p`. Save the Batches API for a separate nightly "weekly code-health" workflow where the 50% saving actually compounds across hundreds of PRs.

---

## Fast recap

- Pre-merge CI review needs **synchronous `claude -p`** — not Batches.
- `-p --output-format json --json-schema` is the three-flag contract. Skip any one and your pipeline breaks.
- Reviewer runs in a **fresh session**. No `--resume`. It sees diff + spec + schema, nothing more.
- Gate on a **deterministic field** (`severity == "blocking"`), not on self-reported confidence.
- Variation A shows bias emerging from shared sessions. Variation B shows SLA breaking under batch latency. Both are the wrong choices the exam will put in front of you.
