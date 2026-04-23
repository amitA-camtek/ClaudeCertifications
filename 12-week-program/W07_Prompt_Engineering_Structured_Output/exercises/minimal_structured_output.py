"""
W07 — Minimal structured-output example: BEFORE vs AFTER.

Scenario:
    We want to extract three fields from an invoice text blob:
        vendor_name (string), total_usd (number), due_date (string | null).

    BEFORE: ask Claude to reply in natural language with JSON embedded.
            Produces format drift -- markdown fences, prose before/after,
            missing fields, trailing commas, sometimes wrong types.
    AFTER:  define a tool with a JSON Schema matching the output shape,
            then force the model to call that tool via
              tool_choice={"type": "tool", "name": "extract_invoice"}.
            The model's tool_use block's .input IS the structured output,
            guaranteed to match the schema's shape / types / required fields.

Exam point this illustrates:
    - Schema + forced tool_choice eliminates SYNTAX errors (format, types).
    - It does NOT eliminate SEMANTIC errors (wrong value for a field).
    - "Ask the model to reply with JSON in text" is an anti-pattern.

Run: ANTHROPIC_API_KEY=... python minimal_structured_output.py
"""

from __future__ import annotations
import json
import re

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Fake input — a realistic-enough invoice blob. Same blob used for BEFORE/AFTER.
# ---------------------------------------------------------------------------

INVOICE_TEXT = """
ACME WIDGETS LLC
INVOICE #A-2211
---
Bill To:    Globex Corp
Due Date:   2026-05-15
Line items:
  Widget, qty 10 @ $12.50   $125.00
  Freight                    $15.00
Total due:                  $140.00
Terms: Net 30
"""


# ===========================================================================
# BEFORE  --  ask for JSON in natural language. Prone to syntax errors.
# ===========================================================================

BEFORE_SYSTEM = (
    "You extract invoice fields. Reply with a JSON object containing exactly "
    "these keys: vendor_name (string), total_usd (number), due_date "
    "(string or null). Do not include any explanation."
)


def extract_before(invoice_text: str) -> dict | str:
    """No tool. No tool_choice. Just a text reply that might be JSON."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=BEFORE_SYSTEM,
        messages=[{"role": "user", "content": invoice_text}],
    )
    raw = "".join(b.text for b in resp.content if b.type == "text").strip()

    # This is the part every team ends up writing by hand when they go the
    # natural-language-JSON route. It is fragile by construction.
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Real failure modes we've seen in this pattern:
        #   - Prose before/after the JSON block
        #   - Markdown fences the model wasn't told to omit (or was, and ignored)
        #   - Trailing commas, unquoted keys, single quotes
        #   - Missing required field
        return f"[PARSE ERROR] {e}\n---raw---\n{raw}"


# ===========================================================================
# AFTER  --  tool_use + JSON Schema + forced tool_choice. Shape guaranteed.
# ===========================================================================

EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": (
        "Record the structured fields extracted from an invoice document. "
        "Call this once per invoice with the extracted values."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {
                "type": "string",
                "description": "The vendor / supplier name (the party issuing the invoice).",
            },
            "total_usd": {
                "type": "number",
                "description": "The grand total in USD as a number (no currency symbol, no commas).",
            },
            "due_date": {
                # Nullable on purpose -- if the source doesn't have a due date,
                # the model should return null rather than fabricate one.
                "type": ["string", "null"],
                "description": "ISO 8601 date (YYYY-MM-DD) when payment is due, or null if not present.",
            },
        },
        "required": ["vendor_name", "total_usd", "due_date"],
    },
}

AFTER_SYSTEM = (
    "You extract invoice fields. Call the extract_invoice tool exactly once "
    "with the extracted values. If a field is not present in the source, "
    "return null for that field -- do NOT fabricate values."
)


def extract_after(invoice_text: str) -> dict:
    """Tool + forced tool_choice. The .input of the tool_use block is our result."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=AFTER_SYSTEM,
        tools=[EXTRACT_TOOL],
        # Forced specific tool: the model MUST call extract_invoice this turn.
        # This is the key line. tool_choice="auto" would let it reply in prose.
        tool_choice={"type": "tool", "name": "extract_invoice"},
        messages=[{"role": "user", "content": invoice_text}],
    )

    # The structured output is the tool_use block's .input dict. The schema
    # guarantees: shape correct, required fields present, types correct.
    for block in resp.content:
        if block.type == "tool_use" and block.name == "extract_invoice":
            return block.input

    raise RuntimeError("tool_use block not found -- this should be impossible with forced tool_choice")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("========== INPUT ==========")
    print(INVOICE_TEXT)

    print("\n========== BEFORE (natural-language JSON) ==========")
    before = extract_before(INVOICE_TEXT)
    print(before)
    print(
        "\nNote: this pattern 'works' most of the time, but fails "
        "unpredictably on markdown fences, prose preamble, trailing commas, "
        "and missing fields. The post-processing is load-bearing -- every "
        "prod team ends up writing brittle regex cleanup, then graduating to "
        "the AFTER pattern."
    )

    print("\n========== AFTER (tool_use + JSON Schema + forced tool_choice) ==========")
    after = extract_after(INVOICE_TEXT)
    print(json.dumps(after, indent=2))
    print(
        "\nShape-guaranteed:\n"
        "  - 'vendor_name' is present and is a string\n"
        "  - 'total_usd'   is present and is a number\n"
        "  - 'due_date'    is present and is string OR null\n"
        "Schema does NOT guarantee the VALUES are correct -- that's a semantic\n"
        "concern handled by downstream validators or a second pass."
    )
