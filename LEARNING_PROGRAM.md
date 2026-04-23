# Claude Certified Architect – Foundations: 6-Week Learning Program

> Based on the official Exam Guide (Version 0.1, Feb 10 2025). Passing score: 720/1000. Exam is scenario-based multiple choice (4 of 6 scenarios shown per exam).

---

## How to use this program

- **Time budget:** ~8–10 hrs/week × 6 weeks (≈ 50–60 hrs total). Compress to 3–4 weeks by doubling daily time if you already have 6+ mo hands-on.
- **Daily loop:** 30 min read docs → 30 min watch video → 60–90 min build/practice → 15 min flashcards.
- **Each domain ends with a hands-on exercise from the exam guide + self-quiz against the sample questions.**
- **Video links:** Where I'm not 100% sure a specific video exists at a given URL, I use YouTube *search* links (they always work and surface current official content). Official channel: [Anthropic on YouTube](https://www.youtube.com/@anthropic-ai).

---

## Core resources (bookmark these first)

| Resource | URL |
|---|---|
| Anthropic documentation (hub) | https://docs.anthropic.com/ |
| Claude API docs | https://docs.anthropic.com/en/api/overview |
| Claude Code docs | https://docs.anthropic.com/en/docs/claude-code/overview |
| Claude Agent SDK docs | https://docs.anthropic.com/en/api/agent-sdk/overview |
| Model Context Protocol spec | https://modelcontextprotocol.io/ |
| MCP intro / tutorials | https://modelcontextprotocol.io/introduction |
| Claude cookbook (code examples) | https://github.com/anthropics/anthropic-cookbook |
| Claude Code GitHub | https://github.com/anthropics/claude-code |
| Prompt engineering guide | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview |
| Tool use guide | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview |
| Message Batches API | https://docs.anthropic.com/en/docs/build-with-claude/batch-processing |
| Anthropic YouTube channel | https://www.youtube.com/@anthropic-ai |
| Anthropic courses (GitHub) | https://github.com/anthropics/courses |

---

## Week 0 — Orientation (≈ 3 hrs)

**Goal:** install the stack, read the exam guide once end-to-end, watch one overview talk.

1. Install Claude Code: https://docs.anthropic.com/en/docs/claude-code/setup
2. Create an Anthropic API key + store as env var: https://docs.anthropic.com/en/api/getting-started
3. Skim the exam guide PDF you already have.
4. **Video:** "Building effective agents with Claude" — search: https://www.youtube.com/results?search_query=anthropic+building+effective+agents
5. **Read:** https://www.anthropic.com/research/building-effective-agents (foundational article; the exam's whole mental model comes from this + "How we built our multi-agent research system")
6. **Read:** https://www.anthropic.com/engineering/built-multi-agent-research-system

---

## Week 1 — Domain 1: Agentic Architecture & Orchestration (27%)

The largest domain. Focus: the agentic loop, coordinator/subagent patterns, hooks, session mgmt.

### Topics (from exam guide task statements 1.1–1.7)
- Agentic loop lifecycle: `stop_reason == "tool_use"` vs `"end_turn"`.
- Hub-and-spoke coordinator + isolated subagent context.
- `Task` tool for spawning subagents; `allowedTools` must include `"Task"`.
- `AgentDefinition`, `fork_session`, `--resume <name>`.
- `PostToolUse` and pre-tool-call hooks — **deterministic** enforcement vs prompt-based guidance.
- Task decomposition: fixed prompt chains vs adaptive decomposition.

### Docs
- Agent SDK overview: https://docs.anthropic.com/en/api/agent-sdk/overview
- Subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Session resume / fork: https://docs.anthropic.com/en/docs/claude-code/manage-sessions

### Videos
- Anthropic channel — agent design playlist: https://www.youtube.com/@anthropic-ai/videos
- Search: https://www.youtube.com/results?search_query=claude+agent+sdk+tutorial
- Search: https://www.youtube.com/results?search_query=anthropic+multi+agent+research+system

### Hands-on (Exercise 1 from exam guide)
Build a multi-tool agent with escalation:
1. Define 3–4 MCP tools with rich descriptions (include 2 near-similar tools).
2. Run an agentic loop that branches on `stop_reason`.
3. Add a pre-tool hook that blocks operations above a $ threshold.
4. Test a multi-concern message ("refund + address change + loyalty question") — verify decomposition + unified reply.

### Self-quiz
- Re-answer **Sample Questions 1, 3, 7, 8, 9** from the PDF without looking at the answer key.

---

## Week 2 — Domain 2: Tool Design & MCP Integration (18%)

### Topics (task statements 2.1–2.5)
- Tool descriptions as the primary selection signal; splitting vs consolidating.
- `isError`, `errorCategory`, `isRetryable` structured errors.
- Scoping tools per subagent; `tool_choice`: `"auto"` / `"any"` / forced `{"type":"tool","name":...}`.
- `.mcp.json` (project) vs `~/.claude.json` (user); `${ENV_VAR}` expansion.
- MCP *resources* for content catalogs vs MCP *tools* for actions.
- Built-in tools: Read, Write, Edit, Bash, Grep, Glob — when each is correct.

### Docs
- MCP quickstart: https://modelcontextprotocol.io/quickstart/server
- MCP in Claude Code: https://docs.anthropic.com/en/docs/claude-code/mcp
- Tool use + `tool_choice`: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
- Tool use best practices: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview

### Videos
- Search: https://www.youtube.com/results?search_query=model+context+protocol+MCP+tutorial
- Search: https://www.youtube.com/results?search_query=claude+tool+use+json+schema

### Hands-on
1. Build an MCP server in Python or TS using the quickstart. Expose 2 tools (one "lookup", one "action").
2. Deliberately write minimal descriptions → test with Claude → observe wrong tool selection → rewrite descriptions with input formats, example queries, and boundaries → re-test.
3. Add structured error responses (`errorCategory`, `isRetryable`, friendly message) for: timeout, invalid-input, policy-violation.
4. Wire the server via `.mcp.json` with `${GITHUB_TOKEN}` style env expansion.

### Self-quiz
- Sample Questions **2** and anything involving tool choice or error propagation.

---

## Week 3 — Domain 3: Claude Code Configuration & Workflows (20%)

### Topics (task statements 3.1–3.6)
- CLAUDE.md hierarchy: `~/.claude/CLAUDE.md` (user) → `.claude/CLAUDE.md` / root `CLAUDE.md` (project) → subdirectory files.
- `@import` syntax for modular configs.
- `.claude/rules/` with YAML frontmatter `paths: ["**/*.test.tsx"]` — path-scoped rules.
- `.claude/commands/` (project) vs `~/.claude/commands/` (user) for slash commands.
- `.claude/skills/` with `SKILL.md` frontmatter: `context: fork`, `allowed-tools`, `argument-hint`.
- **Plan mode vs direct execution.** Explore subagent for verbose discovery.
- CI/CD: `-p` / `--print`, `--output-format json`, `--json-schema`. Session context isolation (don't let the generator also review itself).

### Docs
- CLAUDE.md memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Slash commands: https://docs.anthropic.com/en/docs/claude-code/slash-commands
- Agent Skills: https://docs.anthropic.com/en/docs/claude-code/skills
- Plan mode: https://docs.anthropic.com/en/docs/claude-code/common-workflows
- CI/CD / headless: https://docs.anthropic.com/en/docs/claude-code/ci

### Videos
- Search: https://www.youtube.com/results?search_query=claude+code+claude.md+best+practices
- Search: https://www.youtube.com/results?search_query=claude+code+plan+mode
- Search: https://www.youtube.com/results?search_query=claude+code+ci+github+actions

### Hands-on (Exercise 2 from exam guide)
1. Project CLAUDE.md + two `.claude/rules/*.md` files with different `paths:` globs — verify one loads only on `*.test.*`.
2. One project slash command in `.claude/commands/review.md`.
3. One skill with `context: fork` + `allowed-tools` restriction.
4. Two MCP servers: one team (`.mcp.json`), one personal (`~/.claude.json`) — both live simultaneously.
5. Run the same task 3 ways (single-file fix, 45-file migration, open-ended feature) and note where plan mode pays for itself.

### Self-quiz
- Sample Questions **4, 5, 6, 10, 11, 12**.

---

## Week 4 — Domain 4: Prompt Engineering & Structured Output (20%)

### Topics (task statements 4.1–4.6)
- Explicit, **categorical** criteria > "be conservative" / "high confidence only".
- Few-shot: 2–4 targeted examples for ambiguous cases; reasoning shown, not just answers.
- Structured output via `tool_use` + JSON Schema — eliminates syntax errors, not semantic errors.
- `tool_choice`: `"auto"` (may skip), `"any"` (must call *some* tool), forced specific tool.
- Nullable fields prevent hallucination. `enum` with `"other" + detail` for extensibility.
- Retry-with-error-feedback. Retries don't work when source info is absent.
- Message Batches API: 50% cheaper, up to 24 h window, **no multi-turn tool calling inside one request**, `custom_id` to correlate.
- Multi-instance / multi-pass review: self-review is weak; independent instance catches more.

### Docs
- Prompt engineering overview: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- Multishot (few-shot): https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting
- Tool use + structured output: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
- JSON output patterns: https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency
- Message Batches API: https://docs.anthropic.com/en/docs/build-with-claude/batch-processing

### Videos
- Search: https://www.youtube.com/results?search_query=claude+structured+output+tool+use
- Search: https://www.youtube.com/results?search_query=anthropic+prompt+engineering+few+shot
- Search: https://www.youtube.com/results?search_query=anthropic+message+batches+api

### Hands-on (Exercise 3 from exam guide)
1. Extraction tool with required, optional, and nullable fields + `enum` with `"other" + detail`.
2. Feed it documents where some fields are absent — confirm `null` (not hallucinated) values.
3. Validation-retry loop: Pydantic fails → resend with document + failed output + specific error.
4. Batch 100 docs, fail some intentionally, resubmit failures by `custom_id`.
5. Output field-level confidence → route low-confidence to "human review" queue.

### Self-quiz
- Any question mentioning schemas, false positives, few-shot, or batch processing.

---

## Week 5 — Domain 5: Context Management & Reliability (15%)

### Topics (task statements 5.1–5.6)
- Progressive summarization loses numbers/dates → extract into persistent "case facts" block.
- **Lost-in-the-middle** — put key findings at start or end; use section headers.
- Trim verbose tool outputs (keep 5 relevant fields, not 40).
- Escalation triggers: explicit customer request, policy gap, inability to progress. **Sentiment / self-reported confidence are NOT reliable triggers.**
- Multiple matches → ask for more identifiers, do not heuristically guess.
- Error propagation: return structured context (failure type, attempted query, partial results, alternatives). Don't silently suppress OR kill the whole workflow.
- Scratchpad files for long sessions; `/compact`; crash recovery via manifest exports.
- Provenance: preserve claim→source mapping through synthesis. Record publication dates so "old vs new" isn't read as contradiction. Annotate conflicts; don't pick one arbitrarily.
- Confidence calibration: stratified sampling, accuracy **by document type and by field**, not only aggregate.

### Docs
- Long context tips: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips
- Reduce hallucinations: https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- Context management in Claude Code: https://docs.anthropic.com/en/docs/claude-code/common-workflows
- Sessions + `--resume`: https://docs.anthropic.com/en/docs/claude-code/manage-sessions

### Videos
- Search: https://www.youtube.com/results?search_query=anthropic+long+context+prompting
- Search: https://www.youtube.com/results?search_query=claude+multi+agent+provenance+citations

### Hands-on (Exercise 4 from exam guide)
1. Coordinator + 2 subagents with `allowedTools: ["Task", ...]`; all inter-agent context passed explicitly in prompts.
2. Parallel Task calls in one coordinator turn — measure latency vs sequential.
3. Subagents emit `{ claim, evidence, source_url, publication_date }` objects.
4. Simulate a subagent timeout → coordinator gets structured error → annotates "coverage gap" in final report.
5. Feed conflicting stats from 2 sources → synthesis preserves **both** with attribution.

### Self-quiz
- Any question about escalation, error propagation, or conflicting sources.

---

## Week 6 — Consolidation & practice exam

### Monday–Wednesday — domain drills
- Re-read the "Knowledge of" bullets for every task statement. Make a flashcard for any bullet you can't explain out loud in 20 seconds.
- Flashcard tools: [Anki](https://apps.ankiweb.net/) or a plain Markdown cheat-sheet.

### Thursday — scenario simulation
Pick 4 of the 6 exam scenarios (customer support, code gen, multi-agent research, dev productivity, CI/CD, structured extraction). For each, write a one-page answer to: "What are the top 5 reliability risks and the one correct mitigation for each?"

### Friday — **take the practice exam** (link provided by Anthropic / your certification portal).
- Review every wrong answer. For each: which task statement did it test? Add the gap to your flashcards.

### Saturday — weakest-domain deep dive
Your practice-exam score by domain tells you where to spend the last day. Default: re-do Exercise for whichever domain you scored lowest on.

### Sunday — light review + sit the exam.

---

## Fast reference: the "wrong answer" patterns

The sample questions reward recognizing these anti-patterns in distractors:

| Anti-pattern | Why it's wrong |
|---|---|
| "Add to the system prompt that X is mandatory" | Probabilistic, non-zero failure rate. Use a **hook / programmatic gate** for deterministic compliance. |
| "Have the model self-report confidence 1–10" | LLM self-reported confidence is miscalibrated — especially on hard cases. |
| "Use sentiment analysis to trigger escalation" | Sentiment ≠ case complexity. |
| "Switch to a bigger context window" | Attention quality doesn't scale with window size. Split into passes instead. |
| "Return a generic 'operation failed' on error" | Kills recovery. Always return structured error context. |
| "Empty result set on timeout (mark as success)" | Silent suppression. Caller can't distinguish "no matches" from "I failed". |
| "Retry with exponential backoff forever" | Useless when the info is absent from source. |
| "Give every agent every tool" | 18 tools ≫ 4–5 tools degrades selection. Scope per role. |
| "Have the same session that wrote the code review it" | Self-review retains reasoning bias. Use an independent instance. |
| "Use Message Batches for blocking pre-merge checks" | 24 h window, no SLA. Batch is for overnight/weekly only. |

Internalize these — probably 4–6 exam questions test exactly these traps.

---

## Stretch reading (if you have extra time)

- "How we built our multi-agent research system" — https://www.anthropic.com/engineering/built-multi-agent-research-system
- "Building effective agents" — https://www.anthropic.com/research/building-effective-agents
- Anthropic Academy / courses repo — https://github.com/anthropics/courses (look for `tool_use` and `prompt_engineering_interactive_tutorial`)
- MCP example servers — https://github.com/modelcontextprotocol/servers

---

## Minimum viable prep (if you have only 1 week)

1. Read the exam guide PDF twice.
2. Do Exercises 1 and 3 only.
3. Read the 10-row "wrong answer patterns" table daily.
4. Watch 1–2 Anthropic videos on multi-agent research + tool use.
5. Take the practice exam; review every miss against the task-statement index in the guide.

Good luck.
