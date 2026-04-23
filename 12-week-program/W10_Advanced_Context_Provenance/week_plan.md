# W10 — Advanced Context & Provenance

**Domain:** Exam Prep · 5.4–5.6
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W09 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1 — long-session degradation (attention fade, retrieval drift, reasoning drift); scratchpad files as durable state (survives `/compact` and crashes) |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §1 (mitigations B & C), §2 — `/compact` as lossy compression (pair with scratchpad), subagent delegation as context-management tool, crash-recovery manifests (step index + scratchpad, resume by `step_index + 1`) |
| 1:40–2:20 | Theory+Sketch | Read [reference.md](reference.md) §6–7 — aggregate-accuracy trap; stratified sampling by (document_type × field × confidence bucket); source characterization (primary vs derivative, dates, credibility) |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Build a claim-source mapping with temporal data |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §3–5, §8, §8b — per-claim provenance (`claim`, `source_url`, `publication_date`), publication dates disambiguate old-vs-new from real conflict, conflict annotation (not resolution), well-established / contested / single-source tags, content-type-aware rendering (tables for quantitative, prose for narrative) |
| 1:00–1:45 | Test | **Practice Test 10** — 10 Q on advanced context |
| 1:45–2:20 | Review | Wrong answers → `practice_test/test10_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** provenance mapping demo in `exercises/`, test-10 review, updated weak spots.
