# W08 Study Day — Validation, Batch & Multi-Pass Review (Domain 4.4–4.6)

## The one thing to internalize

**Schemas catch structural errors. Independent reviewers catch semantic errors. These are two different jobs and require two different mechanisms.** A pipeline that uses only one of them will ship bugs. Every W08 exam question is a variant of this split.

## Structural vs semantic, in one table

| Error type | Example | Caught by |
|---|---|---|
| Structural | `invoice_date: "Q3 2024"` when schema wants ISO-8601 | Pydantic / JSON Schema / `tool_use` |
| Semantic | `invoice_date: "2024-08-15"` but the doc clearly says 2024-09-15 | Independent reviewer instance |

Same output file, two completely different failure modes.

## Validation-retry — the correct shape

On a schema failure, re-prompt with:

1. The **original source**.
2. The **exact failed output**.
3. The **specific validator error message** (field name, rule, offending value).
4. Instructions to fix only the flagged field.

Generic "try again" gives the model no gradient. Always include the specific error.

## When retries don't help

If the source does not contain the information, retrying produces **hallucinations or identical failures**. Two to three attempts max. Then:

- If the field is legitimately optional → mark it `Optional[...]` / nullable in the schema and let `null` be a valid answer.
- If the data is truly missing → route to human review.
- **Do not** keep retrying. The model cannot invent data that isn't there without hallucinating it.

## `detected_pattern` / tracked-dismissal fields

If the same field fails with the same category of error across attempts, record `{"field": X, "error_category": Y, "occurrences": N}` and stop early. Same principle for review loops where a reviewer keeps flagging the same class of issue. Deterministic tracking beats "the model will self-correct eventually".

## Synchronous vs Message Batches API

| Mode | Latency | Cost | Use when |
|---|---|---|---|
| Synchronous | Seconds | Full price | Caller is blocked. Pre-merge CI, real-time user-facing, SLA in seconds/minutes. |
| Batches API | Up to 24h | **50% cheaper** | Nobody's waiting. Overnight reprocessing, backfills, weekly reports. |

### Batches API specifics

- **Each request is single-turn.** No multi-turn tool-calling loop inside one batched request.
- **`custom_id`** per request — that's how you correlate input to output. Never rely on order.
- **Status polling** — submit, get batch ID, poll until `ended`, download results.
- Up-to-24h means "could be 15 min, could be 23 hours" — design for the worst case.

Misapplying modes is the fastest path to a wrong answer:
- Batches API for pre-merge CI → PR hangs for a day. Wrong.
- Synchronous for nightly 100k-doc reprocessing → paying full price for latency nobody wanted. Wrong.

## Self-review is broken

A session that produced an output is a biased reviewer of that output. Two reasons:

1. **Reasoning bias carries over** — the reasoning that led to the mistake still looks reasonable during review because it's literally the same reasoning trace.
2. **Confirmation framing** — the session already committed to the output; asking "is this right?" biases it toward yes.

Fix: **independent reviewer instance** — new `messages[]`, new system prompt framed as a critic, no carry-over. Same model is fine; separation is at the session/prompt level.

## Multi-pass review

Two passes, two scopes:

- **Per-record / per-file local pass.** Reviewer sees one record + its source. Catches: extracted value not in the source, summary contradicts the doc, required field wrongly blanked.
- **Cross-record / cross-file integration pass.** Reviewer sees all records together. Catches: duplicate IDs, inconsistent name spellings, totals that don't add up, date ordering conflicts. **These errors are invisible at the per-record level.**

If the exam describes an error that requires comparing records to each other, the answer is an integration pass — not a better per-record prompt.

## Anti-patterns to recognize instantly

- Generic retry with no error context → useless.
- Retrying absent-data cases → hallucinations.
- Same session extracts and reviews → bias.
- Schema validation "catches all errors" → structural only.
- Batches API for SLA-bound work → 24h window doesn't fit.
- Multi-turn tool flow inside one Batches request → each request is single-turn.
- Single aggregate accuracy number → hides per-type and per-field failures. Stratify.

## 3-bullet recap

- **Structural vs semantic**: schemas catch one, independent reviewers catch the other. You need both, they are not substitutes.
- **Retry with specific error feedback, bounded attempts, and absent-data detection** — not a generic retry loop. If the source doesn't have it, stop and escalate, don't hallucinate.
- **Synchronous for blocking/SLA work; Batches API (50% cheaper, up to 24h, single-turn, `custom_id`) for latency-tolerant bulk.** Multi-pass review = per-record local + cross-record integration; aggregate-level errors only show up in the integration pass.
