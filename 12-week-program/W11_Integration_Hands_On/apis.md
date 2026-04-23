# W11 APIs — Claude APIs for this week

> Integration week — the APIs come from W01–W10. This file is a **combined reference + one capstone example** that exercises multiple APIs at once, with run/debug steps.

---

## API recap (by domain)

| Domain | Primary APIs | Covered in |
|---|---|---|
| Agentic loops | `messages.create`, `stop_reason`, `tool_use`/`tool_result` | W01 |
| Multi-agent | Parallel `AsyncAnthropic` + coordinator/subagent manual pattern | W02 |
| Hooks / sessions | `settings.json` hooks, `--resume`, `--fork-session`, `/compact` | W03 |
| Tool design / MCP | `tools=[...]`, `input_schema`, structured errors, MCP SDK, `.mcp.json` | W04 |
| Claude Code config | CLAUDE.md, `.claude/rules/*.md` w/ `paths:`, commands, skills, `/memory` | W05 |
| Plan mode / CI | `claude -p`, `--output-format json`, `--permission-mode plan`, two-session generator/reviewer | W06 |
| Structured output | forced `tool_choice`, nullable, enum + `"other"` | W07 |
| Batch / multi-pass | `messages.batches.create`/`.retrieve`/`.results`, `custom_id` | W08 |
| Context mgmt | `case_facts` block, tool trimming, `count_tokens`, structured errors | W09 |
| Provenance | scratchpad files, manifest for crash recovery, provenance-tagged claims | W10 |

---

## Capstone working example — end-to-end multi-agent extraction pipeline

Brings together: **W01** (loop + stop_reason), **W02** (parallel subagents), **W04** (structured tools + errors), **W07** (forced structured output), **W08** (validation-retry), **W09** (case_facts, trimming), **W10** (provenance).

Save as `capstone.py`:

```python
"""
Capstone: process N invoice documents through a multi-agent pipeline.

Flow:
1. Dispatcher subagent classifies each doc type (parallel).
2. Extractor subagents extract fields per-type (parallel).
3. Validator pass (Pydantic).
4. Retry failures synchronously with specific errors.
5. Coordinator synthesizes a report with provenance.
"""
import anthropic, asyncio, json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Optional, Literal

aclient = anthropic.AsyncAnthropic()
client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5"

DOCS = {
    "D1": "Invoice #INV-100 from Acme Widgets, $1,200 due 2026-05-01. Status: paid.",
    "D2": "Receipt from Beta Corp. Refund issued for $-50 (negative, yes). Status: refunded.",
    "D3": "Purchase Order #PO-42, Gamma LLC, amount TBD. Pending approval.",
}

# --- structured extraction tool (W04/W07) ---
EXTRACT_TOOL = {
    "name": "extract",
    "description": "Extract financial-doc fields. Null for absent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "doc_type": {"type": "string", "enum": ["invoice", "receipt", "purchase_order", "other"]},
            "doc_number": {"type": ["string", "null"]},
            "vendor": {"type": "string"},
            "amount_usd": {"type": ["number", "null"]},
            "status": {"type": "string"},
        },
        "required": ["doc_type", "vendor", "status"],
    },
}

class Extracted(BaseModel):
    doc_type: Literal["invoice", "receipt", "purchase_order", "other"]
    doc_number: Optional[str] = None
    vendor: str
    amount_usd: Optional[float] = None
    status: str

    @classmethod
    def validate_semantics(cls, data: dict) -> "Extracted":
        obj = cls(**data)
        if obj.amount_usd is not None and obj.amount_usd < 0:
            raise ValueError(f"amount_usd must be >= 0 (got {obj.amount_usd})")
        return obj

# --- extractor subagent (async) ---
async def extract_one(doc_id: str, doc: str) -> dict:
    resp = await aclient.messages.create(
        model=MODEL, max_tokens=512,
        system="Extract financial-document fields. Be precise; null for absent.",
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract"},
        messages=[{"role": "user", "content": doc}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return {"doc_id": doc_id, "raw": block.input, "source": doc}
    raise RuntimeError(f"No tool_use block for {doc_id}")

# --- sync retry on validation failure (W08) ---
def retry_extract(doc_id: str, doc: str, prior: dict, err: str) -> dict:
    resp = client.messages.create(
        model=MODEL, max_tokens=512,
        system="Extract financial-document fields. Be precise; null for absent.",
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract"},
        messages=[
            {"role": "user", "content": doc},
            {"role": "assistant", "content": [{"type": "text", "text": json.dumps(prior)}]},
            {"role": "user", "content": f"Validation failed: {err}. Fix the specific issue and re-extract."},
        ],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError(f"retry produced no tool_use for {doc_id}")

# --- coordinator synthesis with provenance (W10) ---
def synthesize(records: list[dict]) -> str:
    rows = "\n".join(
        f"- [{r['doc_id']}] type={r['data']['doc_type']} vendor={r['data']['vendor']} "
        f"amount={r['data'].get('amount_usd')} status={r['data']['status']}"
        for r in records if r["ok"]
    )
    failed = [r["doc_id"] for r in records if not r["ok"]]
    prompt = (
        f"Extracted records:\n{rows}\n\n"
        f"Failed records: {failed}\n\n"
        "Write a 1-paragraph summary. Preserve per-record attribution via [D1], [D2], etc."
    )
    resp = client.messages.create(
        model=MODEL, max_tokens=512,
        system="Summarize extraction results with per-record attribution.",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text

# --- orchestrator ---
async def main():
    # Parallel extraction
    raw = await asyncio.gather(*[extract_one(k, v) for k, v in DOCS.items()])

    # Validate + retry
    records = []
    for item in raw:
        try:
            obj = Extracted.validate_semantics(item["raw"])
            records.append({"doc_id": item["doc_id"], "ok": True, "data": obj.model_dump()})
        except (ValidationError, ValueError) as e:
            print(f"[validate-fail] {item['doc_id']}: {e}")
            try:
                retry_data = retry_extract(item["doc_id"], item["source"], item["raw"], str(e))
                obj = Extracted.validate_semantics(retry_data)
                records.append({"doc_id": item["doc_id"], "ok": True, "data": obj.model_dump(), "retried": True})
            except Exception as e2:
                records.append({"doc_id": item["doc_id"], "ok": False, "error": str(e2)})

    # Report
    print("\n=== RECORDS ===")
    print(json.dumps(records, indent=2))
    print("\n=== SYNTHESIS ===")
    print(synthesize(records))

if __name__ == "__main__":
    asyncio.run(main())
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
python capstone.py
```

**Expected:**
- D1 extracts cleanly on first pass.
- D2 fails validation (negative amount) → sync retry → likely extracts cleanly on retry.
- D3 extracts cleanly (amount_usd = null).
- Synthesis paragraph preserves `[D1], [D2], [D3]` attribution.

---

## Integration debug guide

When things fail at the integration level, diagnose in this order:

1. **Each stage works standalone?** Run `extract_one` alone on one doc. Run validator alone on a sample dict. Isolate first.
2. **Parallelism real?** Total wall-clock time ≈ max(individual) not sum(individual). If sum, you have sequential `await`s.
3. **Retries informative?** Log the exact validator error being fed back. Generic messages produce generic retries.
4. **Provenance preserved?** Every record has `doc_id` from input all the way through to synthesis.
5. **Errors categorized?** `ok/error` per record, not "the whole pipeline failed" when one doc is bad.

---

## Exam connection — integration-level traps

- "Run all docs in a big single prompt" — loses per-record attribution and blows context. The exam rewards per-record isolation.
- "Pool validation — accept if aggregate accuracy > 90%" — hides per-record errors. The exam rewards per-record validation.
- "Retry all failures in a single batch of the failures" — acceptable IF you preserve `custom_id`; otherwise correlation breaks.
- "Let the same subagent extract AND validate" — self-review bias; the exam rewards independent validator.
