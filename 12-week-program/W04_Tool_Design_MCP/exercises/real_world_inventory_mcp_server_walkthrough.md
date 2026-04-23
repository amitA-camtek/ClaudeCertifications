# Walkthrough — Real-world inventory MCP server sketch

This document explains **how each tool's description and error shape changes what the agent actually does**, step by step. Read this after you've read `reference.md` and skimmed `real_world_inventory_mcp_server.py`.

## The scenario

A customer agent is hooked up to this inventory MCP server with four tools:

- `lookup_sku` — static product metadata
- `check_stock` — real-time availability (can time out)
- `place_order` — create an order (policy-gated)
- `cancel_order` — cancel an order (time-window gated)

A customer asks:

> "Hi, I want to order 2 units of SKU ABX-0042 to warehouse-east. My customer ID is C-77."

## Expected tool trace

A well-behaved agent goes through these steps. Notice how every decision is driven by the **description** (which tool to pick) or the **structured error shape** (what to do when something goes wrong).

### Step 1 — `lookup_sku({"sku": "ABX-0042"})`

The agent reads the `lookup_sku` description:

> Use this when the user mentions a SKU and you need name / price / category. **Do NOT use this to check current stock levels — use `check_stock`.**

The user mentioned a SKU, the agent needs price info before placing an order. Correct tool.

Return:

```json
{
  "sku": "ABX-0042",
  "name": "Wireless headphones",
  "category": "audio",
  "unit_price_usd": 149.00,
  "is_discontinued": false
}
```

### Step 2 — `check_stock({"sku": "ABX-0042"})`

The `place_order` description says:

> Use this ONLY after you've verified stock via `check_stock` and have explicit customer confirmation.

So the agent calls `check_stock` first. Return:

```json
{
  "sku": "ABX-0042",
  "total_units_available": 16,
  "per_warehouse": [
    {"warehouse_id": "warehouse-east", "units": 12},
    {"warehouse_id": "warehouse-west", "units": 4}
  ],
  "checked_at_iso": "2026-04-23T14:00:00"
}
```

Stock is sufficient. Warehouse-east has 12 units, customer wants 2. Green light.

### Step 3 — `place_order({...})`

```python
place_order(
    sku="ABX-0042",
    quantity=2,
    customer_id="C-77",
    warehouse_id="warehouse-east",
)
```

Returns an order record with `status: "pending"`. The agent writes a confirmation reply and emits `end_turn`.

## What each tool's description is doing for you

| Tool | Description clause that matters | Failure mode if you removed it |
|---|---|---|
| `lookup_sku` | "Do NOT use this to check stock levels — use `check_stock`" | Agent routinely calls `lookup_sku` when asked about availability; never gets real-time data |
| `check_stock` | "Do NOT use this to place an order — this is read-only" | Agent invents side effects on a read-only tool; might treat `total_units_available: 0` as "order placed for 0 units" |
| `place_order` | "Use this ONLY after you've verified stock via `check_stock`" | Agent places orders before verifying stock; orders rejected downstream; user gets unexpected failures |
| `cancel_order` | "Do NOT use this to place a new order — use `place_order`" | Agent occasionally picks `cancel_order` for wrong requests when the user's phrasing is ambiguous ("I want to change my order") |

The **negative boundary** ("Do NOT use this for X, use Y instead") is load-bearing for every near-similar pair. Without it, the selector guesses.

## What each structured error is doing for you

The five error categories each steer the agent to a different branch of behavior.

### `validation` — `isRetryable: false`

Example: user says "look up headphones for me" and the agent naively passes `sku="headphones"`.

```json
{
  "isError": true,
  "errorCategory": "validation",
  "isRetryable": false,
  "message": "sku must be 7 characters alphanumeric with a hyphen, like 'ABX-0042'"
}
```

The agent sees `isRetryable: false` → doesn't loop. It sees `validation` → knows the input was wrong. It reads `message` → knows what a correct SKU looks like. It asks the user: "What's the SKU for those headphones? It looks like 'ABX-XXXX'."

Without `isRetryable: false`, your loop would retry the same bad input forever. Without `errorCategory: validation`, the agent wouldn't know to ask the user for a better input vs retry vs escalate.

### `not_found` — `isRetryable: false`

Example: `lookup_sku({"sku": "ZZZ-9999"})` on a SKU that doesn't exist.

The agent sees `not_found` → tells the user "I don't have a product with that SKU. Double-check the code?" — instead of silently failing or hallucinating an answer.

### `timeout` — `isRetryable: true`

Example: `check_stock` when the upstream warehouse API is slow.

```json
{
  "isError": true,
  "errorCategory": "timeout",
  "isRetryable": true,
  "retry_after_seconds": 2,
  "message": "Warehouse API at https://inv.example/api did not respond within 5s. This is usually transient."
}
```

Your loop code sees `isRetryable: true` and retries once or twice (bounded). If it keeps timing out, you surface it: "Our stock system is slow right now; I can retry in a minute or place the order without a pre-check." Without `isRetryable`, you'd have to parse the `message` string to decide — probabilistic.

### `policy` — `isRetryable: false`

Example: `place_order({"quantity": 999, ...})` hits the max-per-order cap.

```json
{
  "isError": true,
  "errorCategory": "policy",
  "isRetryable": false,
  "policy_limit": 50,
  "message": "quantity 999 exceeds the per-order cap of 50. Split into multiple orders or escalate."
}
```

Retrying would be pointless — the policy will fail every time. The agent reads `message` and either splits the order automatically (if allowed) or escalates to a human. Critically: the agent does NOT keep retrying.

### `internal` — usually `isRetryable: false`

Example: unknown tool name, or an unhandled exception in the tool body.

The agent surfaces the failure cleanly ("Something went wrong on our side; I've logged this") instead of pretending success.

## Why these fields are load-bearing, as one table

| Field | Without it | With it |
|---|---|---|
| `isError: true` | Agent can't tell error from degenerate-success. Treats empty results as "nothing found" legitimately. | Agent knows something went wrong. |
| `errorCategory` | Agent has to parse `message` string to decide retry vs escalate vs ask. Probabilistic. | Deterministic branch on a typed enum. |
| `isRetryable` | Your loop retries everything or nothing. Either wastes budget or misses transient failures. | Your loop branches deterministically on this boolean. |
| `message` | Agent can't explain the failure to the user in natural language. | Agent paraphrases straight to the user. |

## Variations to try

### 1. Remove `errorCategory` from all errors

Change `make_error` to emit just `{"isError": True, "message": "..."}` and watch the agent behavior:

- Retry logic breaks — your loop no longer knows which errors are `timeout` (retry) vs `policy` (don't retry).
- Agent conflates `validation` errors with `not_found` — it loops apologizing for the wrong thing.
- User-facing messages get vague ("something went wrong"). Compare to the specific category-driven replies you saw above.

**Exam takeaway:** this is exactly the distractor "return a generic error message." It breaks every downstream decision.

### 2. Remove `isRetryable`

Keep `errorCategory` but drop `isRetryable`. Now your loop has to *infer* retry-ability from the category. Some categories are ambiguous (is `internal` retryable? sometimes...). String-parsing sneaks back in.

**Exam takeaway:** `isRetryable` is the one-boolean shortcut that keeps retry logic deterministic. Don't skip it.

### 3. Consolidate `place_order` and `cancel_order` into one `order_action` tool with `action="place" | "cancel"`

Watch the agent:

- Occasionally confuses the two even with a careful description — because the selector operates on tool name + description, not on enum values inside the input.
- Gets *worse* as you add a third action (`modify`).
- You end up writing "if action is 'place' then X, else if 'cancel' then Y" logic inside one giant description — the same branching you were avoiding by having separate tools.

**Exam takeaway:** split actions into separately-named tools. The split-vs-consolidate rule exists because the selector can't see past the tool boundary.

### 4. Expand to 8+ tools on one agent

Add `list_orders`, `update_shipping_address`, `apply_discount_code`, `check_customer_tier`, etc. — until you have 9 tools. Watch the agent:

- Start picking `list_orders` when the user says "look up ABX-0042" (name confusion: "look up" / "list").
- Latency goes up (bigger catalog on every call).
- Selection accuracy on near-similar pairs drops measurably.

**Exam takeaway:** the 4–5-tools-per-agent rule isn't a suggestion. Past ~6–7 tools, selection degrades. The fix is to split responsibilities into specialist subagents (W02) — a customer agent and an orders agent, each with their own 4-tool catalog, coordinated via `Task`.

### 5. Swap `place_order` from an MCP tool to an MCP resource

Try it. Resources are read-only content — there's no way to invoke them with parameters that modify state. The agent has no mechanism to "place" anything.

**Exam takeaway:** tools are actions, resources are read-only content. Don't swap them. This is the single cleanest distractor question on MCP — if a test asks "where would you expose `place_order`", the answer is always *tool*, never *resource*.

### 6. Replace `${INVENTORY_API_KEY}` with a literal secret in `.mcp.json` and commit it

Don't actually do this. But recognize it on the exam: hardcoded secrets in committed config is the canonical wrong answer. Always use `${ENV_VAR}` expansion.

## The exam-relevant takeaways from this example

1. **Descriptions decide selection.** Six clauses per tool: what / input+example / output shape / positive boundary / negative boundary / error shape. Missing the negative boundary is the most common, most expensive omission.
2. **Structured errors enable deterministic retry.** `isError`, `errorCategory` (one of five), `isRetryable` (boolean), friendly `message`. Your loop branches on typed fields, not on string-parsing.
3. **Split actions, don't consolidate.** `place_order` and `cancel_order` are separate tools on purpose. The selector picks by tool name + description, not by enum values inside inputs.
4. **4–5 tools per agent, max.** Cross-domain work is a subagent boundary (W02), not "add another tool to this agent."
5. **MCP tools do actions; MCP resources hold read-only content.** Don't swap them.
6. **`.mcp.json` is project-scoped and committed; secrets go through `${ENV_VAR}`.** `~/.claude.json` is personal.
