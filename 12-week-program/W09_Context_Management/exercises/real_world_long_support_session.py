"""
W09 — Real-world long-running support session.

Scenario:
    A customer writes in about a defective product. Over 15+ turns the agent:
      - Handles an ambiguous lookup (3 candidate orders for "my recent order")
      - Hits a transient tool timeout and recovers locally
      - Encounters a policy gap (unusual request not covered by policy)
      - Decides whether to escalate using the correct triggers, and
        explicitly IGNORES the distractor signals (sentiment, self-reported
        confidence)

Everything the exam tests for Domain 5.1-5.3 is exercised here:

    1. Case facts block (`CaseFacts`) is updated every turn and re-injected
       at the TOP and BOTTOM of every prompt context. Position-aware
       ordering against the "lost in the middle" effect.
    2. Verbose tool outputs (40 fields) are trimmed to 5 relevant fields
       at the wrapper boundary before appearing in history.
    3. Escalation decision is structured: ONLY triggers on
           (a) explicit customer request
           (b) identified policy gap
           (c) inability to progress after >= 2 concrete attempts
       It does NOT trigger on sentiment ("customer sounds frustrated") or
       self-reported confidence ("I'm 3/10 confident"). Those signals are
       deliberately present in the transcript to show they're ignored.
    4. Tool failures return structured errors:
           {failure_type, attempted_query, partial_results, alternatives}
       Never a generic "operation failed", never a silent empty result.
    5. Multiple-match handling: the agent asks for a distinguishing
       identifier instead of guessing.

This file is deliberately offline — no API calls. The "agent" is a scripted
decision function that reads the case_facts and the latest customer turn
and decides what to do next. That lets you SEE every decision rule the
exam asks about, and modify them to see the failure modes.

Run: python real_world_long_support_session.py
"""

from __future__ import annotations
import json
import random
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any


# =============================================================================
# Fake backend — deliberately returns a bloated 40-field order record so we
# can demonstrate trimming at the tool boundary.
# =============================================================================

ORDERS_BLOATED = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "C-77",
        "item": "Wireless headphones",
        "sku": "SKU-AX42",
        "amount_usd": 149.00,
        "currency": "USD",
        "tax_usd": 12.30,
        "shipping_usd": 0.00,
        "discount_usd": 0.00,
        "ordered_at": "2026-04-11",
        "shipped_at": "2026-04-12",
        "delivered_at": "2026-04-15",
        "status": "delivered",
        "warehouse_id": "WH-EU-03",
        "carrier": "DHL",
        "tracking_number": "DHL-884-221-9921",
        "carrier_events": [
            {"ts": "2026-04-12T09:01Z", "event": "picked_up"},
            {"ts": "2026-04-13T14:22Z", "event": "in_transit"},
            {"ts": "2026-04-15T10:07Z", "event": "delivered"},
        ],
        "payment_method": "visa_**_4242",
        "gift_wrap": False,
        "signature_required": False,
        "internal_flags": {"fraud_score": 0.02, "priority": "standard"},
        "fulfillment_notes": "",
        "returns_policy_snapshot": "refund_window_30d;loyalty_override_60d",
        "billing_zip": "10178",
        "shipping_zip": "10178",
        "promo_codes": [],
        "device_fingerprint": "fp-ab12cd34",
        "ab_cohort": "control",
        "notification_prefs": {"email": True, "sms": False},
        "loyalty_points_accrued": 149,
        "invoice_pdf_url": "[internal]/invoices/ORD-1001.pdf",
        "refund_history": [],
        "exchange_history": [],
        "chat_session_ids": ["sess-8812", "sess-9021"],
        "created_by_agent": "web",
        "last_modified_at": "2026-04-15T10:07Z",
        "raw_webhook_payloads": "[ ... 12 kB of JSON ... ]",
        "analytics_tags": ["category:audio", "brand:acme"],
        "customer_segments": ["loyal", "high_ltv"],
        "support_flags": [],
        "locale": "en-DE",
    },
    "ORD-0999": {
        "order_id": "ORD-0999",
        "customer_id": "C-77",
        "item": "USB-C cable (2m)",
        "amount_usd": 19.00,
        "ordered_at": "2026-04-10",
        "delivered_at": "2026-04-13",
        "status": "delivered",
        # (other 32 fields elided for brevity — same shape)
    },
    "ORD-0975": {
        "order_id": "ORD-0975",
        "customer_id": "C-77",
        "item": "Phone case (midnight blue)",
        "amount_usd": 24.00,
        "ordered_at": "2026-04-05",
        "delivered_at": "2026-04-08",
        "status": "delivered",
    },
}

POLICY = {
    "refund_window_days": 30,
    "loyalty_override_days": 60,
    "covered_reasons": ["defective_product", "wrong_item", "not_delivered"],
    # Note: NO provision for "change of mind after 45 days" — this is the
    # policy gap we'll hit later and escalate on.
}


# =============================================================================
# Tool wrappers — this is where TRIMMING happens.
# =============================================================================

RELEVANT_ORDER_FIELDS = {
    "order_id",
    "item",
    "amount_usd",
    "ordered_at",
    "delivered_at",
}


def tool_search_orders(customer_id: str, hint: str) -> dict:
    """Search the customer's recent orders by fuzzy hint.

    Returns a trimmed candidate list. If the hint matches > 1 order, we
    DO NOT pick for the agent — we return all candidates and let the agent
    ask the customer to disambiguate.
    """
    candidates = [
        o
        for o in ORDERS_BLOATED.values()
        if o.get("customer_id") == customer_id
    ]
    # Trim each candidate to only the 5 fields the agent needs.
    trimmed = [
        {k: o[k] for k in RELEVANT_ORDER_FIELDS if k in o} for o in candidates
    ]
    return {
        "failure_type": None,
        "attempted_query": {"customer_id": customer_id, "hint": hint},
        "partial_results": trimmed,
        "alternatives": [],
    }


def tool_get_order(order_id: str, _simulate_timeout: bool = False) -> dict:
    """Fetch an order by ID. Trim to 5 fields.

    If `_simulate_timeout` is True, return a STRUCTURED error (not a
    generic one, not a silent empty result).
    """
    if _simulate_timeout:
        return {
            "failure_type": "timeout",
            "attempted_query": {"order_id": order_id},
            "partial_results": [],
            "alternatives": [
                "retry_same_call",
                "search_orders_by_customer_id",
                "ask_user_for_alternate_identifier",
            ],
        }

    raw = ORDERS_BLOATED.get(order_id)
    if raw is None:
        return {
            "failure_type": "not_found",
            "attempted_query": {"order_id": order_id},
            "partial_results": [],
            "alternatives": ["search_orders_by_customer_id"],
        }

    trimmed = {k: raw[k] for k in RELEVANT_ORDER_FIELDS if k in raw}
    return {
        "failure_type": None,
        "attempted_query": {"order_id": order_id},
        "partial_results": [trimmed],
        "alternatives": [],
    }


def tool_check_policy(reason: str, days_since_purchase: int) -> dict:
    """Check whether the refund policy covers a given reason + age."""
    if reason not in POLICY["covered_reasons"]:
        return {
            "failure_type": "policy_gap",
            "attempted_query": {
                "reason": reason,
                "days_since_purchase": days_since_purchase,
            },
            "partial_results": [],
            "alternatives": ["escalate_to_human"],
        }
    if days_since_purchase > POLICY["refund_window_days"]:
        return {
            "failure_type": None,
            "attempted_query": {
                "reason": reason,
                "days_since_purchase": days_since_purchase,
            },
            "partial_results": [{"eligible": False, "within_window": False}],
            "alternatives": ["check_loyalty_override"],
        }
    return {
        "failure_type": None,
        "attempted_query": {
            "reason": reason,
            "days_since_purchase": days_since_purchase,
        },
        "partial_results": [{"eligible": True, "within_window": True}],
        "alternatives": [],
    }


# =============================================================================
# Case facts block — the durable-values store
# =============================================================================

@dataclass
class CaseFacts:
    order_id: str | None = None
    customer_id: str | None = None
    issue_type: str | None = None
    amount_usd: float | None = None
    purchase_date: str | None = None
    delivery_date: str | None = None
    policy_references: list[str] = field(default_factory=list)
    agreed_actions: list[str] = field(default_factory=list)
    confirmation_id: str | None = None

    def render_block(self) -> str:
        return (
            "## CURRENT CASE FACTS (authoritative — use these over dialogue)\n"
            + json.dumps(asdict(self), indent=2, default=str)
        )


# =============================================================================
# Attempt / escalation tracking — the ONLY escalation triggers that count
# =============================================================================

@dataclass
class EscalationState:
    """Tracks the three VALID escalation triggers.

    Explicitly omits sentiment and self-reported confidence. If you want to
    see the distractor logic, see the `BAD_MODE_*` flags in __main__.
    """

    explicit_customer_request: bool = False
    policy_gap_detected: bool = False
    failed_attempts: list[str] = field(default_factory=list)

    def should_escalate(self) -> tuple[bool, str | None]:
        if self.explicit_customer_request:
            return True, "explicit_customer_request"
        if self.policy_gap_detected:
            return True, "policy_gap_detected"
        if len(self.failed_attempts) >= 2:
            return True, "inability_to_progress"
        return False, None


# =============================================================================
# Position-aware context rendering
# =============================================================================

def render_context(
    system_role: str,
    case_facts: CaseFacts,
    history: list[dict],
    latest_user_msg: str,
) -> str:
    """Put case_facts at the START and repeat at the END. Section headers.

    The key point for the exam: do NOT rely on the model finding a fact
    buried in the middle of a 40-turn history. Surface it at start + end.
    """
    parts = []
    parts.append("## ROLE\n" + system_role)
    parts.append(case_facts.render_block())  # START

    parts.append("## POLICY\n" + json.dumps(POLICY, indent=2))
    parts.append("## CONVERSATION HISTORY\n" + _render_history(history))
    parts.append("## LATEST CUSTOMER MESSAGE\n" + latest_user_msg)

    parts.append(case_facts.render_block())  # END — same block repeated
    return "\n\n".join(parts)


def _render_history(history: list[dict]) -> str:
    lines = []
    for h in history:
        if h["kind"] == "msg":
            lines.append(f"[{h['role']}] {h['text']}")
        elif h["kind"] == "tool":
            # Tool results are already trimmed; show only what's relevant.
            lines.append(
                f"[tool:{h['name']}] "
                + json.dumps(h["result"], separators=(",", ":"))
            )
    return "\n".join(lines)


# =============================================================================
# Scripted "agent" decisions
# =============================================================================
# This stands in for what an LLM would do. We spell out the rules so the
# exam-relevant behavior is inspectable. Every decision below has a one-line
# comment tying it to a W09 concept.

@dataclass
class AgentDecision:
    reply_to_customer: str = ""
    tool_call: tuple[str, dict] | None = None
    escalate_reason: str | None = None
    terminate: bool = False


def agent_step(
    turn_idx: int,
    customer_msg: str,
    case_facts: CaseFacts,
    escalation: EscalationState,
    history: list[dict],
    *,
    bad_use_sentiment: bool = False,
    bad_use_self_confidence: bool = False,
) -> AgentDecision:
    """Script the agent's decision for each turn of the canned conversation.

    The `bad_*` flags let you see the distractor logic trigger incorrectly.
    Leave them False for the correct behavior the exam rewards.
    """

    msg_lower = customer_msg.lower()

    # -- Explicit human-escalation request (VALID trigger) ------------------
    if any(p in msg_lower for p in ("speak to a human", "human agent", "real person")):
        escalation.explicit_customer_request = True
        return AgentDecision(
            reply_to_customer=(
                "Understood — I'm handing you to a human agent right now. "
                "They'll have the full case context."
            ),
            escalate_reason="explicit_customer_request",
        )

    # -- DISTRACTOR (off by default) ----------------------------------------
    # These branches exist so you can flip the flags in __main__ and SEE the
    # agent make the wrong choice. In the default run they're skipped.
    if bad_use_sentiment and any(
        p in msg_lower for p in ("frustrated", "angry", "upset", "furious")
    ):
        # WRONG — sentiment is NOT a valid escalation trigger.
        return AgentDecision(
            reply_to_customer="[BAD MODE] Escalating because customer sounds frustrated.",
            escalate_reason="sentiment_BAD_TRIGGER",
        )
    if bad_use_self_confidence:
        fake_self_rated = random.choice([2, 3, 4])  # "I feel 3/10 confident"
        if fake_self_rated <= 4:
            # WRONG — self-reported confidence is miscalibrated.
            return AgentDecision(
                reply_to_customer="[BAD MODE] Escalating because I rated my confidence low.",
                escalate_reason="self_confidence_BAD_TRIGGER",
            )

    # -- Turn-by-turn scripted flow -----------------------------------------
    if turn_idx == 0:
        return AgentDecision(
            reply_to_customer=(
                "I'm sorry to hear that. Could you share your customer ID "
                "and the order you'd like to discuss?"
            )
        )

    if turn_idx == 2:
        # Customer gave customer_id but a fuzzy hint ("my recent order").
        case_facts.customer_id = "C-77"
        case_facts.issue_type = "defective_product"
        return AgentDecision(
            tool_call=("search_orders", {"customer_id": "C-77", "hint": "recent"})
        )

    if turn_idx == 3:
        # Tool returned 3 candidates. MULTIPLE-MATCH rule: ask, don't guess.
        return AgentDecision(
            reply_to_customer=(
                "I see 3 recent orders on your account. To make sure I work "
                "on the right one, could you share the order ID, the item "
                "name, or the exact purchase date?"
            )
        )

    if turn_idx == 5:
        # Customer gave ORD-1001. First tool call — simulate a timeout.
        return AgentDecision(
            tool_call=("get_order_with_timeout", {"order_id": "ORD-1001"})
        )

    if turn_idx == 6:
        # Timeout came back STRUCTURED. Local recovery: retry once.
        escalation.failed_attempts.append("get_order:timeout")
        return AgentDecision(
            tool_call=("get_order", {"order_id": "ORD-1001"})
        )

    if turn_idx == 7:
        # Success. Populate case_facts from the trimmed tool result.
        last = history[-1]
        if last["kind"] == "tool" and last["result"]["failure_type"] is None:
            row = last["result"]["partial_results"][0]
            case_facts.order_id = row["order_id"]
            case_facts.amount_usd = row["amount_usd"]
            case_facts.purchase_date = row["ordered_at"]
            case_facts.delivery_date = row["delivered_at"]
        return AgentDecision(
            tool_call=(
                "check_policy",
                {"reason": "defective_product", "days_since_purchase": 12},
            )
        )

    if turn_idx == 8:
        # Policy says eligible. Record it, tell the customer.
        case_facts.policy_references.append("refund_window_30d")
        case_facts.agreed_actions.append("full_refund_approved")
        return AgentDecision(
            reply_to_customer=(
                f"Confirmed: ORD-1001, Wireless headphones, $149.00. You're "
                f"within the 30-day window. I'll issue a full refund of "
                f"$149.00 now."
            )
        )

    if turn_idx == 10:
        # Customer asks for an unusual additional favor not covered by policy.
        # This is a POLICY GAP — valid escalation trigger.
        escalation.policy_gap_detected = True
        return AgentDecision(
            reply_to_customer=(
                "That additional request isn't something our policy covers, "
                "so I'll route you to a human agent who can make a call on "
                "it. Your refund for $149.00 on ORD-1001 is already approved "
                "— that stays in place."
            ),
            escalate_reason="policy_gap_detected",
        )

    if turn_idx == 12:
        case_facts.confirmation_id = "RF-1001"
        return AgentDecision(
            reply_to_customer=(
                f"Refund confirmation: RF-1001 for $149.00 on ORD-1001. "
                f"You'll see the credit in 3–5 business days. Human agent "
                f"is joining shortly for the other request."
            ),
            terminate=True,
        )

    # Default: acknowledge and wait.
    return AgentDecision(reply_to_customer="Thanks — one moment.")


# =============================================================================
# Scripted customer turns (15+ turns incl. tool results)
# =============================================================================

CUSTOMER_TURNS: list[str] = [
    "Hi, my headphones stopped working after a week. I'm really frustrated — this is the second time this has happened.",
    "",  # placeholder so turn indices align with agent_step's branches
    "I'm customer C-77. It was my recent order — the wireless headphones I think.",
    "",  # agent searched orders
    "",  # agent asked for disambiguation
    "Sorry, yes — it's ORD-1001, purchased 2026-04-11.",
    "",  # agent hit timeout
    "",  # agent retried successfully, fetched policy
    "",  # agent confirmed eligibility
    "Great, thank you. Also — can you waive the restocking fee on a different old order from last year too? It's been bothering me.",
    "",  # agent detected policy gap
    "Okay, that makes sense. Thanks for the refund though.",
    "",  # agent sent confirmation + handoff
]


# =============================================================================
# Driver
# =============================================================================

def run_session(
    *,
    bad_use_sentiment: bool = False,
    bad_use_self_confidence: bool = False,
) -> None:
    case_facts = CaseFacts()
    escalation = EscalationState()
    history: list[dict] = []
    tool_dispatch = {
        "search_orders": lambda **kw: tool_search_orders(**kw),
        "get_order": lambda **kw: tool_get_order(**kw, _simulate_timeout=False),
        "get_order_with_timeout": lambda **kw: tool_get_order(
            **kw, _simulate_timeout=True
        ),
        "check_policy": lambda **kw: tool_check_policy(**kw),
    }

    SYSTEM_ROLE = (
        "You are a customer support agent handling refund requests. Use the "
        "tools; respect policy; escalate ONLY on explicit request, policy "
        "gap, or inability to progress after 2+ concrete attempts."
    )

    for turn_idx, customer_msg in enumerate(CUSTOMER_TURNS):
        if customer_msg:
            history.append({"kind": "msg", "role": "customer", "text": customer_msg})
            print(f"\n--- TURN {turn_idx} | CUSTOMER ---")
            print(customer_msg)

        # Render the context the way it would go to the model: case_facts at
        # start AND end, with section headers.
        _ = render_context(SYSTEM_ROLE, case_facts, history, customer_msg)

        decision = agent_step(
            turn_idx,
            customer_msg,
            case_facts,
            escalation,
            history,
            bad_use_sentiment=bad_use_sentiment,
            bad_use_self_confidence=bad_use_self_confidence,
        )

        if decision.tool_call is not None:
            name, args = decision.tool_call
            result = tool_dispatch[name](**args)
            history.append({"kind": "tool", "name": name, "result": result})
            print(f"\n--- TURN {turn_idx} | AGENT → TOOL {name} ---")
            print(f"args: {args}")
            print(f"result (trimmed): {json.dumps(result, indent=2)}")
            continue

        if decision.reply_to_customer:
            history.append(
                {"kind": "msg", "role": "agent", "text": decision.reply_to_customer}
            )
            print(f"\n--- TURN {turn_idx} | AGENT ---")
            print(decision.reply_to_customer)

        if decision.escalate_reason:
            # Structured escalation — check against the valid triggers.
            should, reason = escalation.should_escalate()
            print(f"\n>>> ESCALATION CHECK: should={should} reason={reason}")
            if not should:
                print(
                    ">>> NOT escalating — the signal that fired wasn't a valid "
                    "trigger.\n>>> (This is what the distractor flags demonstrate.)"
                )

        if decision.terminate:
            break

    print("\n" + "=" * 72)
    print("FINAL CASE FACTS (durable, survived every turn):")
    print("=" * 72)
    print(json.dumps(asdict(case_facts), indent=2))
    print()
    print("ESCALATION STATE:")
    print(json.dumps(asdict(escalation), indent=2))


if __name__ == "__main__":
    print("=" * 72)
    print("CORRECT MODE — valid triggers only")
    print("=" * 72)
    run_session()

    # Uncomment to see the distractor (sentiment-triggered) behavior fire
    # on turn 0 because the customer wrote the word 'frustrated':
    #
    # print("\n\n" + "=" * 72)
    # print("BAD MODE — sentiment-triggered escalation (distractor)")
    # print("=" * 72)
    # run_session(bad_use_sentiment=True)
