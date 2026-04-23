# Practice Test 7 — Answer Key & Explanations

## Quick key
| Q  | Answer |
|----|--------|
| 1  | B |
| 2  | C |
| 3  | B |
| 4  | C |
| 5  | B |
| 6  | C |
| 7  | B |
| 8  | C |
| 9  | B |
| 10 | D |

## Detailed explanations

### Q1 — Answer: B

**Why B is correct:** Nullable fields are the primary anti-hallucination lever in a schema. When `due_date` is required and non-nullable (`"type": "string"`), the model has no legitimate "absent" answer and will fabricate one. Making the type `["string", "null"]` while still required, combined with a "return null when absent" instruction, gives the model a legitimate absent answer so it stops inventing dates (§6).

**Why the others are wrong:**
- A. "Tell the model harder" loses to deterministic mechanism. Temperature and prompt warnings don't remove the fabrication pressure created by a non-nullable required field (§6, §9).
- C. Making the field optional creates inconsistent downstream handling code and still doesn't instruct the model what to do when the field is absent. Required + nullable is the correct pattern (§6).
- D. LLM self-rated confidence is miscalibrated, especially on hard cases. The reference explicitly calls this out as an anti-pattern (§9).

**Reference:** §6 (Schema design — nullable as anti-hallucination lever), §9 (Anti-patterns)

---

### Q2 — Answer: C

**Why C is correct:** The correct way to get structured output from Claude is to define a tool whose `input_schema` matches the desired shape and force the call with `tool_choice: {"type": "tool", "name": ...}`. This guarantees valid JSON, required fields present, type matches, and enum membership — eliminating the syntax class of errors entirely (§4).

**Why the others are wrong:**
- A. "Natural-language JSON + stronger wording" is the exam's canonical anti-pattern. It is probabilistic and still produces trailing commas, markdown fences, and prose preambles (§4, §9).
- B. Swapping models does not fix the fundamental issue that natural-language JSON has no deterministic shape guarantee.
- D. Regex post-processing is a band-aid on the anti-pattern; the deterministic mechanism (tool_use + schema) removes the failure mode at its source (§9).

**Reference:** §4 (Structured output via tool_use + JSON Schema), §9 (Anti-patterns)

---

### Q3 — Answer: B

**Why B is correct:** Vague criteria ("important", "unsure") are miscalibrated — the model has no shared definition and phrasing drift produces inconsistent results. Categorical criteria give a mechanical decision rule: explicit threshold (`affected_users >= 100`), explicit feature (`severity is blocker`), and an explicit escalation trigger (`severity cannot be determined from the ticket text`) (§2).

**Why the others are wrong:**
- A. Adding "carefully" and "genuinely" is just re-wording vague criteria. Same vibes, same inconsistency (§2, §9).
- C. Self-rated importance on a 1–10 scale is miscalibrated; the reference explicitly flags "ask the model to self-rate confidence" as an anti-pattern (§9).
- D. A justification helps reviewers but doesn't fix the underlying vague criterion — the classification itself remains miscalibrated (§2).

**Reference:** §2 (Explicit, categorical criteria), §9 (Anti-patterns)

---

### Q4 — Answer: C

**Why C is correct:** A closed enum without `"other"` is a design smell when the input domain can have novel values. The extensibility pattern is `enum: [..., "other"]` plus a nullable detail field, with a rule: "if no exact match, set `payment_terms="other"` and put the verbatim phrase into `payment_terms_detail`." New terms route cleanly, and the raw signal is preserved for downstream handling (§7).

**Why the others are wrong:**
- A. Whack-a-mole. Every new term requires a schema update and deploy; the pipeline breaks in the meantime. The reference says this is also fine for *known* values but not the primary fix (§7, §11).
- B. Removing the enum loses all enum guarantees (validator coverage, consistent downstream handling). You lose signal for novelty without gaining it.
- D. Self-rated confidence is miscalibrated (§9) and doesn't solve the core schema-brittleness problem.

**Reference:** §7 (Enums with "other" + detail), §9 (Anti-patterns)

---

### Q5 — Answer: B

**Why B is correct:** `{"type": "any"}` forces the model to call *some* tool this turn but lets it choose which — exactly the shape of "multiple classification tools, must pick one." This is the reference's canonical example for `"any"`: `classify_as_urgent`, `classify_as_normal`, `classify_as_spam` (§5).

**Why the others are wrong:**
- A. `auto` + a prompt instruction is probabilistic and loses to `tool_choice`; same pattern as W01 ("add a rule to the prompt" loses to the deterministic mechanism) (§5, §9).
- C. Forcing one specific tool collapses all inputs to that class — you lose classification entirely. Forced specific is for single-schema extraction, not multi-class choice (§5).
- D. `"none"` forbids tool calls and defeats the whole purpose; text-only replies are what you're trying to stop (§5).

**Reference:** §5 (tool_choice — three modes, "any" vs forced specific)

---

### Q6 — Answer: C

**Why C is correct:** The exam-critical distinction: a JSON Schema eliminates SYNTAX errors (valid JSON, required fields, type correctness, enum membership) but does NOT eliminate SEMANTIC errors (wrong value in a field, customer name in vendor_name, subtotal in total_usd, hallucinated content that is type-valid). The reference calls this out as a common distractor (§4).

**Why the others are wrong:**
- A. "Guarantees meaning" is the exact distractor the reference warns about — schema handles shape only (§4).
- B. A schema cannot tell vendor names from customer names; both are strings. Semantic correctness requires downstream validators, a second pass, or human review (§4).
- D. Schema enforcement is unconditional on every tool call; confidence is not a factor and shouldn't be (self-rated confidence is an anti-pattern) (§9).

**Reference:** §4 (What the schema does NOT guarantee), §9 (Anti-patterns), §11 (Exam probes)

---

### Q7 — Answer: B

**Why B is correct:** Few-shot examples are pure budget; spend them on what the model gets wrong. The reference is explicit: 2–4 examples, covering ambiguous / edge cases, showing reasoning. Easy cases are already handled and waste a slot. Balancing easy and hard actually over-weights the happy path (§3).

**Why the others are wrong:**
- A. Balancing easy cases wastes examples on cases the model already gets right, and can over-weight the happy path (§3).
- C. One canonical example is pattern noise, not pattern signal — explicitly called out as an anti-pattern (§9).
- D. 15 examples causes diminishing returns, context bloat, and over-fitting — explicitly an anti-pattern (§9).

**Reference:** §3 (Few-shot prompting rules), §9 (Anti-patterns)

---

### Q8 — Answer: C

**Why C is correct:** Prompt instructions are probabilistic — the model will occasionally skip them no matter how emphatic. To *guarantee* the tool call, use `tool_choice: {"type": "tool", "name": "extract_invoice"}`. This is a direct instance of the recurring theme: deterministic mechanism beats prompt instruction (§5, §9).

**Why the others are wrong:**
- A. Emphasis and repetition are still probabilistic. The reference names this exact anti-pattern: "Add 'you must call the tool' to the system prompt to enforce use → Wrong — probabilistic. Use tool_choice to force (deterministic)." (§9).
- B. It's not a model bug; it's prompt-based enforcement working as designed (probabilistically).
- D. Placement in user vs system message doesn't make the instruction deterministic; tool_choice is the mechanism (§5, §8).

**Reference:** §5 (Anti-pattern: "auto" for mandatory extraction), §9 (Anti-patterns)

---

### Q9 — Answer: B

**Why B is correct:** The reference is explicit on placement: classification criteria go in the system prompt, the schema goes in `input_schema`, and the raw document goes in the user message. Mixing criteria and data in one user message causes the model to treat them with equal weight, and the criteria get lost in the data (§8).

**Why the others are wrong:**
- A. "Colocation improves coherence" is the misconception the reference warns against — criteria get diluted (§8).
- C. XML tags help with structure but don't fix the placement rule: criteria belong in the system prompt regardless of tagging (§8).
- D. Putting the document in the system prompt is wrong; the document (raw input) belongs in the user message (§8).

**Reference:** §8 (System-prompt placement for criteria and few-shot)

---

### Q10 — Answer: D

**Why D is correct:** The false-positive-impact framing from the reference: when false positives are cheap and false negatives are catastrophic (medical escalation is the named example), make the criterion **permissive** and add a human review gate on positives. Option D is a concrete categorical criterion (explicit symptom list + explicit vitals check) that is intentionally permissive and pairs with a human review gate (§2).

**Why the others are wrong:**
- A. Requiring ALL of (word "emergency" AND bad vitals AND nurse flag) is a strict criterion — the wrong direction for catastrophic false negatives. The reference prescribes strict criteria when false positives are expensive, not when false negatives are catastrophic (§2).
- B. Vague criteria ("seems serious", "seems in distress") are miscalibrated and don't give the model a mechanical decision rule (§2, §9).
- C. LLM self-rated confidence is miscalibrated, especially on hard cases — an explicit anti-pattern (§9).

**Reference:** §2 (False-positive-impact framing), §9 (Anti-patterns)
