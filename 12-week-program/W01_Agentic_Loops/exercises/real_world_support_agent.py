"""
W01 — Real-world agentic loop: customer support refund agent.

Scenario:
    A customer writes in asking for a refund. The agent must:
      1. Look up the order by ID.
      2. Check the refund policy window.
      3. Check the customer's purchase history (loyalty signals).
      4. Decide whether to approve / deny / escalate the refund.
      5. If approved, issue it; always draft a customer-facing reply.

Why this exercise is useful for the exam:
    - Multi-tool (5 tools) — forces the model to pick correctly (tool descriptions matter).
    - Parallel tool calls — steps 1, 2, 3 are independent; the model will typically call
      them in a single assistant turn, which means the loop must bundle ALL tool_results
      into ONE user turn. This is the #1 place people get the loop shape wrong.
    - Natural multi-iteration termination via stop_reason, not heuristics.
    - Realistic enough to map onto actual product work.

Data is fake and in-memory so it runs without any real backend.

Run: ANTHROPIC_API_KEY=... python real_world_support_agent.py
"""

from __future__ import annotations
import json
from datetime import datetime, timedelta

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Fake backend (stands in for DB / Stripe / CRM)
# ---------------------------------------------------------------------------

TODAY = datetime(2026, 4, 23)

ORDERS = {
    "ORD-1001": {
        "customer_id": "C-77",
        "item": "Wireless headphones",
        "amount_usd": 149.00,
        "ordered_at": (TODAY - timedelta(days=12)).isoformat(),
        "status": "delivered",
        "delivered_at": (TODAY - timedelta(days=8)).isoformat(),
    },
    "ORD-1002": {
        "customer_id": "C-77",
        "item": "USB-C cable",
        "amount_usd": 19.00,
        "ordered_at": (TODAY - timedelta(days=95)).isoformat(),
        "status": "delivered",
        "delivered_at": (TODAY - timedelta(days=90)).isoformat(),
    },
}

CUSTOMERS = {
    "C-77": {
        "name": "Dana Levi",
        "email": "dana@example.com",
        "lifetime_value_usd": 1_240.00,
        "signup_year": 2021,
        "total_orders": 14,
    },
}

POLICY = {
    "refund_window_days": 30,
    "loyalty_override_days": 60,
    "loyalty_threshold_ltv_usd": 1_000.00,
    "escalation_threshold_usd": 500.00,
}

REFUNDS_ISSUED: list[dict] = []

# ---------------------------------------------------------------------------
# Tools exposed to the model
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_order",
        "description": (
            "Fetch an order by order ID. Returns item, amount, order date, delivery "
            "date, and status. Use this first when a customer references an order."
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
            "Fetch customer profile by customer ID. Returns name, email, lifetime "
            "spend, signup year, and total order count. Use this when you need "
            "loyalty signals to apply the loyalty-override refund window."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_refund_policy",
        "description": (
            "Fetch the current refund policy: standard window in days, loyalty "
            "override window, loyalty threshold (lifetime-value USD), and the USD "
            "amount above which refunds must be escalated to a human agent."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "issue_refund",
        "description": (
            "Issue a refund for an order. Call this ONLY after you've confirmed "
            "eligibility via get_order + get_refund_policy (+ get_customer for "
            "loyalty overrides). Returns a refund confirmation ID."
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
            "Flag this conversation for a human agent. Use when the refund amount "
            "is above the escalation threshold, or when the eligibility decision "
            "is ambiguous and you don't want to auto-decide."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool implementations (this is YOUR code — the model does not execute these)
# ---------------------------------------------------------------------------

def _tool_get_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "not_found", "order_id": order_id}
    return {"order_id": order_id, **order}


def _tool_get_customer(customer_id: str) -> dict:
    cust = CUSTOMERS.get(customer_id)
    if not cust:
        return {"error": "not_found", "customer_id": customer_id}
    return {"customer_id": customer_id, **cust}


def _tool_get_refund_policy() -> dict:
    return POLICY


def _tool_issue_refund(order_id: str, amount_usd: float, reason: str) -> dict:
    confirmation = f"RF-{len(REFUNDS_ISSUED) + 1001}"
    record = {
        "confirmation_id": confirmation,
        "order_id": order_id,
        "amount_usd": amount_usd,
        "reason": reason,
        "issued_at": TODAY.isoformat(),
    }
    REFUNDS_ISSUED.append(record)
    return record


def _tool_escalate_to_human(reason: str) -> dict:
    return {"escalated": True, "reason": reason, "queue": "tier-2-support"}


def run_tool(name: str, tool_input: dict) -> str:
    dispatch = {
        "get_order": _tool_get_order,
        "get_customer": _tool_get_customer,
        "get_refund_policy": _tool_get_refund_policy,
        "issue_refund": _tool_issue_refund,
        "escalate_to_human": _tool_escalate_to_human,
    }
    result = dispatch[name](**tool_input)
    # tool_result content is commonly a string; JSON stringify for clarity.
    return json.dumps(result)


# ---------------------------------------------------------------------------
# The agentic loop
# ---------------------------------------------------------------------------

SYSTEM = (
    "You are a customer support agent. When a customer asks for a refund, use "
    "the tools to verify the order, look up the refund policy, and check "
    "customer loyalty signals. Approve the refund if it's within policy, or "
    "within the loyalty override window for high-LTV customers. Escalate to a "
    "human if the refund exceeds the escalation threshold, or if the case is "
    "ambiguous. Always end your turn with a short, warm reply addressed to the "
    "customer summarizing what you did."
)


def agentic_loop(user_input: str, safety_fuse: int = 25, verbose: bool = True) -> str:
    messages = [{"role": "user", "content": user_input}]

    for iteration in range(safety_fuse):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if verbose:
            print(f"\n--- iter {iteration} | stop_reason={resp.stop_reason} ---")
            for block in resp.content:
                if block.type == "text":
                    print(f"[text] {block.text}")
                elif block.type == "tool_use":
                    print(f"[tool_use] {block.name}({block.input})")

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            # Collect ALL tool_use blocks from this turn and send ALL results back
            # in ONE user message. This is the exam-critical invariant.
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
                    if verbose:
                        print(f"[tool_result for {block.id}] {result}")
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError("safety fuse tripped — loop did not terminate naturally")


# ---------------------------------------------------------------------------
# Try it
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    customer_message = (
        "Hi, I'm Dana (customer C-77). I'd like a refund on order ORD-1001 — "
        "the headphones stopped working after a week. Thanks!"
    )
    final_reply = agentic_loop(customer_message)
    print("\n===== FINAL REPLY TO CUSTOMER =====")
    print(final_reply)
    print("\n===== REFUNDS ISSUED =====")
    print(REFUNDS_ISSUED)
