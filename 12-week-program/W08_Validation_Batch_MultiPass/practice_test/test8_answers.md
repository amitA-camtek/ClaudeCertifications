# Practice Test 8 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | C |
| 2 | B |
| 3 | B |
| 4 | B |
| 5 | B |
| 6 | B |
| 7 | B |
| 8 | C |
| 9 | C |
| 10 | B |

## Detailed explanations

### Q1 — Answer: C

**Why C is correct:** The schema passed, so the failure is not structural — it's semantic. §1 explicitly states that `tool_use` with a JSON Schema guarantees only that the output matches the schema, not that the data is correct. Field swaps (buyer/seller) are exactly the semantic class §6 calls out, and the prescribed fix is an independent reviewer instance.

**Why the others are wrong:**
- A. A regex on the buyer field cannot distinguish a valid company name that happens to be the seller — this is semantic, not structural.
- B. Pydantic post-validators still operate on structure/type/format; they can't know the buyer vs. seller identity from the source.
- D. `temperature=0` doesn't eliminate semantic bias; §6 lists "higher/lower temperature" and "bigger model" as wrong answers to this kind of question.

**Reference:** §1, §6 of reference.md

---

### Q2 — Answer: B

**Why B is correct:** §2 defines the correct retry prompt shape: original source + prior failed output + **specific** field-level validator error. Without the specific error, the model "has no gradient" and will often emit the same bad value again.

**Why the others are wrong:**
- A. §2 caps retries at 2–3 attempts; more is listed as an anti-pattern in §8.
- C. Changing model doesn't give the model a signal about what was wrong.
- D. "Think step by step" / vague encouragement is exactly the useless "try again" phrasing §2 rejects.

**Reference:** §2 of reference.md

---

### Q3 — Answer: B

**Why B is correct:** §3 is dedicated to this scenario: when the source truly lacks the field, retries produce hallucinations or identical failures. The fix is upstream — mark the field `Optional`/nullable, detect absent-data records before they enter the retry loop, and route to human review or return `null` with a reason.

**Why the others are wrong:**
- A. §3 and §8 explicitly call out "raise retry budget" as an anti-pattern — more retries = more hallucinations when the data isn't there.
- C. Prompt-based hope is weaker than a schema-level fix; §8 repeats: "deterministic mechanisms beat prompt instructions."
- D. Batches vs. synchronous is orthogonal to the retry/absent-data problem (§1 / §5).

**Reference:** §3, §8 of reference.md

---

### Q4 — Answer: B

**Why B is correct:** §5 lists exactly this scenario ("Nightly re-extraction of 50k invoices with a new schema") as the canonical Batches API use case: latency-tolerant bulk work, 50% cheaper, up to 24h window acceptable.

**Why the others are wrong:**
- A. Nobody is waiting; paying full price for unnecessary latency is the synchronous-misuse anti-pattern in §8.
- C. Batches supports the same request parameters as synchronous, including structured output.
- D. §5 is explicit: "The choice is NOT about quality — both produce the same output."

**Reference:** §5 of reference.md

---

### Q5 — Answer: B

**Why B is correct:** §5 lists "Pre-merge lint-check on every PR" as the canonical wrong use of Batches. The 24h window would block PRs for up to a day; blocking/SLA-in-seconds paths must use synchronous.

**Why the others are wrong:**
- A. Batches supports structured output; that's not the issue.
- C. Batches supports system prompts.
- D. §5 is clear: Batches is 50% cheaper than synchronous. Cost isn't the problem — the 24h latency window is.

**Reference:** §5, §8 of reference.md

---

### Q6 — Answer: B

**Why B is correct:** §5 spells out the `custom_id` rule: it is how you correlate request ↔ response. Without it, results can't be reliably matched to inputs. §8 lists "Skip `custom_id` — I'll correlate by order" as an explicit anti-pattern.

**Why the others are wrong:**
- A. §8 says results do not guarantee input order.
- C. `custom_id` is a Batches-specific correlation mechanism; synchronous requests don't need it because each call returns inline.
- D. The reference describes `custom_id` as the correct mechanism, not as a hard-required field that causes rejection — the real harm is mis-association, not an API error.

**Reference:** §5, §8 of reference.md

---

### Q7 — Answer: B

**Why B is correct:** §6 is dedicated to this exact scenario. Self-review in the same session carries reasoning bias and confirmation framing — the model "agrees with itself." The fix is an independent instance: new `messages[]`, new reviewer-style system prompt, no shared history. Same model is fine; separation is at the session/prompt level.

**Why the others are wrong:**
- A. Longer self-check prompts don't remove reasoning-bias carryover.
- C. Prompt rules are probabilistic; §8 says "keep the independent reviewer as a deterministic guard."
- D. Temperature tricks are listed as wrong answers in §6.

**Reference:** §6 of reference.md

---

### Q8 — Answer: C

**Why C is correct:** §7 distinguishes Pass 1 (per-record local) from Pass 2 (cross-record integration). Inconsistent customer name spellings across records and non-reconciling running balances are invisible at the per-record level — they're exactly the cross-record errors Pass 2 is built to catch.

**Why the others are wrong:**
- A. A regex on the name field can't enforce consistency across records; it only validates each record in isolation.
- B. The extraction per-record is fine; more retries don't fix cross-record inconsistency.
- D. Sync vs. Batches is orthogonal to review coverage (§5 / §7).

**Reference:** §7 of reference.md

---

### Q9 — Answer: C

**Why C is correct:** §5's "SLA calculation" section gives exactly this formula: if SLA is `S` hours and batch processing is at most `B` hours, submit a batch every `S − B` hours (minus a safety margin). Worst-case latency = wait-for-next-batch + batch-processing. The worked example (30h SLA, 24h B, batch every 4h → 28h worst case) matches this option.

**Why the others are wrong:**
- A. §5 explicitly calls this the "exam trap" — naive readers wrongly disqualify Batches.
- B. One batch per day puts worst-case at ~48h (document uploaded just after cutoff) — SLA blown.
- D. Batches requests are single-turn per request; splitting a document across batches doesn't reduce per-document latency and isn't described in §5.

**Reference:** §5 of reference.md

---

### Q10 — Answer: B

**Why B is correct:** §4 describes `detected_pattern` / tracked-dismissal fields exactly: tracking the field, error category, and occurrence count lets the loop terminate early and escalate with useful context instead of burning retries on a doomed case. §4 closes with the recurring theme: deterministic pattern tracking beats "the model will self-correct eventually."

**Why the others are wrong:**
- A. §3 and §8 explicitly list raising the retry budget and "be thorough" prompts as anti-patterns.
- C. Loosening the schema to `Any` eliminates structural validation entirely — that's giving up, not fixing.
- D. Batches vs. synchronous is unrelated to pattern detection; §5 covers latency/cost, not retry semantics.

**Reference:** §4, §8 of reference.md
