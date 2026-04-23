# Walkthrough — Real-world research synthesis with provenance

Read this after `reference.md` and after looking at `real_world_research_synthesis.py`. This walkthrough maps every piece of that pipeline to the exam concept it exercises, and lists variations to try that make the anti-patterns visible.

---

## The scenario

A strategy lead asks: *"How big was the US passenger EV market in 2024, how fast is it growing, and how reliable are these numbers?"*

The coordinator has access to three subagent types:
- `industry_analyst` — returns claims from a 2025 industry research report
- `regulator_filing` — returns claims from an early-2025 regulator filing
- `academic_paper`   — returns claims from a peer-reviewed 2025 paper

Each subagent returns a list of `Claim` objects, not prose. Every `Claim` carries its own `source_url`, `source_type`, `publication_date`, `author_credibility`, and `confidence_stratum`. **Provenance is born structured and stays structured.**

---

## Expected pipeline trace

### Step 0 — resume check
`read_scratchpad()` looks for `scratchpad.json`. If missing, start fresh. If present and its `scratchpad_hash` matches the content, resume from `state["step_index"] + 1`.

If the scratchpad belongs to a different `session_id`, the pipeline refuses to resume and starts clean. This prevents accidentally merging two unrelated runs' state — the same instinct as W03's *fork, don't resume after a crash*.

### Steps 1–3 — subagents dispatch, scratchpad writes after each
Each subagent returns a `List[Claim]`. After **every** subagent completes:

1. The pipeline stores its claims into `state["completed_subagents"][name]`.
2. Removes that name from `state["pending_subagents"]`.
3. Calls `write_scratchpad(state)`.

`write_scratchpad` writes to `scratchpad.json.tmp` and then `os.replace`s it onto `scratchpad.json`. An interrupted write cannot leave a corrupt file behind. This is the same durability pattern a real crash-recovery manifest uses.

If the process is killed between steps 2 and 3, the next run reads the scratchpad, sees `industry_analyst` and `regulator_filing` already completed, `academic_paper` still pending — and resumes only the remaining work. No lost progress, no re-running completed subagents.

### Step 4 — synthesis
All collected `Claim` objects are grouped by `(topic, field)`. For each group:

1. Count distinct `source_url`s.
2. Count distinct `value`s.
3. Check `publication_date` spread.
4. Decide status:
   - 1 source → `single-source`
   - multiple sources, same value → `well-established`
   - multiple sources, different values, dates spanning >18 months → `well-established` with a temporal-drift annotation
   - multiple sources, different values, similar dates → **`contested`** — preserve all, annotate likely cause

### Step 5 — stratified confidence matrix
`score_claims` compares each numeric claim against a ground-truth accepted range and counts pass/total per `(source_type × field)`. The renderer prints the full matrix with no aggregate number. The absence of an aggregate is deliberate.

---

## Map from pipeline moment → exam concept

| Pipeline moment | Concept exercised |
|---|---|
| Each subagent returns structured `Claim` objects, not prose | **Provenance must be born structured.** Prose kills the `{claim → source}` mapping. |
| Every `Claim` carries `publication_date` | **Publication dates on every claim**, so old-vs-new can be distinguished from real conflict. |
| Every `Claim` carries `source_type` | Source characterization (primary / peer-reviewed / regulator / industry / derivative). |
| `scratchpad.json` written after every step with `write` + `os.replace` | **Crash-recovery manifest pattern** — durable, atomic, resumable. |
| `scratchpad_hash` integrity check on read | Detect a partial/tampered scratchpad; refuse to resume if corrupt (mirrors W03 *don't resume a poisoned session*). |
| `session_id` mismatch → start fresh | Prevents cross-contamination from an unrelated prior run. |
| Synthesis groups by `(topic, field)` not just `topic` | **Field-level** comparison — `size` and `yoy_growth` are different comparison buckets, never collapsed. |
| Synthesis checks `publication_date` spread before declaring a conflict | Distinguishes **temporal drift** from a **real disagreement at the same time**. |
| Synthesis preserves BOTH conflicting claims in the output | **Conflict annotation, not resolution.** Reader judges. |
| Synthesis emits a `likely cause` for contested claims | Helps the reader understand that (e.g.) the disagreement is definitional (LCVs included or not), not factual. |
| `render_report` puts source + date + evidence on the SAME line as the claim | Provenance is not a bibliography at the bottom — it's attached to each sentence. |
| `score_claims` reports by `(source_type × field)` with NO aggregate | **Stratified confidence reporting.** Aggregate would hide per-field collapses (the "due\_date 45%" lesson from the reference). |

---

## Why aggregate accuracy misleads

If the pipeline had printed:

> Overall accuracy: 4/6 = 67%

that tells you almost nothing. It hides:

- `regulator_filing` passes `size_usd_billion` (72 is within the accepted range 70–92) → 1/1
- `industry_report` passes `size_usd_billion` (89 in 70–92) → 1/1
- `peer_reviewed` passes `size_usd_billion` (80 in 70–92) → 1/1
- `industry_report` passes `yoy_growth_pct` (75 in 40–80) → 1/1
- `regulator_filing` passes `yoy_growth_pct` (41 in 40–80) → 1/1
- `industry_report` and `peer_reviewed` pass `usd_per_kwh` → 2/2

The matrix makes clear which source_type × field combinations have been corroborated and which haven't. An aggregate collapses that to a single opaque number that reviewers can't act on.

**Exam rule:** when a scenario reports "X% accurate overall," look for the distractor that says "break down by type and by field." That's the correct answer. See the `due_date 45%` example in `reference.md` §6.

---

## Why preserving publication_date matters

Look at `us_ev_market_2024::size_usd_billion` after synthesis. Three sources, three values:

- industry_report, 2025-03-15: $89B
- regulator_filing, 2025-01-20: $72B
- peer_reviewed,    2025-02-05: $80B

All three publication dates are within ~60 days of each other. The synthesis step's date-spread check returns ~54 days → well below the 18-month temporal-drift threshold → this is labeled **`contested`**, not drift.

Now imagine the pipeline dropped `publication_date` to save tokens (the anti-pattern in the reference). The synthesis step has no way to check the spread. It either:

- Fails to detect the date structure entirely and always calls any numeric disagreement "contested" — over-flagging drift as conflict.
- Or worse, silently picks the highest-authority source and hides the disagreement.

Either way, the reader loses the ability to see *why* three numbers coexist. **Keep the dates. They are the cheapest high-value field on the record.**

---

## Why silent conflict resolution is wrong

Three sources disagree on the 2024 market size. A "helpful" synthesis might:

- Pick the regulator filing because "regulator = most authoritative." → Hides the disagreement. Reader doesn't know two other credible sources said something different.
- Average them to $80.3B. → Invents a number no source ever stated. Worst option; looks authoritative while being pure fabrication.
- Pick the most recent. → Same hide-the-disagreement problem, with a newness bias that wasn't asked for.

The correct output — and the one the pipeline actually produces — shows all three with attribution and annotates:

> Sources disagree at similar publication dates. Preserving BOTH with attribution; not picking one. Likely cause: Industry reports often include light commercial vehicles in 'passenger EV'; regulator filings typically exclude them. Definitional, not factual.

The reader now knows:
1. There IS a real disagreement.
2. The numbers are not wrong — they're answering slightly different questions.
3. Which definition they prefer for their own purposes is THEIR choice to make.

**Exam rule:** when a scenario asks how synthesis should handle conflicting sources, the correct answer is always *"preserve both with attribution and annotate."* Any distractor that picks, averages, or drops is wrong.

---

## Variations to try

### 1. Aggregate-only confidence — reveal the hidden failure

Add a line to the end of `score_claims` that also prints one aggregate:

```python
total_pass = sum(f["pass"] for src in matrix.values() for f in src.values())
total_all  = sum(f["total"] for src in matrix.values() for f in src.values())
print(f"Overall: {total_pass}/{total_all}")
```

Then shift the `yoy_growth_pct` accepted range in `GROUND_TRUTH` down (e.g. `(70, 80)`) so the regulator filing's 41% now fails. Watch the aggregate say "5/6 ≈ 83% — looks fine" while the matrix clearly shows `regulator_filing × yoy_growth_pct` at 0/1. This is the exam's **aggregate-hides-per-field** trap made concrete. Aggregate: reassuring. Matrix: alarm.

### 2. Silent conflict resolution — show what gets lost

Replace the `contested` branch in `synthesize` with:

```python
# ANTI-PATTERN: silently pick the regulator (most authoritative)
canonical = next(c for c in claims if c.source_type == "regulator_filing")
status = "well-established"
annotation = "(silent) picked regulator as canonical"
claims = [canonical]
```

Re-run. The final report now says US 2024 EV market was $72B, full stop. The $89B and $80B sources have vanished. Anyone reading the report has no idea two other credible sources disagreed. This is exactly the failure mode the W10 reference warns about — and exactly what the exam's correct answer is designed to avoid.

### 3. Drop publication_date — break conflict detection

Remove `publication_date` from the `Claim` dataclass (or set every claim's date to the same value). Re-run. The `_date_spread_days` check now always returns 0, so the pipeline cannot distinguish "expected drift" from "real conflict." Any numeric disagreement will be tagged `contested` even when it's just a 2023 stat vs a 2025 stat. Over-flagging — exactly the problem the field prevents.

### 4. Disable the scratchpad — demonstrate brittleness

Comment out all `write_scratchpad(state)` calls inside `run_pipeline`. Simulate a crash after the second subagent by raising `SystemExit` before `academic_paper` runs. Re-run — the second time starts from zero. All prior subagent work is lost. This is the "no manifest at all" anti-pattern from reference §2.

### 5. Bibliography-at-the-bottom — destroy provenance

Change `render_report` to drop the `[source_type, ..., src: ...]` suffix from each claim line and instead append a "Sources: [A, B, C]" section at the end. The output reads fluently but the `{claim → source}` mapping is gone: a reader can't tell which source backed `$89B` vs `$72B`. This is the exact failure mode §3 of the reference calls out. Putting sources at the end is the visual shape of destroyed provenance.

---

## Exam-critical takeaways

1. **Every claim carries its own source and publication_date, end to end.** No bibliography-at-the-bottom. No flattening during synthesis.
2. **Check dates before calling something a conflict.** Without dates, "2023 vs 2025" reads as a contradiction. With dates, you can distinguish drift from disagreement.
3. **Conflicts are annotated, not resolved.** Preserve all sources; name the likely cause if identifiable; let the reader judge. Never silently pick, average, or drop.
4. **Status tags:** `well-established` / `contested` / `single-source`. Single-source is a flag, not a confirmation.
5. **Stratified confidence reporting.** `(source_type × field)` matrix. No aggregate. Aggregates hide per-field collapses — that's the whole reason the exam tests this.
6. **Scratchpad + crash recovery manifest.** Write after every step. Integrity-check on read. Fork, don't resume, when the crash was destructive.
7. **Scope each subagent to one task, returning structured claims.** Same W02 isolation rule, now combined with the W10 provenance layer.
