# W11 Reference — Integration Guide (All Domains)

This is **not** a re-teach of W01–W10. It's a map: how the concepts from each week stack together in the **four hands-on exam exercises**. Every exam scenario is a composition of 3–5 task statements you've already studied. If you can articulate which week each component comes from, you can take apart any exam question the same way.

Prerequisites: W01–W10. If any week's reference still feels fuzzy, patch it before doing these exercises — the integration doesn't work if the pieces don't click.

---

## 1. The four exam exercises at a glance

| # | Exercise | Primary weeks | Primary domains |
|---|---|---|---|
| 1 | Multi-Tool Agent with Escalation | W01, W02, W03, W04 | 1.1–1.7, 2.1–2.5 |
| 2 | Claude Code Team Workflow | W04, W05, W06 | 2.4, 3.1–3.6 |
| 3 | Structured Extraction Pipeline | W07, W08 | 4.1–4.6 |
| 4 | Multi-Agent Research Pipeline | W02, W09, W10 | 1.2–1.3, 5.1–5.6 |

Each exercise is designed so that **getting one piece wrong breaks the whole thing**. That's the point — the exam distractors are almost always one correct piece surrounded by one subtly wrong piece.

---

## 2. Exercise 1 — Multi-Tool Agent with Escalation Logic

### Weeks that compose it

- **W01 (Agentic Loops):** the outer loop branching on `stop_reason`. `end_turn` → return. `tool_use` → bundle all `tool_result`s into ONE user message. `max_tokens` → raise, don't silently terminate.
- **W04 (Tool Design & MCP):** 3–4 tools with *rich* descriptions (input format, when-to-use, return shape). Two near-similar tools (`get_order` vs `get_order_details`, or `cancel_order` vs `refund_order`) to test selection on description quality.
- **W03 (Hooks, Workflows, Sessions):** a `PreToolUse` hook that blocks any `issue_refund` call above `$500` and redirects to `escalate_to_human`. **Deterministic** enforcement — not a line in the system prompt asking the model to "please escalate large refunds."
- **W02 (Multi-Agent Orchestration):** optional adaptive decomposition — a multi-concern message ("refund + address change + loyalty question") is the canonical case. Even without literal subagents, the coordinator-style decomposition-then-synthesis pattern shows up: the model must decompose the three concerns, handle each, then emit ONE unified reply.

### Exam task statements it tests

| Task statement | How the exercise tests it |
|---|---|
| 1.1 — agentic loop lifecycle | The `stop_reason` dispatch in the main loop |
| 1.4 — hooks as deterministic enforcement | The `$500` `PreToolUse` gate |
| 1.5 — prompt-based vs programmatic enforcement | Explicitly NOT using the system prompt to enforce the $500 rule |
| 2.1 — tool descriptions as selection signal | The two near-similar tools; the correct one is chosen only if descriptions disambiguate |
| 2.2 — structured error responses | Tool failures return `{"isError": true, "errorCategory": ..., "isRetryable": ...}` |
| 1.7 — adaptive task decomposition | The multi-concern message |

### Where it breaks

If you put "don't issue refunds over $500" in the **system prompt** instead of a hook, the agent will eventually skip the rule on a well-crafted customer message. The hook makes it impossible. That gap — prompt says vs hook enforces — is the recurring theme of the exercise.

---

## 3. Exercise 2 — Claude Code Team Workflow Configuration

### Weeks that compose it

- **W05 (Claude Code Configuration):** CLAUDE.md hierarchy (user → project → subdirectory). Path-scoped rules in `.claude/rules/*.md` with `paths:` frontmatter. Project slash commands in `.claude/commands/`. Skills in `.claude/skills/` with `context: fork` and `allowed-tools` frontmatter.
- **W04 (Tool Design & MCP):** `.mcp.json` (project, checked into git) vs `~/.claude.json` (user, private). Both active in the same session — the model sees the union of both tool sets.
- **W06 (Plan Mode, Iteration, CI/CD):** plan mode vs direct execution. When the task is "edit one file to fix a typo," plan mode is overhead. When the task is "migrate 45 files to the new API," plan mode is required. When the task is "add a user-facing feature," plan mode is valuable. The exercise makes you articulate the tradeoff explicitly.

### Exam task statements it tests

| Task statement | How the exercise tests it |
|---|---|
| 3.1 — CLAUDE.md hierarchy & merge semantics | User/project/subdir files with overlapping rules; verify precedence |
| 3.2 — path-scoped rules | Two rules with different `paths:` globs — one for `**/*.test.*`, one for `**/migrations/*.sql` |
| 3.3 — slash commands vs skills | One of each, with the right choice for each use case |
| 3.3 — skill frontmatter | `context: fork` and `allowed-tools` on the skill |
| 2.4 — project vs user MCP | `.mcp.json` (team, committed) vs `~/.claude.json` (personal, not committed) |
| 3.4 — plan mode decision | Same task run three ways; articulate where plan mode pays off |

### Where it breaks

- Rule with no `paths:` frontmatter → loads for every file → bloats context → attention degrades on unrelated work.
- Skill without `context: fork` → skill's tool calls pollute main session context.
- Putting a personal MCP server in `.mcp.json` → committed to the team repo → leaks credentials or adds noise for teammates.

---

## 4. Exercise 3 — Structured Extraction Pipeline

### Weeks that compose it

- **W07 (Prompt Engineering & Structured Output):** `tool_use` + JSON Schema for schema-guaranteed output. Required vs optional vs nullable fields. `enum` with `"other"` + `detail` string for extensibility. `tool_choice: {"type": "any"}` to force the model through the extraction tool. Few-shot examples for ambiguous fields.
- **W08 (Validation, Batch, Multi-Pass):** validation-retry loop — Pydantic fails → resend the document + failed output + specific error back to the model. Message Batches API with `custom_id` for correlation. Field-level confidence → low-confidence rows get routed to a human-review queue (not retried forever).

### Exam task statements it tests

| Task statement | How the exercise tests it |
|---|---|
| 4.1 — explicit categorical criteria | Enum values + "other + detail" instead of free-text |
| 4.3 — JSON schemas for structure | The extraction tool definition |
| 4.4 — tool_choice "any" for forced extraction | Prevents the model from "end_turn"ing without calling the tool |
| 4.5 — nullable fields prevent hallucination | Absent field → `null`, not a guessed value |
| 4.6 — validation-retry with specific errors | Pydantic → error string → resend |
| 4.6 — Batches API, custom_id, partial-batch re-submit | 10 docs, 2 fail, resubmit failures |
| 5.6 — field-level confidence + human review | Low-confidence fields routed to queue |

### Where it breaks

- Using free-text for the category field instead of `enum` + `"other"` → model invents new categories on every run → downstream schema breaks.
- Retrying forever on documents where the field genuinely isn't in the source → burn tokens, never succeed.
- Aggregating confidence across all fields into a single document-level score → can't route at field granularity.

---

## 5. Exercise 4 — Multi-Agent Research Pipeline

### Weeks that compose it

- **W02 (Multi-Agent Orchestration):** coordinator + 2 subagents. Coordinator's `allowedTools` must include `"Task"`. Subagents have their own isolated contexts and scoped tools. Parallel `Task` calls in one coordinator turn for independent subtasks.
- **W09 (Context Management):** subagents return structured claim objects — `{claim, evidence, source_url, publication_date}`. Coordinator never sees raw subagent traces, only synthesized structured returns. Error propagation: a subagent timeout returns a structured error object, not silent failure. Coordinator annotates "coverage gap" in the final report instead of pretending the gap doesn't exist.
- **W10 (Advanced Context & Provenance):** claim→source mapping preserved through synthesis. Publication dates preserved so old-vs-new doesn't read as contradiction. Two sources with conflicting stats → synthesis keeps **both** with attribution, not a coin-flip pick.

### Exam task statements it tests

| Task statement | How the exercise tests it |
|---|---|
| 1.2 — coordinator/subagent pattern | The hub-and-spoke skeleton |
| 1.3 — `allowedTools` must include `Task` | Coordinator can't delegate otherwise |
| 1.3 — parallel subagent dispatch | Two `Task` calls in one coordinator turn |
| 5.4 — error propagation with structured context | Subagent timeout → `{status: "timeout", attempted_query: ..., partial_results: [...]}` |
| 5.5 — coverage gaps annotated, not silenced | Final report says "X was not covered because subagent Y timed out" |
| 5.6 — provenance preserved through synthesis | Every claim cited to a source and date |
| 5.6 — conflicts preserved, not resolved arbitrarily | "Source A says 40%, Source B says 55%" — both kept |

### Where it breaks

- Subagent timeout silently returns `""` → coordinator synthesizes as if everything was fine → final report has fabricated claims or coverage gaps with no flag.
- Subagents share a global variable → context isolation breaks → one subagent's rabbit hole pollutes the other.
- Synthesis collapses conflicting stats into "roughly 50%" → provenance lost, exam distractor in action.

---

## 6. The cross-cutting themes (these are the exam)

Two themes appear in **every** exercise. Internalize them.

### Theme A — "deterministic mechanism beats prompt instruction"

Every exercise has at least one spot where a prompt-only enforcement is the wrong answer:

| Exercise | Wrong (prompt-only) | Right (deterministic) |
|---|---|---|
| 1 | "Don't issue refunds over $500" in system prompt | `PreToolUse` hook that blocks the call |
| 2 | "Only apply this rule to test files" in the rule body | `paths: ["**/*.test.*"]` frontmatter |
| 3 | "Please return null if the field is absent" | Nullable field in JSON Schema + `tool_choice: any` |
| 4 | "Please delegate to subagents" in coordinator prompt | `"Task"` in `allowedTools` |

If an exam answer chooses the prompt and a distractor chooses the mechanism — or vice versa — the mechanism is almost always correct.

### Theme B — "structured > unstructured" at every boundary

Every inter-component boundary — agent↔tool, agent↔user, subagent↔coordinator, model↔validator, batch-job↔correlator — passes **structured** data (JSON with a schema) rather than free text. Every failure mode, every confidence report, every conflict is surfaced as structured data the next stage can programmatically act on.

Free-text at a boundary = parseability is probabilistic = distractor-worthy mistake.

---

## 7. How to use this week

1. Read this guide once end-to-end.
2. For each exercise: open the file, read the top-of-file docstring, then **run it** and read the trace. The inline comments call out which week each piece comes from.
3. After running, read the "variations to try" section at the bottom of each exercise and actually try one. That's where the learning compounds — seeing the same skeleton handle a different input.
4. Read `integration_notes.md` last. It lists the recurring anti-patterns across exercises and maps each exercise to sample exam questions.

When you can look at any of the four exercises and name — in 30 seconds, out loud — which week each component comes from and what the "wrong" version of that component would be, you're ready for the practice exam.
