# W10 Reference — Advanced Context & Provenance (Domain 5.4–5.6)

Complete, self-contained study material for Week 10. Read this end-to-end. Every concept the exam tests for task statements 5.4, 5.5, and 5.6 is included here.

Prerequisites: W01 (agentic loop, `stop_reason`), W02 (subagents, context isolation, `Task`), W08 (validation / multi-pass review), W09 (case facts, trimming, position-aware ordering, escalation triggers). W10 is the "long-horizon + provenance" layer on top of W09's in-session context discipline.

---

## 1. Context degradation in extended sessions

A session that started clean can still go bad without anyone editing a message. The enemy isn't a single bad turn — it's accumulated attention load.

Three failure modes that appear as distractors:

- **Attention fade.** Even at nominal context length, the model's attention on any single earlier token drops as more turns accumulate. Key facts buried 30 turns back get "lost in the middle" (see W09 §1) and stop shaping outputs.
- **Retrieval degradation.** Long-session retrieval gets noisier: the model recalls a near-duplicate of a fact but drops a digit, swaps a date, or conflates two sources. Retrieval is approximate, not exact, and gets worse the further back the source is.
- **Reasoning drift.** On turn 80 the model is partly reasoning from its own turn-40 summary, not from the raw evidence. Errors compound.

**None of these are fixed by a bigger context window.** Attention quality doesn't scale with window size — this is the classic exam trap. The answer is always one of: scratchpad files, periodic `/compact` + re-seeding, or subagent delegation for context-heavy subtasks.

### Mitigation A — Scratchpad files (durable state)

A scratchpad file is a plain file on disk (or equivalent durable store) that the agent writes to as it progresses: normalized facts, decisions made, partial results, todo list. The agent re-reads it at the start of each major step.

Why this works:
- It survives `/compact`. History can compress; the file is untouched.
- It survives crashes / restarts. The file is authoritative state (see §3).
- It survives context saturation. The agent reads exactly what it needs back in, instead of trusting memory.

Anti-pattern: "just trust the model to remember what it decided on turn 12." On a 60-turn session, it won't.

### Mitigation B — `/compact`

`/compact` (Claude Code) replaces old turns with a condensed summary, freeing context budget. Useful, but lossy.

- **What survives:** the gist of what happened, who said what, top-level decisions.
- **What's lost:** specific numbers, exact error strings, file paths the model read, intermediate tool outputs.

Combine `/compact` with a scratchpad. Before compacting, write the specifics you'll need later (case facts, IDs, exact dates, numbers) into the scratchpad. Then `/compact` can discard the turn-by-turn noise without losing the load-bearing details. Cross-reference W09 §2 on "case facts" blocks — same idea, promoted from in-context block to durable file.

**Exam trap:** "`/compact` replaces case_facts." Wrong. `/compact` is a compression pass; it can drop specifics. `case_facts` / scratchpad is the preservation mechanism. You use both.

### Mitigation C — Subagent delegation (context isolation, again)

If one subtask is going to pull in a huge volume of raw evidence (reading 40 files, running 20 web searches), don't let it land in the main coordinator's context. Dispatch a subagent (W02 pattern): the subagent burns its own context on the raw work, returns a compact synthesis, and the coordinator stays clean.

W02 Explore subagent is the reference case. W10 just reinforces: **delegation is a context-management tool, not only a parallelism tool.**

---

## 2. Crash recovery manifests

Long sessions crash. Process dies, machine reboots, API errors pile up, network drops. If recovery means "start the whole 2-hour pipeline over," your system is fragile.

A **crash recovery manifest** is a turn-by-turn (or step-by-step) dump of agent state to durable storage — same idea as a write-ahead log.

### What goes in the manifest

| Field | Purpose |
|---|---|
| `session_id` | So you can resume this specific session, not a different one |
| `step_index` | Last step that completed successfully |
| `messages` (or summary + scratchpad) | Enough history to re-seed the loop |
| `subagent_results` | Completed subagent outputs already collected |
| `pending_subagents` | Dispatched but not-yet-returned subagents, for resume-or-restart decision |
| `scratchpad_hash` | Sanity check that the scratchpad on disk matches the manifest |
| `timestamp` | For debugging and stale-manifest detection |

### How recovery works

1. On start, check for an existing manifest.
2. If present and recent, load it, read scratchpad, and resume from `step_index + 1`.
3. If a `pending_subagent` was mid-flight at crash, decide: re-dispatch, or skip and flag as "coverage gap" in the final report (W09 partial-results pattern).

### Anti-patterns

- **No manifest at all.** Crash = full restart. Fine for 30-second tasks; unacceptable for multi-hour research.
- **Manifest without scratchpad.** The manifest says "step 12 done" but doesn't preserve the *content* of step 12's result. Useless.
- **Writing manifest only at the end.** The point is durability during execution. Write after every step.
- **Resuming a poisoned session (W03).** If the crash was caused by a destructive error, don't resume — **fork** from a clean earlier step.

The pattern mirrors W03's `--resume` vs `fork_session` decision, applied to durability rather than branching.

---

## 3. Provenance: `{claim → source}` must survive synthesis

This is the heart of domain 5.5, and it's where the exam is the most punishing.

### The definition

**Provenance** is the `{claim → source}` mapping attached to every factual claim the system produces. Not just "here's a report and here's a bibliography at the bottom" — per-claim attribution that flows unbroken from the subagent that gathered the evidence through the coordinator's synthesis into the final output.

### The minimal provenance record

Every claim should travel as an object like:

```python
{
    "claim": "US EV market hit $X billion in 2025",
    "evidence": "Table 3, row 'Passenger EVs', column 'US revenue'",
    "source_url": "example-industry-report-2025.pdf",
    "source_type": "industry_report",     # primary | derivative | industry_report | news | academic
    "publication_date": "2025-03-15",     # ISO date — see §4
    "author_credibility": "established_firm",   # when checkable; omit or mark unknown otherwise
    "confidence_stratum": "high",         # per-field / per-type bucket — see §6
}
```

The exam-critical fields are `claim`, `source_url`, and `publication_date`. `evidence` and `confidence_stratum` are the rigor multipliers. `source_type` and `author_credibility` are the source-characterization layer (§5).

### Why the mapping must be explicit per claim

A report that says *"EVs grew, interest rates rose, battery costs fell. Sources: \[A, B, C\]"* is broken. You can't tell which source backed which claim, so you can't:
- Audit any single claim.
- Recover when a source turns out to be wrong.
- Weight claims by source quality.
- Detect that two claims cite sources that actually disagree (§4).

**Exam trap:** "One claim, multiple inferred sources" — wrong. Provenance must be explicit per claim, not inferred from a bibliography. A synthesis step that flattens three subagent JSONs into prose and appends a sources list at the end has silently **destroyed** provenance.

---

## 4. Publication dates and "old vs new" disambiguation

A stat from 2023 and a different stat from 2025 may not contradict each other — the world changed. A synthesis pipeline without dates reads them as a contradiction and picks one arbitrarily (or worse, silently).

### The rule

**Every claim carries its `publication_date`. Every conflict detection step reads the date before calling it a conflict.**

### Example

- Source A (published 2023-04): "US EV market: $51B."
- Source B (published 2025-02): "US EV market: $89B."

Naive diff: *"Sources disagree on US EV market size: $51B vs $89B."* That's wrong. Nothing disagrees — these are two different years. The correct annotation is:

> Source A (2023): $51B. Source B (2025): $89B. The difference likely reflects market growth between 2023 and 2025, not a factual disagreement.

### What you lose without publication dates

1. **Real contradictions become indistinguishable from stale-vs-fresh.** You can no longer tell "both sources covering 2025 disagree" (a genuine contested claim) from "one source is from 2019, one is from 2025" (expected drift).
2. **Freshness weighting is impossible.** You can't prefer newer data when appropriate, because you don't know which is newer.
3. **Auditing fails.** A year later, you can't reconstruct whether the report cited a 2023 estimate or a 2025 one.

**Anti-pattern:** "Drop publication dates during synthesis to save tokens." Never do this. Dates are the cheapest high-value field on the record.

---

## 5. Conflict annotation, not conflict resolution

When two sources disagree on the same claim at the same time:

- **Wrong:** silently pick the more recent one. Hides the conflict from the reader.
- **Wrong:** silently pick the higher-authority one. Same problem; also imposes a judgment the reader didn't get to make.
- **Wrong:** drop one. Loses information.
- **Wrong:** average them. Invents a third number that no source actually stated.
- **Right:** preserve BOTH with attribution. Annotate the disagreement. Identify the likely cause if you can. Let the reader judge.

### Annotation template

> **\[CONTESTED\]** Source A (*Industry Report, 2025-03*): $89B. Source B (*Regulator Filing, 2025-01*): $72B. Both cover calendar 2024 US passenger EV revenue. Likely cause: Source A includes light commercial vehicles; Source B excludes them. Neither is obviously wrong.

This is the format the exam expects. The synthesis step's job is **not** to pick a winner. It's to surface the conflict so the human reader can.

### Synthesis output taxonomy

Every claim in the final report should be tagged:

| Tag | Meaning | Reader signal |
|---|---|---|
| `well-established` | Multiple independent sources agree (after date check) | Trust |
| `contested` | Sources disagree at similar dates; both shown with attribution and likely-cause annotation | Read both, decide |
| `single-source` | Only one source found | Flag for caution — no corroboration |

**Exam-critical:** `single-source` is not the same as `well-established`. One source isn't confirmation, it's an unchecked claim. Mark it.

---

## 6. Stratified sampling and field-level confidence

Part of domain 5.6. Applies when a pipeline produces structured outputs at scale (extractions, classifications, summaries) and humans QA a sample.

### The aggregate-accuracy trap

"Our extraction pipeline is 93% accurate." Sounds fine. But that number can hide:

- 99% accurate on `vendor_name` (easy, always printed at top).
- 95% accurate on `total_amount` (usually easy).
- 45% accurate on `due_date` in `invoice`-type documents (hard — the due date wanders by format).
- 88% accurate on `PO_number` in `receipt`-type documents.

In aggregate: 93%. In practice: `due_date` on invoices is failing almost half the time, and your downstream AP process depends on it. **Aggregate accuracy actively misleads.**

### Rule 1 — Report accuracy BY document type AND BY field

Not just a single percentage. A matrix:

|              | `vendor_name` | `total_amount` | `due_date` | `PO_number` |
|--------------|---------------|----------------|------------|-------------|
| `invoice`    | 99%           | 95%            | **45%**    | 88%         |
| `receipt`    | 98%           | 93%            | n/a        | 82%         |
| `po`         | 97%           | n/a            | n/a        | 96%         |

The `45%` jumps out. Nothing in the aggregate told you about it.

### Rule 2 — Stratify the QA sample

Random sampling at 5% on a 10,000-doc batch gives you ~500 samples. If invoices are 20% of the corpus and `due_date` failures are concentrated there, your random sample has ~100 invoices × maybe 40 failures. Detectable, but you're blind to rare document types.

**Stratified sampling** instead: fixed sample per (document_type × field × confidence_bucket). This guarantees coverage of rare types and rare confidence buckets where most of the interesting failure modes hide.

### Rule 3 — Sample by confidence bucket too

Claims the model reports as low-confidence need more QA, not less. Claims it reports as high-confidence also need some QA — those are where miscalibration damage is worst (the model is sure and wrong). Stratify across buckets so you see both.

### Anti-patterns

- **"Random-sample 5% for QA."** Rare modes hide in aggregate stats. Stratify.
- **"Report one accuracy number."** Aggregates hide per-field collapses. Report the matrix.
- **"QA only low-confidence outputs."** Misses high-confidence miscalibrations.
- **"Self-reported confidence replaces QA."** Self-reports are miscalibrated (see LEARNING\_PROGRAM anti-pattern table). QA is orthogonal to, not replaced by, model confidence.

---

## 7. Source characterization

When you have a choice of sources, rank them. When you have only one, mark it.

| Dimension | Values | Why it matters |
|---|---|---|
| **Primary vs derivative** | `primary` (original data / regulator filing / peer-reviewed study) vs `derivative` (news article summarizing the primary, blog post citing the news) | Derivatives introduce a second error channel. A claim with only derivative sources is weaker than one with a primary. |
| **Date** | ISO date | See §4 |
| **Author credibility** | `established_firm` / `peer_reviewed` / `regulator` / `self_published` / `unknown` | Cheap signal. When unknown, mark it so a reader doesn't assume it's checked. |

These aren't about "which source wins." They're about giving the synthesis step (and the reader) enough metadata to judge.

---

## 8. Synthesis output format (the pattern to memorize)

A provenance-preserving final report looks like this:

```
# Executive summary
- Top finding 1 (well-established)
- Top finding 2 (contested — see below)
...

# Findings

## Finding 1: US EV market grew sharply 2023→2025
Status: well-established
Supporting sources:
  - Source A (industry_report, 2025-03): $51B (2023) → $89B (2025). [evidence: Table 3]
  - Source B (regulator_filing, 2025-02): growth of ~70% cited. [evidence: §4.2]

## Finding 2: 2024 US passenger EV revenue
Status: CONTESTED
  - Source A (industry_report, 2025-03): $89B. [evidence: Table 3]
  - Source B (regulator_filing, 2025-01): $72B. [evidence: Filing §2]
  Likely cause: definitional — A includes light commercial vehicles, B does not.

## Finding 3: Battery pack cost in 2025
Status: single-source (flag for caution)
  - Source C (industry_report, 2025-04): $118/kWh. [evidence: Figure 7]
```

Every claim has its source on the same line or block. Every claim has a status tag. Every conflict is annotated. No bibliography-at-the-bottom flattening.

---

## 8b. Content-type-aware rendering — don't flatten everything to prose

The synthesis step has a second job beyond provenance: **match the presentation format to the content type**. Exam-critical point — uniform-format synthesis (everything converted to prose, or everything converted to bullet lists) is *wrong*.

| Content type | Right rendering | Why |
|---|---|---|
| **Quantitative / financial / comparative data** | Table (columns per source, rows per metric, dates in a column) | Enables side-by-side comparison. Prose flattens the structure that makes numbers meaningful. |
| **News / narrative / events** | Prose with inline citations | Stories have temporal flow and causal chains that tables destroy. Inline citation keeps attribution close to the claim. |
| **Technical findings / specs / configurations** | Structured list (bulleted or nested), each item tagged | Discrete items with clear boundaries; lists make individual facts greppable and auditable. |
| **Process / workflow** | Numbered steps | Order matters; numbering makes the sequence unambiguous. |
| **Mixed (most real reports)** | Sectioned, with each section matching its content type | The report is a composition of different content types; each section picks its own rendering. |

### Why this beats uniform format

A synthesis that renders everything as paragraphs hides numeric comparisons inside prose, drowns technical details in narrative, and makes auditability harder for reviewers. A synthesis that renders everything as bullets strips away the narrative that actually explains *why* things happened. Content-type → rendering is not a style preference; it's a reliability concern that directly affects how readers use the output.

### Exam distractor pattern

"For consistency, render all findings as prose with a bibliography at the end." — **wrong** on two counts. Uniform prose format destroys structural signal from quantitative / technical content, and bibliography-at-the-end defeats per-claim provenance (see §8). Match rendering to content; keep provenance per-claim.

---

## 9. Anti-patterns (exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| Silently pick the more recent source on conflict | Hides the conflict from the reader; removes their ability to judge | Preserve BOTH, annotate, flag as `contested` |
| Drop publication dates during synthesis | Real contradictions become indistinguishable from stale-vs-fresh | Dates are mandatory on every claim; read them before declaring a conflict |
| Aggregate-only accuracy reporting ("93% overall") | Hides per-field collapses like `due_date: 45%` | Report by `(document_type × field)` matrix |
| Random sampling for QA | Misses rare document types and rare failure modes | Stratified sampling: fixed quota per (type × field × confidence bucket) |
| Rely on model memory across a long session | Attention degrades, retrieval gets noisy, reasoning drifts off stale summaries | Scratchpad files for durable state; `/compact` only with scratchpad support |
| "`/compact` replaces case_facts" | `/compact` is lossy compression — it drops specifics | Use both. Scratchpad/case_facts preserves; `/compact` reclaims budget |
| One claim, multiple inferred sources ("see bibliography") | Can't audit, can't weight, can't detect conflicts | Explicit per-claim `source_url` on every claim record |
| Average conflicting numbers into one | Invents a value no source ever stated | Show both with attribution |
| Self-reported confidence replaces stratified QA | LLM self-reports are miscalibrated, especially on hard cases | QA with stratified sampling; use self-report as one stratification axis, not a substitute |
| Increase the context window to fix long-session drift | Attention doesn't scale with window size | Scratchpad + `/compact` + subagent delegation |
| No crash recovery manifest on a multi-hour pipeline | Crash = full restart, all work lost | Per-step manifest + scratchpad; resume by `step_index + 1` |
| Resume a crashed destructive session | Poisoned history mis-steers next turn (W03) | Fork from a clean earlier step, not resume |
| Flatten all findings to prose for "consistency" | Hides numeric comparisons, destroys technical structure, breaks per-claim provenance | Match rendering to content type: tables for quantitative data, prose for narrative, lists for specs |

Six to eight exam questions in the domain-5 block test exactly this table.

---

## 10. What the exam will probe

- A scenario describes a long research session producing degraded answers; pick the mitigation (scratchpad + subagent delegation, not "bigger context window").
- Two sources disagree on a number; pick the right synthesis action (annotate both with attribution and date; never silently pick one).
- A pipeline reports "93% accuracy overall"; pick what's wrong (aggregate hides per-field failures; require type × field breakdown).
- A QA plan using random 5% sampling; pick the correction (stratified sampling by type / field / confidence bucket).
- A synthesis step that concatenates subagent outputs and appends a bibliography; pick what's broken (provenance destroyed — claim-to-source mapping is gone).
- A crashed multi-hour pipeline with no recovery path; pick what was missing (per-step manifest + scratchpad; also: fork vs resume).
- "`/compact` will handle all our context problems" scenario; pick the correction (`/compact` is lossy — pair with scratchpad / case_facts).

---

## 11. Fast recap

- **Long-session context degrades** (attention, retrieval, reasoning drift). Fix with scratchpad files, `/compact` + re-seeding, and subagent delegation. Not bigger windows.
- **Crash recovery = per-step manifest + scratchpad.** Resume by `step_index + 1`. Fork, don't resume, when the crash was destructive.
- **Provenance is per-claim, not per-report.** Every claim travels with `{claim, evidence, source_url, source_type, publication_date, confidence_stratum}`. Bibliography-at-the-bottom is broken.
- **Publication dates are mandatory.** Without them, real contradictions can't be distinguished from stale-vs-fresh data.
- **Conflict annotation, never silent resolution.** Preserve both sources; annotate the disagreement and likely cause; tag the claim `contested`.
- **Synthesis tags:** `well-established` / `contested` / `single-source`. Single-source ≠ confirmed.
- **Stratified sampling and a (type × field) accuracy matrix** beat random sampling and aggregate accuracy every time. Rare modes hide in the aggregate.
- **Source characterization** (primary vs derivative, date, author credibility) is the metadata that lets synthesis and readers judge weight.

When you can explain each of those eight bullets out loud in ~20 seconds each, you're ready for the W10 test.
