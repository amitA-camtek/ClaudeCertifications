# Practice Test 4 — Tool Design & MCP

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 2.1–2.5

## Instructions
Solve all 10 questions before opening `test4_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A developer defines a tool as `{"name": "lookup", "description": "Looks up a product."}` and ships it alongside three other similarly-terse tools. At runtime the model often picks the wrong tool or fails to call one at all. According to the reference, what is the single most impactful fix?
- A. Add a system prompt instruction: "always use `lookup` for product questions."
- B. Set `tool_choice: {"type": "any"}` to force the model to call some tool.
- C. Rewrite the description to specify input format/examples, return shape, and positive + negative boundaries — even though it will be ~8× longer.
- D. Rename the tool to `product_lookup` so the name itself carries the intent.

### Q2. An inventory team has two tools: `check_stock` (real-time warehouse count) and `check_availability` (includes backorder ETA). They are genuinely different but the model sometimes swaps them. What does the reference recommend?
- A. Consolidate them into a single `check_inventory` tool with a `mode` enum.
- B. Delete `check_availability` — duplicate-ish tools always pick the loser sometimes.
- C. Keep both, and sharpen each description with explicit negative-boundary clauses ("Do NOT use this for X; use Y instead").
- D. Keep both and set `tool_choice: {"type": "tool", "name": "check_stock"}` at every turn.

### Q3. A tool returns `{"isError": True, "message": "operation failed"}` on every failure mode. The agent retries forever on malformed SKUs and never escalates on policy denials. Which fields from the reference's minimal structured-error shape are missing and would fix this?
- A. `stack_trace` and `http_status`
- B. `errorCategory` and `isRetryable`
- C. `success` and `fallback_tool`
- D. `severity` and `retry_count`

### Q4. A developer bundles `lookup_sku`, `create_sku`, and `delete_sku` into a single tool `sku_tool` with an input `action: "lookup" | "create" | "delete"`. The agent frequently misroutes (e.g., calls it with `action="delete"` when the user asked to look up). What is the design issue per §2?
- A. Enums are not supported in JSON Schema for MCP tools.
- B. The model selects against tool names and descriptions, not enum values inside inputs — modes hide the intent from the selector. Split into separately-named tools.
- C. The tool has too few parameters; adding more would make intent clearer.
- D. The `action` enum needs a default value so the model doesn't have to pick.

### Q5. A coordinator agent has been given direct access to the union of every MCP server's tools — 18 tools in total. Selection accuracy has dropped sharply. What does the reference prescribe?
- A. Increase the system prompt length so each tool is named explicitly in the instructions.
- B. Force `tool_choice: {"type": "any"}` so the model always calls something.
- C. Scope to 4–5 tools per agent; have the coordinator delegate cross-domain work to specialist subagents, each with their own scoped list.
- D. Keep all 18 — flexibility is the priority; selection accuracy is a secondary concern.

### Q6. A team wants to integrate Jira into their Claude Code agent. A community-maintained Jira MCP server exists. What does the reference recommend as the default approach?
- A. Always write a custom MCP server for standard integrations so you control every tool description.
- B. Use the community Jira MCP server; write custom only when the integration is team-specific or a real gap exists that can't be upstreamed.
- C. Skip MCP entirely for Jira and call the Jira REST API from Bash.
- D. Expose Jira as an MCP resource instead of a tool.

### Q7. Which of the following correctly classifies MCP tools vs MCP resources?
- A. `place_order` → resource; the company style guide PDF → tool.
- B. `send_email` → resource; the API reference doc → tool.
- C. `run_query` → tool; the company style guide PDF → resource.
- D. All MCP capabilities are exposed as resources; tools is a legacy term.

### Q8. A developer wants to add a shared MCP server for the team's internal order-management system so every dev who clones the repo gets it automatically. The server needs an API key that must NOT be committed. What is the correct configuration per §6?
- A. Put the server in `~/.claude.json` and email the API key to teammates.
- B. Put the server in `.mcp.json` at the repo root with the literal key `"INVENTORY_API_KEY": "sk-abc123..."` so it Just Works.
- C. Put the server in `.mcp.json` at the repo root, and reference the secret via `${INVENTORY_API_KEY}` env-var expansion; keep the actual value in each dev's env/secret manager.
- D. Put the server in `.mcp.json` with no env at all — API keys are not needed because MCP handles auth.

### Q9. The user asks Claude Code to find every file in the repo that imports `pandas`. Per §8's selection cheatsheet, which built-in tool is correct?
- A. Glob with pattern `import pandas` — Glob searches file contents for the pattern.
- B. Bash running `cat` on every `.py` file and piping through a string match.
- C. Read on each `.py` file individually.
- D. Grep — it searches file contents for a regex or string.

### Q10. An engineer proposes: "On every error, retry with exponential backoff up to 5 attempts. Keep tool error responses as short strings like `'failed'` so descriptions stay cheap." According to the reference, which critique is correct?
- A. The plan is fine; generic strings plus blanket retries is the standard pattern.
- B. The retry plan is fine but descriptions should be even terser (one word) to save tokens.
- C. Both pieces are anti-patterns: retries should branch on a typed `isRetryable` field (not fire on `validation`/`not_found`/`policy`), and error responses should be structured (`isError`, `errorCategory`, `isRetryable`, friendly `message`) — not generic strings.
- D. Only the retry plan is wrong; generic error strings are actually recommended so the model can paraphrase freely.

## Your answers
| Q  | Answer |
|----|--------|
| 1  |        |
| 2  |        |
| 3  |        |
| 4  |        |
| 5  |        |
| 6  |        |
| 7  |        |
| 8  |        |
| 9  |        |
| 10 |        |
