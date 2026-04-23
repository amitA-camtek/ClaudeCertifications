"""
W08 — Minimal validation-retry loop.

What this demonstrates:
    1. Claude extracts a structured record via tool_use + JSON Schema.
    2. A Pydantic model validates the extraction.
    3. If Pydantic rejects it, we re-prompt with:
         - the ORIGINAL source (unchanged)
         - the EXACT failed output
         - the SPECIFIC Pydantic error message
       and try again, bounded to a small retry budget.
    4. If the retries exhaust, we stop and escalate — we do NOT retry
       forever, because if the source lacks the info, more retries just
       produce more hallucinations.

Why this exercise:
    - Exam task statement 4.4: validation-retry loops with specific error
      feedback, bounded attempts, and absent-data detection.
    - Anti-pattern this exercise refuses to implement:
        * generic "please try again" retry with no error context
        * unbounded retries
        * retrying absent-source cases (we detect it and stop)

Source data is a small fake corpus so the exercise runs standalone.

Run: ANTHROPIC_API_KEY=... python minimal_validation_retry.py
"""

from __future__ import annotations
import json
from typing import Optional

import anthropic
from pydantic import BaseModel, Field, ValidationError, field_validator

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 2  # total attempts = 1 initial + MAX_RETRIES retries = 3


# =============================================================================
# Fake source documents (invoices)
# =============================================================================
# Doc 1: complete, should succeed on the first attempt.
# Doc 2: date is phrased ambiguously — "Q3 2024". First attempt likely emits it
#        as-is (structural fail); retry with specific error should get ISO-8601.
# Doc 3: tax ID line is ENTIRELY absent. This is the absent-data case — retries
#        cannot help. The pipeline should detect and escalate, not loop forever.

DOCUMENTS = [
    {
        "doc_id": "INV-001",
        "text": (
            "INVOICE #9001\n"
            "Vendor: Acme Industrial Supplies\n"
            "Date: 2024-08-15\n"
            "Amount: $12,430.00\n"
            "Tax ID: 12-3456789\n"
        ),
    },
    {
        "doc_id": "INV-002",
        "text": (
            "INVOICE #9002\n"
            "Vendor: Globex Corporation\n"
            "Date: Q3 2024\n"              # ambiguous phrasing — will fail ISO validator
            "Amount: $4,200.50\n"
            "Tax ID: 98-7654321\n"
        ),
    },
    {
        "doc_id": "INV-003",
        "text": (
            "INVOICE #9003\n"
            "Vendor: Initech LLC\n"
            "Date: 2024-09-02\n"
            "Amount: $775.00\n"
            # Tax ID line deliberately missing — ABSENT SOURCE DATA.
        ),
    },
]


# =============================================================================
# Pydantic schema — the source of truth for validation
# =============================================================================

class Invoice(BaseModel):
    vendor: str = Field(..., min_length=1)
    invoice_date: str = Field(..., description="ISO-8601 date, YYYY-MM-DD")
    amount_usd: float = Field(..., gt=0)
    # Nullable on purpose: some invoices legitimately lack a tax ID line.
    # This is the schema-level answer to "what do we do when the source
    # doesn't have it?" — allow null, don't force the model to hallucinate.
    tax_id: Optional[str] = None

    @field_validator("invoice_date")
    @classmethod
    def must_be_iso_date(cls, v: str) -> str:
        # Strict ISO-8601 YYYY-MM-DD check; anything else rejected with a
        # field-specific error the retry loop will forward to the model.
        import re
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError(
                f"invoice_date must be ISO-8601 YYYY-MM-DD, got '{v}'"
            )
        return v


# =============================================================================
# Tool definition — tool_use enforces the JSON *shape*, Pydantic enforces the
# semantics on top. Both layers matter: tool_use prevents malformed JSON;
# Pydantic catches format rules the schema can't express cleanly.
# =============================================================================

EXTRACT_TOOL = {
    "name": "emit_invoice",
    "description": (
        "Emit the extracted invoice record. Call this exactly once per "
        "document. If a field is genuinely absent from the source, pass null "
        "for that field rather than guessing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string"},
            "invoice_date": {
                "type": "string",
                "description": "ISO-8601 YYYY-MM-DD, e.g. 2024-08-15",
            },
            "amount_usd": {"type": "number"},
            "tax_id": {"type": ["string", "null"]},
        },
        "required": ["vendor", "invoice_date", "amount_usd", "tax_id"],
    },
}


SYSTEM_PROMPT = (
    "You extract structured invoice data from raw text. "
    "Call the emit_invoice tool exactly once with the fields you extracted. "
    "If a field is absent from the source, pass null — do NOT invent values."
)


# =============================================================================
# Single-attempt extraction
# =============================================================================

def call_extractor(messages: list[dict]) -> tuple[dict, str]:
    """
    Returns (parsed_tool_input, tool_use_id).
    Raises if the model didn't call the tool (which would itself be a failure
    we'd want to handle — using tool_choice={"type":"tool", "name":...} forces
    it, which is how exam task-statement 4.3 says to guarantee extraction).
    """
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "emit_invoice"},
        messages=messages,
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "emit_invoice":
            return block.input, block.id
    raise RuntimeError("model did not call emit_invoice")


# =============================================================================
# The validation-retry loop — the exam-critical part
# =============================================================================

def extract_with_retry(doc: dict) -> dict:
    """
    Returns a structured result:
        {"doc_id": ..., "status": "ok"|"failed_validation"|"absent_data",
         "record": {...} or None, "attempts": N, "last_error": str|None,
         "detected_pattern": {...} or None}
    """
    source_text = doc["text"]
    doc_id = doc["doc_id"]

    # Initial user message — just the source document.
    messages: list[dict] = [
        {
            "role": "user",
            "content": f"Extract invoice data from this document:\n\n{source_text}",
        }
    ]

    # Track repeated errors on the same field — the detected_pattern concept.
    # If we see the same field fail in the same category twice in a row,
    # we stop early because more retries won't help.
    last_error_field: Optional[str] = None
    last_error_category: Optional[str] = None
    repeated_same_failure = 0

    for attempt in range(1, MAX_RETRIES + 2):  # 1..MAX_RETRIES+1
        print(f"\n--- [{doc_id}] attempt {attempt} ---")
        raw_input, tool_use_id = call_extractor(messages)
        print(f"    model emitted: {json.dumps(raw_input)}")

        # Append the assistant's tool_use turn to history so the next user
        # turn can reference it by tool_use_id per the API contract.
        messages.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": tool_use_id,
                        "name": "emit_invoice",
                        "input": raw_input,
                    }
                ],
            }
        )

        # ---- Validation ------------------------------------------------------
        try:
            record = Invoice(**raw_input)
            print(f"    OK — passed Pydantic validation")
            return {
                "doc_id": doc_id,
                "status": "ok",
                "record": record.model_dump(),
                "attempts": attempt,
                "last_error": None,
                "detected_pattern": None,
            }
        except ValidationError as e:
            # Pull the most specific field-level error for the retry prompt.
            err_detail = e.errors()[0]
            err_field = ".".join(str(p) for p in err_detail["loc"])
            err_msg = err_detail["msg"]
            err_category = err_detail["type"]
            full_err = f"field '{err_field}': {err_msg} (type={err_category})"
            print(f"    FAIL — {full_err}")

            # ---- detected_pattern / absent-data detection -------------------
            if err_field == last_error_field and err_category == last_error_category:
                repeated_same_failure += 1
            else:
                repeated_same_failure = 0
                last_error_field = err_field
                last_error_category = err_category

            # Heuristic: if the same field fails the same way twice in a row
            # AND the source plainly lacks the field, treat it as absent data
            # and stop. We do NOT burn remaining attempts on a doomed case.
            source_looks_absent = _field_absent_in_source(err_field, source_text)
            if repeated_same_failure >= 1 and source_looks_absent:
                print(
                    f"    STOP — detected_pattern: field '{err_field}' "
                    f"repeatedly failing and source lacks the data. "
                    f"Escalating instead of retrying."
                )
                return {
                    "doc_id": doc_id,
                    "status": "absent_data",
                    "record": None,
                    "attempts": attempt,
                    "last_error": full_err,
                    "detected_pattern": {
                        "field": err_field,
                        "error_category": err_category,
                        "occurrences": repeated_same_failure + 1,
                        "source_lacks_field": True,
                    },
                }

            # ---- Budget check -----------------------------------------------
            if attempt > MAX_RETRIES:
                print(f"    STOP — retry budget exhausted ({MAX_RETRIES} retries).")
                return {
                    "doc_id": doc_id,
                    "status": "failed_validation",
                    "record": None,
                    "attempts": attempt,
                    "last_error": full_err,
                    "detected_pattern": None,
                }

            # ---- Build the retry prompt -------------------------------------
            # This is the exam-critical shape: original source + failed output
            # + SPECIFIC validator error. NOT "please try again".
            retry_prompt = (
                "Your previous extraction failed validation.\n\n"
                f"ORIGINAL SOURCE:\n{source_text}\n\n"
                f"YOUR PREVIOUS OUTPUT:\n{json.dumps(raw_input, indent=2)}\n\n"
                f"VALIDATION ERROR:\n{full_err}\n\n"
                "Produce a corrected extraction by calling emit_invoice again. "
                "Fix ONLY the field the validator flagged. If the source does "
                "not contain the value, pass null for that field — do not invent."
            )

            # We must pair the previous tool_use with a tool_result before the
            # next user message, or the API will reject our history.
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"VALIDATION FAILED: {full_err}",
                            "is_error": True,
                        },
                        {"type": "text", "text": retry_prompt},
                    ],
                }
            )

    # Unreachable — the loop always returns from inside.
    raise RuntimeError("retry loop fell through unexpectedly")


def _field_absent_in_source(field_name: str, source_text: str) -> bool:
    """
    Crude heuristic for "does the source even contain this field's data?"
    In a real system this is more sophisticated (NER, section detection, etc).
    For the exercise it's enough to cover the obvious cases.
    """
    hints = {
        "tax_id": ["tax id", "ein", "vat"],
        "invoice_date": ["date"],
        "amount_usd": ["amount", "total", "$"],
        "vendor": ["vendor", "supplier", "from:"],
    }
    source_lower = source_text.lower()
    for hint in hints.get(field_name, []):
        if hint in source_lower:
            return False
    return True


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    results = []
    for doc in DOCUMENTS:
        result = extract_with_retry(doc)
        results.append(result)

    print("\n\n========= FINAL RESULTS =========\n")
    for r in results:
        print(json.dumps(r, indent=2))
        print("-" * 40)

    # Summary — the shape you'd actually ship as a pipeline metric.
    ok = sum(1 for r in results if r["status"] == "ok")
    absent = sum(1 for r in results if r["status"] == "absent_data")
    failed = sum(1 for r in results if r["status"] == "failed_validation")
    print(
        f"\nSummary: ok={ok}  absent_data={absent}  failed_validation={failed}"
    )
    # Note the absent_data bucket is separate from failed_validation on
    # purpose — same aggregate metric would hide that some failures are
    # schema-should-be-nullable (fixable upstream) vs genuinely bad extractions.
