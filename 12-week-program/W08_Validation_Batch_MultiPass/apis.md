# W08 APIs — Claude APIs for this week

> APIs relevant to **validation-retry loops, Message Batches, and multi-pass review**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Message Batches API** — `client.messages.batches.create()` / `.retrieve()` / `.results()` | Bulk single-turn jobs; 50% off; up to 24 h | Overnight extraction, weekly eval |
| **`custom_id`** on each request | Correlate input to output since results are unordered | Any batch |
| **Validation-retry loop** (built on Messages API) | Catch semantic errors after structural schema passes | Production extraction |
| **Independent-reviewer pattern** (two separate Messages API calls) | Avoid self-review bias | Multi-pass QA |

---

## API snippets

### Create a batch
```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "doc-001",
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Extract invoice data: ..."}],
            },
        },
        {
            "custom_id": "doc-002",
            "params": { ... },
        },
    ]
)
print(batch.id, batch.processing_status)  # "in_progress"
```

### Poll for completion
```python
import time
while True:
    batch = client.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(30)
```

### Stream results
```python
for line in client.messages.batches.results(batch.id):
    # `line` is a MessageBatchIndividualResponse; custom_id matches input
    if line.result.type == "succeeded":
        text = line.result.message.content[0].text
        print(line.custom_id, "->", text[:80])
    elif line.result.type == "errored":
        print(line.custom_id, "ERROR:", line.result.error)
```

---

## Working example — batch 5 docs + validate + retry failures

Save as `batch_extract.py`:

```python
"""
Batched extraction with validation-retry for failures.
- Submit 5 docs as a batch.
- Poll.
- Validate each result semantically.
- Retry synchronously the ones that failed validation (batch is single-turn;
  multi-turn retry requires sync).
"""
import anthropic, json, time
from pydantic import BaseModel, ValidationError
from typing import Optional

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5"

DOCS = {
    "doc-001": "Invoice #INV-001 from Acme, $1,200 due 2026-05-01. Paid.",
    "doc-002": "Bill from Beta Corp, amount $(unspecified) due 2026-06-15. Pending.",
    "doc-003": "Receipt from Gamma LLC. Total: -$50 refund issued.",  # negative — validator should catch
    "doc-004": "Invoice 42 from Delta, $800, due 2026-07-01. Overdue.",
    "doc-005": "Quote from Epsilon. No amount yet. Status unclear.",
}

TOOL = {
    "name": "extract",
    "description": "Extract invoice fields.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": ["string", "null"]},
            "amount_usd": {"type": ["number", "null"]},
            "vendor": {"type": "string"},
            "status": {"type": "string", "enum": ["paid", "pending", "overdue", "other"]},
        },
        "required": ["vendor", "status"],
    },
}

SYSTEM = "Extract invoice fields. Nulls for absent fields. Do not invent amounts."

class Extracted(BaseModel):
    invoice_number: Optional[str] = None
    amount_usd: Optional[float] = None
    vendor: str
    status: str

    @classmethod
    def validate_semantics(cls, data: dict) -> "Extracted":
        obj = cls(**data)
        if obj.amount_usd is not None and obj.amount_usd < 0:
            raise ValueError("amount_usd must be >= 0")
        return obj

def build_request(custom_id: str, doc: str) -> dict:
    return {
        "custom_id": custom_id,
        "params": {
            "model": MODEL,
            "max_tokens": 512,
            "system": SYSTEM,
            "tools": [TOOL],
            "tool_choice": {"type": "tool", "name": "extract"},
            "messages": [{"role": "user", "content": doc}],
        },
    }

def submit_batch(reqs: list[dict]) -> str:
    batch = client.messages.batches.create(requests=reqs)
    print(f"[batch] submitted {batch.id}, status={batch.processing_status}")
    return batch.id

def wait_for_batch(batch_id: str, poll_s: int = 10) -> None:
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            print(f"[batch] ended. counts: {batch.request_counts}")
            return
        print(f"[batch] {batch.processing_status}...")
        time.sleep(poll_s)

def collect_results(batch_id: str) -> dict[str, dict]:
    out = {}
    for line in client.messages.batches.results(batch_id):
        if line.result.type == "succeeded":
            msg = line.result.message
            for block in msg.content:
                if block.type == "tool_use":
                    out[line.custom_id] = {"ok": True, "data": block.input}
                    break
            else:
                out[line.custom_id] = {"ok": False, "error": "no tool_use block"}
        else:
            out[line.custom_id] = {"ok": False, "error": str(line.result.error)}
    return out

def sync_retry(custom_id: str, doc: str, prior: dict, err: str) -> dict:
    """For failures: run a sync call with the validator error fed back."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "extract"},
        messages=[
            {"role": "user", "content": doc},
            {"role": "assistant", "content": [{"type": "text", "text": json.dumps(prior)}]},
            {"role": "user", "content": f"Validation failed: {err}. Fix and re-extract."},
        ],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError(f"retry did not produce tool_use for {custom_id}")

def main():
    # 1. Submit batch
    reqs = [build_request(cid, doc) for cid, doc in DOCS.items()]
    batch_id = submit_batch(reqs)

    # 2. Poll
    wait_for_batch(batch_id)

    # 3. Collect
    raw = collect_results(batch_id)

    # 4. Validate; collect failures
    final = {}
    for cid, row in raw.items():
        if not row["ok"]:
            final[cid] = {"ok": False, "error": row["error"]}
            continue
        try:
            obj = Extracted.validate_semantics(row["data"])
            final[cid] = {"ok": True, "data": obj.model_dump()}
        except (ValidationError, ValueError) as e:
            print(f"[validate-fail] {cid}: {e}")
            # 5. Sync retry
            try:
                retry_data = sync_retry(cid, DOCS[cid], row["data"], str(e))
                obj = Extracted.validate_semantics(retry_data)
                final[cid] = {"ok": True, "data": obj.model_dump(), "retried": True}
            except Exception as e2:
                final[cid] = {"ok": False, "error": f"retry failed: {e2}"}

    # 6. Report
    print("\n=== FINAL ===")
    print(json.dumps(final, indent=2, default=str))
    print(f"\nSucceeded: {sum(1 for v in final.values() if v['ok'])}/{len(final)}")

if __name__ == "__main__":
    main()
```

---

## How to run

**Setup:**
```bash
pip install anthropic pydantic
```

**Set API key:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Run:**
```bash
python batch_extract.py
```

**Expected:**
- Batch submitted; polling prints every 10s.
- Completion in 1–30 minutes (typical for small batches; can be up to 24 h per SLA).
- Doc 3 fails validation (negative amount) → sync retry → likely succeeds on retry.
- Final report shows 4/5 or 5/5 succeeded.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| Batch stuck "in_progress" > 1 h | Normal — up to 24 h SLA | Wait; OR check status at console.anthropic.com |
| `batches.results()` returns nothing | Called before `processing_status == "ended"` | Add the wait loop as shown |
| `custom_id` mismatch on join | Submitted with duplicate `custom_id`s | Each `custom_id` must be unique within a batch |
| Only one batch allowed | Per-account concurrency limit | Wait for previous to end; batch more per request instead |
| Retry succeeds but no real change | Validator error too vague | Make error message specific: "amount_usd was -50 but must be >= 0" |
| Retry loop infinite | No bound on retries | Use `max_retries=2` and accept the 3rd failure as `final[cid]={"ok":False}` |
| Cost higher than expected | Not using batch for bulk — using sync | Batch is ~50% off; confirm `batches.create` not `messages.create` |

**Inspect a specific result:**
```python
for line in client.messages.batches.results(batch_id):
    if line.custom_id == "doc-003":
        print(json.dumps(line.model_dump(), indent=2, default=str))
        break
```

**Smoke-test synchronously first** (before committing to batch cost & time):
Change `submit_batch + wait + collect` to a loop of `client.messages.create` calls. Prove extraction works. Then switch to batch for scale.

---

## Exam connection

- **Batch is NOT for blocking pre-merge checks** — 24 h window, no SLA. Exam distractor.
- **Batch is single-turn** — no multi-turn tool calling inside one batched request. Retries need sync.
- **`custom_id` is mandatory** for result correlation — results come back unordered.
- **Validation-retry with specific error** works when the info IS in the document; useless when absent.
- **50% cost savings** is worth memorizing as a fact.
