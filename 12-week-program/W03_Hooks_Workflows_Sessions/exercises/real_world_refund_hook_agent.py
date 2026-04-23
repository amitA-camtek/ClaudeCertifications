"""
W03 — Real-world agentic loop WITH a PreToolUse hook: refund agent with
deterministic over-cap enforcement.

Scenario:
    Same customer-support world as W01, but now policy says: refunds over
    $500 MUST be escalated to a human. The system prompt says so too — and
    sometimes the model obeys, sometimes it doesn't. We don't accept
    "sometimes." So we wire a PreToolUse hook that deterministically blocks
    any `issue_refund` call with amount_usd > 500 and feeds the reason back
    to the model so it can recover by calling `escalate_to_human` instead.

Why this exercise is useful for the exam:
    * Shows the PreToolUse lifecycle: hook fires BEFORE the tool runs; the
      tool body never executes on a blocked call; the model sees the hook's
      `reason` string as the tool_result.
    * Shows recovery: the model, seeing "blocked because > $500 — escalate
      instead," pivots to `escalate_to_human` in the next iteration.
    * Demonstrates the W03 theme: deterministic enforcement (the hook)
      beats probabilistic guidance (the system prompt). Even if the prompt
      rule fails, the refund still doesn't go through.
    * Verbose trace output — you can read the loop turn-by-turn and map
      each moment to exam concepts.

Data is fake and in-memory so this runs without any real backend.

Run: ANTHROPIC_API_KEY=... python real_world_refund_hook_agent.py
"""

from __future__ import annotations
import json
from datetime import datetime, timedelta

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# Fake backend (stands in for DB / Stripe / CRM)
# =============================================================================

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
    # The interesting one: an expensive item that MUST trigger the hook.
    "ORD-2002": {
        "customer_id": "C-77",
        "item": "Pro audio interface",
        "amount_usd": 820.00,
        "ordered_at": (TODAY - timedelta(days=5)).isoformat(),
        "status": "delivered",
        "delivered_at": (TODAY - timedelta(days=2)).isoformat(),
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
    "escalation_threshold_usd": 500.00,  # The hook enforces this deterministically.
}

# Side-effect tracking. A refund "actually happened" only if it appears here.
# This is how we verify the hook worked: after a blocked run, this stays empty.
REFUNDS_ISSUED: list[dict] = []
ESCALATIONS: list[dict] = []
HOOK_TRACE: list[dict] = []  # every PreToolUse decision we made, for audit.


# =============================================================================
# Tools exposed to the model
# =============================================================================

TOOLS = [
    {
        "name": "get_order",
        "description": (
            "Fetch an order by order ID. Returns item, amount, order date, "
            "delivery date, and status. Use this first when a customer "
            "references an order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "get_refund_policy",
        "description": (
            "Fetch the current refund policy: standard window in days and "
            "the USD amount above which refunds must be escalated."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "issue_refund",
        "description": (
            "Issue a refund for an order. Call this ONLY after you've "
            "confirmed eligibility via get_order + get_refund_policy. "
            "Returns a refund confirmation ID."
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
            "Flag this conversation for a human agent. Use when the refund "
            "amount is above the escalation threshold, or when eligibility "
            "is ambiguous. Returns a ticket ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["reason"],
        },
    },
]


# =============================================================================
# Tool implementations (YOUR code — the model does not execute these)
# =============================================================================

def _tool_get_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "not_found", "order_id": order_id}
    return {"order_id": order_id, **order}


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


def _tool_escalate_to_human(reason: str, order_id: str | None = None) -> dict:
    ticket = f"ESC-{len(ESCALATIONS) + 501}"
    record = {
        "ticket_id": ticket,
        "order_id": order_id,
        "reason": reason,
        "queue": "tier-2-support",
    }
    ESCALATIONS.append(record)
    return record


def run_tool(name: str, tool_input: dict) -> str:
    dispatch = {
        "get_order": _tool_get_order,
        "get_refund_policy": _tool_get_refund_policy,
        "issue_refund": _tool_issue_refund,
        "escalate_to_human": _tool_escalate_to_human,
    }
    result = dispatch[name](**tool_input)
    return json.dumps(result)


# =============================================================================
# The PreToolUse hook — DETERMINISTIC ENFORCEMENT
# =============================================================================
#
# This is the exam-critical piece. In production under Claude Code this would
# be an external script registered in `.claude/settings.json` and invoked by
# the harness via stdin/stdout JSON. Here, because we're running a raw
# Messages API loop ourselves, we simulate the same contract in-process: the
# same pure function (`decide`) would work unchanged as a standalone hook
# script.
#
# See minimal_hook_example.py in this folder for the standalone-script
# version of the same logic + the settings.json wiring.
# =============================================================================

REFUND_CAP_USD = POLICY["escalation_threshold_usd"]


def pretool_hook_decide(event: dict) -> dict:
    """
    Pure function matching the hook-script contract:
      input: {tool_name, tool_input, ...}
      output: {decision: "approve" | "block", reason?: str}
    """
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}

    if tool_name != "issue_refund":
        return {"decision": "approve"}

    try:
        amount = float(tool_input.get("amount_usd", 0))
    except (TypeError, ValueError):
        return {
            "decision": "block",
            "reason": (
                "issue_refund was called with a non-numeric amount_usd. "
                "Refusing. Call escalate_to_human if the amount is unclear."
            ),
        }

    if amount > REFUND_CAP_USD:
        return {
            "decision": "block",
            "reason": (
                f"Refund amount ${amount:.2f} exceeds the ${REFUND_CAP_USD:.2f} "
                f"auto-approve cap. Do NOT retry issue_refund. Call "
                f"escalate_to_human with order_id and a brief reason instead."
            ),
        }

    return {"decision": "approve"}


def apply_pretool_hook(tool_name: str, tool_input: dict) -> tuple[bool, str | None]:
    """
    Run the hook. Returns (blocked, reason_if_blocked).

    On block, the TOOL MUST NOT RUN. Instead, `reason` becomes the tool_result
    returned to the model — exactly as the real Claude Code harness does it.
    """
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
    }
    decision = pretool_hook_decide(event)
    HOOK_TRACE.append({"event": event, "decision": decision})

    print(f"    [PreToolUse hook] tool={tool_name} -> {decision}")

    if decision.get("decision") == "block":
        return True, decision.get("reason", "blocked by hook")
    return False, None


# =============================================================================
# The agentic loop (W01 shape + the hook interception)
# =============================================================================

SYSTEM = (
    "You are a customer support refund agent. When a customer asks for a "
    "refund, use get_order and get_refund_policy to verify eligibility. "
    "Approve refunds within policy. If the amount exceeds the escalation "
    "threshold, call escalate_to_human instead of issue_refund. Always "
    "finish with a short, warm reply to the customer summarizing what you "
    "did. If a tool call is blocked, read the returned reason and pick a "
    "different tool that satisfies it — do not retry the same call."
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
                    print(f"  [text] {block.text}")
                elif block.type == "tool_use":
                    print(f"  [tool_use] {block.name}({block.input})")

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            # Gather all tool_use blocks from this assistant turn. For each:
            #   1. Run the PreToolUse hook.
            #   2. If the hook blocks, DO NOT execute the tool; the hook's
            #      `reason` becomes the tool_result the model sees.
            #   3. Otherwise, run the tool normally.
            # All tool_result blocks go back in ONE user turn (W01 invariant).
            tool_results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue

                blocked, reason = apply_pretool_hook(block.name, dict(block.input))
                if blocked:
                    # Critical: the tool's implementation is NOT called. The
                    # model sees the hook's reason and can recover on the
                    # next iteration by choosing a different tool.
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"[BLOCKED BY HOOK] {reason}",
                        "is_error": True,
                    })
                    if verbose:
                        print(f"  [tool_result for {block.id}] BLOCKED: {reason}")
                    continue

                result = run_tool(block.name, dict(block.input))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
                if verbose:
                    print(f"  [tool_result for {block.id}] {result}")

            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError("safety fuse tripped — loop did not terminate naturally")


# =============================================================================
# Try it
# =============================================================================

if __name__ == "__main__":
    # This is the expensive-item case. Prompt alone would *probably* steer the
    # model to `escalate_to_human`, but "probably" is the whole problem. The
    # PreToolUse hook makes it 100%.
    customer_message = (
        "Hi, I'm Dana (customer C-77). I'd like a refund on order ORD-2002, "
        "the Pro audio interface — it arrived defective. Please process the "
        "refund. Thanks!"
    )
    print("===== INPUT =====")
    print(customer_message)

    final_reply = agentic_loop(customer_message)

    print("\n\n===== FINAL REPLY TO CUSTOMER =====")
    print(final_reply)
    print("\n===== SIDE EFFECTS =====")
    print(f"REFUNDS_ISSUED : {REFUNDS_ISSUED}")
    print(f"ESCALATIONS    : {ESCALATIONS}")
    print("\n===== HOOK TRACE =====")
    for entry in HOOK_TRACE:
        print(json.dumps(entry, indent=2))

    # Invariant check — the exam-critical outcome:
    #   no refund over $500 should ever appear in REFUNDS_ISSUED,
    #   regardless of what the model tried to do.
    assert all(r["amount_usd"] <= REFUND_CAP_USD for r in REFUNDS_ISSUED), (
        "FATAL: a refund above the cap was issued. The hook did not run."
    )
    print("\n[invariant OK] No refund above the $500 cap was issued.")
