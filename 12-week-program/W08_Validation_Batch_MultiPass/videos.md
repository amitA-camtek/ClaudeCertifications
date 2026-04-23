# W08 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** validation-retry loops, when retries can't help, Message Batches API (50% cheaper, 24 h, single-turn, `custom_id`), self-review bias, independent reviewer pass.

---

## Talk 1 — Validation-retry loops, done right

- **Structure is not semantics.** `tool_use` + JSON Schema guarantees the shape; it does *not* guarantee the values are correct. Run a domain validator (Pydantic, a business-rules checker, a regex on formats) after the LLM, and feed failures back.
- **The retry prompt must contain three things:**
  1. The original source document.
  2. The prior (invalid) output.
  3. The **specific** validator error — "field `amount` must be > 0; you returned -15."
  Omit any of these and the retry is a coin flip.
- **Bound retries to 2–3 attempts.** More is wasted spend. If it hasn't converged in 3 tries, something structural is wrong (schema, prompt, source coverage) and a retry won't fix it.
- **Retries can't help when the info is absent.** If the document doesn't contain the field, retrying with better error messages doesn't conjure the data. Map to `null` (via nullable field) and route for human review.
- **`detected_pattern` fields** — if the validator can say "this looks like a truncated document" or "this looks like a different form type," thread that hint into the retry prompt. Pattern-aware early termination beats generic retry.

---

## Talk 2 — Message Batches API walkthrough

- **The tradeoffs you must memorize:**
  - **50% cheaper** than sync.
  - **Up to 24 h** completion window (no SLA; could finish in 10 minutes, could take 23).
  - **Single-turn only** — no multi-turn tool-calling inside one batched request. (You can submit many single-turn requests in one batch.)
  - **`custom_id`** on every request; results come back keyed by `custom_id`.
- **Right uses:** overnight extraction, weekly backfills, large-scale evaluations, A/B prompt comparisons.
- **Wrong uses:** anything user-blocking, pre-merge CI, real-time chat. The 24-h window kills SLA.
- **Pattern: submit → poll → process.**
  1. Build a JSONL of requests, each with `custom_id`.
  2. Submit via batches endpoint; receive a batch ID.
  3. Poll for `processing_status: ended`.
  4. Download results; rejoin by `custom_id`.
  5. **Partial failures are normal.** Some requests error; pick them out, fix inputs, resubmit those `custom_id`s in a new batch.

---

## Talk 3 — Multi-pass and the self-review trap

- **Self-review is weak.** When the same session that wrote the code reviews it, it keeps the writer's reasoning state — the blind spots carry over. Empirically catches ~10-30% of bugs the writer missed; an independent instance catches 2-3× more.
- **Independent instance = fresh everything.** New `messages: []`, new system prompt, fresh model call. Give it the *artifact*, not the conversation.
- **Per-record vs integration pass.**
  - **Per-record** pass does one item at a time. Best accuracy per item, no cross-contamination.
  - **Integration pass** takes all per-record outputs and checks cross-record invariants (duplicate IDs, sum consistency, conflicts).
  - You almost always want both. Per-record catches field-level errors; integration catches structural errors.
- **Stratified sampling for evaluation.** Don't just measure aggregate accuracy — measure **by document type and by field**. Aggregate hides failure modes: 95% accuracy overall could mean 99% on easy types and 60% on one hard type.

---

## Exam-relevance one-liners

- "Retry with exponential backoff" on an absent-info case → **useless, map to null + human review.**
- "Use Message Batches for blocking pre-merge checks" → **24 h window, no SLA — wrong.**
- "Use Message Batches for multi-turn tool-using agent loops" → **single-turn only — wrong.**
- "Have the same session review its own output" → **self-review retains reasoning bias — wrong.**
- "Measure aggregate accuracy" → **hides per-type failures; stratify.**

---

## Optional external viewing

- Search — Anthropic Message Batches API: https://www.youtube.com/results?search_query=anthropic+message+batches+api
- Search — LLM self-consistency / self-review: https://www.youtube.com/results?search_query=claude+self+consistency+multi+pass
- Anthropic docs hub: https://docs.anthropic.com/
