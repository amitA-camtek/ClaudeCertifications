"""
W11 Exercise 3 — Structured Data Extraction Pipeline.

Integrates:
    W07 — tool_use + JSON Schema for schema-guaranteed output; required/optional/
          nullable fields; enum with "other" + detail; tool_choice="any" to
          FORCE extraction (no end_turn without a tool call).
    W08 — validation-retry loop (Pydantic → specific error → resend);
          batch processing with custom_id; resubmit only failures; field-level
          confidence → low-confidence rows routed to "human review" queue.

Scenario:
    10 loan-application intake notes. Extract structured fields:
      - applicant_name (required, string)
      - loan_amount_usd (required, number)
      - loan_purpose (enum: ["home", "auto", "education", "business", "other"] + detail if "other")
      - employment_status (nullable enum — null if genuinely absent)
      - co_applicant_name (optional string — may be omitted)
      - notes (optional free-text)

    Plus per-field confidence: "high" | "medium" | "low".

    Two documents are intentionally malformed (missing the loan amount, or with
    ambiguous purpose) to exercise the retry path and the human-review queue.

Why this shape:
    - `loan_purpose` with enum + "other" shows how to constrain vocabulary but
      still capture novelty — THE canonical exam pattern.
    - `employment_status` nullable shows "null, not hallucinated" — another
      canonical exam pattern.
    - Per-field confidence shows how to route at FIELD granularity, not document
      granularity — the W10 / Domain 5.6 theme.

Run: ANTHROPIC_API_KEY=... python exercise_3_structured_extraction_pipeline.py

Variations to try (bottom of file): drop the nullable and watch hallucinations;
remove tool_choice="any" and watch the model skip the tool on a short doc;
raise the confidence threshold and watch the human-review queue fill up.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel, Field, ValidationError

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# =============================================================================
# The schema (W07 — this is the deterministic contract)
# =============================================================================

LOAN_PURPOSE_ENUM = ["home", "auto", "education", "business", "other"]
EMPLOYMENT_ENUM = ["employed", "self_employed", "unemployed", "retired", "student"]
CONFIDENCE_ENUM = ["high", "medium", "low"]

EXTRACTION_TOOL = {
    "name": "record_loan_application",
    "description": (
        "Record a structured loan-application entry extracted from free-text "
        "intake notes. Every call MUST fill in applicant_name and loan_amount_usd "
        "from the text. Fields that are genuinely absent from the text must be "
        "null (for nullable fields) or omitted (for optional fields). NEVER "
        "guess or fill plausible-sounding defaults. Provide a confidence label "
        "for each extracted field based on how clearly the text supports it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # --- required ---
            "applicant_name": {
                "type": "string",
                "description": "Full name of the primary applicant, as written in the text.",
            },
            "loan_amount_usd": {
                "type": "number",
                "description": "Loan amount in USD. Integer or decimal.",
            },
            "loan_purpose": {
                "type": "string",
                "enum": LOAN_PURPOSE_ENUM,
                "description": (
                    "Category of the loan purpose. Use 'other' if none of the "
                    "listed categories fit; in that case, loan_purpose_detail "
                    "MUST be filled."
                ),
            },
            "loan_purpose_detail": {
                "type": ["string", "null"],
                "description": (
                    "Required IFF loan_purpose == 'other'. Short free-text "
                    "description of the actual purpose. Null otherwise."
                ),
            },
            # --- nullable (field present, value null if truly absent) ---
            "employment_status": {
                "type": ["string", "null"],
                "enum": EMPLOYMENT_ENUM + [None],
                "description": (
                    "Employment status of the applicant. MUST be null if the "
                    "text does not state or clearly imply it. Do NOT guess."
                ),
            },
            # --- optional (may be omitted entirely) ---
            "co_applicant_name": {
                "type": "string",
                "description": "Name of a co-applicant, if one is mentioned. Omit the field entirely if none.",
            },
            "notes": {
                "type": "string",
                "description": "Additional observations the extractor wants to flag. Omit if none.",
            },
            # --- field-level confidence ---
            "confidence": {
                "type": "object",
                "description": "Per-field confidence labels.",
                "properties": {
                    "applicant_name": {"type": "string", "enum": CONFIDENCE_ENUM},
                    "loan_amount_usd": {"type": "string", "enum": CONFIDENCE_ENUM},
                    "loan_purpose": {"type": "string", "enum": CONFIDENCE_ENUM},
                    "employment_status": {"type": "string", "enum": CONFIDENCE_ENUM},
                },
                "required": ["applicant_name", "loan_amount_usd", "loan_purpose"],
            },
        },
        "required": ["applicant_name", "loan_amount_usd", "loan_purpose",
                     "loan_purpose_detail", "employment_status", "confidence"],
    },
}


# =============================================================================
# Pydantic validator (W08 — the validation half of retry-with-specific-error)
# =============================================================================

class ConfidenceModel(BaseModel):
    applicant_name: Literal["high", "medium", "low"]
    loan_amount_usd: Literal["high", "medium", "low"]
    loan_purpose: Literal["high", "medium", "low"]
    employment_status: Optional[Literal["high", "medium", "low"]] = None


class LoanApplication(BaseModel):
    applicant_name: str = Field(..., min_length=2)
    loan_amount_usd: float = Field(..., gt=0)
    loan_purpose: Literal["home", "auto", "education", "business", "other"]
    loan_purpose_detail: Optional[str] = None
    employment_status: Optional[Literal[
        "employed", "self_employed", "unemployed", "retired", "student"
    ]] = None
    co_applicant_name: Optional[str] = None
    notes: Optional[str] = None
    confidence: ConfidenceModel

    def validate_other_detail(self) -> str | None:
        """Cross-field rule: if purpose=='other', detail MUST be present."""
        if self.loan_purpose == "other" and not self.loan_purpose_detail:
            return "loan_purpose is 'other' but loan_purpose_detail is missing."
        if self.loan_purpose != "other" and self.loan_purpose_detail:
            return f"loan_purpose is '{self.loan_purpose}' but loan_purpose_detail was set (should be null)."
        return None


# =============================================================================
# Fake input documents — 10 intake notes, 2 intentionally broken.
# =============================================================================

DOCUMENTS: list[dict] = [
    {"custom_id": "doc-001",
     "text": "Applicant Dana Peretz requests $35,000 for a home down payment. "
             "Employed as a software engineer at TechCorp for 6 years."},
    {"custom_id": "doc-002",
     "text": "Yossi Kohen seeks an auto loan of $22,500 to purchase a used Toyota. "
             "Self-employed (freelance plumber). Co-applicant: Rivka Kohen."},
    {"custom_id": "doc-003",
     "text": "Mira Ashkenazi — $18,000 — tuition for a master's program in "
             "environmental engineering at Tel Aviv University. Currently a student."},
    {"custom_id": "doc-004",
     "text": "Applicant: Omar Haddad. Requesting $150,000 to expand a family "
             "restaurant (second location). Self-employed restaurateur."},
    {"custom_id": "doc-005",
     "text": "Noam Levi, $8,500 loan. Purpose: sailboat (recreational). "
             "Retired as of last year."},  # -> "other" + detail
    {"custom_id": "doc-006",
     "text": "Shira Ben-Ari applies for $45,000 for home renovation. "
             "No employment details given."},  # -> employment_status null
    {"custom_id": "doc-007",
     "text": "Applicant: Eitan Gross. $12,000. A cow."},  # INTENTIONALLY WEIRD → "other" + thin detail
    {"custom_id": "doc-008",
     "text": "Tal Rosen, $60,000 auto loan for a new electric SUV. "
             "Employed at a hospital; co-applicant: Dor Rosen."},
    # --- Intentionally broken #1: amount missing ---
    {"custom_id": "doc-009",
     "text": "Applicant Avi Danon would like to take out a loan for business "
             "expansion. Employed full time."},  # no amount
    # --- Intentionally broken #2: applicant name unreadable ---
    {"custom_id": "doc-010",
     "text": "[NAME REDACTED FOR AUDIT] requests $25,000 for an education loan. "
             "Student at Technion."},  # name not extractable
]

# =============================================================================
# Single-document extraction call (W07 — tool_choice="any" FORCES extraction)
# =============================================================================

SYSTEM = (
    "You extract structured loan-application fields from free-text intake notes. "
    "You MUST call the record_loan_application tool exactly once per document. "
    "If a required field is not supported by the text, still call the tool but "
    "use null (for nullable fields) or leave optional fields omitted. For the "
    "confidence object, use 'low' for any field where the text is weak or "
    "missing, 'high' only when the value is unambiguous. Do NOT guess "
    "plausible-sounding defaults for missing required fields — if the amount "
    "or name is not extractable, the downstream validator will catch it."
)


def extract_once(doc_text: str, prior_error: str | None = None) -> dict:
    """One extraction call. If prior_error is set, we're in a retry and we
    embed the previous failure into the prompt (W08 — retry with specific error)."""
    user_content = f"INTAKE NOTES:\n{doc_text}"
    if prior_error:
        user_content = (
            f"INTAKE NOTES:\n{doc_text}\n\n"
            f"PREVIOUS EXTRACTION WAS REJECTED by the downstream validator "
            f"with this specific error:\n  {prior_error}\n\n"
            f"Fix ONLY the problem described above. Do not change fields that "
            f"were correct. Respond by calling record_loan_application again."
        )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        tools=[EXTRACTION_TOOL],
        # W07 — forcing the tool means the model CANNOT end_turn without extracting.
        tool_choice={"type": "tool", "name": "record_loan_application"},
        messages=[{"role": "user", "content": user_content}],
    )

    # With tool_choice forcing a specific tool, exactly one tool_use block is returned.
    for b in resp.content:
        if b.type == "tool_use" and b.name == "record_loan_application":
            return b.input
    raise RuntimeError("Expected a tool_use block but got none (this shouldn't happen with forced tool_choice).")


# =============================================================================
# Validation loop — one retry, then give up and mark for human review (W08)
# =============================================================================

MAX_RETRIES = 1  # The model gets ONE retry with error feedback. Then stop.


@dataclass
class ExtractionResult:
    custom_id: str
    status: Literal["ok", "human_review"]
    attempts: int
    record: dict | None = None
    errors: list[str] = field(default_factory=list)


def validate(record: dict) -> tuple[LoanApplication | None, str | None]:
    """Return (valid model, None) on success, (None, error string) on failure."""
    try:
        model = LoanApplication(**record)
    except ValidationError as e:
        # Summarize the Pydantic error in a way the model can act on.
        msgs = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            msgs.append(f"{loc}: {err['msg']}")
        return None, "; ".join(msgs)

    cross = model.validate_other_detail()
    if cross:
        return None, cross
    return model, None


def extract_with_retry(doc: dict) -> ExtractionResult:
    result = ExtractionResult(custom_id=doc["custom_id"], status="ok", attempts=0)
    last_error: str | None = None

    for attempt in range(MAX_RETRIES + 1):
        result.attempts += 1
        try:
            raw = extract_once(doc["text"], prior_error=last_error)
        except Exception as e:
            result.errors.append(f"api_error: {e}")
            result.status = "human_review"
            return result

        model, err = validate(raw)
        if model is not None:
            result.record = raw
            return result

        result.errors.append(err or "unknown validation error")
        last_error = err

    # Retries exhausted
    result.status = "human_review"
    result.record = raw  # last attempt's raw output, for the human to look at
    return result


# =============================================================================
# Batch driver — 10 documents, 2 intentionally broken.
# =============================================================================
#
# NOTE: this exercise uses SYNCHRONOUS per-doc calls rather than the Message
# Batches API, because (a) you can't run a real batch without an account that
# has Batches enabled, and (b) the W08 concepts the exam tests — custom_id
# correlation, partial resubmit of failures — are isomorphic between sync and
# batched. The variable `custom_id` on each doc is the same identifier you'd
# use in a real Batches submission.
# =============================================================================

HUMAN_REVIEW_QUEUE: list[dict] = []
LOW_CONFIDENCE_QUEUE: list[dict] = []


def is_low_confidence(record: dict) -> list[str]:
    """Return the list of fields whose confidence is 'low'. Empty list = fine."""
    conf = record.get("confidence", {})
    return [field_name for field_name, level in conf.items() if level == "low"]


def run_batch(docs: list[dict]) -> list[ExtractionResult]:
    results: list[ExtractionResult] = []

    print("=" * 70)
    print(f"PASS 1 — extracting {len(docs)} documents")
    print("=" * 70)

    for doc in docs:
        res = extract_with_retry(doc)
        results.append(res)
        print(f"\n[{res.custom_id}] status={res.status} attempts={res.attempts}")
        if res.errors:
            for e in res.errors:
                print(f"    error: {e}")
        if res.record:
            print(f"    extracted: {json.dumps(res.record, indent=2)[:500]}")

    # W08 — partial re-submit: collect the ones that failed and show how you'd
    # resubmit them. With a real Batches API call you'd build a new batch
    # containing only the failed custom_ids. Here, we've already retried once
    # inline, so "human_review" means validation-retry is exhausted.
    failed = [r for r in results if r.status == "human_review"]
    print("\n" + "=" * 70)
    print(f"PASS 2 — human-review queue has {len(failed)} docs:")
    for r in failed:
        HUMAN_REVIEW_QUEUE.append(
            {"custom_id": r.custom_id, "errors": r.errors, "last_record": r.record}
        )
        print(f"  {r.custom_id}: {r.errors}")

    # W10 / Domain 5.6 — field-level confidence routing.
    for r in results:
        if r.status != "ok" or r.record is None:
            continue
        low = is_low_confidence(r.record)
        if low:
            LOW_CONFIDENCE_QUEUE.append(
                {"custom_id": r.custom_id, "low_fields": low, "record": r.record}
            )

    print("\n" + "=" * 70)
    print(f"LOW-CONFIDENCE FIELD QUEUE: {len(LOW_CONFIDENCE_QUEUE)} docs")
    print("(These passed validation but have field-level low confidence — "
          "route to human spot-check, not to automatic acceptance.)")
    for e in LOW_CONFIDENCE_QUEUE:
        print(f"  {e['custom_id']}: low confidence on {e['low_fields']}")

    return results


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    results = run_batch(DOCUMENTS)

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    ok = sum(1 for r in results if r.status == "ok")
    hr = sum(1 for r in results if r.status == "human_review")
    print(f"  OK:            {ok} / {len(results)}")
    print(f"  Human review:  {hr} / {len(results)}")
    print(f"  Low-conf fields routed: {len(LOW_CONFIDENCE_QUEUE)}")

    # Spot-check: verify doc-006 employment_status is actually null (not guessed).
    for r in results:
        if r.custom_id == "doc-006" and r.record:
            emp = r.record.get("employment_status")
            assert emp is None, (
                f"FAIL: doc-006 should have employment_status == null, got {emp!r}. "
                f"Nullable fields MUST NOT be hallucinated."
            )
            print(f"\n[CHECK] doc-006 employment_status == None ✓ (nullable respected)")


# =============================================================================
# Variations to try
# =============================================================================
#
# V1. Remove `"null"` from employment_status's type and remove the instruction
#     about leaving it null. Re-run. Watch the model invent an employment
#     status for doc-006 where the text is silent. That's hallucination.
#     (Exam task 4.5 — nullable fields prevent hallucination.)
#
# V2. Change tool_choice to {"type": "auto"} and feed doc-010 (name redacted).
#     The model may end_turn with a polite refusal instead of extracting. That's
#     the opposite failure mode — use tool_choice="any" or a forced specific
#     tool to GUARANTEE extraction is attempted. (Exam task 4.4.)
#
# V3. Remove the `enum` from loan_purpose and let it be free-text. Re-run doc-005
#     (sailboat). You'll get "recreational", "sailing", "boat", "leisure vehicle" —
#     different answers on different runs. Enum + "other" + detail gives you a
#     stable vocabulary for 99% of cases and a pressure valve for the 1%.
#     (Exam task 4.3 — categorical criteria over free text.)
#
# V4. In the retry prompt, strip out the specific error and just say "please try
#     again". Watch the retry rate drop — the model needs the specific failure
#     to fix the specific problem. (Exam task 4.6 — specific errors, not generic.)
#
# V5. Set MAX_RETRIES = 5. Doc-009 (missing amount) will still fail — the info
#     simply isn't in the source. Retrying forever wastes tokens on documents
#     where the answer cannot be derived. Route to human review after one retry.
#     (Exam trap: "retry with exponential backoff forever" = wrong answer.)
