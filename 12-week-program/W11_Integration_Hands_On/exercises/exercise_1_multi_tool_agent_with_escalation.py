"""
W11 Exercise 1 — Multi-Tool Customer Support Agent with Escalation Logic.

Integrates:
    W01 — the agentic loop, stop_reason branching, parallel tool_result bundling.
    W02 — adaptive decomposition of a multi-concern customer message.
    W03 — a PreToolUse hook that DETERMINISTICALLY blocks refunds over $500
          (not a line in the system prompt; a hard gate in the loop).
    W04 — 4 tools with rich descriptions, including TWO near-similar tools
          (update_shipping_address vs set_billing_address) to force the model
          to disambiguate on description text. Tools return STRUCTURED errors.

Scenario:
    A customer writes a single message with THREE concerns:
      1. "Refund order ORD-2001 ($649)"  → must be blocked by the $500 hook
                                             → the agent should pivot to escalate.
      2. "Change my shipping address"     → near-similar-tool selection test.
      3. "Am I still a Gold loyalty member?" → lookup-only.

    A well-integrated agent will, in ONE or TWO coordinator turns:
      - call get_order + get_customer + get_loyalty_status in parallel,
      - attempt issue_refund → HOOK BLOCKS → fall back to escalate_to_human,
      - call update_shipping_address (not set_billing_address),
      - emit ONE unified end_turn reply that addresses all three concerns.

Run: ANTHROPIC_API_KEY=... python exercise_1_multi_tool_agent_with_escalation.py

Variations to try (bottom of file): swap the hook for a prompt rule and watch it
leak; give the two similar tools identical descriptions and watch selection fail.
"""

from __future__ import annotations
import json
from datetime import datetime, timedelta

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# =============================================================================
# Fake backend (stands in for DB / CRM / payments)
# =============================================================================

TODAY = datetime(2026, 4, 23)

ORDERS = {
    "ORD-2001": {
        "customer_id": "C-99",
        "item": "4K OLED Monitor",
        "amount_usd": 649.00,
        "ordered_at": (TODAY - timedelta(days=10)).isoformat(),
        "status": "delivered",
        "shipping_address": "12 Herzl St, Tel Aviv, IL",
    },
}

CUSTOMERS = {
    "C-99": {
        "name": "Noa Ben-David",
        "email": "noa@example.com",
        "shipping_address": "12 Herzl St, Tel Aviv, IL",
        "billing_address": "12 Herzl St, Tel Aviv, IL",
        "loyalty_tier": "Gold",
        "loyalty_points": 3420,
    },
}

ESCALATIONS: list[dict] = []
REFUNDS: list[dict] = []

# =============================================================================
# Tool definitions (W04: rich descriptions, 2 near-similar tools)
# =============================================================================

TOOLS = [
    {
        "name": "get_order",
        "description": (
            "Look up an order by order ID. Returns item name, amount in USD, "
            "ship date, status, and the shipping address on file. "
            "Use this whenever the customer references an ORD-xxxx identifier."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "get_customer",
        "description": (
            "Fetch a customer profile by customer ID (format: C-xx). Returns "
            "name, email, current shipping and billing addresses, loyalty tier, "
            "and loyalty point balance. Use this when the customer asks about "
            "loyalty status OR when you need the current address before changing it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    },
    # ---- Two near-similar tools: selection must come from descriptions. ----
    {
        "name": "update_shipping_address",
        "description": (
            "Update the SHIPPING address on a customer's account. This is the "
            "address that future orders will be DELIVERED to. Use this when the "
            "customer says 'change my address', 'ship to a new place', or "
            "'update where you deliver to'. Does NOT affect billing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "new_address": {"type": "string"},
            },
            "required": ["customer_id", "new_address"],
        },
    },
    {
        "name": "set_billing_address",
        "description": (
            "Update the BILLING address on a customer's account. This is the "
            "address associated with the customer's payment method for invoicing "
            "and tax purposes. Use ONLY when the customer explicitly mentions "
            "billing, invoices, or their card's statement address. Does NOT "
            "affect where orders ship."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "new_address": {"type": "string"},
            },
            "required": ["customer_id", "new_address"],
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Issue a refund for a delivered order. Input: order_id, amount_usd, "
            "reason (short string). Returns a refund confirmation ID. "
            "NOTE: refunds above the company policy threshold will be rejected "
            "automatically by a server-side guard — if that happens, you must "
            "fall back to escalate_to_human."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount_usd": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["order_id", "amount_usd", "reason"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Flag this conversation for a tier-2 human support agent. Use when "
            "the automated tools block an action (e.g. refund over policy "
            "threshold), or when the case is ambiguous. Input: a reason string "
            "summarizing why escalation is needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]

# =============================================================================
# Tool implementations — return STRUCTURED errors, not bare strings (W04)
# =============================================================================

def _ok(payload: dict) -> dict:
    return {"isError": False, **payload}


def _err(category: str, retryable: bool, message: str, **extra) -> dict:
    return {
        "isError": True,
        "errorCategory": category,
        "isRetryable": retryable,
        "message": message,
        **extra,
    }


def _tool_get_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return _err("not_found", False, f"No order named {order_id}.")
    return _ok({"order_id": order_id, **order})


def _tool_get_customer(customer_id: str) -> dict:
    cust = CUSTOMERS.get(customer_id)
    if not cust:
        return _err("not_found", False, f"No customer named {customer_id}.")
    return _ok({"customer_id": customer_id, **cust})


def _tool_update_shipping_address(customer_id: str, new_address: str) -> dict:
    if customer_id not in CUSTOMERS:
        return _err("not_found", False, f"No customer {customer_id}.")
    CUSTOMERS[customer_id]["shipping_address"] = new_address
    return _ok({"updated": "shipping_address", "new_value": new_address})


def _tool_set_billing_address(customer_id: str, new_address: str) -> dict:
    if customer_id not in CUSTOMERS:
        return _err("not_found", False, f"No customer {customer_id}.")
    CUSTOMERS[customer_id]["billing_address"] = new_address
    return _ok({"updated": "billing_address", "new_value": new_address})


def _tool_issue_refund(order_id: str, amount_usd: float, reason: str) -> dict:
    # NOTE: the $500 check is NOT here — it's in the PreToolUse hook.
    # The hook is the deterministic gate; this function just runs the action.
    conf = f"RF-{len(REFUNDS) + 1001}"
    REFUNDS.append(
        {"confirmation_id": conf, "order_id": order_id,
         "amount_usd": amount_usd, "reason": reason}
    )
    return _ok({"confirmation_id": conf, "refunded_usd": amount_usd})


def _tool_escalate_to_human(reason: str) -> dict:
    ESCALATIONS.append({"reason": reason, "at": TODAY.isoformat()})
    return _ok({"escalated": True, "queue": "tier-2-support", "reason": reason})


# =============================================================================
# W03 — PreToolUse hook: the DETERMINISTIC $500 refund gate.
# =============================================================================
#
# A hook runs BEFORE the tool executes. It can:
#   - allow the call (return None or allow=True)
#   - block the call and return a synthesized tool_result the model will see
#     just as if the tool itself refused.
#
# This is the exam-critical pattern: the $500 rule is NOT in the system prompt.
# The system prompt is probabilistic; the hook is deterministic. The model
# literally cannot bypass the hook no matter what a cleverly worded message says.

REFUND_POLICY_THRESHOLD_USD = 500.00


def pre_tool_use_hook(tool_name: str, tool_input: dict) -> dict | None:
    """Return None to allow the call; return a dict to BLOCK it with that result."""
    if tool_name == "issue_refund":
        amount = float(tool_input.get("amount_usd", 0))
        if amount > REFUND_POLICY_THRESHOLD_USD:
            # Structured error — the model sees this as the tool's own response.
            return _err(
                "policy_violation",
                retryable=False,
                message=(
                    f"Refund amount ${amount:.2f} exceeds the automated limit "
                    f"of ${REFUND_POLICY_THRESHOLD_USD:.2f}. This refund cannot "
                    f"be processed automatically. Please escalate to a human "
                    f"agent by calling escalate_to_human with a clear reason."
                ),
                threshold_usd=REFUND_POLICY_THRESHOLD_USD,
                attempted_amount_usd=amount,
            )
    return None  # allow


# =============================================================================
# Dispatch
# =============================================================================

DISPATCH = {
    "get_order": _tool_get_order,
    "get_customer": _tool_get_customer,
    "update_shipping_address": _tool_update_shipping_address,
    "set_billing_address": _tool_set_billing_address,
    "issue_refund": _tool_issue_refund,
    "escalate_to_human": _tool_escalate_to_human,
}


def run_tool_with_hook(name: str, tool_input: dict) -> str:
    """Run the hook; if it blocks, return the hook's synthesized result.
    Otherwise run the real tool."""
    blocked = pre_tool_use_hook(name, tool_input)
    if blocked is not None:
        print(f"  [HOOK BLOCKED {name}] → {blocked['message']}")
        return json.dumps(blocked)
    result = DISPATCH[name](**tool_input)
    return json.dumps(result)


# =============================================================================
# The agentic loop (W01 skeleton — same shape as every prior week)
# =============================================================================

SYSTEM = (
    "You are a customer-support agent. Customers may raise MULTIPLE concerns in "
    "a single message; handle each concern and produce ONE unified reply at the "
    "end. Use tools to look up facts before acting. Prefer calling independent "
    "lookups IN PARALLEL (same turn). If a tool returns a policy_violation "
    "error, do NOT retry — fall back to escalate_to_human. Close every "
    "conversation with a warm, specific, customer-facing summary."
)


def agentic_loop(user_input: str, safety_fuse: int = 25, verbose: bool = True) -> str:
    messages = [{"role": "user", "content": user_input}]

    for i in range(safety_fuse):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if verbose:
            print(f"\n--- iter {i} | stop_reason={resp.stop_reason} ---")
            for b in resp.content:
                if b.type == "text":
                    print(f"  [text] {b.text[:300]}{'...' if len(b.text) > 300 else ''}")
                elif b.type == "tool_use":
                    print(f"  [tool_use id={b.id}] {b.name}({b.input})")

        # W01 — branch on stop_reason, NEVER on text parsing.
        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            # W01 — bundle ALL tool_results into ONE user turn.
            tool_results = []
            for b in resp.content:
                if b.type == "tool_use":
                    result_str = run_tool_with_hook(b.name, b.input)
                    if verbose:
                        print(f"  [tool_result {b.id}] {result_str}")
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": b.id,
                         "content": result_str}
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        if resp.stop_reason == "max_tokens":
            # W01 — never silently treat truncation as completion.
            raise RuntimeError("Response truncated (max_tokens); raise the cap.")

        raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError("safety fuse tripped — loop did not terminate naturally")


# =============================================================================
# Entry point — the multi-concern message
# =============================================================================

if __name__ == "__main__":
    customer_message = (
        "Hi, I'm Noa (customer C-99). A few things in one message, sorry:\n"
        "  (1) I'd like a refund on order ORD-2001 — the monitor arrived with "
        "      a dead pixel. The order was $649.\n"
        "  (2) Please update where you ship my orders to: 45 Rothschild Blvd, "
        "      Tel Aviv, IL. (My billing card details haven't changed.)\n"
        "  (3) Also — am I still at Gold loyalty tier? Just curious.\n"
        "Thanks!"
    )

    print("=" * 70)
    print("CUSTOMER MESSAGE:")
    print(customer_message)
    print("=" * 70)

    final = agentic_loop(customer_message)

    print("\n\n" + "=" * 70)
    print("FINAL REPLY TO CUSTOMER")
    print("=" * 70)
    print(final)
    print("\n" + "=" * 70)
    print(f"REFUNDS ISSUED: {REFUNDS}")
    print(f"ESCALATIONS:   {ESCALATIONS}")
    print(f"SHIPPING ADDR: {CUSTOMERS['C-99']['shipping_address']}")
    print(f"BILLING ADDR:  {CUSTOMERS['C-99']['billing_address']}  (should be unchanged)")
    print("=" * 70)


# =============================================================================
# Variations to try (manual experiments — highly recommended)
# =============================================================================
#
# V1. Remove the hook and put "Never issue refunds over $500" at the END of the
#     system prompt. Run 5 times. Eventually the model will comply with the
#     customer's implicit pressure and call issue_refund(649). That failure is
#     exactly why deterministic > probabilistic. (Exam theme A.)
#
# V2. Replace the descriptions on update_shipping_address and set_billing_address
#     with both equal to "Update an address on a customer account." Run again.
#     Watch the model guess — often wrong. Bad descriptions = unreliable
#     selection. (W04, task statement 2.1.)
#
# V3. Raise the hook threshold to $10_000 so nothing is blocked. The agent will
#     happily refund $649 and never escalate — good for seeing that the ESCALATIONS
#     list stays empty when the hook doesn't fire.
#
# V4. Add a third near-similar tool `update_delivery_address` with the same
#     shape. Now the model has 3 candidates. Does it still pick the right one?
#     (Tool crowding degrades selection — W04 rule of thumb: 4–5 tools max.)
#
# V5. Feed the agent ONLY concern (2). Watch it NOT call get_order — because
#     the model is good at picking only the tools it needs when the task is
#     narrow. Contrast with the full message above, where it calls 3 lookups
#     in parallel.
