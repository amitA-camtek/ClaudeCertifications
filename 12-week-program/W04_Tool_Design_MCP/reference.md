# W04 Reference — Tool Design & MCP Integration (Domain 2.1–2.5)

Complete, self-contained study material for Week 4. Read this end-to-end. Every concept the exam tests for task statements 2.1–2.5 is here.

Prerequisites: W01 (agentic loop, `tool_choice`) and W02 (tool scoping per subagent). Tool design is the lever that decides whether a correctly-shaped loop actually picks the right action.

---

## 1. Tool descriptions are the primary selection signal

When the model has N tools available, it picks one by reading the `description` field. Not the `name`, not your system prompt, not hope — the description.

A bad description = the model picks the wrong tool, or picks no tool when it should have. A system prompt saying "always use `get_stock` for inventory questions" is a probabilistic hint. A good description is a **specification** that makes the right choice obvious.

### What a good description contains

1. **What the tool does**, in one clause.
2. **Input format** — be explicit about shape, units, examples ("`sku` is a 7-character alphanumeric like `ABX-0042`").
3. **Output format** — what the model will see back. Shapes, key names, whether nulls are possible.
4. **Positive boundary** — "Use this for X" with a concrete scenario.
5. **Negative boundary** — "Do NOT use this for Y; use `other_tool` instead." This is the single highest-leverage addition for disambiguating near-similar tools.
6. **Error behavior** (if meaningful) — "Returns `{isError:true, errorCategory:'not_found'}` when the SKU doesn't exist."

### Bad vs good — worked example

```python
# BAD
{"name": "lookup", "description": "Looks up a product."}

# GOOD
{
  "name": "lookup_sku",
  "description": (
    "Look up a product by its SKU. "
    "Input: `sku`, a 7-character alphanumeric code like 'ABX-0042'. "
    "Returns: {name, category, unit_price_usd, is_discontinued}. "
    "Use this when the user mentions a SKU or product code. "
    "Do NOT use this to check current stock levels — use `check_stock` for that. "
    "Returns {isError:true, errorCategory:'not_found'} if the SKU doesn't exist."
  ),
}
```

The good version is ~8× longer. **Tokens spent on descriptions are the best-spent tokens in your whole prompt.** A terse description that "saves tokens" costs you selection accuracy on every call for the life of the agent. That is the wrong trade.

### Exam distractor pattern

"To save tokens and speed up the agent, keep tool descriptions terse (one sentence, no examples)." — **wrong**. Selection quality collapses. Distractors exploit the intuitive-but-wrong token-frugality argument.

---

## 2. Split vs consolidate — disambiguating near-similar tools

Two tools whose job overlaps confuse the model. You have three levers:

| Situation | Fix |
|---|---|
| `search_orders` and `find_order` do the same thing | **Consolidate.** Delete one. Duplicate tools always pick the loser sometimes. |
| `check_stock` (real-time warehouse) and `check_availability` (includes backorder ETA) — truly different | **Keep both, but sharpen descriptions** with explicit negative boundaries in each: "Do NOT use this for X; use `Y` instead." |
| One mega-tool with a `mode` enum (`action="lookup" | "create" | "delete"`) | **Split** into `lookup_sku`, `create_sku`, `delete_sku`. The model selects against tool *names and descriptions*, not enum values inside inputs. Modes inside one tool hide the intent from the selector. |

**Rule of thumb:** if you can't write the negative-boundary clause without contorting it, the two tools probably shouldn't both exist — consolidate.

---

## 3. Structured error responses

A tool's return value is an input to the model's next reasoning turn. Generic errors (`"operation failed"`) strand the model — it can't tell if it should retry, pick a different tool, ask the user, or escalate. Structured errors tell it.

### The minimal shape

```python
{
  "isError": True,
  "errorCategory": "timeout",       # enum-style, see below
  "isRetryable": True,               # boolean — drives retry logic deterministically
  "message": "The warehouse API didn't respond within 5s. It's usually transient.",
  # plus any useful context the model can act on:
  "attempted_sku": "ABX-0042",
  "retry_after_seconds": 2,
}
```

### `errorCategory` values the exam cares about

| Category | Meaning | Typical `isRetryable` | Typical model response |
|---|---|---|---|
| `validation` | Input was malformed (bad SKU format, missing field) | `False` | Don't retry blindly. Re-read input, fix, try again — or ask the user. |
| `not_found` | Well-formed request, target doesn't exist | `False` | Ask user for clarification; don't loop. |
| `timeout` | Upstream was slow, no verdict yet | `True` | Retry (bounded). Inform user if it persists. |
| `policy` | Action refused by business rule (refund > threshold, after-hours op) | `False` | Escalate or explain policy to user. Retrying will not help. |
| `internal` | Bug on our side | Usually `False` | Surface clearly; don't pretend success. |

### Why `isRetryable` is load-bearing

Without it, the model (or your loop code) has to parse the message string to decide whether to retry. That's probabilistic. **With it, retry is a deterministic branch** on a typed field.

```python
if result.get("isError"):
    if result.get("isRetryable") and attempts < 3:
        # deterministic retry
        ...
    else:
        # surface to model / user
        ...
```

### The `message` field

Keep it user-friendly enough that the model can paraphrase it straight to the user. Avoid stack traces and internal error codes. The model will copy the tone of what you return.

### Exam distractor pattern

"On error, return a generic string like `'operation failed'` so the model can decide what to do." — **wrong**. You've destroyed every signal needed to decide. Retries fire when they shouldn't; escalation is missed; users get "something went wrong" with no recourse.

---

## 4. Tool distribution per agent (scope)

**Hard rule: 4–5 tools per agent, maximum. More degrades selection.**

As the tool count rises:
- Descriptions compete for attention. Near-similar pairs blur.
- Total token cost of the tool catalog grows on every call.
- Selection accuracy drops measurably past ~6–7 tools.

### Scoping per role (the W02 tie-in)

A coordinator needs `Task`, possibly `Read`/`Write`. A refund subagent needs `get_order`, `get_customer`, `get_refund_policy`, `issue_refund`, `escalate_to_human` — exactly 5. An inventory subagent needs `lookup_sku`, `check_stock`, `place_order`, `cancel_order` — exactly 4.

Never hand one agent the union of every MCP server's tools. If the coordinator needs inventory *and* refunds, it delegates to specialist subagents, each with their own scoped list.

### Exam distractor pattern

"Give every agent access to every tool so it has maximum flexibility." — **wrong**. Flexibility is not the bottleneck; **selection** is. Scoping is the fix.

---

## 5. `tool_choice` — quick refresher with the W04 angle

From W01, refreshed:

| `tool_choice` | Behavior | When to use |
|---|---|---|
| `{"type": "auto"}` (default) | Model decides | General agent loops |
| `{"type": "any"}` | Must call *some* tool | Structured-output extraction where you want a tool call even if the model is tempted to just write prose |
| `{"type": "tool", "name": "X"}` | Must call this specific tool | Scripted steps; one-shot extraction through a known schema tool |
| `{"type": "none"}` | Cannot call any tool | Final synthesis turn where you don't want more actions |

**W04-specific angle:** when tool descriptions are well-written, `"auto"` works. When you're reaching for `"any"` or forced-specific to "make the model pick the right tool", ask first whether the description is actually telling the model how to choose. Often forcing is a band-aid for a bad description.

---

## 6. MCP — what it is, what's in scope for the exam

**Model Context Protocol (MCP)** is how external systems expose tools (and resources) to a Claude agent without you having to write in-process Python for each one. An MCP server runs as its own process; Claude Code (or the Agent SDK) connects over stdio or HTTP and discovers its tools.

For the exam, you must know:

- How to declare an MCP server in config.
- Scope: project vs user.
- Secrets via `${ENV_VAR}` expansion.
- Tools vs resources.

You do **not** need to memorize the MCP wire protocol.

### `.mcp.json` (project) vs `~/.claude.json` (user)

| File | Scope | Use when |
|---|---|---|
| `.mcp.json` (at repo root) | **Project** — shared with every dev who clones the repo | The tool is part of the project (team DB, project issue tracker). Checked into git. |
| `~/.claude.json` | **User** — personal to your machine | Personal tools (your own scratchpad, personal GitHub token scope). Not committed. |

If both exist and declare the same server, project config wins for that project.

### `${ENV_VAR}` expansion — secrets

Never commit secrets. MCP config supports environment-variable expansion so the config file stays safe to share:

```json
{
  "mcpServers": {
    "inventory": {
      "command": "python",
      "args": ["-m", "inventory_mcp"],
      "env": {
        "INVENTORY_API_URL": "${INVENTORY_API_URL}",
        "INVENTORY_API_KEY": "${INVENTORY_API_KEY}"
      }
    }
  }
}
```

The literal string `${INVENTORY_API_KEY}` gets replaced by the environment value at load time. Commit the config; keep the env file uncommitted (`.env`, shell rc, secret manager).

### Exam distractor pattern

"Embed the API key directly in `.mcp.json` and check it into the repo." — **wrong**. Use `${ENV_VAR}` expansion.

### Community MCP servers vs custom implementations

For any **standard integration** (Jira, GitHub, GitLab, Postgres, Sentry, S3, Slack, Linear, ...) there's almost certainly a community-maintained MCP server already. Use it. Do not write your own.

Community servers give you:
- Tools iterated on and debugged by many users against the real API.
- Descriptions refined over many PRs (which matters — see §1).
- Bug reports and improvements you don't have to make yourself.

Write a **custom MCP server** only when:
- The integration is **team-specific** — your internal order-management system, your bespoke analytics warehouse, your proprietary document store, your own compliance workflow.
- A community server exists but lacks a specific tool / resource you need *and* upstreaming isn't viable.

### Exam distractor pattern

"Build a custom MCP server for Jira integration to ensure team-specific behavior." — **wrong** in the default case. Use the community Jira MCP server first; fork/extend or write custom only when a real team-specific gap exists. Reinventing standard integrations wastes time and ships worse tool descriptions than the community version.

---

## 7. MCP *resources* vs MCP *tools*

Both are MCP concepts. They serve different purposes and the exam tests the distinction.

| | **Tools** | **Resources** |
|---|---|---|
| Purpose | **Actions** — do something, often with side effects | **Read-only content** — catalog of data Claude can attach to its context |
| Invocation | Model calls via `tool_use` | Claude Code attaches content by URI |
| Side effects | Yes (create, update, delete) | No |
| Examples | `place_order`, `send_email`, `run_query` | Company style guide, API docs, design spec, static schema catalog |

**Rule:** if the thing modifies state or executes a query with parameters, it's a **tool**. If it's "here's a fixed document the agent should be able to pull into context", it's a **resource**.

### Exam distractor pattern

"Expose `place_order` as an MCP resource so the agent can place orders." — **wrong**. Resources are read-only. Actions are tools. Getting this backward is a common distractor.

---

## 8. Built-in tools (Claude Code) — when each is correct

Claude Code ships with a fixed set of file/shell tools. Know which one is *correct* for a given job — using the wrong one is a recurring distractor.

| Tool | When it's correct | When it's wrong |
|---|---|---|
| **Read** | You already know the file path and want its contents (possibly a slice via `offset`/`limit`) | Searching across unknown files; finding files by name |
| **Grep** | Searching **file contents** for a regex or string | Finding files by filename pattern (that's Glob); reading a known file |
| **Glob** | Finding files whose **path** matches a pattern (`**/*.test.ts`, `src/**/*.py`) | Searching inside files (that's Grep) |
| **Bash** | Running shell commands, git ops, invoking test runners, any non-file action | File operations that have a dedicated tool (Read/Write/Edit/Grep/Glob) — the dedicated ones are safer and cheaper |
| **Edit** | **In-place** change to an existing file (string replacement) | Creating a new file; wholesale rewrite of a large file |
| **Write** | Creating a new file, or a full rewrite where Edit would need many replacements | Small targeted changes (use Edit) |

Quick selection cheatsheet:

- Know the path → **Read**.
- Know the filename pattern → **Glob**.
- Searching content → **Grep**.
- New file or full rewrite → **Write**.
- Patch existing file → **Edit**.
- Shell / git / anything else → **Bash**.

### Exam distractor pattern

"To find all files that import `pandas`, use Glob with pattern `import pandas`." — **wrong**. Glob matches *paths*, not contents. Use **Grep**.

---

## 9. Anti-patterns (these ARE the exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| "Terse tool descriptions save tokens and speed the agent" | Selection quality collapses; wrong tool picked on every ambiguous call | Rich descriptions: input, examples, positive + negative boundaries, return shape |
| "Return a generic `'operation failed'` string on error" | Breaks retry logic; model can't tell retryable from fatal | Structured error: `isError`, `errorCategory`, `isRetryable`, user-friendly `message` |
| "Retry on every error with exponential backoff" | Wastes budget on `validation` / `not_found` / `policy` errors that will never succeed | Branch on `isRetryable`; only retry what the server marked retryable |
| "Give every agent every tool for maximum flexibility" | Degrades selection past ~5–7 tools; context bloat; near-similar tools collide | Scope to 4–5 per role; delegate cross-domain work to specialist subagents |
| "Combine `lookup`, `create`, `delete` into one tool with a `mode` enum input" | Selector sees one tool; intent hidden in enum value; misrouting goes unnoticed | Split into separately-named tools with distinct descriptions |
| "Use `tool_choice: any` to force the model to pick the right tool" | Band-aid for a bad description; forces *a* tool, not the *right* one | Fix the description; use forcing only for genuinely scripted steps |
| "Expose an `place_order` action as an MCP resource" | Resources are read-only content, not actions | Expose actions as MCP **tools**; resources are for static/read-only catalogs |
| "Commit `INVENTORY_API_KEY=sk-...` directly into `.mcp.json`" | Secret leak into git history | Use `${ENV_VAR}` expansion; keep the secret in env / secret manager |
| "Use `~/.claude.json` for the team's shared project MCP server" | Each dev has to reconfigure; drift across the team | `.mcp.json` at repo root — project-scoped, committed |
| "Use Glob to search inside files" | Glob matches paths, not contents | Use **Grep** for content search |
| "Use Bash `cat` to read a file whose path you know" | Dedicated tool exists | Use **Read** — cheaper, safer, pageable |
| "Add to the system prompt: 'always use tool X for inventory'" | Probabilistic hint; model will sometimes skip | Fix the tool description so selection is obvious from the catalog alone |

Last-row theme (from W01, repeated): **deterministic mechanisms beat prompt instructions**. In W04 the deterministic mechanism is the tool *description* itself — it's part of the catalog the model always sees.

---

## 10. What the exam will probe

Based on exam guide task statements 2.1–2.5, expect:

- Given two candidate tool descriptions for the same tool, pick the better one (and know why).
- Given a tool that returns generic errors, identify which structured fields are missing and what a correct error object looks like.
- Scenario: "the agent keeps picking the wrong tool" — identify whether the fix is description, split/consolidate, or `tool_choice` (almost always description).
- Scenario: "the agent is retrying forever on bad inputs" — identify the missing `isRetryable=False` or `errorCategory=validation`.
- Given a task (find files by name / search content / edit a file), pick the correct built-in tool.
- `.mcp.json` vs `~/.claude.json` scope questions.
- MCP tool vs MCP resource classification.
- Secret handling via `${ENV_VAR}`.
- Tool-count questions: agent has 15 tools and misroutes — what's the fix? (Scope per role; delegate; don't pile all tools on one agent.)

---

## 11. Fast recap

- **Descriptions are the selector.** Input format, examples, positive + negative boundaries, return shape. Tokens spent here are the best-spent tokens in the prompt.
- **Split vs consolidate** by intent, not by clever enum inputs. Mega-tools hide intent from the selector.
- **Structured errors**: `isError`, `errorCategory` (`validation`/`not_found`/`timeout`/`policy`/`internal`), `isRetryable`, friendly `message`. Retry logic branches on `isRetryable`.
- **4–5 tools per agent.** Scope by role; delegate cross-domain work.
- **`tool_choice`**: `auto` by default; `any` / forced-specific for scripted extraction. Forcing is not a fix for bad descriptions.
- **`.mcp.json`** = project (committed); **`~/.claude.json`** = user (personal). Secrets via `${ENV_VAR}`.
- **MCP tools = actions; MCP resources = read-only content.** Don't swap them.
- **Built-ins**: Read (known path), Grep (content), Glob (paths), Edit (patch), Write (new/rewrite), Bash (everything else).

When you can explain each of those eight bullets out loud in ~20 seconds each, you're ready for the W04 test.
