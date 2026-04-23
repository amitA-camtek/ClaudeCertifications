# W07 APIs — Claude APIs for this week

> APIs relevant to **prompt engineering and structured output**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Messages API** with `tools` + forced `tool_choice` | Structured output via `tool_use` block — no JSON parsing |
| **`input_schema`** (JSON Schema subset) | Enforce field types, nullability, enums |
| **`tool_choice`** modes — `"auto"` / `"any"` / `{"type":"tool","name":"..."}` | Control tool selection |
| **`system` prompt** with few-shot examples | Steer behavior with 2–4 edge-case examples |
| **Pydantic validation** (outside Anthropic, but pairs with it) | Business-rule validation after structural schema passes |

---

## API snippets

### Forced tool call for extraction
```python
tool_choice={"type": "tool", "name": "extract_invoice"}
```
Model MUST call that specific tool; the `input` field is your structured output.

### Nullable field
```json
"vendor_tax_id": {"type": ["string", "null"]}
```
Allows the model to return `null` rather than hallucinate.

### Enum with `"other"` escape
```json
"status": {"type": "string", "enum": ["paid", "pending", "overdue", "other"]},
"status_other_detail": {"type": ["string", "null"]}
```

---

## Working example — structured invoice extractor with validation

Save as `extract.py`:

```python
"""
Structured-output extraction via forced tool_use.
Schema enforces structure; Pydantic validates semantics; retry loop handles failures.
"""
import anthropic, json
from pydantic import BaseModel, ValidationError, field_validator
from typing import Literal, Optional

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5"

TOOL = {
    "name": "extract_invoice",
    "description": "Extract structured invoice fields from the document. Return nulls for absent fields.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "amount_usd": {"type": ["number", "null"]},
            "due_date": {"type": ["string", "null"], "description": "ISO 8601, YYYY-MM-DD"},
            "vendor_name": {"type": "string"},
            "vendor_tax_id": {"type": ["string", "null"]},
            "status": {"type": "string", "enum": ["paid", "pending", "overdue", "other"]},
            "status_other_detail": {"type": ["string", "null"]},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
        "required": ["invoice_number", "vendor_name", "status", "confidence"],
    },
}

SYSTEM = """You are an invoice extractor. Extract fields exactly as they appear in the document.

Rules:
- If a field is absent from the document, return null (never guess).
- Use status='other' + status_other_detail for values outside the enum.
- Set confidence='low' when the field required interpretation; 'high' when verbatim.

Examples:

Input: "Invoice #A-42 from Acme Corp for $1,200 due 2026-05-01. Status: paid."
Output: {invoice_number: "A-42", amount_usd: 1200, due_date: "2026-05-01", vendor_name: "Acme Corp", vendor_tax_id: null, status: "paid", status_other_detail: null, confidence: "high"}

Input: "Bill from Beta LLC, amount TBD, status: cancelled"
Output: {invoice_number: null-like, vendor_name: "Beta LLC", amount_usd: null, due_date: null, vendor_tax_id: null, status: "other", status_other_detail: "cancelled", confidence: "medium"}
""".strip()

# Pydantic for semantic validation (not structural — that's the schema's job)
class Invoice(BaseModel):
    invoice_number: str
    amount_usd: Optional[float] = None
    due_date: Optional[str] = None
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    status: Literal["paid", "pending", "overdue", "other"]
    status_other_detail: Optional[str] = None
    confidence: Literal["high", "medium", "low"]

    @field_validator("amount_usd")
    @classmethod
    def amount_nonneg(cls, v):
        if v is not None and v < 0:
            raise ValueError("amount_usd must be >= 0")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_iso(cls, v):
        if v is not None:
            import re
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("due_date must be YYYY-MM-DD")
        return v

def extract_once(document: str, prior_attempt: dict | None = None, error: str | None = None) -> dict:
    messages = [{"role": "user", "content": f"Document:\n{document}"}]
    if prior_attempt:
        messages.append({"role": "assistant", "content": json.dumps(prior_attempt)})
        messages.append({"role": "user", "content": f"Validation failed: {error}\nFix and re-extract."})
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "extract_invoice"},
        messages=messages,
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("Model did not produce tool_use block")

def extract(document: str, max_retries: int = 2) -> Invoice:
    attempt = None
    err = None
    for i in range(max_retries + 1):
        attempt = extract_once(document, attempt, err)
        try:
            return Invoice(**attempt)
        except ValidationError as e:
            err = str(e)
            print(f"[retry {i}] validation failed: {err[:200]}")
    raise ValueError(f"Gave up after {max_retries + 1} attempts. Last attempt: {attempt}. Last error: {err}")

if __name__ == "__main__":
    DOCS = [
        "Invoice #INV-2026-042 from Acme Widgets Inc, $4,320.50 due 2026-06-15. Payment received last week.",
        "Bill from Gamma Solutions Ltd. Amount not specified in this document. Status notes: on hold pending review.",
    ]
    for doc in DOCS:
        print("\n=== Document ===")
        print(doc)
        inv = extract(doc)
        print("=== Extracted ===")
        print(inv.model_dump_json(indent=2))
```

---

## How to run

**Setup:**
```bash
pip install anthropic pydantic
```

**Set API key (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Run:**
```bash
python extract.py
```

**Expected:**
- First doc extracts cleanly: status=`paid`, confidence=`high`, all fields populated.
- Second doc: `amount_usd=null`, `status="other"`, `status_other_detail="on hold pending review"`, `confidence="medium"`.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: Model did not produce tool_use block` | Didn't force the tool | Ensure `tool_choice={"type":"tool","name":"extract_invoice"}` |
| Fields consistently hallucinated | Field declared required, not nullable | Change to `"type": ["string", "null"]` and mention null-on-absence in the system prompt |
| Dates in wrong format | No example of correct format in system prompt | Add a literal example; add Pydantic validator as belt-and-braces |
| Retry loop never converges | Retry prompt missing the specific error | Log each retry's error; feed exact validator message back |
| Model returns enum value not in list | Forgot `"other"` escape | Add `"other"` + detail field |
| Pydantic accepts but data is wrong | Schema is structural, not semantic | Add `@field_validator` for domain rules (e.g., amount > 0) |

**Inspect the raw `tool_use.input`:**
Replace `return block.input` with `print(json.dumps(block.input, indent=2)); return block.input` to see exactly what the model produced.

**Compare few-shot impact:**
Temporarily remove the two examples from `SYSTEM` and re-run — accuracy drops visibly. Add them back with edge cases (null fields, `other` status).

---

## Exam connection

- **Forced `tool_choice`** = the right way to get structured output; exam distractor is "ask for JSON in the prompt text."
- **Nullable fields prevent hallucination** — this example demonstrates `null` returns when info is absent.
- **Enum with `"other"` + detail** handles schema extensibility without redeploying.
- **Validation-retry loop with specific error** is the W08 pattern previewed here; schema ≠ semantics.
- **Field-level `confidence`** lets you route low-confidence records to human review.
