# W07 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** categorical criteria vs vague wording, few-shot on edge cases, `tool_use` + `input_schema` + forced `tool_choice`, nullable fields, enums with `"other"` + detail.

---

## Talk 1 — "Prompt Engineering with Claude" (interactive tutorial themes)

- **Be explicit and categorical, not vague.**
  - Vague: "be conservative," "only mark important issues," "only when you're confident."
  - Categorical: "mark an issue severity=high if (a) it affects data integrity OR (b) it blocks a user-facing flow OR (c) it is a security vulnerability. Otherwise severity=medium or low."
  - **Why:** "conservative" encodes zero information the model can act on. Checklists do.
- **False-positive-impact framing.** If false positives are expensive (alerting humans on nothing), say so and give criteria that bias against them. If false negatives are expensive (missing a fraud case), say the opposite. The model calibrates when you tell it the asymmetry; otherwise it picks the middle, which is rarely what you want.
- **Show, don't tell.** "Use professional tone" produces average output. Two examples of the exact tone you want produces that tone.

---

## Talk 2 — Few-shot examples: the ones that matter

- **2–4 examples is the sweet spot.** Fewer and the pattern isn't legible; more and you waste tokens without improving accuracy.
- **Pick ambiguous / edge cases, not canonical ones.** An extraction example where the field is obvious teaches the model nothing. An example where the field is *almost* absent (and you show the nullable handling) teaches the decision rule.
- **Show reasoning, not just answers.** Good example: "Input: ... Reasoning: the document mentions '$X' twice; the second mention is in a footnote referring to a prior year — so the current-year amount is the first. Output: {...}" Then the model learns to do the same disambiguation.
- **Placement:**
  - **System prompt** for examples that illustrate the task shape itself.
  - **Message pairs** (user/assistant) for examples showing the exact turn format.
- **Few-shot doesn't fix the wrong model, the wrong schema, or the wrong prompt.** It amplifies whatever else you've got right.

---

## Talk 3 — Structured output via `tool_use` + JSON Schema

- **Mechanism:** define a tool whose `input_schema` is your output schema. Force it with `tool_choice: {"type": "tool", "name": "<tool>"}`. The model's response becomes a `tool_use` block with JSON that matches the schema — no parsing, no regex, no "please output JSON and nothing else" prompt magic.
- **Schemas fix syntax, not semantics.** The `amount` field will be a number, but a schema cannot prevent the model from putting `0` there when the document actually says `$500`. Accuracy is a prompt-and-example problem.
- **Anti-pattern: asking for JSON in the prompt text** ("respond with only valid JSON, no markdown, no explanation"). Works most of the time; breaks on edge cases (truncation, preamble, markdown fences); costs you debug time. Use `tool_use` + schema instead.

---

## Talk 4 — `tool_choice` modes in practice

- **`"auto"`** — model decides; may answer without any tool. Right when you want normal conversation plus optional tool use.
- **`"any"`** — model must call *some* tool this turn. Right when at least one tool is definitely needed but you don't want to pin which.
- **`{"type": "tool", "name": "extract"}`** — force a specific tool. Right for structured-output extraction; also right when you know exactly which tool should run next.
- **Common bug:** `"auto"` when you needed `"any"`. Model answers in prose and your JSON parser chokes. Fix at the API, not at the parser.

---

## Talk 5 — Nullable, enums, and the "other + detail" escape hatch

- **Nullable is the anti-hallucination lever.** If a field is nullable and absent from the source, the model returns `null`. If it's required, the model invents a value. Every optional field should be explicitly `"type": ["string", "null"]`.
- **Enums prevent drift.** `"status": {"enum": ["open", "closed", "pending"]}` forces the model into the set. But the world changes and you don't want to redeploy for every new case.
- **`"other"` + `other_detail`.** Add `"other"` to the enum and require a free-text `other_detail` when selected. You catch new categories without losing structure.
- **Field-level confidence.** Add a `confidence: "high" | "medium" | "low"` per field. Route low-confidence records to a human-review queue rather than trusting them downstream.

---

## Optional external viewing

- Search — Claude structured output tool use: https://www.youtube.com/results?search_query=claude+structured+output+tool+use
- Search — Anthropic prompt engineering few-shot: https://www.youtube.com/results?search_query=anthropic+prompt+engineering+few+shot
- Anthropic courses repo (prompt engineering interactive tutorial): https://github.com/anthropics/courses
