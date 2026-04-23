# W10 APIs — Claude APIs for this week

> APIs relevant to **advanced context management and provenance**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Messages API** with scratchpad file I/O | Durable state outside the context window | Long-running agents |
| **Manifest pattern** (plain file, JSON lines) | Crash recovery: records intended step + outcome | Non-idempotent workflows |
| **Async Messages API** + subagent delegation | Offload context-heavy work to isolated subagent contexts | Coordinator does integration only |
| **Tool outputs with provenance fields** — `{claim, source_url, publication_date, source_type}` | Preserve attribution through synthesis | Multi-agent research |

---

## API snippets

### Scratchpad read-modify-write
```python
from pathlib import Path
SCRATCH = Path("scratchpad.json")

def load_scratch() -> dict:
    return json.loads(SCRATCH.read_text()) if SCRATCH.exists() else {}

def save_scratch(d: dict) -> None:
    SCRATCH.write_text(json.dumps(d, indent=2))
```

### Manifest pattern for crash recovery
```python
from pathlib import Path
MANIFEST = Path("manifest.jsonl")

def record(step_index: int, intent: str, status: str, result=None) -> None:
    with MANIFEST.open("a") as f:
        f.write(json.dumps({
            "step_index": step_index, "intent": intent,
            "status": status, "result": result, "ts": time.time()
        }) + "\n")

def resume_from() -> int:
    if not MANIFEST.exists(): return 0
    last = None
    for line in MANIFEST.open():
        last = json.loads(line)
    if last is None: return 0
    if last["status"] == "done":
        return last["step_index"] + 1
    # last step did not complete — re-run if idempotent
    return last["step_index"]
```

### Provenance-tagged claim
```python
claim = {
    "claim": "Anthropic was founded in 2021.",
    "source_url": "https://www.anthropic.com/company",
    "source_type": "primary",  # primary | secondary | derivative
    "publication_date": "2024-01-15",
    "confidence": "high",
}
```

---

## Working example — coordinator + 2 subagents with scratchpad, manifest, provenance, and conflict annotation

Save as `research_agent.py`:

```python
"""
Research coordinator with:
- Subagents returning structured provenance-tagged claims.
- Scratchpad for durable cross-turn state.
- Manifest for crash recovery.
- Conflict annotation (not resolution).
"""
import anthropic, asyncio, json, time
from pathlib import Path

aclient = anthropic.AsyncAnthropic()
MODEL = "claude-sonnet-4-5"

SCRATCH = Path("scratchpad.json")
MANIFEST = Path("manifest.jsonl")

# --- durable state helpers ---
def load_scratch() -> dict:
    return json.loads(SCRATCH.read_text()) if SCRATCH.exists() else {"claims": []}

def save_scratch(d: dict) -> None:
    SCRATCH.write_text(json.dumps(d, indent=2))

def record(step_index: int, intent: str, status: str, result=None) -> None:
    with MANIFEST.open("a") as f:
        f.write(json.dumps({
            "step_index": step_index, "intent": intent,
            "status": status, "result_summary": str(result)[:200] if result else None,
            "ts": time.time(),
        }) + "\n")

def resume_from() -> int:
    if not MANIFEST.exists(): return 0
    last = None
    for line in MANIFEST.open():
        last = json.loads(line)
    return (last["step_index"] + 1) if (last and last["status"] == "done") else (last["step_index"] if last else 0)

# --- subagent: structured claim output ---
SUBAGENT_SYSTEM = """You are a research subagent. Answer the question with structured claims.

Return ONLY valid JSON: a list of claims, each with:
- claim: a single declarative sentence
- source_url: URL if known, else null
- source_type: "primary" | "secondary" | "derivative"
- publication_date: YYYY-MM-DD if known, else null
- confidence: "high" | "medium" | "low"

Do not wrap in prose. Do not use markdown fences.
"""

async def subagent(question: str) -> list[dict]:
    resp = await aclient.messages.create(
        model=MODEL, max_tokens=1024, system=SUBAGENT_SYSTEM,
        messages=[{"role": "user", "content": question}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json\n"): text = text[5:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [{"claim": f"[parse-fail] {text[:200]}",
                 "source_url": None, "source_type": "derivative",
                 "publication_date": None, "confidence": "low"}]

# --- coordinator: synthesize with conflict annotation ---
COORDINATOR_SYSTEM = """You are a research coordinator. You receive structured claims from subagents.

Synthesis rules:
- Preserve source attribution on every statement.
- If two claims conflict, annotate BOTH with their dates/sources; do not pick arbitrarily.
- If dates suggest a timeline (old source + new source), say "As of [date], ..." rather than calling it a conflict.
- Tag each paragraph of output with a tier: well-established / contested / single-source.

Output markdown with inline citations like [S1, 2024-01-15].
"""

async def coordinator(question: str, claims: list[dict]) -> str:
    numbered = "\n".join(
        f"S{i+1} [{c.get('source_type','?')}, {c.get('publication_date','?')}]: "
        f"{c.get('claim','?')} (conf={c.get('confidence','?')})"
        for i, c in enumerate(claims)
    )
    prompt = f"Question: {question}\n\nClaims:\n{numbered}\n\nSynthesize with conflict annotation."
    resp = await aclient.messages.create(
        model=MODEL, max_tokens=1500, system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text

# --- workflow ---
async def run():
    scratch = load_scratch()
    start = resume_from()
    print(f"[resume] starting from step {start}")

    steps = [
        ("subagent-history", "When was Anthropic founded and by whom?"),
        ("subagent-product", "What is MCP (Model Context Protocol) and when was it released?"),
    ]

    for idx in range(start, len(steps)):
        key, question = steps[idx]
        record(idx, f"spawn {key}", "started")
        print(f"[step {idx}] {key}: {question}")
        try:
            claims = await subagent(question)
            scratch["claims"].extend([{**c, "subagent": key} for c in claims])
            save_scratch(scratch)
            record(idx, f"spawn {key}", "done", claims)
        except Exception as e:
            record(idx, f"spawn {key}", "failed", str(e))
            raise

    # Synthesis step
    synth_idx = len(steps)
    record(synth_idx, "synthesize", "started")
    final = await coordinator(
        "Brief history of Anthropic and their MCP standard.",
        scratch["claims"],
    )
    record(synth_idx, "synthesize", "done", final[:200])

    print("\n=== FINAL ===")
    print(final)

if __name__ == "__main__":
    asyncio.run(run())
```

---

## How to run

**Setup:**
```bash
pip install anthropic
```

**Set API key:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**First run (from scratch):**
```bash
# Clear any prior state
rm -f scratchpad.json manifest.jsonl
python research_agent.py
```

**Test crash recovery:**
```bash
# Start fresh
rm -f scratchpad.json manifest.jsonl

# Run — interrupt with Ctrl+C after the first subagent completes
python research_agent.py     # wait for step 0 to finish, then Ctrl+C mid-step-1

# Re-run — should resume from step 1, not redo step 0
python research_agent.py
```

Look at `manifest.jsonl` to see the recovery trail.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| Subagent returns prose not JSON | Missing "do not use markdown fences" in system prompt | Strengthen prompt; add the `tool_use` pattern from W07 for hard enforcement |
| Crash recovery skips a step it shouldn't | `resume_from` treats "failed" as "done" | Current logic is `status == "done"` → skip; `status == "failed"` → retry. Audit `record()` calls |
| Scratchpad bloats after many runs | Not trimming old claims | Add a `"purge_before": <ts>` field and strip claims older than N hours |
| Coordinator ignores dates | Not formatted in the input | Format each claim with `[source_type, date]:` prefix (as in the example) |
| Coordinator picks a single source arbitrarily | System prompt too weak | Add: "If you pick one source and discard others, you are wrong. Annotate." |
| Subagents run sequentially | Used `await subagent(...)` in a loop | Use `asyncio.gather()` for parallel spawns |

**Inspect provenance preservation:**
```python
print(json.dumps(scratch["claims"], indent=2))
```
Every claim should have a `source_url` or `source_type` and a `publication_date`.

**Verify conflict annotation in output:**
Grep the final output for phrases like "As of", "Source A", "Source B", "contested". If the synthesis says "The answer is X" without attribution, the prompt is too weak.

---

## Exam connection

- **Scratchpad + manifest > bigger context window** for long sessions / crash recovery.
- **Provenance preserved through synthesis** is the correct answer for multi-agent research failure modes.
- **Conflict annotation, not arbitrary resolution** — the exam explicitly tests this.
- **Source characterization (primary / secondary, dates)** distinguishes "conflict" from "timeline."
- **`/compact` is lossy** — paired with scratchpad for precision.
