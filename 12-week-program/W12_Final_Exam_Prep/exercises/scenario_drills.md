# Scenario Drills — Top 5 Reliability Risks and Their One Correct Mitigation

The exam shows 4 of 6 scenario families on any given sitting. You cannot predict which four, so drill all six. For each scenario below: the top 5 reliability risks a production deployment must handle, and the one correct mitigation for each (with task-statement references).

Work through each scenario on paper before reading the answer. Then compare. If you missed a risk or named the wrong mitigation, that's a W11 weak-spot entry.

---

## Scenario 1 — Customer Support Automation

A tier-1 support agent handles refund requests, address changes, order status, and policy questions. It has tools `get_order`, `get_customer`, `get_refund_policy`, `issue_refund`, `escalate_to_human`.

### Risk 1 — Refund above policy cap is issued
A $9,000 refund goes through because the system prompt said "never refund above $500" and the model was talked out of it by a persistent customer.
- **Mitigation:** PreToolUse hook on `issue_refund` that blocks `amount_usd > 500` with `decision: "block"`, `reason` telling the model to call `escalate_to_human`. Prompt rule can stay as belt-and-suspenders, but the hook is load-bearing. (TS 1.4, 1.5)

### Risk 2 — Multi-concern message gets a partial reply
Customer's message mentions a refund, an address change, and a loyalty question. The agent handles the refund and stops.
- **Mitigation:** Adaptive decomposition in the coordinator — the coordinator spots N concerns, dispatches N specialist subagents in parallel, synthesizes one unified reply. Fixed prompt chain is wrong here because the shape of the input varies per message. (TS 1.2, 1.7)

### Risk 3 — Agent escalates on polite wording, doesn't escalate on a policy gap
"Sentiment-based" escalation fires when the customer uses angry language and misses when a polite customer hits an edge case the policy doesn't cover.
- **Mitigation:** Categorical escalation triggers: explicit customer demand ("I want to speak to a manager"), detected policy gap (request outside documented policy), inability to progress (missing data the agent cannot obtain). Sentiment and self-reported confidence are NOT reliable triggers. (TS 5.2)

### Risk 4 — Timeout on `get_order` silently returns an empty result, agent tells customer "no order found"
The warehouse API timed out. The tool returned `[]`. The agent concluded the order doesn't exist and told the customer so.
- **Mitigation:** Structured error object from the tool: `{isError: true, errorCategory: "timeout", isRetryable: true, message: "..."}`. The agent branches on `isRetryable`, retries a bounded number of times, and if still failing escalates with partial context — not with a false "not found". (TS 2.2, 5.3)

### Risk 5 — Long support session degrades; the agent contradicts a promise it made 40 turns ago
Progressive summarization lost the concrete facts (refund amount, date promised, order number).
- **Mitigation:** Extract concrete facts into a persistent "case facts" block the agent rereads each turn (not a summary). Combine with position-aware ordering: the block goes near the end of the context so the model attends to it. Bigger context window is not the fix. (TS 5.1)

---

## Scenario 2 — Code Generation / Review

An engineer uses Claude Code to write new features and review PRs. Some work runs interactively; some runs in CI.

### Risk 1 — Scope creep and lost coverage on a multi-file migration
A 45-file Jest → Vitest migration is done in direct execution mode; halfway through, the agent loses track and leaves half the files unconverted.
- **Mitigation:** Plan mode. The written plan is the migration checklist; approval gates execution; coverage is visible. Plan mode is *for* multi-file / ambiguous / hard-to-reverse work. Direct is only for small well-specified edits. (TS 3.4)

### Risk 2 — Self-review in CI rationalizes the generator's bugs
A single session generates the migration script and reviews itself. The reviewer "knows" why each choice was made and approves its own flawed output.
- **Mitigation:** Separate fresh session for the reviewer. No `--resume`, no shared transcript. The reviewer sees only the artifact (diff) and the spec, not the generator's reasoning trace. Same isolation principle as hub-and-spoke subagents. (TS 3.6, 1.2)

### Risk 3 — CI output is natural-language text; downstream script parses it with regex
Next model update changes the phrasing slightly, the regex breaks silently, the pipeline passes PRs it shouldn't.
- **Mitigation:** `claude -p --output-format json --json-schema review.schema.json`. The schema is the contract. Never regex natural language. (TS 3.6, 4.3)

### Risk 4 — Model hallucinates an imported function that doesn't exist
The generator writes `from utils import parse_ids` when that function isn't in `utils`. Tests would catch it; the generator doesn't run them.
- **Mitigation:** TDD iteration — ask for the failing test first, then the implementation, then refactor. Each step has a deterministic success signal (tests pass). "Be careful about imports" in the prompt is probabilistic and insufficient. (TS 3.5)

### Risk 5 — Main Claude Code session gets cluttered by multi-tool exploration from a skill
A `/pr-summary` skill does many `git diff` / `gh pr view` / `Read` calls, and every intermediate turn pollutes the main session's context.
- **Mitigation:** Set `context: fork` in the skill's `SKILL.md` frontmatter. The skill runs in an isolated session; only its final message returns to the main session. This is runtime isolation, not a prompt rule. (TS 3.3)

---

## Scenario 3 — Multi-Agent Research

A research pipeline answers open-ended questions by dispatching researcher subagents, gathering evidence, and synthesizing a final report with citations.

### Risk 1 — Coordinator tries to do everything itself; its context blows up
The coordinator has all web tools and ignores the prompt hint "you should delegate". The main session fills with raw fetch content.
- **Mitigation:** Configuration, not prose. Add `"Task"` to `allowedTools`; remove web tools from the coordinator entirely; give web tools only to the `researcher` subagent. Now the coordinator *has* to delegate — it has no alternative. (TS 1.3)

### Risk 2 — Independent research subtasks run sequentially, wall-clock is 3× slower than it needs to be
The coordinator researches topic A, then B, then C, with no data dependency between them.
- **Mitigation:** Parallel `Task` dispatch — coordinator emits N `tool_use` blocks for `Task` in one assistant turn; the SDK runs them in parallel; one `user` turn returns all N results. Serial is only correct when B needs A's output. (TS 1.2)

### Risk 3 — Synthesis silently picks one source when two disagree; conflict signal is lost
Source A says stat X; source B says stat Y. The synthesis outputs X with no mention that B disagreed.
- **Mitigation:** Preserve conflict in the synthesis. Each claim carries `{claim, evidence, source_url, publication_date}`; the final report annotates contested vs well-established claims and attributes both sides where they disagree. Don't arbitrarily pick. (TS 5.5, 5.6)

### Risk 4 — Old and new sources read as a contradiction because dates are missing
A 2020 paper and a 2024 paper give different numbers; the synthesizer flags a contradiction when it's really "the field updated".
- **Mitigation:** Record `publication_date` with every claim. Synthesizer uses recency as a tiebreaker for "same question, different time" and preserves the older finding as "as of 2020". (TS 5.5)

### Risk 5 — A researcher subagent times out; the coordinator drops the report entirely instead of noting the coverage gap
The failure propagates as a generic error; the coordinator aborts.
- **Mitigation:** Structured error from the subagent (`errorCategory`, attempted queries, partial results). The coordinator annotates a "coverage gap for topic X" in the final report and proceeds with the rest. Local recovery first (retry with narrower scope), then graceful degradation. (TS 5.3)

---

## Scenario 4 — Developer Productivity (Claude Code team workflows)

A team standardizes on Claude Code with shared CLAUDE.md, rules, commands, skills, and MCP servers.

### Risk 1 — Every developer gets different behavior from Claude Code
One dev has a personal `~/.claude/CLAUDE.md` override that everyone assumed was shared. Another is missing the project rules because they cloned shallow.
- **Mitigation:** Team-wide config goes in project scope: `<repo>/CLAUDE.md` and `<repo>/.claude/*`, committed to git. Personal prefs only in `~/.claude/…`. Audit for team-essential rules that leaked into user scope. (TS 3.1)

### Risk 2 — Root `CLAUDE.md` has 400 lines; context is crowded and unrelated rules drown out the relevant ones
Every turn pays for migration-specific, testing-specific, and front-end-specific rules regardless of what files are being touched.
- **Mitigation:** Split into `.claude/rules/migrations.md`, `.claude/rules/testing.md`, `.claude/rules/frontend.md` — each with a `paths:` frontmatter glob. Rules load only when matching files are touched. (TS 3.2)

### Risk 3 — `.mcp.json` has literal API keys; secrets leaked into the repo
Someone committed `"GITHUB_TOKEN": "ghp_..."` directly.
- **Mitigation:** `${ENV_VAR}` expansion: `"GITHUB_TOKEN": "${GITHUB_TOKEN}"`. Secrets live in each developer's environment / secret manager; the committed config is a template. Rotate the leaked token. (TS 2.4)

### Risk 4 — `/review` command is a giant multi-step workflow that pollutes the invoking session with dozens of diffs and greps
It's implemented as `.claude/commands/review.md`, so the body runs in the current session.
- **Mitigation:** Reimplement as a skill — `.claude/skills/review/SKILL.md` with `allowed-tools` scoped to the tools it actually needs and `context: fork` to isolate the exploration. Commands are for single-turn saved prompts; skills are for multi-step capabilities. (TS 3.3)

### Risk 5 — Nobody knows whether to use plan mode; "when in doubt, plan" or "always direct for speed" both fail
Plan mode is overkill for small fixes; direct execution loses coverage on multi-file work.
- **Mitigation:** Document a team-level decision rule in the project `CLAUDE.md`: plan mode for (a) scope ambiguity, (b) >3 files or >3 modules, (c) schema/config/prod-affecting changes, (d) "make this codebase better" tasks. Direct for single-file well-specified edits and bugs with a known repro. (TS 3.4)

---

## Scenario 5 — CI/CD Integration

Claude is wired into a GitHub Actions pipeline for pre-merge checks, nightly data jobs, and release-note generation.

### Risk 1 — Pre-merge check uses Message Batches API; PRs stall for up to 24 h in "checks pending"
Batch looked attractive because it's 50% cheaper.
- **Mitigation:** Synchronous `claude -p` for anything blocking a user action (pre-merge, build gate, release cut). Batches are only correct for latency-tolerant bulk work: nightly classifications, weekly reports, backfills. (TS 3.6)

### Risk 2 — CI step parses assistant natural language; output shape drifts silently with model updates
A phrase change like "Found 3 issues:" → "Identified 3 issues:" breaks the regex; the pipeline passes PRs it shouldn't.
- **Mitigation:** `--output-format json --json-schema ./review.schema.json`. The schema is the contract. Pipeline code consumes the JSON with a standard parser. (TS 3.6, 4.3)

### Risk 3 — Retry on failure just re-runs the same command with the same inputs; no error context fed back
A validation error on extraction gets retried blindly, hits the same error, burns the retry budget, fails the pipeline.
- **Mitigation:** Structured error response from the extractor (`isError`, `errorCategory`, `isRetryable`, specific validation message). Retry logic branches on `isRetryable`; retry payload includes the specific error for the model to correct. Unretryable errors route to human review. (TS 2.2, 4.4)

### Risk 4 — Generator and reviewer share a session; reviewer rationalizes generator's mistakes
Same `--session-id` is reused across two `claude -p` invocations for speed.
- **Mitigation:** Separate fresh sessions. Generator writes artifact to disk; reviewer invocation has no `--resume` and reads only the artifact + spec. Self-review retains bias; independent review is the fix. (TS 3.6)

### Risk 5 — Nightly bulk job runs serially against the standard API; cost explodes and latency is hours
100k tickets being classified one at a time.
- **Mitigation:** Message Batches API for this exact use case: 50% cheaper, up to 24 h window (fine for overnight), `custom_id` per ticket so results correlate back. Latency-tolerant bulk is batches' sweet spot. (TS 3.6, 4.5)

---

## Scenario 6 — Structured Extraction

A pipeline extracts structured fields from invoices, contracts, or support tickets and feeds them to downstream systems.

### Risk 1 — Model sometimes replies in prose instead of calling the extraction tool
`tool_choice: "auto"` lets the model decide, and on some inputs it narrates the extraction instead of calling the tool.
- **Mitigation:** `tool_choice: {"type":"tool","name":"extract_invoice"}` — forced specific. The tool call is guaranteed. "Add 'you must call the tool' to the prompt" is the probabilistic trap. (TS 4.3)

### Risk 2 — Model hallucinates a `due_date` when the invoice has none
The field is declared as `type: "string"` and required. The model is forced to produce a string; when the data isn't there, it fabricates.
- **Mitigation:** Declare the field `type: ["string", "null"]`, keep it required (always present in output), and instruct "return null if the field is not present in the source". Nullable fields are the primary anti-hallucination lever. (TS 4.3)

### Risk 3 — Novel payment term ("Net 45") breaks the pipeline; enum doesn't cover it
Schema has `"enum": ["net_30", "net_60", "due_on_receipt"]`. Either the model miscategorizes silently or the validator rejects.
- **Mitigation:** Add `"other"` to the enum and a companion `payment_terms_detail` nullable string field. System prompt rule: "If the terms don't match an enum value, use `other` and put the verbatim phrase in the detail field." Extensible by design. (TS 4.3)

### Risk 4 — Pipeline claims "100% extraction accuracy" because JSON validates, but fields are semantically wrong
`vendor_name` is populated with the customer's name; the schema can't tell.
- **Mitigation:** Combine schema (shape) with downstream validators (semantic checks — e.g., Pydantic validator that the total equals the sum of line items) and stratified human review sampling. Schema eliminates SYNTAX errors, not SEMANTIC errors. (TS 4.3, 4.6)

### Risk 5 — Retry loop on validation failure gives the model no specific error; it fails the same way again
Retry prompt is "Please try again; the previous output was invalid."
- **Mitigation:** Validation-retry loop appends the specific validator error AND the failed output to the retry prompt: "You produced `total_usd = 'N/A'`, which failed validation: expected number, got string. Correct the output." Retry with specific signal is useful; retry without signal burns budget. Also — if the source information is actually absent, no amount of retrying will help; route to null / escalation. (TS 4.4)

---

## How to drill

Monday through Friday of W12, for each scenario:

1. Cover the risks + mitigations, read only the scenario paragraph.
2. On paper, write out what you think the top 5 risks are and one fix for each. 10 minutes.
3. Uncover, compare. Score yourself 0–5 on "had the risk" and 0–5 on "had the correct mitigation".
4. Any 4/5 or lower → add to `notes/weak_spots.md` as an entry to re-read the relevant week's reference.

By Saturday, all six scenarios should be 5/5 on both axes.
