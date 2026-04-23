# W12 Reference — Final Exam Prep (All Domains)

This week does not introduce new material. It compresses W01–W10 into the smallest footprint you can walk into the exam with, runs drills on the shape of the actual exam, and targets whichever domain is weakest in your W11 `notes/weak_spots.md`.

Read this file end-to-end on Monday morning. Re-read the "Master wrong-answer patterns" table and the "Deterministic mechanism beats prompt instruction" section on exam eve.

---

## 1. How to use this week

Six working blocks, one per day, ~2.5 h each. The point is to reduce surface area, not add to it.

| Day | Block | What you do |
|---|---|---|
| Mon | Domain drills — strongest first | Reread `domain_cheatsheet.md`. Re-do the practice test for each of your 3 strongest domains. Quick confirmation pass. |
| Tue | Scenario simulation | Work through `exercises/scenario_drills.md`. Each of the 6 exam scenarios, 5 reliability risks and their one correct mitigation. Handwritten answers, then check. |
| Wed | Full practice exam | Practice Exam 2, untimed. Record every miss in `notes/weak_spots.md`. |
| Thu | Weakest-domain deep dive | Identify the weakest domain from Wed's exam using the percentages in section 3. Fill in `notes/weakest_domain_plan_template.md` and execute it. |
| Fri | Full practice exam, timed | Practice Exam 3, strict timer. Treat it as dress rehearsal. |
| Sat | Light review | Reread `anti_patterns_master_list.md`, the wrong-answer table in section 4 below, and `exam_day_playbook.md`. No new content. |
| Sun | Exam day | Calm, fed, hydrated. The playbook does the work; you ride it. |

Do not try to cram new topics this week. Anything you don't know by Monday you will not learn well enough to help on Sunday.

---

## 2. Exam format recap

- **60 multiple-choice questions.**
- **5 domains, weighted:** Agentic Architecture & Orchestration 27%, Tool Design & MCP Integration 18%, Claude Code Configuration & Workflows 20%, Prompt Engineering & Structured Output 20%, Context Management & Reliability 15%.
- **6 scenario families** (customer support automation, code generation/review, multi-agent research, developer productivity, CI/CD integration, structured extraction). **4 of the 6 are shown on any given exam.** You cannot predict which four, so you must be fluent in all six.
- **Passing score: 720/1000.** Scaled, not raw. Approximately 70–75% raw accuracy lands you there.
- **Format: scenario-based multiple choice.** Every question frames a real failure mode; the distractors are plausible at a glance.

Expected domain question counts (27/18/20/20/15 of 60): roughly **16 / 11 / 12 / 12 / 9**. If you miss even domain by 30%, you can still pass if the others are solid. If you miss two domains by 30%, you are under the line. Know where your weak domains are.

---

## 3. Five-domain compressed cheat sheet

Task statement numbers refer to the exam guide (1.1–5.6). These are the bullets you must be able to speak out loud in ~20 seconds each.

### Domain 1 — Agentic Architecture & Orchestration (27%, TS 1.1–1.7)

1. **Agentic loop lifecycle (1.1):** loop until `stop_reason == "end_turn"`. Handle `tool_use` by running tools in your code and feeding `tool_result` blocks back in a `user` message keyed by `tool_use_id`. High `safety_fuse`, not a tight iteration cap.
2. **Message-history contract (1.1):** append every turn; never overwrite. Parallel tool calls → one `user` turn containing all the paired `tool_result` blocks. There is no `"tool"` role.
3. **Hub-and-spoke multi-agent (1.2):** coordinator decomposes + synthesizes, subagents run in isolated contexts and return compact summaries. Never shared memory.
4. **`Task` tool + `AgentDefinition` (1.3):** coordinator's `allowedTools` MUST include `"Task"`; subagents usually do not. Each `AgentDefinition` has `description`, `prompt`, `tools` (scoped), optional `model`.
5. **Hooks — PreToolUse vs PostToolUse (1.4, 1.5):** PreToolUse blocks side effects before they happen; PostToolUse shapes what the model sees after. Hooks are the deterministic mechanism — prompt rules are not.
6. **Sessions (1.6):** `--resume` for coherent continuation, `fork_session` for risky exploration or recovery from a poisoned session, `/compact` for staleness, fresh session when history is worthless. **Never resume into a poisoned context.**
7. **Decomposition (1.7):** fixed prompt chain for known steps, adaptive decomposition for open-ended/multi-concern inputs. Parallelize independent subtasks; serialize when B depends on A.

### Domain 2 — Tool Design & MCP Integration (18%, TS 2.1–2.5)

1. **Descriptions are the selector (2.1):** input format, example inputs, positive + negative boundaries, return shape. Rich descriptions are the highest-leverage tokens in the prompt.
2. **Split vs consolidate (2.1):** split mega-tools with `mode` enums into separately-named tools; consolidate genuine duplicates. Negative boundary ("Do NOT use this for X; use Y") disambiguates near-similar tools.
3. **Structured errors (2.2):** `isError`, `errorCategory` (`validation` / `not_found` / `timeout` / `policy` / `internal`), `isRetryable`, user-friendly `message`. Retry branches on `isRetryable`, not on string parsing.
4. **Tool distribution (2.3):** 4–5 tools per agent max. Scope per role; delegate cross-domain work. 18 tools ≫ 5 tools degrades selection measurably.
5. **`.mcp.json` vs `~/.claude.json` (2.4):** project (committed, shared) vs user (personal). Secrets via `${ENV_VAR}` expansion, never literal.
6. **MCP tools vs MCP resources (2.4):** tools = actions with side effects; resources = read-only content catalogs. Don't expose an action as a resource.
7. **Built-in tools (2.5):** Read (known path), Grep (content search), Glob (path pattern), Edit (in-place patch), Write (new file / full rewrite), Bash (everything else). Glob searches paths, not contents.

### Domain 3 — Claude Code Configuration & Workflows (20%, TS 3.1–3.6)

1. **Three scopes (3.1):** user (`~/.claude/…`), project (`<repo>/.claude/…` or `<repo>/CLAUDE.md`), subdirectory (nested `CLAUDE.md`). More-specific wins on conflict; all levels stack.
2. **CLAUDE.md vs rules vs commands vs skills (3.2):** CLAUDE.md = always-on context; `.claude/rules/*.md` with `paths:` frontmatter = passive, path-scoped; `.claude/commands/*.md` = user-invoked saved prompt; `.claude/skills/<n>/SKILL.md` = multi-step capability with `allowed-tools`, optional `context: fork`.
3. **`@import` (3.1):** inlines content at load time. Modularity, not conditional loading. Does not save tokens.
4. **Plan mode vs direct execution (3.4):** plan for ambiguous / multi-file / hard-to-reverse work; direct for small well-specified edits. 45-file migration → plan. 3-line null check → direct.
5. **Iterative refinement (3.5):** concrete feedback (file/function/behavior) or deterministic (TDD red-green-refactor). Vague "make it better" wastes turns. Interview/clarifying-questions pattern for ambiguous specs.
6. **Headless CI (3.6):** `-p` + `--output-format json` + `--json-schema`. Never regex natural language. **Generator and reviewer run in SEPARATE fresh sessions** — no `--resume`, no shared transcript. Self-review retains bias.
7. **Message Batches API (3.6):** 50% cheaper, up to 24 h window, `custom_id` correlation, single-turn tool use only. Right for overnight bulk; WRONG for blocking pre-merge checks.

### Domain 4 — Prompt Engineering & Structured Output (20%, TS 4.1–4.6)

1. **Categorical beats vague (4.1):** "severity=blocker AND impact>=100" beats "important". Explicit thresholds and feature checks, not "be conservative" / "high confidence only".
2. **Few-shot = 2–4 examples on ambiguous cases (4.2):** show reasoning, not just answers. Spend slots on edge cases, not canonical ones. One example is pattern noise; 15 is context bloat.
3. **Structured output via `tool_use` + `input_schema` + forced `tool_choice` (4.3):** eliminates syntax errors. Does NOT eliminate semantic errors (wrong field value, hallucination).
4. **`tool_choice` (4.3):** `auto` (model decides), `any` (must call some tool), forced specific `{"type":"tool","name":...}` (must call this one). Extraction → forced specific.
5. **Nullable + required (4.3):** the primary anti-hallucination lever. Field is always in output, value is either real or `null` when absent. Non-nullable required fields force fabrication on missing data.
6. **Validation-retry loops (4.4):** append the specific validation error to the retry prompt, not a generic "try again". Retries don't help when the source info is absent — that's an escalation.
7. **Batch vs sync + multi-pass review (4.5, 4.6):** batch for latency-tolerant; sync for anything blocking. Per-file local pass + cross-file integration pass. Independent instance reviews, not self-review.

### Domain 5 — Context Management & Reliability (15%, TS 5.1–5.6)

1. **Progressive summarization loses numbers/dates (5.1):** extract into a persistent "case facts" block that survives compaction.
2. **Lost-in-the-middle (5.1):** key findings go at start or end; section headers; position-aware ordering.
3. **Trim verbose tool outputs (5.1):** 5 relevant fields > 40 dumped fields. Normalize in a PostToolUse hook if the upstream is noisy.
4. **Escalation triggers (5.2):** explicit customer demand, policy gap, or inability to progress. **Sentiment and self-reported confidence are NOT reliable triggers.** Multiple matches → ask for more identifiers, don't guess.
5. **Error propagation (5.3):** structured context (failure type, attempted query, partial results, alternatives). Never silent empty-set-on-timeout. Never generic "operation failed". Local recovery first; escalate with partial results.
6. **Scratchpad files + `/compact` + crash-recovery manifests (5.4):** durable state survives session loss. Bigger context window does NOT fix stale context.
7. **Provenance (5.5, 5.6):** preserve claim→source mappings through synthesis. Record publication dates (so old vs new doesn't read as contradiction). Annotate conflicts, don't pick one arbitrarily. Stratified sampling, accuracy by document type + field, not only aggregate.

---

## 4. Master wrong-answer patterns (consolidated from W01–W10)

Every row below is a distractor that has appeared in the training material. Learn to reject them on sight.

| # | Anti-pattern | Why it's wrong | Correct approach | Domain |
|---|---|---|---|---|
| 1 | Parse `resp.content` text for "done" / "finished" | Probabilistic; model phrasing varies across runs | `stop_reason == "end_turn"` only | 1 |
| 2 | Tight iteration cap (3–5) to force termination | Truncates legitimate multi-step work | High safety fuse + natural `end_turn` | 1 |
| 3 | Run tools "inside" the model call | API does not execute tools | Execute in your code; return `tool_result` | 1 |
| 4 | Use `"role": "tool"` for tool results | No such role in the Messages API | Tool results go in a `user` message | 1 |
| 5 | Send each `tool_result` as its own `user` turn | Violates the parallel-tool contract | Bundle all `tool_result` blocks into one `user` turn | 1 |
| 6 | Silently treat `max_tokens` like `end_turn` | Returns truncated output as if complete | Raise or continue with larger `max_tokens` | 1 |
| 7 | "Add 'you must always call tool X' to system prompt" | Probabilistic; model will sometimes skip | `tool_choice` (forced specific or `any`) | 1, 4 |
| 8 | Give every subagent every tool | 18 tools ≫ 5 tools degrades selection | Scope 4–5 per role; delegate cross-domain | 1, 2 |
| 9 | Let subagents share memory or see each other's context | Breaks isolation; re-creates single-agent problems | Explicit prompts + structured returns | 1 |
| 10 | "Add to coordinator prompt: 'you must delegate'" | Won't work without `"Task"` in `allowedTools` | Add `"Task"` to `allowedTools` | 1 |
| 11 | Have the coordinator review its own reasoning | Self-review retains bias | Independent subagent / fresh instance | 1, 3 |
| 12 | Run all subagents sequentially "for safety" | Wastes latency on independent work | Parallel when independent, serial when dependent | 1 |
| 13 | Let one big subagent do everything | Reproduces the single-agent problems | Decompose further | 1 |
| 14 | Adaptive decomposition for a fixed-shape task | Adds reasoning turn + failure mode for no benefit | Fixed prompt chain | 1 |
| 15 | "Add NEVER refund > $500 to system prompt" | Probabilistic; model can be talked out of it | PreToolUse hook with `decision: "block"` | 1 |
| 16 | Use PostToolUse to prevent a destructive action | Fires after the tool ran; damage done | PreToolUse is the only option for "prevent" | 1 |
| 17 | Resume a session after a failed destructive op | Poisoned history mis-steers the next turn | Fork from a clean point, or start fresh | 1 |
| 18 | Use sentiment analysis to trigger escalation | Sentiment ≠ case complexity | Categorical triggers: explicit demand / policy gap / inability to progress | 1, 5 |
| 19 | "Increase context window" to fix stale session | Attention doesn't scale with window size | `/compact`, fork + seed, or start fresh | 1, 5 |
| 20 | Start a new session every turn to avoid staleness | Throws away useful context | Resume when coherent; compact / fork when stale | 1 |
| 21 | Terse tool descriptions to "save tokens" | Selection quality collapses | Rich descriptions: input, examples, boundaries, return shape | 2 |
| 22 | Return generic `"operation failed"` on error | Breaks retry logic; model can't tell fatal from transient | Structured error: `isError`, `errorCategory`, `isRetryable`, `message` | 2, 5 |
| 23 | Retry every error with exponential backoff | Useless for `validation` / `not_found` / `policy` errors | Branch on `isRetryable`; retry only marked-retryable | 2 |
| 24 | One mega-tool with a `mode` enum input | Selector can't see intent; hides misrouting | Split into separately-named tools | 2 |
| 25 | Use `tool_choice: any` to fix selection | Forces *a* tool, not the *right* tool | Fix the description; force only for scripted steps | 2, 4 |
| 26 | Expose `place_order` as an MCP resource | Resources are read-only content | Expose as an MCP tool | 2 |
| 27 | Hardcode API key in `.mcp.json` | Leaks into git history | `${ENV_VAR}` expansion | 2 |
| 28 | Put team MCP server in `~/.claude.json` | Each dev must reconfigure; team drifts | `.mcp.json` at repo root, committed | 2 |
| 29 | Use Glob to search inside files | Glob matches paths, not contents | Grep for content | 2 |
| 30 | Use Bash `cat` to read a file whose path you know | Dedicated tool exists, cheaper + safer | Read | 2 |
| 31 | Put every rule in root `CLAUDE.md` | Bloats every turn; attention degrades | `.claude/rules/*.md` with `paths:` frontmatter | 3 |
| 32 | Rule file with no `paths:` frontmatter | Loads globally anyway, with worse discoverability | Add `paths:`, or move to root `CLAUDE.md` | 3 |
| 33 | Use a rule for a user-invoked action | Rules are passive; user can't invoke them | Command (`.claude/commands/*.md`) | 3 |
| 34 | Use a command for a tool-scoped multi-step workflow | Commands run in current session, no tool scoping | Skill with `allowed-tools` | 3 |
| 35 | Skill doing heavy exploration without `context: fork` | Pollutes main session | Set `context: fork` in SKILL.md | 3 |
| 36 | Put team-wide config in `~/.claude/CLAUDE.md` | User scope isn't shared | Project `CLAUDE.md`, committed | 3 |
| 37 | "Add instructions that the skill should fork" in prose | Isolation is a runtime mechanism, not a prompt hint | Set `context: fork` | 3 |
| 38 | Plan mode for a 3-line null check | Overhead dwarfs the edit | Direct execution | 3 |
| 39 | Direct execution for a 45-file migration | Lose coverage mid-run; half-migrated code | Plan mode (the plan IS the checklist) | 3 |
| 40 | Same session generates AND reviews code in CI | Self-review retains generator's bias | Separate fresh sessions; reviewer sees artifacts only | 3 |
| 41 | Regex natural-language CI output | Format drifts silently across model versions | `--output-format json --json-schema` | 3 |
| 42 | Message Batches for blocking pre-merge check | Up to 24 h window, no SLA | Synchronous `claude -p` | 3 |
| 43 | "Make it better" as iterative refinement feedback | Not actionable; model guesses | Concrete: file, function, expected behavior | 3 |
| 44 | "Output JSON with these fields" in natural language | Syntax errors: trailing commas, markdown fences, commentary | `tool_use` + `input_schema` + forced `tool_choice` | 4 |
| 45 | "JSON Schema eliminates all extraction errors" | Shape is guaranteed; semantics are not | Schema + downstream validators / human review | 4 |
| 46 | `tool_choice: auto` for mandatory extraction | Model may reply in prose and skip the tool | Forced specific `{"type":"tool","name":...}` | 4 |
| 47 | Make every field required and non-null | Forces fabrication on missing source data | Nullable on "might be absent" + null-when-absent instruction | 4 |
| 48 | Closed enum with no `"other"` | Breaks on novel values or miscategorizes silently | `enum` with `"other"` + companion detail field | 4 |
| 49 | "Flag high-confidence findings only" | Vague; miscalibrated across inputs | Categorical criterion with explicit threshold | 4 |
| 50 | Ask the model to self-rate confidence 1–10 | LLM self-confidence is miscalibrated, worse on hard cases | Categorical criteria + downstream validation; empirical calibration if you need uncertainty | 4, 5 |
| 51 | Give 15 few-shot examples | Diminishing returns, bloat, over-fitting | 2–4 examples on ambiguous cases, reasoning shown | 4 |
| 52 | Retry validation loop with generic "try again" | Model doesn't know what was wrong | Append the specific validation error + the failed output to the retry prompt | 4 |
| 53 | Retry when the info is absent from source | No amount of retrying reveals what isn't there | Escalate / mark null / route to human review | 4 |
| 54 | Progressive summarization of case notes | Numbers and dates get dropped | Persistent "case facts" block extracted + preserved | 5 |
| 55 | Put key finding in the middle of a long context | Lost-in-the-middle effect | Start or end, section headers, position-aware ordering | 5 |
| 56 | Silent empty-result-set on tool timeout | Caller can't tell "no matches" from "I failed" | Structured error with `errorCategory: timeout` | 5 |
| 57 | Multiple matches → pick the most plausible one | Heuristic guessing; loses integrity | Ask user for more identifiers | 5 |
| 58 | Pick one source when sources conflict | Silently discards disagreement signal | Preserve both; annotate the conflict with attribution + dates | 5 |
| 59 | Ignore publication dates in synthesis | Old vs new reads as contradiction | Record and preserve `publication_date`; order by recency where relevant | 5 |
| 60 | Aggregate accuracy only (no stratification) | Hides domain-specific failure modes | Accuracy by document type AND by field; stratified sampling | 5 |

Count: 60 rows. The exam has 60 questions. That's not a coincidence of framing — roughly one distractor per question is a variant of one of these rows.

---

## 5. The recurring exam meta-theme — "deterministic mechanism beats prompt instruction"

This single idea is the spine of the exam. Every week's reference ends on it because the distractors test it under every domain's clothing.

The principle:

> A **prompt instruction** is a probabilistic ask. The model complies most of the time, fails silently some of the time, and on the fails it is **confident**.
> A **deterministic mechanism** is code, configuration, or an API contract that runs outside the model's reasoning. It cannot be talked out of compliance. Its failure mode is a hard error, not a silent drift.

When two candidate answers both look plausible, and one is a deterministic mechanism while the other is a prompt rule, **the deterministic one is right**. Every time.

### The deterministic–probabilistic table (memorize this shape)

| Concern | Probabilistic (wrong on exam) | Deterministic (right on exam) |
|---|---|---|
| Stop refunds above a dollar threshold | "NEVER refund more than $500" in prompt | PreToolUse hook that blocks `amount_usd > 500` |
| Redact PII before the model sees it | "Redact patient names" in prompt | PostToolUse hook that regexes + replaces |
| Prevent `rm -rf /` | "Do not run destructive commands" in prompt | PreToolUse hook on Bash with deny-list |
| Force a specific tool to be called | "You must call `extract_invoice`" in prompt | `tool_choice: {"type":"tool","name":"extract_invoice"}` |
| Force *some* tool call | "Always use a tool" in prompt | `tool_choice: {"type":"any"}` |
| Force delegation to a subagent | "You must delegate research" in prompt | Remove web tools from coordinator; add `"Task"`; only researcher has web |
| Guarantee output shape | "Output valid JSON with these fields" in prompt | `tool_use` with `input_schema` + forced `tool_choice` |
| Prevent a field from being fabricated | "Don't hallucinate the due date" in prompt | Field declared `type: ["string", "null"]` + null-when-absent rule |
| Prevent a skill from polluting main context | "Skill, please don't leak context" in prompt | `context: fork` in SKILL.md frontmatter |
| Prevent self-review bias | "Review with fresh eyes" in prompt | Separate fresh CI session; reviewer sees artifacts only |
| Pre-merge check latency | "Try to run fast" in prompt | Synchronous `claude -p` — never batches |
| Categorical decision rule | "Be conservative" / "high confidence" in prompt | "severity=blocker AND impact>=100" as explicit criterion |
| Escalation trigger | "Escalate if the customer sounds upset" in prompt | Categorical: amount > X OR policy gap OR inability to progress |

### The 6–8 exam questions that test this theme directly

Based on the distractor structure across W01–W10, expect this theme behind roughly one question in six. Canonical shapes:

1. **Refund cap enforcement.** Candidate fixes: strengthen the prompt vs register a PreToolUse hook. Hook wins.
2. **Mandatory structured output.** Candidate fixes: stronger prompt telling the model to always call `extract_X` vs set `tool_choice` to forced specific. `tool_choice` wins.
3. **Coordinator won't delegate.** Candidate fixes: tell the coordinator in its prompt to delegate vs add `"Task"` to `allowedTools` (and/or scope its own tools down). Configuration wins.
4. **Skill leaking context into main session.** Candidate fixes: add "please don't pollute" to SKILL.md prose vs set `context: fork` in frontmatter. Frontmatter wins.
5. **PII leak prevention.** Candidate fixes: instruct the model to redact before returning vs PostToolUse hook that redacts the raw tool response before the model sees it. Hook wins.
6. **CI reviewer keeps rationalizing the generator's bugs.** Candidate fixes: tell the reviewer to be more critical vs run the reviewer in a separate fresh session with no `--resume`. Isolation wins.
7. **Model hallucinates a field that's not in the source.** Candidate fixes: "don't hallucinate" in prompt vs nullable field + null-when-absent instruction. Schema wins.
8. **Output shape drift in CI.** Candidate fixes: regex more carefully vs `--output-format json --json-schema`. Schema wins.

Every one of these is a direct probabilistic-vs-deterministic test. When you see the shape, pick the deterministic answer without re-reading the distractor three times.

---

## 6. The fast checklist before you click "submit" on any question

1. **What domain is this?** Use the 27/18/20/20/15 weighting to calibrate expected difficulty.
2. **What failure mode is the scenario describing?** Name it in your head.
3. **Scan the four options for the probabilistic-vs-deterministic pair.** Reject the prompt-only option.
4. **Scan for the "pile more tools on one agent" / "give every agent every tool" distractor.** Reject.
5. **Scan for "add to system prompt" where a hook, schema, or `tool_choice` is available.** Reject.
6. **Scan for "parse natural language" / "read the text" / "check for the word 'done'" distractors.** Reject.
7. **Scan for "resume the session after crash" distractors.** Reject — fork or fresh, never resume poisoned.
8. Pick the remaining option. Move on.

If two options survive step 7, the more deterministic and the more specific one wins. That's the tiebreaker.
