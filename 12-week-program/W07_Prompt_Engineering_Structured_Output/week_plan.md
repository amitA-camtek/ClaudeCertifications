# W07 — Prompt Engineering & Structured Output

**Domain:** Applied Knowledge · 4.1–4.3
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W06 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §2 — categorical criteria (explicit thresholds, feature checks) vs vague wording (`important`, `confident`); false-positive-impact framing |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3 — few-shot = 2–4 examples on ambiguous edge cases (not canonical ones), show reasoning, placement in system prompt vs message pairs |
| 1:40–2:20 | Build | Read [reference.md](reference.md) §4 — `tool_use` + `input_schema` + forced `tool_choice` for structured output; schemas fix **syntax**, not semantics |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Exercise `tool_choice` modes: `auto` vs `any` vs forced specific tool |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §6–7 — required / optional / nullable (nullable is the anti-hallucination lever); enums with `"other"` + detail field for extensibility |
| 1:00–1:45 | Test | **Practice Test 7** — 10 Q on prompt engineering |
| 1:45–2:20 | Review | Wrong answers → `practice_test/test7_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** JSON-schema tool call in `exercises/`, test-7 review, updated weak spots.
