"""
W04 — Real-world MCP-style server sketch: inventory / order management.

Scenario:
    An e-commerce backend exposes four tools to a Claude agent:

        lookup_sku     — STATIC product metadata (name, price, category)
        check_stock    — REAL-TIME stock across warehouses (can time out)
        place_order    — action: creates an order (subject to policy checks)
        cancel_order   — action: cancels an existing order

    The agent uses these to answer questions like:
        "Is ABX-0042 in stock? If so, place an order for 2 units for
        customer C-77 shipping to 'warehouse-east'."

Why this exercise is useful for the exam:
    * Exercises the 4-tools-per-agent distribution rule (W04 §4).
    * Every tool returns STRUCTURED ERRORS with isError / errorCategory /
      isRetryable / message, covering all five error categories the exam
      tests:
        validation  (bad SKU format, missing field)
        not_found   (SKU doesn't exist, order doesn't exist)
        timeout     (warehouse API didn't respond in time)
        policy      (quantity above threshold, after-hours cancel window)
        internal    (unexpected server bug)
    * Shows tool descriptions with all six clauses: what / input format+
      example / return shape / positive boundary / negative boundary /
      error shape (W04 §1).
    * Demonstrates the split-vs-consolidate rule — `place_order` and
      `cancel_order` are SEPARATE tools, not one tool with an `action`
      enum (W04 §2).

MCP wire protocol:
    This file is a FUNCTION-CALL-LEVEL SKETCH. It does not speak the
    actual MCP JSON-RPC protocol over stdio. In a real MCP server you'd
    decorate each handler like this:

        from mcp.server import Server
        server = Server("inventory")

        @server.tool()
        def lookup_sku(sku: str) -> dict: ...

    and the MCP framework would handle registration, schema emission, and
    request routing. For study purposes we expose the functions directly;
    the mental model is identical.

Run: python real_world_inventory_mcp_server.py
    (prints the tool catalog and runs a few canned invocations,
    including each of the five error categories.)
"""

from __future__ import annotations
import json
import os
import random
from datetime import datetime, timedelta
from typing import Any


# =============================================================================
# Fake in-memory backend (stands in for a real warehouse API + order DB)
# =============================================================================

TODAY = datetime(2026, 4, 23, 14, 0, 0)  # a Thursday afternoon

# Static product catalog — keyed by SKU.
PRODUCTS: dict[str, dict] = {
    "ABX-0042": {
        "name": "Wireless headphones",
        "category": "audio",
        "unit_price_usd": 149.00,
        "is_discontinued": False,
    },
    "USB-1199": {
        "name": "USB-C cable 2m",
        "category": "accessories",
        "unit_price_usd": 19.00,
        "is_discontinued": False,
    },
    "LEG-9000": {
        "name": "Legacy adapter",
        "category": "accessories",
        "unit_price_usd": 9.00,
        "is_discontinued": True,
    },
}

# Real-time stock, per warehouse.
STOCK: dict[str, dict[str, int]] = {
    "ABX-0042": {"warehouse-east": 12, "warehouse-west": 4},
    "USB-1199": {"warehouse-east": 240, "warehouse-west": 180},
    "LEG-9000": {"warehouse-east": 0, "warehouse-west": 0},
}

# Orders keyed by order_id.
ORDERS: dict[str, dict] = {
    "ORD-5001": {
        "customer_id": "C-77",
        "sku": "USB-1199",
        "quantity": 3,
        "placed_at": (TODAY - timedelta(hours=2)).isoformat(),
        "status": "pending",
    },
    "ORD-5002": {
        "customer_id": "C-77",
        "sku": "ABX-0042",
        "quantity": 1,
        "placed_at": (TODAY - timedelta(days=5)).isoformat(),
        "status": "shipped",
    },
}

# Business policy — the kind of rule that triggers `errorCategory: policy`.
POLICY = {
    "max_quantity_per_order": 50,
    "cancel_window_hours": 24,       # can only cancel within 24h of placement
    "max_order_value_usd": 10_000,
}

# Config sourced from environment (in a real MCP server, via ${ENV_VAR}
# expansion from .mcp.json — see the example at the bottom of this file).
INVENTORY_API_URL = os.environ.get("INVENTORY_API_URL", "https://inv.example/api")
INVENTORY_API_KEY = os.environ.get("INVENTORY_API_KEY", "")  # not used here, but
# in a real server you'd refuse to start without it.


# =============================================================================
# Structured error helper
# =============================================================================
#
# Every tool returns either a successful result dict, or an error dict
# with this shape. The model reads these fields and decides what to do;
# your loop code branches deterministically on `isRetryable`.

def make_error(
    category: str,
    message: str,
    *,
    is_retryable: bool,
    **extra: Any,
) -> dict:
    """Shape every error the same way so retry/escalate logic is deterministic.

    category MUST be one of:
        validation | not_found | timeout | policy | internal
    """
    assert category in {"validation", "not_found", "timeout", "policy", "internal"}
    err = {
        "isError": True,
        "errorCategory": category,
        "isRetryable": is_retryable,
        "message": message,
    }
    err.update(extra)
    return err


# =============================================================================
# Tool 1: lookup_sku — STATIC metadata
# =============================================================================
#
# In a real MCP server:
#   @server.tool()
#   def lookup_sku(sku: str) -> dict: ...

TOOL_LOOKUP_SKU = {
    "name": "lookup_sku",
    "description": (
        "Look up STATIC product metadata by SKU. "
        "Input: `sku`, a 7-character alphanumeric code like 'ABX-0042' "
        "or 'USB-1199'. Must be an exact SKU — do NOT pass product names "
        "or free text. "
        "Returns: {sku, name, category, unit_price_usd, is_discontinued}. "
        "Use this when the user mentions a SKU and you need name / price "
        "/ category. Cheap and cacheable. "
        "Do NOT use this to check current stock levels — use `check_stock`. "
        "On unknown SKU returns {isError: true, errorCategory: 'not_found', "
        "isRetryable: false, message: ...}. "
        "On malformed SKU returns {isError: true, errorCategory: "
        "'validation', isRetryable: false, message: ...}."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sku": {
                "type": "string",
                "description": "7-char alphanumeric SKU, e.g. 'ABX-0042'",
            }
        },
        "required": ["sku"],
    },
}


def _validate_sku(sku: Any) -> str | None:
    """Return error-message string if bad, None if ok."""
    if not isinstance(sku, str):
        return "sku must be a string"
    if len(sku) != 7 or "-" not in sku:
        return (
            "sku must be 7 characters alphanumeric with a hyphen, "
            "like 'ABX-0042'"
        )
    return None


def lookup_sku(sku: str) -> dict:
    err = _validate_sku(sku)
    if err:
        return make_error("validation", err, is_retryable=False, attempted_sku=sku)

    product = PRODUCTS.get(sku)
    if product is None:
        return make_error(
            "not_found",
            f"SKU '{sku}' does not exist in the catalog.",
            is_retryable=False,
            attempted_sku=sku,
        )
    return {"sku": sku, **product}


# =============================================================================
# Tool 2: check_stock — REAL-TIME, can time out
# =============================================================================
#
# In a real MCP server:
#   @server.tool()
#   def check_stock(sku: str) -> dict: ...

TOOL_CHECK_STOCK = {
    "name": "check_stock",
    "description": (
        "Check REAL-TIME stock levels for a SKU across warehouses. "
        "Input: `sku`, a 7-character alphanumeric code like 'ABX-0042'. "
        "Returns: {sku, total_units_available, per_warehouse: "
        "[{warehouse_id, units}], checked_at_iso}. "
        "`total_units_available` may legitimately be 0. "
        "Use this when the user asks about availability, 'is X in stock', "
        "'how many left', or before attempting to place an order. Hits a "
        "live system and can time out. "
        "Do NOT use this to fetch product name, price, or category — use "
        "`lookup_sku`. Do NOT use this to place an order — this is "
        "read-only. "
        "On upstream timeout returns {isError: true, errorCategory: "
        "'timeout', isRetryable: true, retry_after_seconds: 2, message: ...}. "
        "On unknown SKU returns {isError: true, errorCategory: "
        "'not_found', isRetryable: false, message: ...}."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sku": {
                "type": "string",
                "description": "7-char alphanumeric SKU, e.g. 'ABX-0042'",
            }
        },
        "required": ["sku"],
    },
}


# Simulate flaky upstream. Flip this env var to force a timeout for demo.
def _simulate_upstream_timeout() -> bool:
    return os.environ.get("INVENTORY_FORCE_TIMEOUT") == "1"


def check_stock(sku: str) -> dict:
    err = _validate_sku(sku)
    if err:
        return make_error("validation", err, is_retryable=False, attempted_sku=sku)

    if _simulate_upstream_timeout():
        return make_error(
            "timeout",
            f"Warehouse API at {INVENTORY_API_URL} did not respond within "
            "5s. This is usually transient.",
            is_retryable=True,
            retry_after_seconds=2,
            attempted_sku=sku,
        )

    if sku not in STOCK:
        return make_error(
            "not_found",
            f"SKU '{sku}' has no stock record.",
            is_retryable=False,
            attempted_sku=sku,
        )

    per_wh = [
        {"warehouse_id": wh, "units": n} for wh, n in STOCK[sku].items()
    ]
    return {
        "sku": sku,
        "total_units_available": sum(STOCK[sku].values()),
        "per_warehouse": per_wh,
        "checked_at_iso": TODAY.isoformat(),
    }


# =============================================================================
# Tool 3: place_order — ACTION, subject to policy checks
# =============================================================================
#
# In a real MCP server:
#   @server.tool()
#   def place_order(sku: str, quantity: int, customer_id: str,
#                   warehouse_id: str) -> dict: ...
#
# Note: this is a SEPARATE tool from cancel_order. We deliberately did
# NOT consolidate them into a single `order_action(action="place"|"cancel")`
# tool — the selector picks by tool name + description, not by enum values
# inside inputs. Keep actions as named tools.

TOOL_PLACE_ORDER = {
    "name": "place_order",
    "description": (
        "Place a new order for a given SKU, quantity, customer, and "
        "warehouse. "
        "Input: `sku` (7-char alphanumeric), `quantity` (positive int, "
        "max 50 per order by policy), `customer_id` (e.g. 'C-77'), "
        "`warehouse_id` (one of 'warehouse-east', 'warehouse-west'). "
        "Returns: {order_id, sku, quantity, customer_id, warehouse_id, "
        "placed_at_iso, status: 'pending'}. "
        "Use this ONLY after you've verified stock via `check_stock` and "
        "have explicit customer confirmation. "
        "Do NOT use this to cancel — use `cancel_order`. Do NOT call "
        "speculatively. "
        "Returns structured errors: "
        "{errorCategory: 'validation', isRetryable: false} on bad input; "
        "{errorCategory: 'policy', isRetryable: false} when quantity "
        "exceeds max_quantity_per_order or total value exceeds the policy "
        "cap; "
        "{errorCategory: 'not_found', isRetryable: false} for unknown SKU."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "quantity": {"type": "integer", "minimum": 1},
            "customer_id": {"type": "string"},
            "warehouse_id": {
                "type": "string",
                "enum": ["warehouse-east", "warehouse-west"],
            },
        },
        "required": ["sku", "quantity", "customer_id", "warehouse_id"],
    },
}


def place_order(
    sku: str,
    quantity: int,
    customer_id: str,
    warehouse_id: str,
) -> dict:
    # --- validation -----------------------------------------------------
    err = _validate_sku(sku)
    if err:
        return make_error("validation", err, is_retryable=False)

    if not isinstance(quantity, int) or quantity <= 0:
        return make_error(
            "validation",
            "quantity must be a positive integer",
            is_retryable=False,
        )

    if warehouse_id not in {"warehouse-east", "warehouse-west"}:
        return make_error(
            "validation",
            "warehouse_id must be 'warehouse-east' or 'warehouse-west'",
            is_retryable=False,
        )

    # --- not_found ------------------------------------------------------
    if sku not in PRODUCTS:
        return make_error(
            "not_found",
            f"SKU '{sku}' does not exist in the catalog.",
            is_retryable=False,
        )

    # --- policy ---------------------------------------------------------
    if quantity > POLICY["max_quantity_per_order"]:
        return make_error(
            "policy",
            f"quantity {quantity} exceeds the per-order cap of "
            f"{POLICY['max_quantity_per_order']}. Split into multiple "
            "orders or escalate.",
            is_retryable=False,
            policy_limit=POLICY["max_quantity_per_order"],
        )

    unit_price = PRODUCTS[sku]["unit_price_usd"]
    total_value = unit_price * quantity
    if total_value > POLICY["max_order_value_usd"]:
        return make_error(
            "policy",
            f"order total ${total_value:,.2f} exceeds the policy cap of "
            f"${POLICY['max_order_value_usd']:,.2f}. Escalate to a human "
            "account manager.",
            is_retryable=False,
            policy_limit_usd=POLICY["max_order_value_usd"],
        )

    # --- success --------------------------------------------------------
    order_id = f"ORD-{5000 + len(ORDERS) + 1}"
    record = {
        "order_id": order_id,
        "sku": sku,
        "quantity": quantity,
        "customer_id": customer_id,
        "warehouse_id": warehouse_id,
        "placed_at_iso": TODAY.isoformat(),
        "status": "pending",
    }
    ORDERS[order_id] = {
        "customer_id": customer_id,
        "sku": sku,
        "quantity": quantity,
        "placed_at": record["placed_at_iso"],
        "status": "pending",
    }
    return record


# =============================================================================
# Tool 4: cancel_order — ACTION, policy-gated by time window
# =============================================================================
#
# In a real MCP server:
#   @server.tool()
#   def cancel_order(order_id: str, reason: str) -> dict: ...

TOOL_CANCEL_ORDER = {
    "name": "cancel_order",
    "description": (
        "Cancel an existing pending order by order ID. "
        "Input: `order_id` (e.g. 'ORD-5001'), `reason` (short free-text "
        "string for the audit log). "
        "Returns: {order_id, status: 'cancelled', cancelled_at_iso, "
        "reason}. "
        "Use this when the customer explicitly asks to cancel and the "
        "order is still within the 24-hour cancellation window. "
        "Do NOT use this to place a new order — use `place_order`. Do NOT "
        "use this on already-shipped orders; they must be handled as a "
        "return. "
        "Returns {errorCategory: 'not_found', isRetryable: false} if the "
        "order_id doesn't exist; {errorCategory: 'policy', isRetryable: "
        "false} if outside the 24-hour window or already shipped."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["order_id", "reason"],
    },
}


def cancel_order(order_id: str, reason: str) -> dict:
    if not isinstance(order_id, str) or not order_id.startswith("ORD-"):
        return make_error(
            "validation",
            "order_id must be a string starting with 'ORD-'",
            is_retryable=False,
        )

    order = ORDERS.get(order_id)
    if order is None:
        return make_error(
            "not_found",
            f"Order '{order_id}' does not exist.",
            is_retryable=False,
            attempted_order_id=order_id,
        )

    if order["status"] == "shipped":
        return make_error(
            "policy",
            f"Order '{order_id}' has already shipped and cannot be "
            "cancelled. Initiate a return instead.",
            is_retryable=False,
        )

    placed_at = datetime.fromisoformat(order["placed_at"])
    age = TODAY - placed_at
    if age > timedelta(hours=POLICY["cancel_window_hours"]):
        return make_error(
            "policy",
            f"Order '{order_id}' is outside the "
            f"{POLICY['cancel_window_hours']}-hour cancellation window "
            f"(placed {age.total_seconds() / 3600:.1f}h ago).",
            is_retryable=False,
            cancel_window_hours=POLICY["cancel_window_hours"],
        )

    order["status"] = "cancelled"
    return {
        "order_id": order_id,
        "status": "cancelled",
        "cancelled_at_iso": TODAY.isoformat(),
        "reason": reason,
    }


# =============================================================================
# Tool catalog + dispatcher (what an MCP client would see)
# =============================================================================

TOOLS = [TOOL_LOOKUP_SKU, TOOL_CHECK_STOCK, TOOL_PLACE_ORDER, TOOL_CANCEL_ORDER]
# Note: exactly 4 tools. This respects the W04 rule of 4–5 per agent.

DISPATCH = {
    "lookup_sku": lookup_sku,
    "check_stock": check_stock,
    "place_order": place_order,
    "cancel_order": cancel_order,
}


def call_tool(name: str, arguments: dict) -> dict:
    """Stand-in for the MCP server's request router.

    In a real MCP server, the framework reads a JSON-RPC `tools/call`
    request from stdin, looks up the handler, passes arguments, and
    writes a response to stdout. The handler body (our functions above)
    is the same.
    """
    if name not in DISPATCH:
        return make_error(
            "internal",
            f"Unknown tool '{name}'. This indicates a framework bug "
            "or a stale tool catalog on the client side.",
            is_retryable=False,
        )
    try:
        return DISPATCH[name](**arguments)
    except TypeError as e:
        # Missing/extra kwargs → validation error to the caller.
        return make_error(
            "validation",
            f"Bad arguments for tool '{name}': {e}",
            is_retryable=False,
        )
    except Exception as e:  # noqa: BLE001
        # Genuine bug on our side → internal, not retryable by default.
        return make_error(
            "internal",
            f"Unexpected server error in tool '{name}': {e}",
            is_retryable=False,
        )


# =============================================================================
# Demo — exercise each error category + happy paths
# =============================================================================

def _demo():
    print("=" * 72)
    print("TOOL CATALOG")
    print("=" * 72)
    for t in TOOLS:
        print(f"- {t['name']}: {t['description'][:90]}...")
    print()

    cases: list[tuple[str, dict, str]] = [
        # (tool_name, arguments, what-we're-testing)
        ("lookup_sku", {"sku": "ABX-0042"}, "happy path"),
        ("lookup_sku", {"sku": "oops"}, "validation error (bad format)"),
        ("lookup_sku", {"sku": "ZZZ-9999"}, "not_found error"),
        ("check_stock", {"sku": "ABX-0042"}, "happy path (real-time)"),
        ("place_order", {
            "sku": "ABX-0042", "quantity": 2,
            "customer_id": "C-77", "warehouse_id": "warehouse-east",
        }, "happy path — place order"),
        ("place_order", {
            "sku": "ABX-0042", "quantity": 999,
            "customer_id": "C-77", "warehouse_id": "warehouse-east",
        }, "policy error (quantity cap)"),
        ("cancel_order", {
            "order_id": "ORD-5001", "reason": "customer changed mind",
        }, "happy path — cancel (within window)"),
        ("cancel_order", {
            "order_id": "ORD-5002", "reason": "customer request",
        }, "policy error (already shipped)"),
        ("cancel_order", {
            "order_id": "ORD-9999", "reason": "test",
        }, "not_found error"),
    ]

    for name, args, label in cases:
        print("-" * 72)
        print(f"call_tool({name!r}, {args})  # {label}")
        result = call_tool(name, args)
        print(json.dumps(result, indent=2))
        print()

    # Show a simulated timeout with INVENTORY_FORCE_TIMEOUT=1 in env.
    print("-" * 72)
    print("Simulating a check_stock timeout (INVENTORY_FORCE_TIMEOUT=1):")
    os.environ["INVENTORY_FORCE_TIMEOUT"] = "1"
    try:
        print(json.dumps(call_tool("check_stock", {"sku": "ABX-0042"}), indent=2))
    finally:
        os.environ.pop("INVENTORY_FORCE_TIMEOUT", None)


if __name__ == "__main__":
    _demo()


# =============================================================================
# EXAMPLE .mcp.json — PROJECT-SCOPED CONFIG (committed to the repo)
# =============================================================================
#
# In a real setup you'd check this file in at the repo root as `.mcp.json`.
# Any secret is pulled from the environment via `${ENV_VAR}` expansion so
# the file itself is safe to commit.
#
# {
#   "mcpServers": {
#     "inventory": {
#       "command": "python",
#       "args": ["-m", "real_world_inventory_mcp_server"],
#       "env": {
#         "INVENTORY_API_URL": "${INVENTORY_API_URL}",
#         "INVENTORY_API_KEY": "${INVENTORY_API_KEY}"
#       }
#     }
#   }
# }
#
# Developer setup (NOT committed):
#   export INVENTORY_API_URL="https://inv.internal.example/api"
#   export INVENTORY_API_KEY="sk-live-..."
#
# Contrast with USER-SCOPED config at `~/.claude.json`: same shape, but
# personal to your machine. Use user scope for your own tools; use
# project scope (`.mcp.json`) for anything the team needs.
#
# Anti-pattern: hardcoding the API key directly into .mcp.json and
# committing it. Use ${ENV_VAR} expansion — always.
