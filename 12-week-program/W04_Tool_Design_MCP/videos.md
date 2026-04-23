# W04 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** tool descriptions as selector, structured errors, `tool_choice` modes, `.mcp.json` vs `~/.claude.json`, MCP tools vs resources, built-in tool selection.

---

## Talk 1 — MCP Introduction (Mahesh Murag and others)

- **What MCP is.** A protocol spec for exposing tools and resources to LLM clients. Think of it as "USB-C for agents": the server describes what it offers; the client (Claude Code, Claude Desktop, any agent) picks it up without bespoke integration.
- **Tools vs resources — the distinction the exam loves:**
  - **Tools** = actions the model invokes with arguments. `create_ticket`, `search_inventory`, `issue_refund`. They have side effects or return computed results.
  - **Resources** = content the client can read into context. A product catalog, a document, a knowledge base. Static-ish; the client fetches them; no argument dispatch.
  - **Distractor:** "Expose the product catalog as a `lookup_product` tool." For a catalog the model needs to browse, a resource is usually better — you're not dispatching on arguments, you're providing content.
- **Transport modes:** stdio (local subprocess), SSE over HTTP (remote). Local servers for filesystem/git/shell; remote for API wrappers behind auth.
- **Configuration:**
  - **`.mcp.json`** in the project root, committed to git — **team** servers (shared tools everyone needs).
  - **`~/.claude.json`** in the home directory — **personal** servers (your Linear token, your Jira).
  - Both can coexist simultaneously. Projects using both is the normal case, not an exception.
- **`${ENV_VAR}` expansion** in `.mcp.json` is how secrets avoid the repo. `"token": "${GITHUB_TOKEN}"` reads from the process environment at startup.

---

## Talk 2 — Tool descriptions are the primary selector

- **The model picks tools from descriptions, not names.** If you have `search_v1` and `search_v2` with terse descriptions, the model will guess — often wrong. If you have `search_customer_by_email_v1` with "Use this when you have a valid email address; returns at most 1 match; fails with `invalid_email` if format is wrong" the model picks correctly every time.
- **A well-formed description has four things:**
  1. What the tool does, in one sentence.
  2. Input expectations (formats, valid ranges, required vs optional).
  3. Output shape (what comes back, what an empty result looks like).
  4. Boundaries — **when NOT to use it.** This is the field everyone skips, and it's what resolves "which of these two similar tools" questions.
- **Near-similar tools: split or consolidate?**
  - **Split** if the decision criterion is simple and stable (email vs phone lookup).
  - **Consolidate** if the criterion is fuzzy (returns "nearest match" either way). Two fuzzy tools + the model guessing between them is worse than one tool with a clear argument.
- **4–5 tools per agent is the sweet spot.** Past ~7, selection accuracy degrades noticeably. Past ~15, selection is essentially a coin toss. Scope tools to the role.

---

## Talk 3 — Structured errors, not strings

- **The contract:** tools should return `{ isError: true, errorCategory: "timeout" | "invalid_input" | "policy_violation" | ..., isRetryable: bool, message: "..." }`.
- **Why it matters:** the model (or your retry wrapper) branches on `isRetryable`, not on string parsing. "Rate limited" vs "rate-limited" vs "429 too many requests" is a fragile distinction; `errorCategory: "rate_limit"` is not.
- **Anti-patterns:**
  - Returning a generic `"operation failed"` → model can't tell recoverable from permanent.
  - Returning an empty result on timeout → silent suppression. Caller can't distinguish "no matches" from "I crashed."
  - Raising a Python exception that becomes a tool-use failure → the model sees nothing useful and often retries blindly.

---

## Talk 4 — `tool_choice` and built-in tool selection

- **`tool_choice` modes:**
  - `"auto"` — model decides; may skip tool use entirely. Default.
  - `"any"` — model **must** call some tool this turn. Right when you've guaranteed at least one tool is needed.
  - `{"type": "tool", "name": "..."}` — force a specific tool. Right for structured-output via `tool_use` (see W07).
- **Built-in tools in Claude Code — choose intentionally:**
  - **Read** for a single known path. Not for "find a file" (that's Glob).
  - **Grep** for content search by regex. Not for "files matching a name pattern" (that's Glob).
  - **Glob** for filename patterns.
  - **Bash** as last resort. Running `find` or `grep` via Bash when Glob/Grep exist is an anti-pattern — worse UX, inconsistent output, permission prompts.
  - **Edit** over Write for modifications. Write is for new files or full rewrites.

---

## Optional external viewing

- Search — MCP tutorial: https://www.youtube.com/results?search_query=model+context+protocol+MCP+tutorial
- Search — Claude tool use JSON schema: https://www.youtube.com/results?search_query=claude+tool+use+json+schema
- MCP example servers: https://github.com/modelcontextprotocol/servers
