"""
W08 — Real-world batch extraction pipeline with validation, retry, and
independent reviewer.

Scenario:
    A compliance team has 10 vendor receipts that need to be turned into
    structured records. The pipeline must:

        Step 1 — Extract structured records (tool_use + JSON Schema).
        Step 2 — Validate each record with Pydantic.
        Step 3 — Retry the failures with specific error feedback.
        Step 4 — An INDEPENDENT REVIEWER (new session, new system prompt)
                 reviews the succeeded records for SEMANTIC errors the
                 extractor missed. This is the W08 exam-critical step:
                 self-review would retain bias; an independent instance
                 does not.

Why this exercise:
    - Exercises the full W08 pipeline: schema, retry, multi-pass review.
    - Demonstrates the self-review limitation by design — the extractor
      is wrong about a field in one record, and the INDEPENDENT reviewer
      catches it while the extractor's own reasoning would not.
    - Uses custom_id the way the Message Batches API would, so the code
      shows the correlation pattern you'd ship to production.

NOTE on batching (exam task statement 4.5):
    For this demo we run Step 1 synchronously so the exercise is
    self-contained and observable. In production this is exactly the kind
    of workload where you'd use the Message Batches API instead:
        - 50% cheaper
        - up to 24h window (fine — compliance runs overnight)
        - NOT time-critical — nobody is waiting on a spinner
        - single-turn per request, which fits extraction perfectly
    We simulate the batch by iterating synchronously but we carry the
    custom_id through like the Batches API would, so you can see the
    correlation shape. If this were a pre-merge CI check or a real-time
    user-facing flow, synchronous (what we're doing here) would be the
    correct choice because of the SLA — the batch API's 24h window would
    block the caller.

Run: ANTHROPIC_API_KEY=... python real_world_batch_extract_plus_reviewer.py
"""

from __future__ import annotations
import json
import re
from typing import Optional

import anthropic
from pydantic import BaseModel, Field, ValidationError, field_validator

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 2


# =============================================================================
# 10 fake receipts.
#
# Seeded failures for the demo:
#   - R-004 has the date as "August 15th, 2024" — will trip the ISO validator.
#   - R-007 has "amount: twelve dollars" — will trip the numeric validator.
#   - R-009 has buyer/seller flipped in the source text ("Sold BY: Customer X
#     Sold TO: Acme") so the extractor often emits the WRONG vendor. Schema
#     passes (it's a valid string!) but the SEMANTICS are wrong. This is the
#     case the independent reviewer must catch — it's a semantic error, not
#     a structural one.
# =============================================================================

RECEIPTS = [
    {"custom_id": "R-001", "text": "Receipt\nVendor: Acme Corp\nDate: 2024-07-01\nAmount: $42.00"},
    {"custom_id": "R-002", "text": "Receipt\nVendor: Globex Ltd\nDate: 2024-07-03\nAmount: $117.50"},
    {"custom_id": "R-003", "text": "Receipt\nVendor: Initech\nDate: 2024-07-04\nAmount: $8.99"},
    # Seeded structural failure — non-ISO date
    {"custom_id": "R-004", "text": "Receipt\nVendor: Umbrella Co\nDate: August 15th, 2024\nAmount: $219.00"},
    {"custom_id": "R-005", "text": "Receipt\nVendor: Soylent Industries\nDate: 2024-07-10\nAmount: $63.25"},
    {"custom_id": "R-006", "text": "Receipt\nVendor: Wayne Enterprises\nDate: 2024-07-11\nAmount: $510.00"},
    # Seeded structural failure — non-numeric amount
    {"custom_id": "R-007", "text": "Receipt\nVendor: Stark Industries\nDate: 2024-07-12\nAmount: twelve dollars"},
    {"custom_id": "R-008", "text": "Receipt\nVendor: Tyrell Corp\nDate: 2024-07-13\nAmount: $74.80"},
    # Seeded SEMANTIC trap — buyer/seller swap. Schema will pass either way.
    {"custom_id": "R-009", "text": "Receipt #221\nSold BY: Customer-X Consulting\nSold TO: Acme Corp\nDate: 2024-07-14\nAmount: $1,204.00"},
    {"custom_id": "R-010", "text": "Receipt\nVendor: Cyberdyne Systems\nDate: 2024-07-15\nAmount: $333.33"},
]


# =============================================================================
# Schema & extraction tool
# =============================================================================

class Receipt(BaseModel):
    vendor: str = Field(..., min_length=1)
    purchase_date: str = Field(..., description="ISO-8601 YYYY-MM-DD")
    amount_usd: float = Field(..., gt=0)

    @field_validator("purchase_date")
    @classmethod
    def must_be_iso(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError(
                f"purchase_date must be ISO-8601 YYYY-MM-DD, got '{v}'"
            )
        return v


EXTRACT_TOOL = {
    "name": "emit_receipt",
    "description": "Emit the structured receipt. Call this exactly once.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string", "description": "The entity being PAID (i.e. the seller receiving the money)"},
            "purchase_date": {"type": "string", "description": "ISO-8601 YYYY-MM-DD"},
            "amount_usd": {"type": "number"},
        },
        "required": ["vendor", "purchase_date", "amount_usd"],
    },
}

EXTRACTOR_SYSTEM = (
    "You extract structured receipt data from raw text. "
    "Call emit_receipt exactly once with the fields you extracted. "
    "Vendor = the entity receiving payment (the seller)."
)


# =============================================================================
# Step 1 — Extract. In production this would be:
#     client.messages.batches.create(requests=[...with custom_id each...])
# and later polled. We inline it here for the demo, preserving the same
# custom_id correlation the batch API uses.
# =============================================================================

def extract_one(receipt: dict) -> dict:
    """One synchronous extraction. Returns {custom_id, raw_input, tool_use_id}."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=EXTRACTOR_SYSTEM,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "emit_receipt"},
        messages=[{"role": "user", "content": f"Extract this receipt:\n\n{receipt['text']}"}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return {
                "custom_id": receipt["custom_id"],
                "source_text": receipt["text"],
                "raw_input": block.input,
                "tool_use_id": block.id,
            }
    raise RuntimeError(f"{receipt['custom_id']}: no tool_use block")


def step1_batch_extract(receipts: list[dict]) -> list[dict]:
    print("\n===== STEP 1 — Batch extract (synchronous simulation) =====")
    print("(In production: Message Batches API, 50% cheaper, 24h window,")
    print(" custom_id correlation — which we preserve here.)\n")
    results = []
    for r in receipts:
        out = extract_one(r)
        print(f"  [{out['custom_id']}] extracted: {json.dumps(out['raw_input'])}")
        results.append(out)
    return results


# =============================================================================
# Step 2 — Validate each record. Pydantic catches STRUCTURAL errors only.
# =============================================================================

def step2_validate(extractions: list[dict]) -> tuple[list[dict], list[dict]]:
    print("\n===== STEP 2 — Validate with Pydantic (structural only) =====\n")
    passed, failed = [], []
    for ex in extractions:
        try:
            Receipt(**ex["raw_input"])
            print(f"  [{ex['custom_id']}] OK")
            passed.append(ex)
        except ValidationError as e:
            err_detail = e.errors()[0]
            err = {
                "field": ".".join(str(p) for p in err_detail["loc"]),
                "msg": err_detail["msg"],
                "type": err_detail["type"],
            }
            full = f"field '{err['field']}': {err['msg']} (type={err['type']})"
            print(f"  [{ex['custom_id']}] FAIL — {full}")
            failed.append({**ex, "error": err, "error_full": full})
    return passed, failed


# =============================================================================
# Step 3 — Retry the failures with the exam-critical specific-error feedback.
# =============================================================================

def retry_one(failed: dict) -> dict:
    """Retry a single failed extraction with specific error feedback."""
    custom_id = failed["custom_id"]
    source_text = failed["source_text"]
    prev_input = failed["raw_input"]
    prev_err = failed["error_full"]

    # We start a fresh messages[] — we don't continue the extractor's prior
    # session because we want to pass the original source + previous output
    # + the specific error as a clean input, not buried in chat history.
    last_field: Optional[str] = None
    last_type: Optional[str] = None
    repeat = 0

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                "Your previous extraction failed validation.\n\n"
                f"ORIGINAL SOURCE:\n{source_text}\n\n"
                f"YOUR PREVIOUS OUTPUT:\n{json.dumps(prev_input, indent=2)}\n\n"
                f"VALIDATION ERROR:\n{prev_err}\n\n"
                "Produce a corrected extraction by calling emit_receipt again. "
                "Fix ONLY the field the validator flagged."
            ),
        }
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=EXTRACTOR_SYSTEM,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "emit_receipt"},
            messages=messages,
        )
        tool_block = next((b for b in resp.content if b.type == "tool_use"), None)
        if tool_block is None:
            return {**failed, "retry_status": "no_tool_use", "retry_attempts": attempt}

        messages.append({"role": "assistant", "content": resp.content})
        print(f"  [{custom_id}] retry {attempt}: {json.dumps(tool_block.input)}")

        try:
            Receipt(**tool_block.input)
            return {
                "custom_id": custom_id,
                "source_text": source_text,
                "raw_input": tool_block.input,
                "tool_use_id": tool_block.id,
                "retry_status": "ok",
                "retry_attempts": attempt,
            }
        except ValidationError as e:
            err_detail = e.errors()[0]
            err_field = ".".join(str(p) for p in err_detail["loc"])
            err_type = err_detail["type"]
            err_msg = err_detail["msg"]
            full = f"field '{err_field}': {err_msg} (type={err_type})"
            print(f"    still failing — {full}")

            # detected_pattern: same field, same error type → stop early.
            if err_field == last_field and err_type == last_type:
                repeat += 1
                if repeat >= 1:
                    print(
                        f"    STOP — detected_pattern: '{err_field}/{err_type}' "
                        f"repeated; remaining retries won't help."
                    )
                    return {
                        **failed,
                        "retry_status": "detected_pattern",
                        "retry_attempts": attempt,
                        "last_error": full,
                    }
            else:
                repeat = 0
                last_field, last_type = err_field, err_type

            # Append the next retry prompt with the fresh specific error,
            # keeping the tool_use/tool_result pairing the API requires.
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": f"VALIDATION FAILED: {full}",
                            "is_error": True,
                        },
                        {
                            "type": "text",
                            "text": (
                                f"Still invalid. VALIDATION ERROR:\n{full}\n"
                                "Fix only the flagged field and re-emit."
                            ),
                        },
                    ],
                }
            )

    return {**failed, "retry_status": "exhausted", "retry_attempts": MAX_RETRIES}


def step3_retry(failed: list[dict]) -> list[dict]:
    print("\n===== STEP 3 — Retry failed records with specific-error feedback =====\n")
    recovered = []
    for f in failed:
        print(f"  [{f['custom_id']}] retrying (prev err: {f['error_full']})")
        out = retry_one(f)
        if out.get("retry_status") == "ok":
            recovered.append(out)
            print(f"    -> RECOVERED on attempt {out['retry_attempts']}")
        else:
            print(f"    -> NOT recovered ({out.get('retry_status')})")
    return recovered


# =============================================================================
# Step 4 — INDEPENDENT REVIEWER.
#
# This is the exam-critical step. The reviewer is a separate Claude session:
#   - NEW messages[] (no history from extraction)
#   - NEW system prompt framed as a critic, not an extractor
#   - same model is fine; the separation is at the session/prompt level
#
# The reviewer's job: given (source, extracted_record), say whether the
# record is semantically faithful to the source. A structural check alone
# wouldn't catch things like buyer/seller swaps — the schema passes, but
# the answer is wrong.
# =============================================================================

REVIEWER_SYSTEM = (
    "You are an independent auditor reviewing extracted receipt records. "
    "You did NOT produce these extractions — your only job is to check "
    "whether the extracted fields match the source document. "
    "For each record, decide: does the vendor field name the entity that "
    "RECEIVED the money (the seller), or was a different party extracted by "
    "mistake? Does the date match? Does the amount match? "
    "Call emit_review once with your verdict. Be skeptical — this is an audit, "
    "not a co-sign."
)

REVIEW_TOOL = {
    "name": "emit_review",
    "description": "Record your audit verdict for the extracted record.",
    "input_schema": {
        "type": "object",
        "properties": {
            "semantic_match": {
                "type": "boolean",
                "description": "True if every extracted field is correct relative to the source.",
            },
            "issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of specific issues, empty if semantic_match=true.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
        },
        "required": ["semantic_match", "issues", "confidence"],
    },
}


def review_one(custom_id: str, source_text: str, record: dict) -> dict:
    """Run the independent reviewer in a fresh session."""
    prompt = (
        "Audit this extraction.\n\n"
        f"SOURCE DOCUMENT:\n{source_text}\n\n"
        f"EXTRACTED RECORD:\n{json.dumps(record, indent=2)}\n\n"
        "Check each field against the source. If the vendor field names the "
        "wrong party (e.g., the buyer instead of the seller), flag it. "
        "Call emit_review with your verdict."
    )
    # NOTE: brand-new messages[] — no extractor history.
    # NOTE: REVIEWER_SYSTEM — different system prompt from the extractor.
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=REVIEWER_SYSTEM,
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "emit_review"},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return {"custom_id": custom_id, **block.input}
    return {
        "custom_id": custom_id,
        "semantic_match": False,
        "issues": ["reviewer did not call tool"],
        "confidence": "low",
    }


def step4_independent_review(succeeded: list[dict]) -> list[dict]:
    print("\n===== STEP 4 — Independent reviewer (fresh session, new system prompt) =====\n")
    reviews = []
    for rec in succeeded:
        review = review_one(rec["custom_id"], rec["source_text"], rec["raw_input"])
        flag = "OK" if review["semantic_match"] else "FLAGGED"
        issues = f" — {review['issues']}" if review.get("issues") else ""
        print(f"  [{review['custom_id']}] {flag} (confidence={review.get('confidence')}){issues}")
        reviews.append(review)
    return reviews


# =============================================================================
# Entry point — runs the whole pipeline end-to-end.
# =============================================================================

if __name__ == "__main__":
    # Step 1
    extractions = step1_batch_extract(RECEIPTS)

    # Step 2
    passed, failed = step2_validate(extractions)
    print(f"\n  -> {len(passed)} passed, {len(failed)} failed validation")

    # Step 3 — retry the failures with specific-error feedback
    recovered = step3_retry(failed)
    print(f"\n  -> recovered {len(recovered)} of {len(failed)} via retry")

    # Succeeded set (for the reviewer) = initial passes + recovered retries
    succeeded = passed + recovered

    # Step 4 — independent reviewer catches semantic errors structural validation missed
    reviews = step4_independent_review(succeeded)

    # -------------------------------------------------------------------------
    # Final summary. Note the stratification: we report per-stage counts so
    # a single aggregate metric doesn't hide which stage is catching what.
    # A single "80% accuracy" number would obscure that structural vs
    # semantic errors are being caught by different mechanisms.
    # -------------------------------------------------------------------------
    print("\n\n========= PIPELINE SUMMARY =========")
    print(f"  Total receipts:                  {len(RECEIPTS)}")
    print(f"  Passed initial validation:       {len(passed)}")
    print(f"  Failed initial validation:       {len(failed)}")
    print(f"  Recovered via retry:             {len(recovered)}")
    print(f"  Not recovered (hard failures):   {len(failed) - len(recovered)}")
    print(f"  Submitted to reviewer:           {len(succeeded)}")
    reviewer_flagged = [r for r in reviews if not r.get("semantic_match")]
    print(f"  Reviewer flagged (semantic):     {len(reviewer_flagged)}")
    for r in reviewer_flagged:
        print(f"      [{r['custom_id']}] {r.get('issues')}")
    print(
        "\nKey point: the reviewer-flagged records PASSED schema validation. "
        "That's the structural-vs-semantic split — you need BOTH guards."
    )
