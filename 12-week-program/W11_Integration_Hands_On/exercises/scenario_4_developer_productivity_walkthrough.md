# Scenario 4 walkthrough — Developer Productivity with Claude

Scenario 4 from the exam guide covers an agent that helps engineers **explore unfamiliar codebases, understand legacy systems, generate boilerplate code, and automate repetitive tasks** using the built-in Claude Code tools (Read, Write, Edit, Bash, Grep, Glob) plus MCP server integrations.

Primary domains tested: **Tool Design & MCP Integration**, **Claude Code Configuration & Workflows**, **Agentic Architecture & Orchestration**.

This walkthrough isn't runnable code — it's a mapping of the scenario to the W01–W10 concepts and the exam-critical judgment calls a candidate must make. The other four exam exercises already have runnable code in `exercise_1_*` through `exercise_4_*`; this file fills the Scenario-4 gap at the same level of detail.

---

## The setup

A new engineer joins a team and needs to:

1. **Understand** an unfamiliar service — say, the refund-processing module.
2. **Trace** where a specific error message is coming from.
3. **Generate** boilerplate tests for a new handler.
4. **Automate** a repetitive task (e.g., bumping a version number across 14 files).

Claude Code is available, with built-in tools and one or two MCP servers wired up (Jira for ticket lookup, Postgres for schema inspection — both **community servers**, per W04).

---

## Task 1 — Understand the refund module

**Wrong instinct:** load every file in `src/refunds/` into context via `Read`. Token budget collapses; attention dilutes (W09 lost-in-the-middle).

**Right approach (W04 §8 — built-in tools):**

- Start with **Grep** to find the entry point:
  ```
  grep -r "def process_refund" src/refunds/
  ```
- **Read** only that entry-point file fully.
- Follow imports using **Grep** again on imported symbol names.
- Use **Glob** (e.g., `**/*_test.py`) to find the tests — tests document behavior better than prose comments.
- Only `Read` full files *after* you've found the 3–5 that matter.

This is the **Grep → Read → follow imports → selective Read** loop. Build understanding incrementally; never load upfront.

---

## Task 2 — Trace the error message

**Wrong instinct:** ask Claude *"what causes error X?"* — hallucination risk high (Claude confabulates plausible-sounding but fictional causes).

**Right approach:**

- **Grep** the literal error string across the repo.
- For each match, `Read` enough surrounding lines to see the condition that raises it.
- If the error is a rethrow, recurse: `Grep` the lower-level exception or message.

This is a **fact-finding** workflow. Claude's strength is reading code fast; its weakness is inferring code it hasn't read. Always Grep first, then read, then reason.

---

## Task 3 — Generate boilerplate tests

**Wrong instinct:** plan-mode for a single test file. Overkill (W06 §1).

**Right approach (W06 §1 — plan mode vs direct execution):**

- **Direct execution.** Scope is clear and bounded: *"add tests for `process_refund` covering the happy path, a decline, and a retry."*
- Use **Edit** if the test file exists; **Write** if it's new.
- If `Edit` fails because the anchor text isn't unique, fall back to `Read` + `Write` (W04 §8).

---

## Task 4 — Automate version bumps across 14 files

**Wrong instinct:** `Grep` + manual `Edit` × 14. Boring, error-prone, and wastes an LLM on a deterministic transformation.

**Right approach:**

- Still **direct execution** — scope is bounded, the transformation is mechanical.
- Use **Bash** to run a one-off script (`sed`, a short Python snippet) rather than iterating `Edit` 14 times.
- For deterministic mechanical transformations, a shell command is more reliable than a tool loop — and much cheaper.

This is the W04 tool-selection rule applied: **use Bash when the transformation is deterministic; reserve Read/Write/Edit for work that needs code comprehension.**

---

## Where MCP fits

If the team has community MCP servers wired up (W04 §6):

- **Jira MCP server** → Claude can call `jira.get_issue(ticket_id)` to pull the bug description the engineer is working from. No screenshots, no copy-paste.
- **Postgres MCP server** → Claude can introspect `information_schema` to know the real table shape before generating a query. No guessing column names.

These MCP tools are **scoped cross-role tools** (W04 §4): the agent uses them alongside the built-ins; they don't replace them. The agent's effective tool set stays tight — **4–5 tools max** — even when MCP tools are available. Over-provisioning an agent with 15 tools degrades selection quality, and that rule doesn't relax just because the tools come from MCP.

### Why community MCP servers, not custom

For Jira, Postgres, GitHub, Slack, etc., community MCP servers already exist. Use them. A custom MCP server is only justified for **team-specific** systems (internal order DB, bespoke analytics warehouse, proprietary compliance workflow). Reinventing a standard integration ships worse tool descriptions than the community version and wastes team time.

---

## Exam-critical judgment calls in Scenario 4

1. **Grep before Read.** Scenario 4 questions reward incremental exploration and punish "load everything up front."
2. **Direct execution unless the task is architectural.** Plan mode for boilerplate generation or repetitive changes is a distractor.
3. **Bash for mechanical transformations.** Don't loop the model for a regex replace — use a shell command.
4. **Read + Write when Edit can't find a unique anchor.** Don't force `Edit` with vague text matching; it'll either fail or quietly match the wrong occurrence.
5. **Community MCP servers over custom** (W04). If the scenario describes a Jira / GitHub / standard integration, the correct answer is the community server, not "let's write our own."
6. **Scoped tool sets.** Even with built-ins + MCP, don't hand every agent every tool. 15+ tools → degraded selection.

---

## Distractor patterns specific to Scenario 4

| Wrong answer | Why it's wrong | Correct approach |
|---|---|---|
| "Read every file in the module to build understanding" | Context bloat; lost-in-the-middle | Grep → Read selectively |
| "Use plan mode for the test-boilerplate task" | Plan mode is for architectural / multi-file / ambiguous scope | Direct execution |
| "Write a custom MCP server for Jira" | A community one exists | Community MCP server; custom is for team-specific systems only |
| "Loop Claude 14 times to bump the version number" | Deterministic mechanical work shouldn't waste model calls | Bash / script |
| "Give the productivity agent every built-in tool plus 4 MCP servers" | 15+ tools degrades selection | Scope tightly; add MCP selectively |
| "Ask Claude what the code does before reading the code" | Hallucination risk | Always Grep + Read first, then reason |

---

## How this scenario ties into W01–W10

| Concept from | How it applies here |
|---|---|
| W01 agentic loop | Every tool call round-trips through `stop_reason` — same mechanics as any agent |
| W02 subagent delegation | For large exploration, delegate via `Task` to an Explore subagent so verbose output stays out of main context |
| W04 tool descriptions, built-ins, scoped tools | The whole scenario is a built-in-tools workout |
| W05 CLAUDE.md | Project conventions live in CLAUDE.md so the productivity agent picks the right imports, test style, etc. |
| W06 plan mode vs direct | Pick correctly per task size |
| W09 context management | Grep/Read selectively; trim verbose outputs; case-facts for long exploration sessions |
| W10 scratchpad + `/compact` | For multi-hour exploration, scratchpad durable findings; `/compact` when context fills with verbose tool output |

---

## Practice prompt

Pick a real (or simulated) service module with 20+ files. For each of the four tasks above, write one paragraph answering: *"Which sequence of built-in tools would I use, and why?"*

This is exactly the reasoning the Scenario 4 exam questions will test — proportionate tool choice, incremental exploration, deterministic mechanism over prompt guidance.
