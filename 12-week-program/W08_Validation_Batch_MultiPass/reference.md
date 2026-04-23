# W08 Reference — Validation, Batch & Multi-Pass Review (Domain 4.4–4.6)

Complete, self-contained study material for Week 8. Read this end-to-end. Every concept the exam tests for task statements 4.4–4.6 is here.

Prerequisites: W07 (tool_use + JSON Schema for structured output, `tool_choice`, nullable fields). This week builds on that: W07 gave you *structural* correctness; W08 gives you *semantic* correctness plus the operational plumbing (validation loops, batching, multi-pass review) around it.

---

## 1. Structure vs semantics — the split that drives everything this week

Every extraction/generation task has two failure modes:

| Failure mode | What fails | Who catches it |
|---|---|---|
| **Structural** | Schema violations: missing required field, wrong type, invalid enum, malformed JSON | Pydantic / JSON Schema / `tool_use` enforcement |
| **Semantic** | Schema passes, but the data is *wrong*: the wrong date extracted, a name swapped with a company, the summary contradicts the source | An independent reviewer instance (or a human) |

**Exam-critical distinction:** `tool_use` with a JSON Schema guarantees the output matches the *schema*. It does **not** guarantee the output is *correct*. A distractor that says "schema validation catches semantic errors" is wrong. Schemas catch only the first column.

Every technique this week maps to one of these columns:

- Validation-retry loops → fix structural errors.
- `detected_pattern` / tracked-dismissal fields → prevent infinite structural-retry loops.
- Independent reviewer instances + multi-pass review → catch semantic errors.
- Batch vs synchronous → orthogonal dimension: *when* you run either of the above.

---

## 2. The validation-retry loop

When Claude emits structured output and it fails validation, you have a choice:

1. Throw away the result. (Wasteful and often blocks the pipeline.)
2. Re-prompt Claude with a generic "try again". (Useless — model has no signal about what was wrong.)
3. **Re-prompt with the original source + the failed output + the specific validation error.** (Correct.)

### The shape of a correct retry prompt

```
Your previous extraction failed validation.

ORIGINAL SOURCE:
<full source document, unchanged>

YOUR PREVIOUS OUTPUT:
<the exact JSON you produced>

VALIDATION ERROR:
<the exact Pydantic / JSON Schema error message, field-level>
  e.g. "field 'invoice_date': value 'Q3 2024' does not match format 'YYYY-MM-DD'"

Produce a corrected extraction. Fix ONLY the field(s) the validator flagged.
```

Why this works: the model can now see (a) what it wrote, (b) why the validator rejected it, and (c) the source it should re-read. Without the specific error, the model has no gradient — it will often emit the exact same bad value again.

### Retry attempt budget

Two to three attempts, maximum. Beyond that, you are either:
- Stuck in a loop the model cannot escape (the source really lacks the information), or
- Chasing a structural problem that actually indicates a semantic problem (see §3).

Escalate the record to a human-review queue once the budget is exhausted. Do not retry indefinitely.

---

## 3. When retries don't work — absent source information

The most important failure mode on the exam: **retrying when the information is simply not in the source does not produce correct output — it produces hallucinations or identical failures.**

Example:
- Source: an invoice missing the tax ID line entirely.
- Schema: `tax_id: str` (required, not nullable).
- First attempt: model emits `"tax_id": "000000000"` (hallucinated).
- Validation might even pass (it's a string!). But it's wrong.
- Retry with error feedback doesn't help — the source still doesn't contain the value.

**The fix is upstream, not in the retry loop:**

1. Mark fields that may be absent as `Optional[...]` / nullable in the schema. Null is a legal answer.
2. Detect "absent data" records before they enter the retry loop: if the source clearly lacks the field, bypass retry and route straight to "needs human review" or return with `null` + a reason.
3. If a retry keeps failing on the same field with the same kind of error, assume the source doesn't have it and stop — do **not** burn attempts 2 and 3 on a doomed case.

Exam wording to recognize: *"Invoices without a tax ID cause repeated validation failures. How do you fix the pipeline?"* The right answer is **not** "increase retry budget" or "add 'be thorough' to the prompt". It's "make the field nullable and skip retries when the source lacks the data."

---

## 4. `detected_pattern` / tracked-dismissal fields

A structural error that repeats across attempts often indicates a *category* of problem, not a transient one. The pattern looks like:

- Attempt 1 fails: `invoice_date` is not ISO-8601.
- Attempt 2 fails: `invoice_date` is still not ISO-8601, just phrased differently.
- Attempt 3 fails: same field, same category of error.

If your retry loop only tracks "this attempt failed", you'll keep retrying. If it tracks a **`detected_pattern`** field — e.g., `{"field": "invoice_date", "error_category": "format_mismatch", "occurrences": 3}` — you can stop early and escalate with useful context.

Same idea for dismissal tracking in review loops: if a reviewer keeps flagging the same class of issue and the extractor keeps dismissing it the same way, log `detected_pattern: "reviewer_flags_X / extractor_dismisses"` and escalate — don't just re-run.

**Exam angle:** deterministic pattern tracking beats "the model will self-correct eventually". Same theme as every other week: programmatic mechanism > prompt-based hope.

---

## 5. Batch processing — synchronous vs Message Batches API

Two execution modes for extraction / generation work at volume. The choice is NOT about quality — both produce the same output. It's about **latency tolerance and cost**.

### Synchronous (`client.messages.create`, one request at a time)

- Latency: seconds per request.
- Cost: full list price.
- Use when: **the caller is blocked waiting for the result.**
  - Pre-merge CI checks
  - Real-time user-facing extraction (user pasted a document and is staring at a spinner)
  - Anything with an SLA measured in seconds or minutes
  - Anything inside a blocking code path

### Message Batches API

- Latency: up to **24 hours** per batch.
- Cost: **50% cheaper** than synchronous for the same tokens.
- Use when: **nobody is waiting in real time.**
  - Overnight re-processing of a week's documents
  - Backfill of historical data
  - Weekly compliance report generation
  - Regenerating embeddings / extractions after a schema change

### Batches API — specifics the exam will probe

1. **Each batch request is single-turn.** You send one user message in, you get one assistant response out. **No multi-turn tool-calling loop inside a single batched request.** If your extraction needs the agentic loop (model calls a tool, gets result, calls another tool), you cannot do the whole flow inside Batches — you'd need to unroll it or run it synchronously.
2. **`custom_id`** is how you correlate request ↔ response. You submit `[{"custom_id": "doc_001", "params": {...}}, ...]` and the response stream carries `custom_id` back. Without it, you can't tell which input produced which output.
3. **Status polling.** After submission you get a batch ID; you poll that ID until status is `ended`, then download results. Not push-based.
4. **Up-to-24h window** — it may finish in 15 minutes; it may finish in 23 hours. Design for the worst case.

### Mis-assignment examples to catch on the exam

| Scenario | Wrong mode | Correct mode | Why |
|---|---|---|---|
| Pre-merge lint-check on every PR | Batches API | Synchronous | PR is blocked on the check; 24h is unacceptable |
| Nightly re-extraction of 50k invoices with a new schema | Synchronous | Batches API | Nobody's waiting; 50% discount; latency fine |
| Chat UI where user pastes a receipt and expects instant data | Batches API | Synchronous | Real-time, user-facing |
| Weekly risk report summarizing 10k support tickets | Synchronous | Batches API | Not time-critical; big savings |
| Agentic loop that calls tools, reads results, calls more tools | Batches API | Synchronous | Batches is single-turn per request |

### SLA calculation — when Batches API *is* usable under a deadline

You might have an SLA (say, 30 hours end-to-end) that *sounds* too tight for Batches (24h window), but is achievable if you design the submission cadence correctly.

**Worked example:** you need every document processed within **30 hours of upload**, and Batches takes up to **24 hours** per batch.

Wrong approach: one batch per day. A document uploaded just after that day's cutoff waits up to ~48h worst case → SLA blown.

Correct approach: submit a batch **every 4 hours**. Worst-case latency for any one document = *4h (waiting for the next batch window) + 24h (batch processing) = 28h*. Under 30h — SLA met.

General formula: if SLA is `S` hours and batch processing is at most `B` hours, submit a batch every `S − B` hours (minus a safety margin for variance).

**Exam trap:** the test will describe an SLA and ask whether Batches is appropriate. A naive reader checks only "24h > SLA?" and rules it out. A correct reader checks "can I schedule batches so 4h + 24h < SLA?" and often finds Batches fits where it first looks disqualified.

---

## 6. Self-review is broken — use an independent instance

A single session that produced an extraction is a *bad* reviewer of that same extraction. Two reasons:

1. **Reasoning bias carries over.** The same internal reasoning that led to the mistake during generation still looks reasonable during review. The model "agrees with itself" because it's literally the same reasoning trace in context.
2. **Confirmation framing.** Asking "is this output correct?" in the same session where the output was generated biases the model toward "yes" — it already committed to it.

**Fix: route review through an independent Claude instance** — new `messages[]`, new system prompt, no shared history. The reviewer reads the source + the output with no memory of how the output was produced. It treats the output as external input to critique, not as something it's defending.

### What counts as "independent"

- New API call with a **new, fresh `messages[]`** (not a continuation).
- A **different system prompt** framed as a reviewer, not an extractor.
- Input: the source document + the candidate extraction, presented as two chunks of data.
- No carry-over of prior conversation, tool results, or reasoning text.

Same model is fine; the separation is at the session / prompt level, not the model level.

### Exam wording

*"The extractor sometimes swaps the buyer and seller fields. Adding a self-check step at the end of the extractor prompt doesn't fix it. What's the right approach?"*
Right: run an independent reviewer instance on the output. Wrong: longer prompt, "think step by step", higher temperature, bigger model.

---

## 7. Multi-pass review patterns

One review pass is not always enough. Two levels of review exist and they catch different things:

### Pass 1 — Per-record / per-file local analysis

- Reviewer sees **one** record + its source.
- Catches: the extracted date doesn't appear in this document; the summary references facts not in this document; required field is blank when the source has it.
- Scope: one document at a time.

### Pass 2 — Cross-record / cross-file integration

- Reviewer sees **all** records together (or a sampled aggregate).
- Catches: customer X has three different spellings across records; invoice totals don't match a running balance; the same transaction appears under two IDs; a date ordering contradiction across the set.
- Scope: the whole batch. These errors are **invisible** at the per-record level.

**Exam-critical:** if a question describes an error that's only visible by comparing records to each other (duplicate IDs, inconsistent naming, totals that don't add up), the answer is a **cross-record integration pass**, not a better per-record prompt.

### When to use one, both, or neither

- Schema-only validation: when errors are purely structural and the data is low-stakes.
- Per-record review only: per-record data looks fine but you don't care about aggregate consistency.
- Per-record + cross-record: any time you're producing a *dataset*, not just individual records. Financial, medical, regulatory extractions virtually always need both.

---

## 8. Anti-patterns (these ARE the exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| "Retry any validation failure 10 times" | If the source lacks the info, retries hallucinate or repeat the same error | Bound retries (2–3), detect absent-data cases, escalate to human |
| "Retry with a generic 'please try again' prompt" | Model has no signal about what was wrong → same output | Append source + failed output + **specific** validator error |
| "The same session that did the extraction reviews it" | Reasoning bias — it already agrees with itself | Independent reviewer instance (new `messages[]`, new system prompt) |
| "Schema validation catches all errors" | Schemas catch structural errors only, not semantic ones | Schema + independent reviewer for semantics |
| "Use Message Batches API for pre-merge CI checks" | 24h window, no SLA — PR would hang for a day | Synchronous for blocking paths |
| "Use synchronous for nightly 100k-doc reprocessing" | Pays full price for latency you don't need | Batches API — 50% cheaper, latency tolerated |
| "Put the whole agentic multi-turn flow inside one Batches request" | Each Batches request is single-turn | Use synchronous for the agentic loop; or unroll into single-turn steps |
| "Skip `custom_id` — I'll correlate by order" | Results do not guarantee input order; you'll mis-associate | Always set `custom_id` per request |
| "One aggregated accuracy number across all document types" | Hides per-type and per-field failure modes (90% aggregate can hide 40% on a critical field) | Stratify: accuracy **per document type × per field** |
| "Raise retry budget when a field keeps failing" | If the source truly lacks the field, more retries = more hallucinations | Detect the pattern, make the field nullable, or escalate |
| "One reviewer pass covers both per-record and dataset-level errors" | Per-record review can't see cross-record inconsistencies | Two passes: local + integration |
| "If review catches an issue, add a rule to the extractor prompt to prevent it" | Probabilistic; bias will still leak through on similar cases | Keep the independent reviewer as a deterministic guard in the pipeline |

The last row is this week's version of the recurring exam theme: **deterministic mechanisms (independent reviewer, hooks, schema) beat prompt instructions.** Same principle as W01 (`stop_reason` not text parsing), W02 (`Task` in `allowedTools` not "please delegate"), W03 (hooks not prompt rules). Burn it in — it's the single biggest pattern across the whole exam.

---

## 9. Putting it together — a validated extraction pipeline

A production-shaped pipeline has these stages. Every exam question about extraction pipelines is testing whether you can pick the right stage for a given failure:

1. **Submit to extractor** (synchronous or Batches, per §5).
2. **Schema validation** (Pydantic / JSON Schema). Failures → retry queue.
3. **Retry queue** with specific-error feedback, bounded attempts, absent-data detection (§2–§3). Exhausted → human review.
4. **Per-record semantic review** by an independent reviewer instance (§6). Flags → human review.
5. **Cross-record integration review** (§7). Aggregate-level flags → human review.
6. **Confidence-stratified sampling** for human review (covered in W10 in full — the W08 version is: stratify by doc-type × field, not a single aggregate).

Each stage catches a failure mode the other stages *can't* catch. Collapsing two stages into one (e.g., schema-only, or extractor-self-reviews) is how bad pipelines ship.

---

## 10. What this week's exam questions will probe

- Given a broken retry loop, pick the fix (specific error in prompt; bounded retries; absent-data detection).
- "Schema passes but output is wrong" → independent reviewer, not prompt tweaks, not bigger model.
- Sync vs Batches: given latency-tolerant bulk work, choose Batches; given blocking pre-merge check, choose synchronous.
- Batches specifics: single-turn per request, `custom_id`, 24h window, 50% cheaper.
- Per-record vs cross-record review: pick the right one for the described error (intra-document = per-record; cross-document = integration).
- Self-review failure scenarios: same-session bias; fix with independent instance.
- "How do you measure accuracy?" → stratified by doc type and by field, never a single aggregate.

---

## 11. Fast recap

- Schemas catch **structural** errors; independent reviewers catch **semantic** errors. Two different jobs, two different mechanisms.
- Retry loops: append the **specific** validator error + source + prior output. Bounded to 2–3 attempts. Absent source data → stop, don't hallucinate.
- Synchronous for blocking / latency-sensitive work. Batches API for latency-tolerant bulk — 50% cheaper, up to 24h, single-turn per request, `custom_id` for correlation.
- Self-review retains reasoning bias. Use an **independent instance** (new messages, new system prompt) for review.
- Multi-pass review: per-record local pass **plus** cross-record integration pass. Aggregate-level errors are invisible at the per-record level.
- Deterministic guard (schema, reviewer instance, retry-budget, pattern tracking) beats prompt instruction — every time.

When you can explain each of those six bullets out loud in ~20 seconds each, you're ready for the W08 test.
