# Walkthrough — Real-world batch extraction + independent reviewer

Read this after `reference.md`. Explains what happens inside the pipeline in `real_world_batch_extract_plus_reviewer.py` and maps each step back to the exam task statements.

## The scenario

A compliance team needs to turn 10 vendor receipts into structured records with reliable vendor / date / amount fields. The code runs the full W08 pipeline:

```
Step 1: Extract  (tool_use + JSON Schema)
Step 2: Validate (Pydantic — STRUCTURAL errors only)
Step 3: Retry    (specific-error feedback, bounded attempts, detected_pattern)
Step 4: Review   (INDEPENDENT reviewer instance — SEMANTIC errors)
```

## The seeded failure modes

Three of the 10 receipts are crafted to exercise specific concepts:

| `custom_id` | Trap | Which step catches it |
|---|---|---|
| R-004 | Date in prose form (`"August 15th, 2024"`) | Step 2 validation fails → Step 3 retry recovers with specific-error feedback |
| R-007 | Amount as text (`"twelve dollars"`) | Step 2 validation fails → Step 3 retry recovers |
| R-009 | Buyer/seller swap in source (`Sold BY: Customer-X, Sold TO: Acme`) — extractor often emits the buyer as `vendor` | Step 2 **passes** (string is a valid string!). Step 4 **independent reviewer flags it.** |

R-009 is the exam-critical case. The schema is satisfied. Without an independent reviewer, the error ships.

## Step 1 — Extraction (simulated batch, real correlation)

We run extractions synchronously so the exercise is self-contained and you can watch each record flow through. **In production this is exactly the workload the Message Batches API is designed for:**

- Compliance runs overnight → 24h window is fine.
- 50% cheaper → meaningful at scale.
- Single-turn per request → extraction fits perfectly (no tool loop needed).
- `custom_id` preserved → we carry the same field shape the Batches API uses so the upgrade is mechanical.

The code carries `custom_id` through every step. That's not decoration — it's how Batches returns results (order is not guaranteed, correlation is via `custom_id`).

### When synchronous IS right

If this were:
- a pre-merge CI check → blocking, needs SLA → **synchronous**
- a real-time user-facing UI → user is staring at a spinner → **synchronous**
- an agentic loop with multi-turn tool calls → **synchronous** (Batches is single-turn per request)

So the exercise's inline-synchronous shape is the correct default for *those* workloads. Compliance is not one of them.

## Step 2 — Pydantic validation catches structural errors

Pydantic rejects:
- R-004 (`purchase_date` not ISO-8601)
- R-007 (`amount_usd` not numeric)

Every other record passes this step — **including R-009, the buyer/seller swap.** That's the point: the schema says "vendor is a string" and R-009's `vendor` is a string. The structural guard has done everything it can do.

This is the separation the exam tests: schemas catch structural errors, not semantic ones.

## Step 3 — Retry with specific-error feedback (the correct shape)

The retry prompt includes:

1. **Original source** (unchanged).
2. **Previous output** (so the model can see its own prior mistake).
3. **Specific validator error** (field, rule, offending value).
4. Instructions to fix only the flagged field.

This is the exam-correct shape. A generic "please try again" gives the model no gradient and typically produces the same bad output.

Bounded to `MAX_RETRIES = 2`. And the `detected_pattern` check stops early if the same field fails the same way twice — because more retries on a doomed case just burn attempts and can hallucinate.

R-004 and R-007 both recover on the first retry: the model sees the specific error ("must be ISO-8601 YYYY-MM-DD") and corrects.

## Step 4 — Independent reviewer (the exam-critical step)

Review runs in a **fresh session**:
- New `messages[]` — no extractor history.
- New system prompt (`REVIEWER_SYSTEM`) — framed as an auditor, not an extractor.
- Same model — the separation is at the session/prompt level, not the model level.

The reviewer is given only the source + the candidate record and asked whether they match semantically.

**On R-009:** the reviewer reads "Sold BY: Customer-X Consulting → Sold TO: Acme Corp" alongside the record `{"vendor": "Customer-X Consulting", ...}` and flags the mismatch (the money flows to Acme, so Acme is the vendor). The record passed the schema. The independent reviewer catches it.

### Why self-review would fail here

Imagine instead you tacked a "now review your own extraction" step onto the extractor prompt. Two problems:

1. **Reasoning bias carries over.** The extractor already reasoned its way to "Customer-X Consulting" as vendor. That reasoning is still in context; the self-review will often re-affirm it.
2. **Confirmation framing.** The session already committed to an answer. "Was my answer right?" has a built-in yes-bias in the same-session case.

The independent reviewer has never seen the reasoning. It just sees source + record and has one job: catch the disagreement.

## Expected run output (shape)

```
===== STEP 1 — Batch extract (synchronous simulation) =====
  [R-001] extracted: {"vendor": "Acme Corp", "purchase_date": "2024-07-01", ...}
  ...
  [R-004] extracted: {"vendor": "Umbrella Co", "purchase_date": "August 15th, 2024", ...}
  [R-007] extracted: {"vendor": "Stark Industries", "purchase_date": "2024-07-12", "amount_usd": "twelve dollars"}
  [R-009] extracted: {"vendor": "Customer-X Consulting", "purchase_date": "2024-07-14", "amount_usd": 1204.0}
  ...

===== STEP 2 — Validate with Pydantic (structural only) =====
  [R-001] OK
  ...
  [R-004] FAIL — field 'purchase_date': must be ISO-8601 ...
  [R-007] FAIL — field 'amount_usd': Input should be a valid number ...
  [R-009] OK           <-- schema passes, but vendor is WRONG
  ...

===== STEP 3 — Retry failed records with specific-error feedback =====
  [R-004] retry 1: {... "purchase_date": "2024-08-15" ...}
    -> RECOVERED on attempt 1
  [R-007] retry 1: {... "amount_usd": 12.0 ...}
    -> RECOVERED on attempt 1

===== STEP 4 — Independent reviewer =====
  [R-001] OK
  ...
  [R-009] FLAGGED (confidence=high) — ["vendor should be 'Acme Corp' (the seller), not 'Customer-X Consulting' (the buyer)"]
  ...
```

The pipeline summary makes the structural-vs-semantic split visible: recovered-by-retry (structural) and reviewer-flagged (semantic) land in different buckets. An aggregate "N% accuracy" would hide which mechanism is catching what.

## What this run teaches you — mapped to exam concepts

| Pipeline moment | W08 concept exercised |
|---|---|
| `custom_id` flowing through every step | **Message Batches API correlation** (task statement 4.5) |
| Step 1 is synchronous for the demo, with a comment on when Batches would be right | **Sync vs Batches decision** — latency tolerance, SLA, 24h window, 50% cheaper |
| Pydantic catching R-004 / R-007, NOT catching R-009 | **Structural vs semantic error split** — schemas catch one, not the other |
| Retry prompt embeds source + prior output + specific error | **Validation-retry loop** (task statement 4.4) |
| `MAX_RETRIES = 2` + `detected_pattern` early stop | **Bounded retries + tracked dismissal** — no infinite loops, no hallucination pressure |
| Reviewer runs in a fresh `messages[]` with a new system prompt | **Independent instance for review** (task statement 4.6) |
| R-009 caught by reviewer but not by schema | **Semantic error invisible to structural validation** |
| Pipeline summary stratifies by stage | **Don't ship one aggregate accuracy metric** — failure modes differ by stage |

## Variations to try

1. **Reproduce the self-review bias.** Replace the reviewer with a same-session self-check: after the extractor emits a record, send a follow-up message in the SAME session asking "is this correct?" Keep all the prior tool_use / tool_result turns in `messages[]`. Run it on R-009. You'll observe the self-review frequently says "looks correct" — because the extractor already reasoned itself into that vendor. The independent reviewer variant catches it reliably. This is the exam's self-review limitation, made concrete.

2. **Swap Batches for synchronous on the wrong workload.** Imagine this were a pre-merge CI check instead of overnight compliance. If you replaced Step 1 with a real Batches API call, every PR would hang up to 24 hours waiting for the batch to finish. The latency/cost tradeoff is stark: synchronous is slower per-request and costs more per-token, but it's the only option when the caller is blocked. Run the exercise once and time it; imagine multiplying that wall time by "wait for batch scheduler" and ask whether a developer would tolerate that in CI.

3. **Remove the `detected_pattern` early stop.** Set `MAX_RETRIES = 10` and strip the pattern check. Feed the extractor a receipt whose `amount` line is literally torn off. Watch retries 2-10 emit either the same malformed value or a hallucinated number. The retry budget and pattern check exist precisely to prevent this — more retries on an absent-data case is worse, not better.

4. **Aggregate metric blindness.** Print only a single "X of 10 passed validation" number and hide the per-stage stratification. You'll see R-009's semantic error is completely invisible in the aggregate. Now stratify: `structural_fail`, `recovered_after_retry`, `reviewer_flagged`, `clean`. The stratified view tells you which guard is earning its keep and which cases need human review. That's the "accuracy by document type × field" idea from task statement 4.6.

5. **Make the reviewer dependent (break the isolation).** Pass the extractor's full `messages[]` into the reviewer call (concatenated before the review prompt). Watch the reviewer's flag rate on R-009 drop — it's now re-exposed to the extractor's reasoning and starts agreeing with the wrong answer. That drop is the reasoning-bias effect the exam asks you to recognize.

## Exam-critical takeaways

1. **Schema validation catches structural errors; an independent reviewer catches semantic errors.** Pipelines need both. Collapsing them is how bad data ships.
2. **Retry with specific error feedback, source, and prior output** — not generic "try again". Bound attempts to 2–3 and use `detected_pattern` to stop early on doomed cases.
3. **Absent source data can't be fixed by retrying** — nullable schema + human-review routing, not a bigger retry budget.
4. **Batches API vs synchronous** is a latency/cost decision, not a quality decision. Use Batches for latency-tolerant bulk work (50% cheaper, up to 24h, single-turn, `custom_id`); use synchronous for anything blocking or real-time.
5. **Independent reviewer = new `messages[]` + new system prompt.** Same-session self-review retains reasoning bias; independent instance does not. Same model is fine — the separation is at the session level.
6. **Stratify accuracy by document type × field.** A single aggregate metric hides exactly the failure modes the multi-stage pipeline is supposed to surface.
