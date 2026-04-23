# W12 APIs — Claude APIs for this week

> Final-week appendix: **one-page API cheatsheet** + a **smoke-test script** that exercises the 3 most exam-critical APIs so you walk in confident that every building block still works.

---

## One-page API cheatsheet

### Messages API — the core
```python
import anthropic
client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="...",
    messages=[{"role": "user", "content": "..."}],
    tools=[...],                                     # optional
    tool_choice={"type": "tool", "name": "extract"}, # optional
)
# response.content: list of blocks (text, tool_use)
# response.stop_reason: "end_turn" | "tool_use" | "max_tokens" | ...
```

### Tool use contract
```python
# Each tool:
{"name": "...", "description": "...",
 "input_schema": {"type": "object", "properties": {...}, "required": [...]}}

# Model's tool_use block:
{"type": "tool_use", "id": "toolu_...", "name": "...", "input": {...}}

# Your tool_result (in a user message):
{"type": "tool_result", "tool_use_id": "toolu_...", "content": "..."}

# NOTE: there is NO role="tool" in Claude's API.
```

### Message Batches API
```python
batch = client.messages.batches.create(requests=[
    {"custom_id": "r1", "params": {...messages.create args...}},
])
# poll batch.processing_status until "ended"
for row in client.messages.batches.results(batch.id):
    row.custom_id           # input correlation
    row.result.type         # "succeeded" | "errored"
    row.result.message      # the Message if succeeded
```

### Claude Code CLI
```bash
# Interactive
claude

# Headless
claude -p "prompt" --output-format json

# Plan mode
claude -p "prompt" --permission-mode plan

# Session management
claude --resume <name>
claude --fork-session <name> --name <new-name>
```

### Claude Code config (files)
- `~/.claude/CLAUDE.md` — user scope (loaded first)
- `CLAUDE.md` or `.claude/CLAUDE.md` — project (committed)
- `<subdir>/CLAUDE.md` — subtree override (loaded last → effective-last-word)
- `.claude/rules/<name>.md` with `paths:` frontmatter — conditional
- `.claude/commands/<name>.md` — slash command
- `.claude/skills/<name>/SKILL.md` — multi-step skill; use `context: fork`, `allowed-tools: [...]`
- `.mcp.json` at project root — team MCP servers
- `~/.claude.json` — personal MCP servers
- `/memory` inside Claude Code — which CLAUDE.md files loaded, in order

### Hooks (`settings.json`)
```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "<tool_name>", "hooks": [{"type": "command", "command": "python hook.py"}]}
    ]
  }
}
```
Hook reads JSON on stdin, writes `{"decision":"block|approve","reason":"..."}` on stdout.

### MCP server (Python)
```python
from mcp.server.fastmcp import FastMCP
app = FastMCP("my-server")

@app.tool()
def my_tool(arg: str) -> dict: ...

if __name__ == "__main__":
    app.run()
```

---

## Working example — smoke test

Save as `smoke_test.py` — run the day before the exam to confirm everything still works.

```python
"""
Exam-prep smoke test. Exercises:
1. Messages API basic call.
2. Tool use with stop_reason branching.
3. Structured output via forced tool_choice.
4. (Optional) Batches API round-trip.
"""
import anthropic, json, sys, time

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5"

def test_basic():
    print("\n[1/4] basic messages.create ...")
    r = client.messages.create(
        model=MODEL, max_tokens=128,
        messages=[{"role": "user", "content": "Say OK and nothing else."}],
    )
    assert r.stop_reason == "end_turn", f"expected end_turn, got {r.stop_reason}"
    print(f"  OK — stop_reason={r.stop_reason}, content={r.content[0].text!r}")

def test_tool_use():
    print("\n[2/4] tool_use loop ...")
    tools = [{
        "name": "add", "description": "Add two ints.",
        "input_schema": {"type": "object",
                          "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                          "required": ["a", "b"]},
    }]
    messages = [{"role": "user", "content": "What is 47 + 58?"}]
    r1 = client.messages.create(model=MODEL, max_tokens=256, tools=tools, messages=messages)
    assert r1.stop_reason == "tool_use", f"expected tool_use, got {r1.stop_reason}"
    tu = next(b for b in r1.content if b.type == "tool_use")
    result = str(tu.input["a"] + tu.input["b"])
    messages.append({"role": "assistant", "content": r1.content})
    messages.append({"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tu.id, "content": result}
    ]})
    r2 = client.messages.create(model=MODEL, max_tokens=256, tools=tools, messages=messages)
    assert r2.stop_reason == "end_turn"
    print(f"  OK — tool returned {result}; final: {r2.content[0].text[:80]!r}")

def test_structured():
    print("\n[3/4] forced tool_choice structured output ...")
    tool = {
        "name": "classify", "description": "Classify sentiment.",
        "input_schema": {"type": "object",
                          "properties": {"sentiment": {"type": "string", "enum": ["positive","negative","neutral"]},
                                         "confidence": {"type": "number"}},
                          "required": ["sentiment", "confidence"]},
    }
    r = client.messages.create(
        model=MODEL, max_tokens=256, tools=[tool],
        tool_choice={"type": "tool", "name": "classify"},
        messages=[{"role": "user", "content": "Review: 'best product I ever bought!'"}],
    )
    tu = next(b for b in r.content if b.type == "tool_use")
    assert tu.input["sentiment"] in ("positive", "negative", "neutral")
    print(f"  OK — {json.dumps(tu.input)}")

def test_batch_optional():
    print("\n[4/4] batches (optional — takes minutes) ...")
    if "--skip-batch" in sys.argv:
        print("  SKIPPED"); return
    batch = client.messages.batches.create(requests=[
        {"custom_id": f"p{i}",
         "params": {"model": MODEL, "max_tokens": 64,
                    "messages": [{"role": "user", "content": f"Say {i}."}]}}
        for i in range(3)
    ])
    print(f"  submitted {batch.id}")
    while True:
        b = client.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended": break
        print(f"  {b.processing_status}...")
        time.sleep(15)
    ok = 0
    for row in client.messages.batches.results(batch.id):
        if row.result.type == "succeeded": ok += 1
    assert ok == 3
    print(f"  OK — {ok}/3 succeeded")

if __name__ == "__main__":
    test_basic()
    test_tool_use()
    test_structured()
    test_batch_optional()
    print("\n=== ALL SMOKE TESTS PASSED ===")
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

**Full smoke test (takes a few minutes due to batch):**
```bash
python smoke_test.py
```

**Skip the batch test (30 seconds):**
```bash
python smoke_test.py --skip-batch
```

**Expected:** all 4 tests print `OK` and the script ends with `ALL SMOKE TESTS PASSED`.

---

## If a test fails — triage

| Test | Failure | Likely cause |
|---|---|---|
| [1] basic | `AuthenticationError` | API key missing or wrong |
| [1] basic | `APIConnectionError` | Network / proxy / firewall |
| [2] tool_use | `expected tool_use, got end_turn` | Model answered in prose; check tool description |
| [2] tool_use | `tool_use_id mismatch` | Didn't append `r1.content` verbatim as assistant turn |
| [3] structured | `no tool_use block` | Forgot `tool_choice={"type":"tool","name":"classify"}` |
| [3] structured | `sentiment` not in enum | Schema wasn't enforced — check `"enum"` syntax |
| [4] batch | `concurrent_batch_limit` | An earlier batch is still running; wait for it to end |
| [4] batch | Stuck > 1 hour | Normal per SLA; not a failure |

---

## Exam-day mental checklist (30 seconds before you start)

- `stop_reason` drives termination. `end_turn`, `tool_use`, **`max_tokens` is NOT success**.
- No `role: "tool"`. Tool results go in a `user` message with `tool_result` blocks.
- Deterministic gate > system-prompt guidance.
- Independent reviewer > self-review.
- Structured error with category/retryability > `"operation failed"`.
- Nullable fields > required fields for optional data.
- Stratified eval > aggregate accuracy.
- Batch: 50% off, 24 h, single-turn, `custom_id`. Not for blocking work.
- Scratchpad + manifest > bigger context window.
- Escalation: explicit / policy / inability. **Not sentiment or self-confidence.**

Good luck.
