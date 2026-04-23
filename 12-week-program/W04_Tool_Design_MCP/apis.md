# W04 APIs — Claude APIs for this week

> APIs relevant to **tool design and MCP**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Tool use** — `tools=[...]` + `input_schema` | Declare tools to the Messages API | Every Claude call that should do actions |
| **`tool_choice`** — `"auto"` / `"any"` / `{"type":"tool","name":"..."}` | Control whether / which tool the model must pick | Forcing structured extraction; ensuring tool use |
| **Structured errors** — `{"isError": true, "errorCategory": "...", "isRetryable": bool, "message": "..."}` | Let retry logic branch on category, not string parsing | Every tool that can fail |
| **MCP Python SDK** — `mcp.server.fastmcp.FastMCP` | Build an MCP server exposing tools/resources | Sharing tools across Claude Code, Claude Desktop, etc. |
| **`.mcp.json`** (project) / **`~/.claude.json`** (user) | Register MCP servers with Claude Code | Team vs personal tool wiring |

---

## API snippets

### Tool declaration with boundaries
```python
tools = [{
    "name": "search_customer_by_email",
    "description": (
        "Look up a customer by exact email address. "
        "Input: email (RFC-5322 format). "
        "Returns: customer object with id, name, created_at — or {isError:true, errorCategory:'not_found'}. "
        "Do NOT use for partial-email or fuzzy search — use search_customer_fuzzy for that."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"email": {"type": "string", "format": "email"}},
        "required": ["email"],
    },
}]
```

### Structured error return
```python
def run_search_customer(email: str) -> dict:
    try:
        row = db.find_one({"email": email})
        if row is None:
            return {"isError": True, "errorCategory": "not_found", "isRetryable": False,
                    "message": f"No customer with email {email}"}
        return {"id": row["id"], "name": row["name"], "created_at": row["created_at"]}
    except TimeoutError:
        return {"isError": True, "errorCategory": "timeout", "isRetryable": True,
                "message": "DB timeout; try again"}
```

### `tool_choice` modes
```python
tool_choice={"type": "auto"}                         # default; model may skip tools
tool_choice={"type": "any"}                          # must call SOME tool this turn
tool_choice={"type": "tool", "name": "extract"}      # force this specific tool
```

### `.mcp.json` with env expansion
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
    }
  }
}
```

---

## Working example A — Minimal MCP server (Python)

Save as `mcp_server.py`:

```python
"""
Minimal MCP server with two tools: a lookup (idempotent) and an action (with side effect).
Uses the `mcp` Python SDK (FastMCP).
"""
from mcp.server.fastmcp import FastMCP

app = FastMCP("demo-server")

# In-memory "database" for the demo
INVENTORY = {
    "SKU-100": {"name": "Widget", "stock": 42, "price": 9.99},
    "SKU-200": {"name": "Gadget", "stock": 0,  "price": 24.99},
}

@app.tool()
def get_stock(sku: str) -> dict:
    """Look up stock and price for a SKU.

    Input: sku — a SKU like 'SKU-100'.
    Returns: {name, stock, price}, or a structured error if the SKU is unknown.
    Do NOT use for fuzzy search — SKUs must be exact.
    """
    item = INVENTORY.get(sku)
    if item is None:
        return {"isError": True, "errorCategory": "not_found", "isRetryable": False,
                "message": f"SKU {sku} not in catalog"}
    return {"name": item["name"], "stock": item["stock"], "price": item["price"]}

@app.tool()
def reserve_stock(sku: str, qty: int) -> dict:
    """Reserve `qty` units of `sku`. Returns confirmation or structured error.

    Input: sku (exact), qty (positive integer).
    Fails with errorCategory='out_of_stock' if insufficient stock (not retryable).
    Fails with errorCategory='invalid_input' if qty <= 0 (not retryable).
    """
    if qty <= 0:
        return {"isError": True, "errorCategory": "invalid_input", "isRetryable": False,
                "message": "qty must be > 0"}
    item = INVENTORY.get(sku)
    if item is None:
        return {"isError": True, "errorCategory": "not_found", "isRetryable": False,
                "message": f"SKU {sku} not in catalog"}
    if item["stock"] < qty:
        return {"isError": True, "errorCategory": "out_of_stock", "isRetryable": False,
                "message": f"Only {item['stock']} available, requested {qty}"}
    item["stock"] -= qty
    return {"reserved": qty, "remaining": item["stock"]}

if __name__ == "__main__":
    app.run()  # stdio transport
```

---

## Working example B — Wire it in `.mcp.json`

Save at your project root as `.mcp.json`:

```json
{
  "mcpServers": {
    "demo": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

---

## How to run

**Setup:**
```bash
pip install mcp anthropic
```

**Test server standalone** (from a separate Python shell):
```python
# sanity-check imports only
from mcp.server.fastmcp import FastMCP
print("OK")
```

**Integrate with Claude Code:**
1. Save `mcp_server.py` and `.mcp.json` at your project root.
2. Launch Claude Code: `claude`.
3. Run `/mcp` inside Claude Code — should list `demo` as connected.
4. Ask: *"What's the price and stock of SKU-100?"* → should call `get_stock`.
5. Ask: *"Reserve 50 units of SKU-100"* → should call `reserve_stock` and receive `out_of_stock` error → model adapts.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| `/mcp` shows `demo: failed` | Python not on PATH, or `mcp` not installed | Use absolute path in `.mcp.json` command; `pip install mcp` |
| Server connects but tools not listed | FastMCP version mismatch or missing `@app.tool()` decorator | Check `mcp` version: `pip show mcp`; re-check decorators |
| Model picks wrong tool | Descriptions too terse / overlapping | Add boundaries ("do NOT use for X"), input/output shapes, examples |
| Model retries forever on errors | Error is unstructured string | Return the `{isError, errorCategory, isRetryable}` object |
| Tool gets called with wrong arg types | `input_schema` too loose | Tighten with `pattern`, `enum`, `minimum/maximum`, `required` |

**Inspect MCP handshake:**
```bash
claude --debug
```
Shows `initialize`, `tools/list`, `tools/call` messages. Missing `tools/list` response = server crashed on startup.

**Run MCP server manually to see errors:**
```bash
python mcp_server.py
```
If this crashes, the error will be in the traceback. With stdio transport the server just sits waiting for JSON-RPC over stdin — press Ctrl+C to exit.

---

## Exam connection

- **Tool descriptions with boundaries** ("do NOT use for X") resolve the "two near-similar tools" exam distractor.
- **Structured errors with `errorCategory`** let retry logic branch correctly — the exam tests this against the "parse error message string" distractor.
- **`.mcp.json` vs `~/.claude.json`**: team vs personal. The exam distinguishes committed shared servers from private user servers.
- **Tools vs resources**: SKU lookup in `INVENTORY` could also be exposed as an MCP *resource* if it were a catalog to browse. Tools are for actions/dispatch; resources are for content.
