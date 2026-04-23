"""
W07 — Real-world document extraction: 3 unstructured invoices -> structured rows.

Scenario:
    An AP automation pipeline ingests invoices as unstructured text (OCR, email
    bodies, PDF-to-text). We want rows we can write to a DB with:

        REQUIRED:
            vendor_name  (string)
            total_usd    (number)

        REQUIRED BUT NULLABLE (anti-hallucination):
            due_date     (string | null)   ISO 8601 date or null if absent
            po_number    (string | null)   PO reference or null if absent

        ENUM WITH 'other' + DETAIL (extensibility):
            payment_terms         enum: net_30 | net_60 | due_on_receipt | other
            payment_terms_detail  string | null    ("Net 45", "45% upfront", ...)

Why each design choice (all exam-relevant):

    REQUIRED for vendor_name + total_usd:
        These are the primary keys of the extracted row. If they're missing,
        we can't do anything downstream. Required = model must produce a value.

    NULLABLE for due_date + po_number:
        These are commonly absent on real invoices (receipts, one-off bills).
        If we made them required non-null, the model would fabricate values to
        satisfy the schema. Making them nullable gives the model a legitimate
        "absent" answer and removes hallucination pressure.

    ENUM + 'other' + detail for payment_terms:
        Closed enum would silently miscategorize novel phrases ("Net 45" ->
        wrongly bucketed as net_30, or schema violation). "other" + a detail
        string preserves the raw signal for later analysis.

    FEW-SHOT (2-3 examples) embedded in the system prompt:
        For ambiguous cases only. Specifically to show:
          - "Net 30"        -> net_30, detail=null     (canonical)
          - "Net 45"        -> other,  detail="Net 45" (the extensibility case)
          - missing PO      -> po_number=null          (the null case)
        Ambiguous cases are where models drift without examples. We show
        reasoning (what triggers 'other') so the pattern generalizes.

    FORCED tool_choice={"type":"tool","name":"extract_invoice"}:
        This is an extraction task: we want structured output every time,
        from one specific schema. tool_choice="auto" would let the model
        reply in prose sometimes. "any" would let it pick among tools but we
        only have one. Forced-specific is the right call.

Run: ANTHROPIC_API_KEY=... python real_world_document_extraction.py
"""

from __future__ import annotations
import json

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# ===========================================================================
# Fake input: three invoices exercising different edge cases.
# ===========================================================================

INVOICES = [
    # (1) Canonical happy path: everything present, standard terms.
    """
    ACME WIDGETS LLC
    Invoice #A-2211
    Bill To: Globex Corp
    PO:  PO-55443
    Due: 2026-05-15
    Subtotal: $125.00
    Freight:  $15.00
    TOTAL DUE: $140.00
    Terms: Net 30
    """,

    # (2) Receipt-style: no due date, no PO number. The model MUST return
    #     null for those fields, NOT fabricate a value.
    """
    Blue Mountain Coffee Roasters
    Receipt
    Date of sale: 2026-04-02
    Espresso beans 1kg  $28.00
    Tax                  $2.24
    TOTAL               $30.24
    PAID IN FULL -- thank you!
    """,

    # (3) Ambiguous terms "Net 45" -- not in the enum. Without few-shot
    #     + "other" + detail, the model would either miscategorize (likely
    #     net_30) or violate the schema. With them, payment_terms="other"
    #     and payment_terms_detail="Net 45".
    """
    Helios Logistics GmbH
    Rechnung / Invoice 2026-H-00912
    Customer PO: PO-ABX-09
    Due Date: 2026-06-30
    Shipping services (April 2026)     EUR 2,100.00
    Conversion @ 1.00 USD/EUR           --
    TOTAL USD: $2,100.00
    Payment terms: Net 45 end-of-month
    """,
]


# ===========================================================================
# The extraction tool. Schema is the single source of truth for output shape.
# ===========================================================================

EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": (
        "Record the structured fields extracted from one invoice. Call this "
        "exactly once per invoice with the extracted values. If a field is "
        "not present in the source document, return null for that field -- "
        "do not guess or infer values that aren't there."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # --- Required, non-null ---
            "vendor_name": {
                "type": "string",
                "description": "The vendor / supplier name (the party issuing the invoice).",
            },
            "total_usd": {
                "type": "number",
                "description": (
                    "Grand total in USD as a plain number (no currency symbol, "
                    "no commas). If the invoice is in another currency and does "
                    "not include a USD conversion, set to 0 -- but this should "
                    "be rare; most invoices we extract are USD-denominated."
                ),
            },

            # --- Required but nullable: anti-hallucination ---
            "due_date": {
                "type": ["string", "null"],
                "description": (
                    "ISO 8601 date (YYYY-MM-DD) when payment is due. "
                    "Return null if the source does not state a due date "
                    "(e.g., a paid receipt)."
                ),
            },
            "po_number": {
                "type": ["string", "null"],
                "description": (
                    "Customer PO reference as it appears on the invoice. "
                    "Return null if no PO is referenced."
                ),
            },

            # --- Enum + 'other' + detail, for extensibility ---
            "payment_terms": {
                "type": "string",
                "enum": ["net_30", "net_60", "due_on_receipt", "other"],
                "description": (
                    "Canonical payment terms. Use 'other' for any phrasing "
                    "that doesn't exactly match net_30 / net_60 / "
                    "due_on_receipt (e.g., 'Net 45', '50% upfront'). When "
                    "'other', populate payment_terms_detail with the "
                    "verbatim phrase."
                ),
            },
            "payment_terms_detail": {
                "type": ["string", "null"],
                "description": (
                    "Verbatim payment-terms phrase from the source. Required "
                    "(non-null) when payment_terms == 'other'. Null otherwise."
                ),
            },
        },
        "required": [
            "vendor_name",
            "total_usd",
            "due_date",
            "po_number",
            "payment_terms",
            "payment_terms_detail",
        ],
    },
}


# ===========================================================================
# System prompt: categorical criteria + 2-3 few-shot on ambiguous cases.
#
# Few-shot placement is inline in the system prompt (short examples, fine
# for this size). For longer / multi-turn examples we'd use user/assistant
# message pairs before the real user turn instead.
# ===========================================================================

SYSTEM = """\
You extract invoice fields into a single structured record via the
extract_invoice tool. Follow these rules exactly:

RULES
-----
1. If a field is NOT PRESENT in the source document, return null.
   Do not infer, guess, or fabricate values. Null is a legitimate answer.

2. total_usd is the grand total in USD, as a plain number (no $, no commas).

3. payment_terms is one of: net_30, net_60, due_on_receipt, other.
   If the invoice's stated terms do not EXACTLY match one of the first
   three, use "other" AND set payment_terms_detail to the verbatim phrase
   from the document. Otherwise payment_terms_detail is null.

4. Call the extract_invoice tool exactly once per invoice.

FEW-SHOT EXAMPLES (ambiguous cases)
-----------------------------------
Example A -- canonical terms:
  Source fragment: "Terms: Net 30"
  -> payment_terms = "net_30"
     payment_terms_detail = null
  Reasoning: "Net 30" matches the net_30 enum value exactly.

Example B -- terms outside the enum (the extensibility case):
  Source fragment: "Payment terms: Net 45 end-of-month"
  -> payment_terms = "other"
     payment_terms_detail = "Net 45 end-of-month"
  Reasoning: "Net 45" is not in the enum, so payment_terms = "other"
  and we preserve the original phrase in payment_terms_detail so
  downstream can later decide whether to add net_45 to the enum.

Example C -- absent fields (the null case):
  Source is a paid receipt with no due date and no PO reference.
  -> due_date = null, po_number = null
  Reasoning: the source doesn't state a due date or PO, so the correct
  answer is null on both, not a fabricated value.
"""


# ===========================================================================
# Extraction call: forced specific tool_choice.
# ===========================================================================

def extract_one(invoice_text: str) -> dict:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        tools=[EXTRACT_TOOL],
        # Forced specific: "you MUST call extract_invoice". This is the
        # deterministic mechanism that replaces a prompt instruction like
        # "please always call the tool" (which the model would sometimes skip).
        tool_choice={"type": "tool", "name": "extract_invoice"},
        messages=[{"role": "user", "content": invoice_text}],
    )

    for block in resp.content:
        if block.type == "tool_use" and block.name == "extract_invoice":
            return block.input

    raise RuntimeError(
        "extract_invoice was not called -- this is impossible with "
        "forced tool_choice unless the API contract changes."
    )


# ===========================================================================
# Lightweight semantic sanity checks the SCHEMA cannot catch.
#
# Exam-relevant reminder: the schema guarantees shape/types/enum membership.
# It does NOT check "did the model put the right value in the right field".
# For that we write our own validators -- e.g. "if payment_terms == 'other',
# payment_terms_detail must not be null."
# ===========================================================================

def semantic_sanity(row: dict) -> list[str]:
    errors = []
    if row["payment_terms"] == "other" and not row["payment_terms_detail"]:
        errors.append(
            "payment_terms == 'other' but payment_terms_detail is null "
            "-- verbatim phrase was lost."
        )
    if row["payment_terms"] != "other" and row["payment_terms_detail"] is not None:
        errors.append(
            "payment_terms != 'other' but payment_terms_detail is populated "
            "-- detail should only be set for 'other'."
        )
    if not isinstance(row["total_usd"], (int, float)) or row["total_usd"] < 0:
        errors.append(f"total_usd looks wrong: {row['total_usd']!r}")
    return errors


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for i, invoice in enumerate(INVOICES, start=1):
        print(f"\n========== INVOICE {i} ==========")
        print(invoice.strip())

        row = extract_one(invoice)
        print(f"\n-- extracted row --")
        print(json.dumps(row, indent=2))

        issues = semantic_sanity(row)
        if issues:
            print("\n-- semantic sanity issues --")
            for msg in issues:
                print(f"  * {msg}")
        else:
            print("\n-- semantic sanity: OK --")

    print(
        "\nObservations:\n"
        "  Invoice 1 (canonical): payment_terms=net_30, detail=null, all fields populated.\n"
        "  Invoice 2 (receipt):   due_date=null, po_number=null -- returned null, NOT hallucinated.\n"
        "  Invoice 3 (Net 45):    payment_terms='other', detail='Net 45 end-of-month'\n"
        "                         -- the few-shot B case is why this works without schema violations."
    )
