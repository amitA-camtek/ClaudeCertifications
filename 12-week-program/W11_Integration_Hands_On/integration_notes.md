# W11 Integration Notes — Cross-Cutting Themes & Exam Mapping

Short, direct. Read this after you've run the four exercises. If any of the bullets below surprise you, the fix is probably to re-read the corresponding weekly reference, not to do the exercise again.

---

## 1. Anti-patterns that show up in multiple exercises

The exam keeps recycling the same shapes of wrong answer. Spotting them fast is worth more than anything else. Here's the cross-exercise view.

| Anti-pattern | Shows up in | Correct pattern |
|---|---|---|
| Enforce a business rule via a line in the system prompt | Ex1 ($500 refund rule), Ex2 ("only test files" rule), Ex4 ("please delegate") | Deterministic mechanism: hook, `paths:` frontmatter, `allowedTools` |
| Parse the model's text to decide termination | Ex1, Ex4 (coordinator + subagent loops) | Branch on `stop_reason` only |
| Silent empty result on failure | Ex1 (tool error), Ex3 (extraction fail), Ex4 (subagent timeout) | Structured error `{isError, errorCategory, isRetryable, message}` or `{status: "timeout", attempted_query, partial_results}` |
| Retry forever when source info is absent | Ex1 (policy violation), Ex3 (doc with no amount) | Cap retries, route to human review / escalation |
| Free-text at a structured boundary | Ex3 (free-text category), Ex4 (free-text claim) | JSON Schema with enum + "other" + detail; claim objects with provenance |
| Collapse conflicting data into one answer | Ex4 (22% vs 38%) | Preserve both with source + publication_date |
| One big agent doing everything | Ex4 (if you skip the coordinator) | Hub-and-spoke: coordinator decomposes, subagents in isolated contexts |
| Give every agent every tool | Ex1 (if you don't split near-similar tools), Ex2 (skill without `allowed-tools`), Ex4 (subagents with Task) | Scope tools per role; 4–5 tools per agent; Task only on coordinators |
| Personal config in team repo | Ex2 (`.mcp.json` vs `~/.claude.json`) | User scope (`~/.claude/…`) for personal; project scope (`.claude/…`, `.mcp.json`) for team |
| Self-review in the same session | Ex3 (if you had the extractor verify itself) | Independent instance / multi-pass |
| Same-session generator reviewing own output | Ex2 (CI/CD pattern), Ex3 | Separate session for review (`fork_session` / second instance) |
| Plan mode on a 1-line typo fix; direct execution on a 45-file migration | Ex2 | Plan mode when blast radius is large or design space is open |

Count the rows. Every one of them is a sample-exam distractor you've probably already seen.

---

## 2. The recurring theme — "deterministic mechanism beats prompt instruction"

This is **the** cross-domain exam theme. It appears in every domain and in every exercise:

| Domain | Prompt (probabilistic, wrong) | Mechanism (deterministic, right) |
|---|---|---|
| 1.1 Agentic loops | "stop when you think you're done" | `stop_reason == "end_turn"` |
| 1.3 Multi-agent | "please delegate to subagents" | `"Task"` in `allowedTools` |
| 1.4 Hooks | "don't issue refunds > $500" | `PreToolUse` hook |
| 2.1 Tool design | "use tool X for lookups and tool Y for updates" | Write distinct descriptions so the model selects correctly |
| 2.2 Errors | "if you fail, let the caller know" | Structured error object with category + retryability |
| 3.2 Path rules | "only apply to test files" | `paths: ["**/*.test.*"]` frontmatter |
| 3.3 Skills | "don't edit files from this skill" | `allowed-tools` frontmatter |
| 4.3 Structured output | "return JSON in this shape" | `tool_use` + JSON Schema |
| 4.4 Force extraction | "please always call the tool" | `tool_choice: {"type": "any"}` |
| 4.5 No hallucination | "leave the field blank if you don't know" | Nullable field in schema |
| 5.6 Provenance | "remember to cite your sources" | Pass claim objects with source + date through the synthesis |

The *mechanism* is deterministic — the harness, the API, the schema, the file system, or the runtime enforces it whether the model cooperates or not. The *prompt* is a polite request the model will mostly follow and occasionally not. On the exam, when an answer choice changes the prompt and another answer choice changes the mechanism, **pick the mechanism.**

Corollary: when both answer choices are prompt changes (and none is a mechanism), the exam is testing your prompt-engineering knowledge (W07). When both are mechanism changes, it's testing which mechanism is right (e.g., hook vs schema vs `allowedTools`).

---

## 3. The secondary theme — "structured at every boundary"

Exercise-by-exercise, here's what "structured" means at each boundary:

| Boundary | Structured form |
|---|---|
| Agent → Tool (Ex1, Ex3) | JSON input per `input_schema` |
| Tool → Agent (Ex1) | `{isError, errorCategory, isRetryable, message, ...}` |
| Coordinator → Subagent (Ex4) | Full task description in the `prompt` argument of `spawn_subagent` (explicit, not shared memory) |
| Subagent → Coordinator (Ex4) | JSON `{status, claims: [{claim, evidence, source, publication_date, confidence}]}` or `{status: "timeout", ...}` |
| Model → Validator (Ex3) | Tool call matching the extraction JSON Schema |
| Validator → Model on failure (Ex3) | Text containing the specific error string |
| Config file → Harness (Ex2) | YAML frontmatter (`paths`, `allowed-tools`, `context`) + JSON (`.mcp.json`) |
| Subagent internal trace → Coordinator (Ex4) | ABSENT by design. The isolation boundary is also a structure boundary — the coordinator sees a synthesized return, not the trace. |

Free-text at any of those boundaries = future parsing failure = distractor-worthy wrong answer.

---

## 4. Exercise-to-exam-question mapping

The practice exam sample questions (referenced in `LEARNING_PROGRAM.md`) map onto the four exercises like this. Use this to spot-check weak areas.

### Exercise 1 — Multi-Tool Agent with Escalation

- **Task statement 1.1** — agentic loop `stop_reason` branching. Any question showing a loop with `while "done" not in resp.text` is testing this. The fix is always `stop_reason == "end_turn"`.
- **Task statement 1.4** — hook-vs-prompt for enforcement. Questions describing "an agent sometimes issues refunds above the approval threshold" — the answer is a `PreToolUse` hook.
- **Task statement 1.5** — when to use prompt, when to use tool_choice, when to use hook. Ex1's $500 scenario is the canonical "hook" answer.
- **Task statement 1.7** — adaptive decomposition for multi-concern messages. The 3-concern customer message in Ex1 is a direct mirror of the exam distractor pattern.
- **Task statement 2.1** — tool descriptions as the primary selection signal. Ex1's `update_shipping_address` vs `set_billing_address` is the same shape as the exam's "two similarly named tools, which does the model pick" question.
- **Task statement 2.2** — structured error responses. Ex1's `_err(...)` helper is the canonical shape.

### Exercise 2 — Claude Code Team Workflow

- **Task statement 3.1** — CLAUDE.md hierarchy and merge. Questions asking "user, project, and subdirectory each say something different about X — which wins in folder Y" reduce to "more specific scope wins".
- **Task statement 3.2** — path-scoped rules. Any question asking where a rule that "should only apply to tests" belongs: `.claude/rules/tests.md` with `paths:` frontmatter.
- **Task statement 3.3** — slash commands vs skills. A short, interactive nudge = slash command. A heavy, self-contained workflow with tool restrictions = skill with `context: fork` + `allowed-tools`.
- **Task statement 2.4** — `.mcp.json` (committed, team) vs `~/.claude.json` (personal, not committed). "A developer wants their personal Linear MCP server to be used only on their machine" → user scope.
- **Task statement 3.4** — plan mode decision. Three-mode question in the exam: typo (direct), 45-file migration (plan), open-ended feature (plan). Ex2's table codifies the rule.

### Exercise 3 — Structured Extraction Pipeline

- **Task statement 4.1** — categorical criteria vs vague. Enum + "other" + detail is the correct answer.
- **Task statement 4.3** — `tool_use` + JSON Schema for structured output. Ex3's EXTRACTION_TOOL is the canonical shape.
- **Task statement 4.4** — `tool_choice` options. Ex3 uses forced-specific tool to guarantee extraction; questions asking "the model sometimes ends the turn with a prose apology instead of calling the tool" → force tool_choice.
- **Task statement 4.5** — nullable fields prevent hallucination. The doc-006 assertion in Ex3 (employment_status must be None) is exactly the exam check.
- **Task statement 4.6** — validation-retry with specific error. Questions describing "the model keeps making the same schema mistake after retry" are about passing the specific failure back in.
- **Task statement 5.6** — field-level confidence + stratified human review. LOW_CONFIDENCE_QUEUE in Ex3 is the exam's correct answer — route at field granularity, not at document granularity.
- **Batches trap** — Ex3 uses synchronous calls but the `custom_id` is the same identifier you'd correlate in a real Batches submission. The exam distractor ("use Batches for pre-merge CI checks") is wrong because of the 24-hour SLA — Batches is for latency-tolerant workloads only.

### Exercise 4 — Multi-Agent Research Pipeline

- **Task statement 1.2** — hub-and-spoke. Any "one agent is getting overwhelmed with too many responsibilities" question is a decomposition problem.
- **Task statement 1.3** — coordinator's `allowedTools` must include `"Task"`. The exam distractor is always "add a line to the coordinator's system prompt telling it to delegate."
- **Task statement 1.3** — parallel subagent dispatch. The exercise's latency comparison shows the speedup; the exam question is "when should subagents run in parallel vs sequential" → parallel when independent, sequential when there's a data dependency.
- **Task statement 5.4** — structured error propagation. Ex4's `{status: "timeout", attempted_query, partial_results}` from a timed-out subagent is the canonical shape.
- **Task statement 5.5** — coverage gap annotation. The assertion at the bottom of Ex4 (final report must mention the gap) mirrors the exam's "a subagent fails — what does the coordinator do with the report" question.
- **Task statement 5.6** — conflicting sources with attribution. 22% (2022) vs 38% (2024) preserved with dates is the exam's correct answer; averaging or choosing is the distractor.

---

## 5. The 10-second mental test before picking an answer

For any exam question, check in this order:

1. **Does an answer replace a prompt instruction with a mechanism (hook, `allowedTools`, schema, `paths:`, `tool_choice`)?** → lean toward that answer.
2. **Does an answer convert free-text to structured JSON at a boundary?** → lean toward that answer.
3. **Does an answer preserve provenance / dates / conflicts rather than collapsing?** → lean toward that answer.
4. **Does an answer say "silent" anything (silently drop, silently retry, silently pick)?** → almost always wrong.
5. **Does an answer involve "more prompt" / "longer system prompt" / "remind the model to…"?** → usually wrong, especially when a mechanism exists.
6. **Does an answer parse the model's text to decide control flow?** → wrong. Use `stop_reason`.
7. **Does an answer give an agent every tool / every permission / every rule / unscoped?** → wrong. Scoping is the point.

Seven filters. If after those you still have two candidates, fall back to the specific task statement and match the language of the question to the language of the reference for that week.

---

## 6. What to do next

- Finish running all four exercises end-to-end. Read the trace once — don't skim.
- Try **at least one variation** per exercise. That's where the learning is.
- Take Practice Exam 1 per `week_plan.md`.
- Your two weakest domains (from the practice exam) go in `notes/weak_spots.md` — that feeds directly into W12's targeted review.

When you can look at a multi-part exam question and in your head name (a) which task statement it tests, (b) which exercise from this week it maps to, and (c) which of the seven filters above applies — the exam is approximately already passed.
