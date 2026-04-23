# W10 Study Day — Advanced Context & Provenance (Domain 5.4–5.6)

## The one thing to internalize

**Provenance is per-claim, and it includes a date.** Every factual statement the system produces travels with its own `{claim, evidence, source_url, publication_date, confidence_stratum}` record — unbroken from the subagent that gathered it, through the coordinator's synthesis, into the final output. A bibliography at the bottom of a report is not provenance; it's the absence of provenance.

## The three context-degradation failure modes

Long sessions don't fail at the context-length limit. They fail well before it, in three ways:

- **Attention fade** — key facts buried 30 turns back stop shaping outputs.
- **Retrieval degradation** — the model half-recalls facts, drops a digit, swaps a date.
- **Reasoning drift** — later turns reason from earlier summaries, not from raw evidence. Errors compound.

**A bigger context window does not fix any of these.** The exam trap is always "increase the window" — wrong. The fixes are scratchpad files, `/compact` paired with scratchpad, and subagent delegation for context-heavy subtasks.

## Scratchpad + `/compact`, in one line each

- **Scratchpad file** — durable on-disk state (normalized facts, decisions, partial results). Survives `/compact`, survives crashes, survives context saturation.
- **`/compact`** — lossy compression of history. Keeps the gist, drops the specifics. Pair with scratchpad so the specifics are preserved before you compact.

**"`/compact` replaces case_facts" is the trap answer.** Use both. Compact reclaims budget; scratchpad / case_facts preserves specifics.

## Crash recovery manifest

Per-step dump to durable storage: `session_id`, `step_index`, `messages`-or-summary, `subagent_results`, `pending_subagents`, `scratchpad_hash`, `timestamp`. On restart: load, resume from `step_index + 1`. **Fork instead of resume** when the crash was destructive (W03 rule applied to durability).

## Provenance record shape (memorize)

```python
{
    "claim": "US EV market hit $89B in 2024",
    "evidence": "Table 3, 'Passenger EVs', US revenue column",
    "source_url": "industry-report-2025.pdf",
    "source_type": "industry_report",
    "publication_date": "2025-03-15",
    "author_credibility": "established_firm",
    "confidence_stratum": "high",
}
```

Load-bearing fields: `claim`, `source_url`, `publication_date`. Everything else is rigor multipliers.

## Publication date — why it's non-optional

Without `publication_date`, a 2023 stat vs a 2025 stat reads as a contradiction. It isn't — the world changed. Dates let the synthesis step say *"this is expected drift"* instead of *"these conflict."* Real conflicts (same date, different numbers) and expected drift (different dates) are indistinguishable without the date field. Never drop it to save tokens.

## Conflict annotation, never resolution

Two sources disagree? The synthesis step does NOT pick a winner. It preserves both with attribution, annotates the likely cause, and tags the claim `contested`. The reader judges.

- **Wrong:** silently pick the newer one.
- **Wrong:** silently pick the more authoritative one.
- **Wrong:** average them (invents a number no source stated).
- **Right:** `[CONTESTED] Source A (2025-03): $89B. Source B (2025-01): $72B. Likely cause: A includes LCVs, B excludes.`

## Synthesis output taxonomy

Every claim in the final report is tagged:

- `well-established` — multiple independent sources agree (after date check).
- `contested` — sources disagree at similar dates; both shown, annotated.
- `single-source` — one source only; flag for caution. **Not the same as confirmed.**

## Stratified QA + field-level confidence

"93% accurate overall" hides "45% on `due_date` in `invoice`-type documents." Report a **(document_type × field)** matrix, not one aggregate number. For QA sampling, stratify by `(document_type × field × confidence_bucket)` — never random-sample. Rare document types and rare failure modes are invisible in aggregate and in random samples. That's where the actual pipeline failures live.

## Source characterization

- Primary vs derivative (derivatives add a second error channel).
- Date (already covered).
- Author credibility (`established_firm` / `peer_reviewed` / `regulator` / `self_published` / `unknown` — mark unknown explicitly).

## 3-bullet recap

- **Context degrades in long sessions** through attention fade, retrieval noise, and reasoning drift; fix with scratchpad files + `/compact` paired with scratchpad + subagent delegation for heavy subtasks. Bigger context windows do not fix any of this. Crash recovery = per-step manifest + scratchpad, with fork-not-resume on destructive failures.
- **Provenance is per-claim, not per-report, and always includes `publication_date`.** Every claim travels with `{claim, evidence, source_url, source_type, publication_date, confidence_stratum}` end-to-end. A bibliography at the bottom has destroyed provenance. Publication dates prevent "old vs new" from reading as a contradiction.
- **Conflicts are annotated, not resolved; QA is stratified, not random; accuracy is reported per `(type × field)`, not as one aggregate.** Preserve both conflicting sources with attribution and likely cause. Stratify QA by type × field × confidence bucket to surface rare failure modes. Tag every claim `well-established` / `contested` / `single-source` — single-source is a flag, not a confirmation.
