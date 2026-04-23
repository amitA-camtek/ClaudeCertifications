# Build — Advanced Context & Provenance

**Time:** 40 min · **Goal:** Ship a per-claim provenance object, a stratified-sample QA checker, and a crash-recovery manifest that resumes at `step_index + 1`.

## What you'll have at the end
- `exercises/my_provenance.py` that ingests 5 claims, tags each `well-established` / `contested` / `single-source`, and annotates (not resolves) date-aware conflicts
- A `(document_type x field x confidence)` stratified-sample picker that refuses to report an aggregate-only accuracy number
- A step-indexed manifest written after every step so a crashed run can be resumed at `step_index + 1`

## Prereqs
- Python 3.10+, no API calls, no external deps
- Finished reading [reference.md](../reference.md) §1-§8b
- Target: `exercises/my_provenance.py` (peek at [minimal_provenance_object.py](minimal_provenance_object.py) if stuck)

## Steps

### 1. Define the Claim schema (~6 min)
Pin the minimum viable provenance record. Every subagent in the pipeline must return a list of these objects, never prose.
- [ ] Write a `Claim` dataclass with shape: `{'claim': str, 'source_url': str, 'publication_date': 'YYYY-MM-DD', 'source_type': 'primary|derivative', 'credibility': 'established|contested|single-source', 'evidence': str, 'topic': str}`
- [ ] Add an `.attributed()` method that renders `claim [source_url, publication_date; evidence]` on one line

**Why:** §3 — provenance must travel per-claim; bibliography-at-the-bottom destroys `{claim -> source}`. §7 — `source_type` and credibility are the source-characterization layer.
**Checkpoint:** Instantiate one claim and print `.attributed()`. Source + date appear inline with the claim, not in a separate list.

### 2. Build the stratified-sample picker (~6 min)
Replace "random 5% QA" with a picker that takes a fixed quota per `(document_type x field x confidence_bucket)` cell.
- [ ] Function `pick_sample(claims, quota_per_cell=3)` that groups claims by the 3-tuple key and returns up to `quota_per_cell` per cell
- [ ] Make it raise if the caller asks for a single aggregate accuracy number instead of the `(type x field)` matrix

**Why:** §6 Rule 1-3 — aggregate accuracy hides per-field collapses (e.g. `due_date: 45%` on invoices); low-confidence AND high-confidence buckets both need QA (high-conf miscalibration is the worst failure).
**Checkpoint:** Feed 20 claims across 2 doc types x 2 fields x 3 confidence buckets; every non-empty cell returns at least one sample, rare cells aren't dropped.

### 3. Conflict annotation, not resolution (~8 min)
Group claims by `topic`, read `publication_date` BEFORE declaring a conflict, tag as `well-established` / `contested` / `single-source`.
- [ ] If dates span >12 months and values differ monotonically -> tag `well-established` with a "likely temporal drift" note
- [ ] If dates are within 3 months and values differ -> tag `contested`, preserve BOTH claims with full attribution
- [ ] If only one source (even if multiple claims) -> `single-source`, flag for caution

**Why:** §4 — real contradictions vs stale-vs-fresh are indistinguishable without dates. §5 — synthesis never silently picks a winner, averages, or drops; it surfaces the disagreement for the reader.
**Checkpoint:** Two sources giving $89B (2025-03) vs $72B (2025-01) on 2024 revenue come out `contested` with both values visible.

### 4. Scratchpad + step-index manifest (~8 min)
After each step, write a manifest to `scratchpad/manifest.json` so a crash doesn't lose the work.
- [ ] Manifest fields: `session_id`, `step_index`, `scratchpad_hash`, `timestamp`, `completed_steps: [...]`, `pending_subagents: []`
- [ ] Write scratchpad payload (claim list, partial report) to `scratchpad/state.json` before bumping `step_index`
- [ ] On startup: if manifest exists, load it, verify `scratchpad_hash`, resume at `step_index + 1`

**Why:** §1 Mitigation A — scratchpad survives `/compact` and crashes; "just trust model memory" fails past ~30 turns. §2 — manifest-without-scratchpad is useless (records "step 12 done" but not what step 12 produced).
**Checkpoint:** Kill the process mid-run, restart, confirm it skips completed steps and picks up at the next one. Manifest written AFTER every step, not only at the end.

### 5. Resume-by-`step_index + 1` contract (~4 min)
Make resume explicit, never implicit. Also handle the fork-vs-resume decision.
- [ ] If last step's status is `"destructive_error"` -> refuse to resume; print "fork from step N-1 instead" (W03 pattern)
- [ ] Otherwise resume at `step_index + 1`, re-seed the agent's context from scratchpad (not from raw history)

**Why:** §2 anti-patterns — resuming a poisoned session mis-steers the next turn; fork from clean state instead.
**Checkpoint:** Inject a `destructive_error` into step 3's manifest entry; restart refuses to resume and tells you to fork.

### 6. Content-type-aware rendering (~6 min)
The final report picks a renderer per content type — not uniform prose, not uniform bullets.
- [ ] Quantitative topics (numbers, comparisons) -> table with columns: source / date / value / evidence
- [ ] Narrative topics (events, causal chains) -> prose with inline `[source, date]` citations
- [ ] Spec/config topics -> bulleted list, each item tagged with source

**Why:** §8b — uniform prose hides numeric comparisons and breaks auditability; uniform bullets strip narrative flow. Content-type -> rendering is a reliability concern, not style.
**Checkpoint:** Run against the 5-claim set; the quantitative topic renders as a table, the narrative topic as prose with inline cites, no bibliography at the bottom.

### 7. Wire it up and self-check (~2 min)
- [ ] `if __name__ == "__main__":` block runs all 5 claims through the pipeline and prints the report
- [ ] Pipe output to `out.txt`; grep for "CONTESTED" and "single-source" — both must appear

**Why:** §10 — the exam asks you to spot exactly these tags in a rendered output.

## Verify
Build a 5-claim set with 1 intentional conflict (same topic, same date window, different numbers from two sources). Expected:
- The conflict appears in output tagged `CONTESTED` with BOTH source_urls and dates inline — not silently resolved to one number
- A stale 2023 claim vs a 2025 claim on the same metric does NOT appear as `contested` — the date gap is annotated as expected drift
- `single-source` claims are flagged for caution, not promoted to `well-established`
- Killing the process after step 3 and restarting resumes at step 4; scratchpad hash verifies
- Quantitative findings render as a table, narrative findings as prose with inline citations

**Common mistakes:**
- Reporting "93% accuracy overall" from the QA pass -> §6, demand the `(type x field)` matrix
- Silently picking the newer source on a conflict -> §5, annotate both
- Dropping `publication_date` to save tokens in the synthesis prompt -> §4, dates are the cheapest high-value field
- Manifest written only at end-of-run -> §2, write after every step
- Resuming a crashed destructive session instead of forking -> §2 anti-patterns, W03 reference
- Flattening the final report to uniform prose with a sources list appended -> §8b + §3, double failure

## Stretch — Polish block (30 min on Practice Day)
Build a claim-source mapping with temporal data: extend `my_provenance.py` so it accepts a batch of mixed-date claims and emits a timeline view.
- [ ] Add a `timeline(claims)` function grouping by `topic` then sorting by `publication_date`
- [ ] For each topic, render a 3-column table: `date | value | source` so temporal drift is visually obvious
- [ ] Add a `freshness_weight` helper (not a resolver) that flags which claim is newest but does NOT drop the others
- [ ] Write one paragraph in `notes/polish.md`: why freshness weighting is a reader hint, not a synthesis decision (§5)

## If stuck
Compare with [minimal_provenance_object.py](minimal_provenance_object.py). Read -> close -> rewrite.
