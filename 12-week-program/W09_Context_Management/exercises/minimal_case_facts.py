"""
W09 — Minimal "case facts" pattern demo.

Point of this exercise:
    Show, in the smallest possible runnable form, WHY naive progressive
    summarization silently drops the things that matter most (order IDs,
    amounts, dates, policy references), and HOW extracting a persistent
    `case_facts` block fixes it.

No real API calls — the "LLM summarizer" here is a deliberately lossy stub
that mimics what real summarization does: it keeps the gist, drops the
numbers. This way the exercise runs offline and the point is crisp.

The demo has three parts:
    1. A fake 10-turn support conversation with a defective-headphones refund.
    2. NAIVE mode: feed the whole conversation through the lossy summarizer,
       then ask "what was the refund amount / order id?" — it's gone.
    3. CASE-FACTS mode: maintain a structured `case_facts` dict per turn,
       re-inject it at the top of every "context snapshot". The numbers
       survive even though the dialogue is summarized.

Run:  python minimal_case_facts.py
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Fake 10-turn support conversation (defective-headphones refund case)
# ---------------------------------------------------------------------------

CONVERSATION: list[tuple[str, str]] = [
    ("customer", "Hi, my wireless headphones stopped working after a week."),
    ("agent", "I'm sorry to hear that. Could you share the order ID?"),
    ("customer", "It's ORD-1001. I bought them on 2026-04-11."),
    ("agent", "Thanks. Looking up ORD-1001 now."),
    ("agent", "I can see ORD-1001: Wireless headphones, $149.00, delivered 2026-04-15."),
    ("customer", "Right. I'd like a full refund please."),
    ("agent", "You're within the 30-day refund window (refund_window_30d). Approved."),
    ("agent", "I've initiated a refund of $149.00 to your original payment method."),
    ("customer", "Great, thanks!"),
    ("agent", "Confirmation RF-1001. You'll see the $149.00 credit in 3-5 business days."),
]


# ---------------------------------------------------------------------------
# Lossy summarizer stub
# ---------------------------------------------------------------------------
# Real LLM summarization keeps the meaning and drops specific values.
# We mimic that here by stripping all numbers, IDs, and date-like tokens from
# the turns before joining them. This is deliberately obvious so you can SEE
# what gets lost without needing a real API call.

_ID_PATTERN = re.compile(r"\b(?:ORD|RF|C)-\d+\b")
_AMOUNT_PATTERN = re.compile(r"\$\d+(?:\.\d+)?")
_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_POLICY_PATTERN = re.compile(r"\b[a-z_]+_\d+[a-z]?\b")  # e.g. refund_window_30d


def lossy_summarize(turns: list[tuple[str, str]]) -> str:
    """Mimic naive LLM summarization: keep the gist, drop the specifics."""
    stripped = []
    for role, text in turns:
        t = _ID_PATTERN.sub("[ID]", text)
        t = _AMOUNT_PATTERN.sub("[AMOUNT]", t)
        t = _DATE_PATTERN.sub("[DATE]", t)
        t = _POLICY_PATTERN.sub("[POLICY]", t)
        stripped.append(f"{role}: {t}")
    # "summary" sentence — just a concatenation with redactions
    return (
        "Summary of conversation so far:\n"
        + " ".join(stripped)
        + "\nCustomer was helped with a refund."
    )


# ---------------------------------------------------------------------------
# Case facts block
# ---------------------------------------------------------------------------

@dataclass
class CaseFacts:
    """Durable values that MUST survive summarization.

    Rule: if a human paraphrasing the transcript would lose it, put it here.
    """

    order_id: str | None = None
    customer_id: str | None = None
    issue_type: str | None = None
    amount_usd: float | None = None
    purchase_date: str | None = None
    delivery_date: str | None = None
    policy_references: list[str] = field(default_factory=list)
    agreed_actions: list[str] = field(default_factory=list)
    confirmation_id: str | None = None

    def to_block(self) -> str:
        """Render as the block you re-inject at the TOP of every turn."""
        return (
            "## CURRENT CASE FACTS (authoritative — use these over the dialogue)\n"
            + json.dumps(self.__dict__, indent=2, default=str)
        )


def extract_facts_from_turn(facts: CaseFacts, role: str, text: str) -> None:
    """Update the case_facts block from a new turn.

    In a real agent this would be a structured tool call, an LLM extraction,
    or output from the tool wrappers themselves. Here it's regex-based so the
    demo is deterministic and runnable with no API key.
    """
    if m := _ID_PATTERN.search(text):
        tok = m.group()
        if tok.startswith("ORD-"):
            facts.order_id = tok
        elif tok.startswith("C-"):
            facts.customer_id = tok
        elif tok.startswith("RF-"):
            facts.confirmation_id = tok

    if m := _AMOUNT_PATTERN.search(text):
        facts.amount_usd = float(m.group().lstrip("$"))

    for m in _DATE_PATTERN.finditer(text):
        d = m.group()
        # first date seen = purchase, second = delivery (naive heuristic
        # sufficient for this demo; real agents would rely on tool outputs)
        if facts.purchase_date is None:
            facts.purchase_date = d
        elif facts.delivery_date is None and d != facts.purchase_date:
            facts.delivery_date = d

    for m in _POLICY_PATTERN.finditer(text):
        ref = m.group()
        if ref not in facts.policy_references:
            facts.policy_references.append(ref)

    if "refund" in text.lower() and "approved" in text.lower():
        if "full_refund_approved" not in facts.agreed_actions:
            facts.agreed_actions.append("full_refund_approved")

    if "stopped working" in text.lower() or "defective" in text.lower():
        facts.issue_type = facts.issue_type or "defective_product"


# ---------------------------------------------------------------------------
# The two modes
# ---------------------------------------------------------------------------

def context_naive(turns: list[tuple[str, str]]) -> str:
    """Naive: just summarize. Watch the numbers disappear."""
    return lossy_summarize(turns)


def context_with_case_facts(
    turns: list[tuple[str, str]], facts: CaseFacts
) -> str:
    """Case-facts mode: put the structured block at the START, let the
    summarizer do whatever it likes with the dialogue."""
    return (
        facts.to_block()
        + "\n\n"
        + lossy_summarize(turns)
        + "\n\n"
        # Repeat at the END too — position-aware ordering, start + end.
        + facts.to_block()
    )


# ---------------------------------------------------------------------------
# Simulated "later turn" question that needs the facts
# ---------------------------------------------------------------------------

def can_answer(context: str) -> dict[str, bool]:
    """Very simple check: does the context still contain the critical values?

    This stands in for "can the agent still answer a question that depends on
    these values". If the numbers aren't in the context, the agent has no way
    to ground the answer.
    """
    return {
        "has_order_id": "ORD-1001" in context,
        "has_amount": "149.00" in context or "149" in context,
        "has_purchase_date": "2026-04-11" in context,
        "has_delivery_date": "2026-04-15" in context,
        "has_policy_ref": "refund_window_30d" in context,
        "has_confirmation": "RF-1001" in context,
    }


# ---------------------------------------------------------------------------
# Run the demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Build the case_facts block progressively, turn by turn, the way an
    # agent's code would update it each iteration.
    facts = CaseFacts()
    for role, text in CONVERSATION:
        extract_facts_from_turn(facts, role, text)

    naive_ctx = context_naive(CONVERSATION)
    rich_ctx = context_with_case_facts(CONVERSATION, facts)

    print("=" * 72)
    print("NAIVE MODE — history run through a lossy summarizer, no case_facts")
    print("=" * 72)
    print(naive_ctx)
    print()
    print("What survived?", json.dumps(can_answer(naive_ctx), indent=2))

    print()
    print("=" * 72)
    print("CASE-FACTS MODE — same lossy summarizer, but case_facts at start+end")
    print("=" * 72)
    print(rich_ctx)
    print()
    print("What survived?", json.dumps(can_answer(rich_ctx), indent=2))

    print()
    print("=" * 72)
    print("TAKEAWAY")
    print("=" * 72)
    print(
        "Naive summarization kept the GIST ('customer was helped with a refund')\n"
        "and deleted the NUMBERS. The agent can no longer tell the customer what\n"
        "the refund amount was, which order, or the confirmation ID.\n\n"
        "The case_facts block sits OUTSIDE the summarizable dialogue. Updated\n"
        "per turn, re-injected at the top (and the bottom, for position-aware\n"
        "ordering against 'lost in the middle'), it preserves the exact values\n"
        "the agent needs to act.\n\n"
        "This is the pattern the exam means by 'extract case facts into a\n"
        "persistent block'. It is not a prompt technique — it is a data\n"
        "structure your agent code maintains."
    )
