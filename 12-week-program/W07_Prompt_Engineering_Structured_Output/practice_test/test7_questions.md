# Practice Test 7 — Prompt Engineering & Structured Output

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 4.1–4.3

## Instructions
Solve all 10 questions before opening `test7_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1.
Your team's invoice-extraction pipeline keeps producing `due_date` values that are not present in the source invoices — the model fabricates plausible-looking dates. The current schema declares `due_date` as `{"type": "string"}` and marks it required. Which change is the primary anti-hallucination lever?
- A. Lower the temperature to 0 and add "do not hallucinate dates" to the system prompt.
- B. Change `due_date` to `{"type": ["string", "null"]}`, keep it required, and instruct the model to return `null` when the source has no due date.
- C. Remove `due_date` from the required list so the model can omit it.
- D. Ask the model to self-rate its confidence per field and drop fields below 0.8.

### Q2.
You need strict JSON output for a downstream Python consumer that validates with Pydantic. The current prompt says "Reply with a JSON object containing vendor_name, total_usd, due_date — no markdown, no commentary." About 3% of responses have trailing commas, markdown fences, or prose preambles, breaking the parser. What's the correct fix?
- A. Add emphatic warnings like "CRITICAL: output only valid JSON, no markdown, no prose."
- B. Switch to a higher-capability model and retry failures.
- C. Define a tool whose `input_schema` matches the target shape and set `tool_choice` to `{"type": "tool", "name": "<tool>"}`.
- D. Keep the natural-language prompt but post-process the string with a regex that strips markdown fences.

### Q3.
A classification prompt says: "Classify important bugs as high priority; escalate if you're unsure." Results are wildly inconsistent across runs. Which rewrite best addresses the root cause?
- A. "Carefully classify important bugs as high priority; escalate only if you're genuinely unsure."
- B. "Classify as TIER_1 if severity is blocker AND affected_users >= 100; otherwise TIER_2. Escalate if severity cannot be determined from the ticket text."
- C. "Rate each bug's importance 1–10 and classify 8+ as high priority."
- D. "Classify important bugs as high priority and add a one-sentence justification so we can review."

### Q4.
Your extraction pipeline worked until vendors started sending invoices with `"Net 45"` payment terms. Your enum is `["net_30", "net_60", "due_on_receipt"]` and the pipeline now either silently picks `net_30` or fails schema validation. What is the correct design change?
- A. Add `net_45` to the enum and redeploy; repeat for every new term you encounter.
- B. Remove the enum constraint and accept any string for `payment_terms`.
- C. Add `"other"` to the enum plus a `payment_terms_detail` nullable string, and instruct the model to set `payment_terms="other"` with the verbatim phrase in detail when no exact match exists.
- D. Ask the model to rate its confidence in the enum match and fall back to manual review below a threshold.

### Q5.
You have three classification tools — `classify_as_urgent`, `classify_as_normal`, `classify_as_spam` — and every incoming email must be classified by exactly one of them. You currently use `tool_choice: {"type": "auto"}` and the model sometimes just replies in prose. Which `tool_choice` mode is correct here?
- A. `{"type": "auto"}` with a stronger system-prompt instruction to always call a tool.
- B. `{"type": "any"}` so the model must call some tool but can choose which of the three.
- C. `{"type": "tool", "name": "classify_as_normal"}` as a safe default.
- D. `{"type": "none"}` so the model replies in text describing the class.

### Q6.
Which statement about JSON Schema enforcement via `tool_use` is correct?
- A. A JSON Schema guarantees both the shape and the meaning of extracted fields.
- B. A JSON Schema prevents the model from extracting the customer's name into a `vendor_name` field.
- C. A JSON Schema guarantees valid JSON syntax, required fields present, types matching, and enum membership, but does not catch semantic errors like wrong-field-for-the-value.
- D. A JSON Schema only matters when the model is uncertain; confident extractions bypass it.

### Q7.
Your model is inconsistent on ambiguous edge cases: "Net 45", "upon receipt of goods", "2% 10 / Net 30". Easy cases like "Net 30" and "Net 60" work perfectly. A teammate suggests adding six few-shot examples: one for each easy case and one for each hard case. What's the better approach?
- A. Keep their plan — balancing easy and hard shows the model the full pattern.
- B. Drop the easy-case examples; use 2–4 few-shot examples covering only the ambiguous cases, ideally showing reasoning.
- C. Replace the few-shot block with a single canonical example ("Net 30 → net_30") — one clear example is enough.
- D. Add 15 examples covering every term you've ever seen; more data always helps.

### Q8.
A junior engineer writes this system prompt for an extraction task:

> "You must call the `extract_invoice` tool on every request. Do not reply in prose. This is critical."

and leaves `tool_choice` at the default `"auto"`. Occasionally the model still replies in natural language. What's the right diagnosis?
- A. The instruction needs to be more emphatic — add ALL CAPS and repeat it three times.
- B. The model is buggy on this version; switch models.
- C. Prompt instructions are probabilistic; to guarantee the tool call, use `tool_choice: {"type": "tool", "name": "extract_invoice"}` — deterministic mechanism beats prompt instruction.
- D. Move the instruction from the system prompt into the user message, where the model pays more attention.

### Q9.
A teammate proposes this architecture: put the classification criteria, the 2-shot examples, AND the raw document text all together in one user message so the model "sees everything at once." On the exam, which critique is correct?
- A. This is ideal — colocation improves coherence.
- B. Criteria and examples get treated with equal weight to the data and tend to get lost; put criteria and few-shot in the system prompt, and the raw document alone in the user message.
- C. It's fine as long as you separate the three blocks with XML tags.
- D. Only the schema should be in the user message; everything else goes in the system prompt including the document.

### Q10.
You design a schema for a medical-triage escalation tool. False negatives (failing to escalate a real emergency) are catastrophic; false positives (escalating a non-emergency) are cheap. Which criterion design matches the false-positive-impact framing from the reference?
- A. Strict criterion: "Escalate only if the patient explicitly uses the word 'emergency' AND vitals are outside normal range AND a nurse has flagged the case."
- B. Vague criterion: "Escalate if the case seems serious or the patient seems in distress."
- C. Self-rated confidence: "Escalate if your confidence that this is an emergency is >= 0.9."
- D. Permissive categorical criterion: "Escalate if any of {chest pain, difficulty breathing, loss of consciousness, severe bleeding, stroke symptoms} is mentioned OR vitals are outside normal range" — with a human review gate on positives.

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
