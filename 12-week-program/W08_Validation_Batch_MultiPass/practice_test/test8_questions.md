# Practice Test 8 — Validation, Batch & Multi-Pass

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 4.4–4.6

## Instructions
Solve all 10 questions before opening `test8_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. An extraction pipeline uses `tool_use` with a strict JSON Schema. QA reports that 8% of outputs pass schema validation but have the wrong buyer name (the seller name was extracted into the buyer field instead). Which statement best describes the situation?
- A. Tighten the JSON Schema to add a regex on the buyer field — that will catch the swap.
- B. This is a structural error; add Pydantic post-validators to reject it.
- C. This is a semantic error; schemas only catch structural errors and an independent reviewer instance is required.
- D. Raise `temperature` to 0 and the swaps will stop.

### Q2. A validation-retry loop currently re-prompts Claude with the text "Your last output was invalid. Try again." After three attempts it still fails on the same field. Which change most directly fixes the loop?
- A. Increase the retry budget from 3 to 10 attempts.
- B. Append the original source, the previous failed output, and the specific field-level validator error to the retry prompt.
- C. Switch the model to a larger one for the retries only.
- D. Append "think step by step and be extra careful" to the retry prompt.

### Q3. An invoice extraction pipeline requires `tax_id: str` (non-nullable). About 12% of invoices have no tax ID line at all. The retry loop keeps failing or produces values like `"000000000"`. What is the correct fix?
- A. Raise the retry budget to 10 so the model eventually finds it.
- B. Make `tax_id` `Optional`/nullable, detect absent-data records before entering the retry loop, and route them to human review or return `null` with a reason.
- C. Add "never hallucinate a tax ID" to the extractor prompt.
- D. Run the extraction through Message Batches API so retries are cheaper.

### Q4. Your team needs to re-extract 50,000 historical invoices overnight under a new schema. No user is waiting in real time. Which execution mode is correct and why?
- A. Synchronous — lower latency is always better.
- B. Message Batches API — latency is tolerated and batches cost 50% less than synchronous for the same tokens.
- C. Synchronous with high parallelism — batches don't support JSON Schema.
- D. Message Batches API because batches give higher-quality output than synchronous.

### Q5. A developer proposes running the pre-merge CI lint check (which must block the PR until it completes) via the Message Batches API to save money. Why is this the wrong choice?
- A. Batches API doesn't support structured output.
- B. Batches API has up to a 24-hour processing window, which would block PRs for up to a day; blocking paths need synchronous.
- C. Batches API cannot use system prompts.
- D. Batches API is more expensive than synchronous for small batches.

### Q6. A team submits Message Batches requests without setting `custom_id`, planning to correlate inputs to outputs by the order of results. What is the problem with this approach?
- A. Nothing — results are returned in submission order.
- B. Results are not guaranteed to be returned in input order, so correlation by order will mis-associate inputs and outputs; always set `custom_id` per request.
- C. `custom_id` is only needed for synchronous requests.
- D. Batches API rejects requests without `custom_id`.

### Q7. An extraction pipeline currently ends with a "self-check" step appended to the same prompt: "Now review your output and confirm it is correct." Buyer/seller swaps still slip through. Which is the best fix?
- A. Make the self-check prompt longer and add examples.
- B. Route review through an independent Claude instance with a fresh `messages[]` and a reviewer system prompt — separation is at the session/prompt level.
- C. Add "do not swap fields" to the extractor system prompt.
- D. Run the self-check at a higher temperature so the model disagrees with itself more.

### Q8. A financial pipeline extracts invoice records. Per-record review passes cleanly, but auditors notice that customer "Acme Corp" appears as "ACME Corporation" and "acme corp." across records, and a running balance doesn't reconcile across the dataset. Which review stage is missing?
- A. A stricter schema with a regex on the customer name field.
- B. More retry attempts at the extraction stage.
- C. A cross-record / cross-file integration review pass that sees all records together — aggregate-level errors are invisible at the per-record level.
- D. A synchronous-vs-batches mode change.

### Q9. Your SLA is that every document must be processed within 30 hours of upload. Message Batches processing takes up to 24 hours per batch. A colleague claims Batches is automatically disqualified because 24h is "too close" to 30h. What's the correct analysis?
- A. They're right — any SLA under 48h rules out Batches.
- B. Submit one batch per day; worst-case is still under 30h.
- C. Submit a batch roughly every `SLA − B` hours (e.g., every ~4–6h with a safety margin). Worst case ≈ 4h wait + 24h processing = 28h, under the 30h SLA.
- D. Split each document across multiple batches to reduce per-document latency.

### Q10. A retry loop has failed three times on the same field (`invoice_date`) with the same category of error (format mismatch). The system currently only tracks "this attempt failed / this attempt succeeded". Which improvement best aligns with the reference's guidance?
- A. Increase the retry budget to 15 and add "be thorough" to the prompt.
- B. Track a `detected_pattern` field (e.g., `{"field": "invoice_date", "error_category": "format_mismatch", "occurrences": 3}`) so the loop can terminate early and escalate with useful context.
- C. Switch the field to `Any` in the schema so it never fails validation.
- D. Move the extraction to Message Batches to let the model "cool off" between attempts.

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
