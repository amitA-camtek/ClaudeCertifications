# W04 Study Day — Tool Design & MCP Integration (Domain 2.1–2.5)

## The one thing to internalize

**The tool `description` is the selector. Everything else — system prompt, `tool_choice`, naming — is secondary.**

If the model picks the wrong tool, the first fix is almost always "rewrite the description" (input format, examples, positive boundary, negative boundary, return shape). Not "add a rule to the system prompt." Not "force it with `tool_choice`." Descriptions are the deterministic layer the model always sees.

## Anti-patterns that appear as distractors on the exam

| Wrong answer | Why it's wrong |
|---|---|
| "Keep tool descriptions terse to save tokens" | Tokens spent on descriptions are the best-spent tokens in the prompt. Terse descriptions collapse selection quality. |
| "On error, return `'operation failed'`" | Kills retry logic. Model can't tell transient (retry) from fatal (ask user / escalate). |
| "Retry on every error with exponential backoff" | Burns budget on `validation` / `not_found` / `policy` errors that will never succeed. Retry only when `isRetryable: true`. |
| "Give every agent every tool — flexibility is good" | Past ~5–7 tools, selection degrades. 4–5 per agent, scoped by role. Cross-domain work → delegate to a subagent. |
| "Combine lookup/create/delete into one tool with a `mode` enum" | The selector picks by *tool name + description*, not by enum values inside inputs. Hide intent = misrouting. Split into separate tools. |
| "Force the right tool with `tool_choice: any`" | Band-aid for a bad description. `any` forces *a* tool, not the *right* tool. Fix the description first. |
| "Expose `place_order` as an MCP resource" | Resources are **read-only content**. Actions are **tools**. Don't swap them. |
| "Embed the API key in `.mcp.json` and commit it" | Secret in git history. Use `${ENV_VAR}` expansion. |
| "Use `~/.claude.json` for the team's shared MCP server" | That's user-scoped. Team servers go in project-scoped `.mcp.json` at the repo root (committed). |
| "Use Glob to find files that import pandas" | Glob matches **paths**, not contents. Use **Grep** for content. |

## The good-description checklist (memorize this shape)

```python
{
  "name": "lookup_sku",
  "description": (
    "Look up a product by SKU. "                                    # 1. what
    "Input: `sku`, a 7-char alphanumeric like 'ABX-0042'. "         # 2. input format + example
    "Returns: {name, category, unit_price_usd, is_discontinued}. "  # 3. output shape
    "Use this when the user mentions a SKU or product code. "       # 4. positive boundary
    "Do NOT use this to check stock levels — use `check_stock`. "   # 5. negative boundary
    "Returns {isError:true, errorCategory:'not_found'} on miss."    # 6. error shape
  ),
  "input_schema": {...},
}
```

Six clauses. If any is missing, the model will eventually make the wrong call it implies.

## The structured-error checklist

Every error return from a tool should have:

```python
{
  "isError": True,
  "errorCategory": "timeout",   # validation | not_found | timeout | policy | internal
  "isRetryable": True,           # drives deterministic retry branch
  "message": "Human-readable explanation the model can paraphrase to the user.",
  # optional actionable context:
  "retry_after_seconds": 2,
  "attempted_sku": "ABX-0042",
}
```

Three invariants:
1. **`isError: True`** is present whenever something went wrong. Silent `{}` or truncated results are the worst case — model thinks it succeeded.
2. **`errorCategory`** is one of a small enum. `validation` and `not_found` mean "don't retry, ask user or try a different approach." `timeout` means "maybe retry." `policy` means "escalate, don't retry." `internal` means "surface it; don't pretend success."
3. **`isRetryable`** is a boolean the loop code branches on. No string-parsing of `message`.

## Tool-count rule

- **4–5 tools per agent, max.**
- Coordinator with `Task` delegates cross-domain work to specialists.
- When you're tempted to add a 7th tool, ask: "should a subagent own this instead?"

## `.mcp.json` vs `~/.claude.json`

- `.mcp.json` at repo root → **project** scope → committed → team shared.
- `~/.claude.json` → **user** scope → personal → not committed.
- Secrets in **both** use `${ENV_VAR}` expansion.

## MCP tools vs MCP resources

- **Tools** = actions with side effects (`place_order`, `run_query`). Model invokes via `tool_use`.
- **Resources** = read-only content (style guide, API docs, static catalog). Attached by URI.
- Action → tool. Document → resource. Getting this backward is a distractor.

## Built-in tools — one-liner reminders

| Tool | One-liner |
|---|---|
| Read | Known file path, want contents |
| Grep | Search inside files (content) |
| Glob | Find files by path pattern |
| Edit | Patch existing file in place |
| Write | New file or full rewrite |
| Bash | Shell / git / test runner / anything else |

## 3-bullet recap

- **Descriptions are the selector.** Six clauses: what, input format+example, output shape, positive boundary, negative boundary, error shape.
- **Structured errors** (`isError`, `errorCategory`, `isRetryable`, `message`) turn retry into a deterministic branch. Generic strings break everything downstream.
- **Scope tools per role (4–5)**; `.mcp.json` = project (committed), `~/.claude.json` = user; secrets via `${ENV_VAR}`; tools do actions, resources hold read-only content.
