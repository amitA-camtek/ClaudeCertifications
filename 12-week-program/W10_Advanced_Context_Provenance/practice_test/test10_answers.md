# Practice Test 10 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | B |
| 4 | C |
| 5 | C |
| 6 | C |
| 7 | B |
| 8 | C |
| 9 | C |
| 10 | B |

## Detailed explanations

### Q1 — Answer: B

**Why B is correct:** Long-session degradation has three modes — attention fade, retrieval degradation, reasoning drift — and none of them are fixed by a bigger context window. Attention quality does not scale with window size; this is the classic exam trap. The fix is scratchpad files, `/compact` + re-seeding, and subagent delegation (§1).

**Why the others are wrong:**
- A. The reference explicitly says "None of these are fixed by a bigger context window" (§1).
- C. Temperature is not the mechanism; the degradation is structural, not stochastic.
- D. `/compact` is part of the recommended mitigation, not the problem.

**Reference:** §1 of reference.md

### Q2 — Answer: B

**Why B is correct:** Provenance is the per-claim `{claim → source}` mapping. Every factual claim must travel as an object like `{claim, evidence, source_url, source_type, publication_date, ...}` flowing unbroken from the gathering subagent through synthesis into the final output (§3).

**Why the others are wrong:**
- A. Prose + bibliography-at-the-bottom destroys per-claim provenance — the exam trap in §3.
- C. Provenance must be explicit per claim, not inferred from a bibliography (§3 exam trap).
- D. Dropping `publication_date` is explicitly called out as an anti-pattern in §4; dates are the cheapest high-value field on the record.

**Reference:** §3, §4 of reference.md

### Q3 — Answer: B

**Why B is correct:** Aggregate accuracy actively misleads. A 93% overall can hide a `due_date` on invoices at 45% while easy fields like `vendor_name` run at 99%. The correct report is a `(document_type × field)` matrix (§6, Rule 1).

**Why the others are wrong:**
- A. The reference does not make a benchmark claim; the problem is the aggregate itself hiding per-field collapses.
- C. Confidence intervals are not the issue; granularity by type and field is.
- D. "One accuracy number" is listed as an anti-pattern (§6 anti-patterns; §9 table).

**Reference:** §6 of reference.md

### Q4 — Answer: C

**Why C is correct:** When two sources disagree on the same claim at similar dates, the synthesis step's job is not to pick a winner. Preserve BOTH with attribution, tag the claim `contested`, and annotate the likely cause (e.g., definitional differences). Let the reader judge (§5).

**Why the others are wrong:**
- A. Silently picking the more recent source hides the conflict (§5 anti-patterns; §9 table).
- B. Averaging invents a third number no source ever stated (§5 anti-patterns).
- D. Silently dropping a source loses information and imposes a judgment the reader didn't get to make (§5).

**Reference:** §5 of reference.md

### Q5 — Answer: C

**Why C is correct:** A manifest without scratchpad is one of the explicit anti-patterns: the manifest says "step 12 done" but doesn't preserve the *content* of step 12's result. Recovery requires manifest + scratchpad together so the resumed loop has real state to work from (§2 anti-patterns).

**Why the others are wrong:**
- A. `step_index` alone is not sufficient — the manifest-without-scratchpad anti-pattern (§2).
- B. Writing only at the end defeats durability during execution and is itself an anti-pattern (§2).
- D. Storing verbatim token streams is not required; a summary plus scratchpad is the pattern (§2 manifest fields).

**Reference:** §2 of reference.md

### Q6 — Answer: C

**Why C is correct:** The synthesis taxonomy has three tags: `well-established`, `contested`, `single-source`. A `single-source` claim is not the same as `well-established` — one source is an unchecked claim and must be flagged for caution (§5).

**Why the others are wrong:**
- A. Recency and firm type do not upgrade a single-source claim to well-established; corroboration requires multiple independent sources (§5 taxonomy).
- B. `contested` requires two or more sources that disagree, not one source standing alone (§5).
- D. Omitting loses information; the correct behavior is include and mark (§5).

**Reference:** §5 of reference.md

### Q7 — Answer: B

**Why B is correct:** Two anti-patterns are combined here. "QA only low-confidence outputs" misses high-confidence miscalibrations (where the model is sure and wrong), and "self-reported confidence replaces QA" is explicitly rejected because LLM self-reports are miscalibrated. QA stratifies across confidence buckets, including high-confidence (§6, Rule 3 + anti-patterns).

**Why the others are wrong:**
- A. High-confidence outputs need QA — that is where miscalibration damage is worst (§6 Rule 3).
- C. Random 5% is itself an anti-pattern; rare modes hide in aggregate samples (§6 Rule 2).
- D. Confidence buckets are exactly one of the stratification axes the reference prescribes (§6 Rule 3).

**Reference:** §6 of reference.md

### Q8 — Answer: C

**Why C is correct:** Subagent delegation is a context-management tool, not only a parallelism tool. When a subtask will pull in large volumes of raw evidence, dispatch a subagent: it burns its own context on the raw work and returns a compact synthesis, keeping the coordinator clean (§1 Mitigation C).

**Why the others are wrong:**
- A. Doing the work in the coordinator saturates its context and triggers the degradation modes in §1.
- B. `/compact` before is lossy and does not solve the incoming 40-file load; it only reclaims past budget.
- D. 40 files is exactly the size of subtask subagents are designed for (W02 Explore pattern referenced in §1).

**Reference:** §1 of reference.md

### Q9 — Answer: C

**Why C is correct:** Content-type-aware rendering requires quantitative / comparative data to be rendered as a table (columns per source, rows per metric, dates in a column). Uniform prose for "consistency" is an exam distractor — it flattens the structure that makes numbers meaningful, and a bibliography at the end of the memo defeats per-claim provenance (§8b; §9 table).

**Why the others are wrong:**
- A. Uniform prose is explicitly the distractor pattern — wrong on two counts in §8b.
- B. Uniform bullet lists strips away narrative context for other sections; the rule is match rendering to content type, not pick one format for everything (§8b).
- D. The problem is structural, not cosmetic (§8b).

**Reference:** §8b, §9 of reference.md

### Q10 — Answer: B

**Why B is correct:** `/compact` is a lossy compression pass — it preserves the gist but can drop specific numbers, exact error strings, file paths, and intermediate tool outputs. The correct pattern combines both: write load-bearing specifics to a scratchpad / `case_facts` *before* compacting, then let `/compact` reclaim budget without losing specifics (§1 Mitigation B; exam trap).

**Why the others are wrong:**
- A. `/compact` is explicitly described as lossy, not lossless (§1 Mitigation B).
- C. The exam trap "`/compact` replaces case_facts" is explicitly called out as wrong in §1 and §9 table.
- D. Not running `/compact` leaves the window to saturate; the correct answer is to pair it with a scratchpad, not abandon it.

**Reference:** §1 of reference.md
