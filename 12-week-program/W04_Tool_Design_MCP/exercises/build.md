# Build — Tool Design & MCP

**Time:** 40 min · **Goal:** Draft a scoped 3–5 tool catalog for one concrete agent — with rich descriptions, structured errors, and a chosen `tool_choice` mode.

## What you'll have at the end
- `exercises/my_tools.py` — 3–5 tool schemas with input/output contracts, positive + negative boundaries, and error shapes in each description
- A one-line `tool_choice` decision and a written split-vs-consolidate verdict at the top of the file

## Prereqs
- Python 3.10+ (no SDK needed — this is a schema-design exercise, not a runtime one)
- Finished reading [reference.md](../reference.md) §1–§5
- Target: `exercises/my_tools.py` with 3–5 well-designed tool schemas (peek at [minimal_tool_descriptions.py](minimal_tool_descriptions.py) if stuck)

## Steps

### 1. Pick a concrete scenario (~4 min)
Write one scoped agent role at the top of `my_tools.py` as a comment. Pick a role you can describe in 2 sentences — e.g. "refund subagent for an e-commerce support flow", "inventory subagent", "PR-triage subagent".
- [ ] State: domain, user-visible job, what's out of scope (delegated elsewhere)
- [ ] Name 3–5 candidate tools (not 6+, not 2)

**Why:** §4 — 4–5 tools per agent max; selection degrades past that.
**Checkpoint:** The out-of-scope sentence names a sibling subagent you'd delegate to instead of piling on tools.

### 2. Draft each tool's description with all six clauses (~10 min)
For each tool, write a description that names, in order: (1) what it does, (2) input shape with a concrete example, (3) return shape with key names, (4) one scenario when to use it, (5) one scenario when NOT to use it and which tool to use instead, (6) the error shape it may return.
- [ ] Example target: a `search_customers` tool whose description names what it accepts (`email` or `customer_id`), what it returns (`{customer_id, name, email, tier}`), one scenario when to use it ("user provides an email or ID"), one when NOT to ("do NOT use for order lookup — use `get_order`")
- [ ] Every description ~6–10 lines long; terseness is the wrong trade

**Why:** §1 — the description is the selector; negative boundary is the highest-leverage clause.
**Checkpoint:** Each description contains the literal phrase "Do NOT use this" pointing at a sibling tool or a user-clarification path.

### 3. Lock down `input_schema` precision (~5 min)
Match the input schema to the description. If the description says "7-char alphanumeric SKU like 'ABX-0042'", the schema's `sku.description` says the same thing. Required fields are actually required.
- [ ] Every property has a `description` (not just a `type`)
- [ ] `required` list is explicit — no optional sneaking in as "kind of required"

**Why:** §1 — input format precision stops the model from inventing malformed inputs (which then trigger `validation` errors that §3 says you shouldn't retry).
**Checkpoint:** Pasting any tool's `input_schema` into a reviewer tells them the exact input shape without reading the description.

### 4. Split-vs-consolidate pass (~5 min)
Scan your 3–5 tools for near-similar pairs. For each pair, decide: consolidate (delete one), sharpen (keep both with explicit negative boundaries pointing at each other), or split (if one tool has a `mode` enum, break it into separately-named tools).
- [ ] Write a one-line verdict comment above each ambiguous pair: `# KEEP BOTH: check_stock is real-time, lookup_sku is static metadata — negative boundaries in each point to the other`
- [ ] If any tool has `action: "create" | "delete" | "lookup"`, split it now

**Why:** §2 — mega-tools with mode enums hide intent from the selector; duplicates always pick the loser sometimes.
**Checkpoint:** You can state out loud, for each pair, the one-sentence distinction a user would hear.

### 5. Wire structured error fields into every description (~8 min)
Each tool's description ends with its error contract. Every error response shape your tool can emit must be named (at least the category and retryability). Use this shape exactly:

```python
{"isError": True, "errorCategory": "not_found",
 "isRetryable": False, "message": "SKU 'ABX-0042' not found."}
```

- [ ] Each tool names which `errorCategory` values it may return (`validation`, `not_found`, `timeout`, `policy`, `internal`)
- [ ] `isRetryable` is set per category, not hand-waved — `timeout` = true; `validation`/`not_found`/`policy` = false

**Why:** §3 — `isRetryable` is load-bearing; without it, retry logic either parses strings or retries forever on unfixable errors.
**Checkpoint:** Reading any description, you know exactly which failures your retry loop should fire on.

### 6. Pick `tool_choice` per use case (~4 min)
Add a top-of-file comment: `TOOL_CHOICE = {"type": "auto"}` (or `"any"`, or forced-specific) with a one-line justification tying the choice to the agent's job.
- [ ] Default to `auto`. Only pick `any` or forced-specific if this is a scripted/extraction step
- [ ] If you're reaching for `any` because selection feels shaky, go back to Step 2 and fix the description

**Why:** §5 — forcing `tool_choice` is a band-aid for weak descriptions, not a cure.
**Checkpoint:** Your justification references the agent's job, not "to make sure the model picks the right tool".

### 7. Compare against the minimal reference (~4 min)
Open [minimal_tool_descriptions.py](minimal_tool_descriptions.py). Read the `GOOD_TOOLS` list end-to-end, close the file, then re-read your descriptions.
- [ ] For each of your tools, confirm all six clauses from Step 2 are present
- [ ] Fix any you skimmed past

**Why:** §1 — the six-clause pattern is what distinguishes selectable from ambiguous.
**Checkpoint:** Your file is shorter in scope (3–5 tools) but per-tool description quality matches the reference.

## Verify
Review your 3–5 tool schemas. Check:
- Every description contains an explicit "Do NOT use this for X — use `Y` instead" clause (§1, §2)
- Near-similar tools are either consolidated or each description's negative boundary names the sibling by name (§2)
- Every tool names its `errorCategory` values and the `isRetryable` verdict per category (§3)
- Tool count is 3–5; out-of-scope work is named as a delegated sibling, not added as a 6th tool (§4)
- `tool_choice` is `auto` unless there's a scripted-extraction justification written down (§5)

**Common mistakes:**
- One-sentence descriptions that "save tokens" → §1 (selection collapses; wrong trade)
- Two tools with overlapping jobs and no negative boundary pointing at each other → §2
- A single tool with `action: "lookup" | "create" | "delete"` enum input → §2 (split it)
- Returning `"operation failed"` strings instead of the four-field error shape → §3
- Forcing `tool_choice: "any"` to compensate for ambiguous descriptions → §5

## Stretch — Polish block (30 min on Practice Day)
From the Polish row of [week_plan.md](../week_plan.md): wire a local MCP server using `.mcp.json`.
- [ ] Create `.mcp.json` at the repo root declaring one server (stdio `command` + `args`)
- [ ] Use `${ENV_VAR}` expansion for any secret (API key, DB URL) — never inline the literal value (§6)
- [ ] Decide scope: project (`.mcp.json`, committed) vs user (`~/.claude.json`, personal). Team-shared → project (§6)
- [ ] Classify each capability you expose: action with side effects = **tool**; read-only static content = **resource** (§7)
- [ ] Sanity-check: would a community MCP server already cover this? If yes (Jira/GitHub/Postgres/Slack/...), use the community one instead of writing custom (§6)

## If stuck
Compare with [minimal_tool_descriptions.py](minimal_tool_descriptions.py). Read → close → rewrite.
