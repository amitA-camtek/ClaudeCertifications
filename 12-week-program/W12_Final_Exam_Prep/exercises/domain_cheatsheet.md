# Domain Cheat Sheet — Memorize This Card

One section per domain. 15–20 lines max per section. Read this every morning of exam week. By Sunday you should be able to recite any section aloud without looking.

Task-statement numbers in parentheses match the exam guide.

---

## Domain 1 — Agentic Architecture & Orchestration (27%)

- **Loop terminates on `stop_reason == "end_turn"`.** Never parse text for "done". (1.1)
- **Other `stop_reason`s:** `tool_use` (run tools, append `tool_result`), `max_tokens` (truncated — raise or continue), `stop_sequence` (rare), `pause_turn` / `refusal` (handle, don't ignore).
- **Message contract:** full history appended every turn. Tool results live in a `user` message (no `"tool"` role), one message, all paired by `tool_use_id`.
- **Parallel tool use:** one assistant turn with N `tool_use` blocks → one `user` turn with N paired `tool_result` blocks.
- **High `safety_fuse` (25/50/100), not tight cap.** Tight caps truncate real work.
- **Hub-and-spoke:** coordinator decomposes + synthesizes; subagents run isolated; return compact synthesis; never shared memory. (1.2)
- **`Task` tool = delegation mechanism.** Coordinator `allowedTools` MUST include `"Task"`; subagents usually must NOT. (1.3)
- **`AgentDefinition` fields:** `description` (selection signal), `prompt`, `tools` (scoped subset), optional `model`.
- **Parallel vs serial subagents:** parallel when independent; serial when B needs A's output.
- **PreToolUse hook = block/approve before tool runs.** PostToolUse hook = shape/redact/log after. (1.4)
- **Hook script contract:** JSON on stdin, `{"decision":"block|approve","reason":"..."}` on stdout. Registered in `settings.json` with `matcher`. (1.5)
- **Deterministic (hook/`tool_choice`/schema/config) beats probabilistic (prompt).** THE theme.
- **Sessions:** `--resume` only when clean and continuing; `fork_session` for risky exploration OR recovery from poisoned session; `/compact` for staleness; fresh session for different task. (1.6)
- **Never resume into a poisoned context.** Canonical distractor.
- **Bigger context window does NOT fix stale context.** Compact, fork, or fresh.
- **Fixed prompt chain** for known steps; **adaptive decomposition** for open-ended/multi-concern. (1.7)

---

## Domain 2 — Tool Design & MCP Integration (18%)

- **Tool descriptions are the primary selection signal.** Not the name, not the system prompt. (2.1)
- **A good description has:** what, input format with example, output shape, positive boundary ("use for X"), negative boundary ("do NOT use for Y; use Z"), error behavior.
- **Terse descriptions "to save tokens" = distractor.** Tokens here are the best spent in the prompt.
- **Consolidate** true duplicates. **Split** mega-tools with `mode` enums into separately-named tools. **Keep both, sharpen** when truly distinct.
- **Structured error object:** `isError: true`, `errorCategory` (`validation` / `not_found` / `timeout` / `policy` / `internal`), `isRetryable: bool`, user-friendly `message`. (2.2)
- **Retry logic branches on `isRetryable`**, not on parsing the message string.
- **4–5 tools per agent, max.** More degrades selection. Scope by role; delegate cross-domain work. (2.3)
- **`tool_choice`:** `auto` (default), `any` (must call some tool), forced `{"type":"tool","name":X}` (must call X), `none` (cannot call).
- **`.mcp.json`** (repo root) = project scope, committed, shared. **`~/.claude.json`** = user scope, personal, uncommitted. (2.4)
- **Secrets via `${ENV_VAR}` expansion.** Never literal. Project config commits with placeholders; env supplies values.
- **MCP tools = actions (side effects).** **MCP resources = read-only content.** Don't swap.
- **Built-in tools:** Read (known path), Grep (content search), Glob (path patterns), Edit (in-place patch), Write (new file / full rewrite), Bash (everything else). (2.5)
- **Glob = paths, not contents.** Canonical distractor: "use Glob to find files importing pandas" → wrong, use Grep.
- **Bash `cat` for a known path = wrong.** Use Read.

---

## Domain 3 — Claude Code Configuration & Workflows (20%)

- **Three scopes:** user (`~/.claude/…`), project (`<repo>/.claude/…` or `<repo>/CLAUDE.md`), subdirectory (nested `CLAUDE.md`). All stack; more-specific wins on conflict. (3.1)
- **CLAUDE.md** = always-on context. Put tech stack, layout, team conventions here. DO NOT put path-specific rules here.
- **`.claude/rules/*.md` with `paths:` frontmatter** = passive, path-scoped guidance. Loads only when a matching file is touched. (3.2)
- **Rule without `paths:` frontmatter** = loads globally, same as root CLAUDE.md — usually a mistake.
- **`.claude/commands/*.md`** = user-invoked saved prompt (`/name`). Project scope wins over user scope on name collision.
- **`.claude/skills/<name>/SKILL.md`** = multi-step capability. Frontmatter: `description`, `argument-hint`, `allowed-tools`, `context: fork|default`, optional `model`.
- **`context: fork`** = runtime isolation from main session. Use for multi-step skills that do heavy exploration. (3.3)
- **Rule vs command vs skill:** passive-by-path vs active-invoked-prompt vs active-capability-with-scoped-tools.
- **`@import`** inlines at load time. Modularity, not conditional loading; doesn't save tokens.
- **Plan mode** for ambiguous / multi-file / hard-to-reverse. **Direct** for small well-specified edits. 45-file migration → plan; 3-line null check → direct. (3.4)
- **Iterative refinement feedback:** concrete (file/function/behavior) or deterministic (TDD red-green-refactor). "Make it better" is a distractor. (3.5)
- **Interview/clarifying-questions pattern** for ambiguous specs. Don't add more prompt rules — ask more questions.
- **Headless CI:** `-p` + `--output-format json` + `--json-schema`. All three. (3.6)
- **Generator and reviewer run in SEPARATE fresh sessions.** No `--resume`, no shared transcript. Self-review retains bias.
- **Message Batches API:** 50% cheaper, up to 24 h window, `custom_id` correlation, no multi-turn tool loop inside one request. Right for overnight bulk; **WRONG for blocking pre-merge checks**.
- **Secrets in `.mcp.json` via `${ENV_VAR}`.** Same rule as Domain 2.

---

## Domain 4 — Prompt Engineering & Structured Output (20%)

- **Categorical criteria beat vague instructions.** "severity=blocker AND impact>=100" beats "important bugs". (4.1)
- **Vague words to avoid:** "important", "conservative", "high confidence", "unsure", "appropriate". All miscalibrated.
- **Write thresholds from the consequence of being wrong** — false-positive vs false-negative framing.
- **Few-shot = 2–4 examples on ambiguous/edge cases**, not canonical ones. Show reasoning, not just the answer. (4.2)
- **One example = pattern noise. 15 examples = bloat + over-fitting.** Sweet spot is 2–4.
- **Structured output:** `tool_use` + `input_schema` + forced `tool_choice: {"type":"tool","name":X}`. (4.3)
- **JSON Schema eliminates SYNTAX errors. It does NOT eliminate SEMANTIC errors.** Wrong field value, hallucinated content, wrong subtotal-vs-total → all invisible to the schema.
- **`tool_choice` modes:** `auto` (may skip), `any` (must pick some tool), forced specific (must pick this one), `none` (cannot pick).
- **Extraction task = forced specific.** `auto` is the wrong default here.
- **Nullable fields are the primary anti-hallucination lever.** `type: ["string","null"]` + "return null when absent" instruction. Non-nullable required fields force fabrication on missing data.
- **Required + nullable pattern:** field always present, value is real or explicit null.
- **Enum + `"other"` + detail field** for any enum whose input domain can have novel values. Closed enums are a design smell.
- **Validation-retry loop:** append the specific validation error + the failed output to the retry prompt. Generic "try again" doesn't help. (4.4)
- **Retries don't work when source info is absent.** Escalate / null / human review.
- **Batch vs sync:** batch for latency-tolerant bulk; sync for blocking / user-visible SLA work. (4.5)
- **Multi-pass review:** per-file local analysis + cross-file integration pass. Independent instance, not self-review. (4.6)
- **Criteria in system prompt; schema in the tool; document in the user message.** Don't mix.

---

## Domain 5 — Context Management & Reliability (15%)

- **Progressive summarization loses numbers/dates.** Extract into a persistent "case facts" block that survives compaction. (5.1)
- **Lost-in-the-middle:** the model attends best to the start and the end of long context. Key findings go there; section headers help.
- **Trim verbose tool outputs.** Keep 5 relevant fields, not 40. Normalize in a PostToolUse hook if the upstream is noisy.
- **Escalation triggers that WORK:** explicit customer demand, policy gap, inability to progress. (5.2)
- **Escalation triggers that DON'T work:** sentiment, self-reported confidence, "the customer seems upset". Canonical distractor.
- **Multiple matches → ask for more identifiers.** Never heuristically guess the "most likely" match.
- **Error propagation = structured context.** Failure type, attempted query, partial results, alternatives. (5.3)
- **Never silent empty-result-set on timeout.** Caller can't distinguish "no matches" from "I failed".
- **Never generic `"operation failed"`.** Kills retry and escalation logic.
- **Local recovery before coordinator escalation.** Try alternate query / scope first; escalate with partial results if the coordinator needs to decide.
- **Scratchpad files for long sessions.** Structured state (decisions, open questions, current step) — survives crashes. (5.4)
- **`/compact`** for staleness; **fork + seed** when `/compact` is too lossy; **crash-recovery manifest** for cross-session durability.
- **Bigger context window does NOT fix stale context.** Structural fixes only.
- **Provenance:** preserve `{claim, source, publication_date}` tuples through synthesis. (5.5)
- **Record publication dates** so "old vs new" doesn't read as contradiction.
- **Conflicting sources → annotate the conflict**, attribute both, don't pick one arbitrarily.
- **Human review for uncertainty:** stratified sampling, accuracy by document type AND by field, not only aggregate. (5.6)
- **Field-level confidence from the extractor** → low-confidence fields route to human queue.

---

## The single sentence to memorize

> **Deterministic mechanism beats prompt instruction.** Hooks, `tool_choice`, JSON Schema, `context: fork`, separate sessions, scoped tool lists, structured errors, nullable fields — every one of them beats "add it to the prompt."

If you remember only one thing walking in, remember that sentence.
