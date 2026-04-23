# Practice Test 10 — Advanced Context & Provenance

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 5.4–5.6

## Instructions
Solve all 10 questions before opening `test10_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A researcher has been running an agentic session for 80 turns. Outputs are getting vaguer, dates are occasionally off by a digit, and the model keeps reasoning from its own turn-40 summary instead of the raw evidence. The team proposes "upgrade to a larger context window model" as the fix. What is the correct diagnosis?
- A. Context window size is the bottleneck — a larger window will restore fidelity.
- B. Attention quality does not scale with window size; the fix is scratchpad files, `/compact` with re-seeding, and subagent delegation.
- C. The model needs a higher temperature to break out of the summary-of-a-summary loop.
- D. The fix is to disable `/compact` entirely so no information is ever lost.

### Q2. A legal-research agent must produce a memo that cites each factual assertion back to a specific paragraph in a source PDF, with the publication date of the filing. Which synthesis design satisfies W10's provenance rules?
- A. Concatenate subagent outputs into prose and append a bibliography of all PDFs at the end of the memo.
- B. Attach a single `{claim, evidence, source_url, publication_date}` record to every claim, flowing unbroken from the subagent that gathered it into the final report.
- C. Let the coordinator infer which source backs which claim based on topic overlap with the bibliography.
- D. Drop `publication_date` during synthesis to save tokens; the filing year is usually obvious from context.

### Q3. A QA team reports "our extraction pipeline is 93% accurate overall" on a 10,000-document batch of invoices, receipts, and POs. What is the primary problem with this report?
- A. 93% is below industry benchmark and the pipeline should be retrained.
- B. The aggregate hides per-field failures — e.g., `due_date` on invoices might be 45% while `vendor_name` is 99%; report a `(document_type × field)` matrix instead.
- C. The team should report only confidence intervals, not point estimates.
- D. 93% is acceptable; no breakdown is needed as long as the overall number stays above 90%.

### Q4. Two industry reports disagree on 2024 US passenger EV revenue. Source A (Industry Report, 2025-03) says $89B; Source B (Regulator Filing, 2025-01) says $72B. Both cover calendar 2024. What is the correct synthesis behavior?
- A. Silently pick the more recent source (A) since it was published later.
- B. Average the two numbers and report $80.5B as the consensus estimate.
- C. Preserve BOTH with attribution, tag the claim `contested`, and annotate the likely cause (e.g., definitional differences).
- D. Pick the higher-authority source (B, regulator) and drop A entirely.

### Q5. A multi-hour research pipeline crashes at step 47 of 60 after a network failure. The team has a manifest that records `session_id`, `step_index`, and a timestamp for every completed step, but no scratchpad. On restart, the system reads the manifest and resumes from step 48. What is still broken?
- A. Nothing — `step_index` is sufficient to resume correctly.
- B. The manifest should have been written only at the end of the session to avoid I/O overhead.
- C. The manifest tells the system *that* step 12 finished, but not *what* step 12 produced; without a scratchpad preserving content, resumed steps operate on missing context.
- D. The manifest should have stored the full token stream of every message verbatim instead of a summary.

### Q6. An agent finds exactly one source for a claim about 2025 battery pack cost. No corroborating source exists. How should the synthesis tag this claim?
- A. `well-established`, because the single source is recent and from an industry firm.
- B. `contested`, because there is nothing to compare it against.
- C. `single-source` with a flag for caution — one source is not confirmation, just an unchecked claim.
- D. Omit it from the report; one source isn't enough to include.

### Q7. A pipeline lead proposes: "We'll QA only the low-confidence outputs — the high-confidence ones are fine by definition, and self-reported confidence from the model replaces the need for human sampling anyway." Which of the following correctly identifies what is wrong?
- A. Nothing is wrong; high-confidence outputs do not need QA.
- B. Self-reported model confidence is miscalibrated (especially on hard cases and high-confidence wrongs), and QA should stratify across confidence buckets — including high-confidence — not skip them.
- C. The only problem is that the QA sample size is too small; a random 5% across all outputs would fix everything.
- D. Confidence buckets should not be used as a stratification axis at all.

### Q8. A coordinator agent is about to dispatch a subtask that will read 40 files and run 20 web searches. The coordinator's context is already 60% full. What is the W10-recommended pattern?
- A. Let the coordinator do the work directly so the evidence stays in one place.
- B. Run `/compact` first to free budget, then do the work in the coordinator.
- C. Dispatch a subagent; the subagent burns its own context on the raw work and returns a compact synthesis, keeping the coordinator clean — delegation is a context-management tool, not only a parallelism tool.
- D. Skip the task; 40 files is too many for any agent to handle.

### Q9. A report section compares 2024 revenue figures across four vendors drawn from three industry reports with different definitions. The team renders the section as flowing prose paragraphs with a bibliography at the end of the memo "for consistency with the rest of the report." What is wrong, per W10's content-type-aware rendering rule?
- A. Nothing — uniform prose format is always preferred for readability.
- B. Prose should be replaced by a single top-level bullet list applied to every section of the report.
- C. Quantitative comparative data should be rendered as a table (columns per source, rows per metric, dates in a column), and provenance must stay per-claim — the end-of-memo bibliography destroys claim-to-source mapping.
- D. The issue is only font choice; Markdown tables render poorly in some viewers.

### Q10. A team runs a long session and relies entirely on `/compact` to manage context, insisting it "replaces the need for a case_facts block or scratchpad." Twelve turns later, the model has lost specific IDs, exact dates, and the file paths it previously read. What is the correct mental model?
- A. `/compact` is a lossless operation; the missing details must have been a model bug.
- B. `/compact` is a lossy compression pass — it preserves gist, not specifics. Use a scratchpad / `case_facts` to preserve load-bearing specifics *before* compacting; `/compact` reclaims budget, the scratchpad preserves.
- C. `/compact` and `case_facts` are equivalent mechanisms; use whichever is more convenient.
- D. The fix is to never run `/compact` in a long session, even when the window is full.

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
