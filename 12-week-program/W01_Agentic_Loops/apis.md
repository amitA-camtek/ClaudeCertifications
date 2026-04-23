# W01 APIs — Claude APIs for this week

> APIs relevant to **agentic loops**, with runnable examples and step-by-step run/debug instructions. Everything below is copy-paste-runnable on Windows (Python 3.10+).

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Messages API** — `client.messages.create()` | Single turn: send messages, receive a response | Every turn of the agent loop |
| **Tool use** — `tools=[...]`, `tool_choice`, `tool_use`/`tool_result` blocks | Let the model call external functions | How the agent "does" anything |
| **Stop reason** — `response.stop_reason` | Contract for termination: `end_turn` / `tool_use` / `max_tokens` | Deciding whether to loop or return |

---

## API snippets

### Messages API — minimum call
```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
resp = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.content[0].text)
print(resp.stop_reason)  # "end_turn"
```

### Tool use — declaring a tool
```python
tools = [{
    "name": "calculator",
    "description": "Evaluate a simple arithmetic expression. Input: a string like '2 + 3 * 4'. Returns the numeric result.",
    "input_schema": {
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
}]
```

### Stop-reason branching
```python
if resp.stop_reason == "tool_use":
    # extract tool_use block, run tool, append tool_result, resend
    ...
elif resp.stop_reason == "end_turn":
    # done
    ...
elif resp.stop_reason == "max_tokens":
    # NOT success — raise or resume
    raise RuntimeError("Hit max_tokens mid-generation")
```

---

## Working example — full agentic loop

Save as `agent_loop.py`:

```python
"""
Minimal agentic loop. Calculator tool + stop_reason-driven termination.
"""
import anthropic

client = anthropic.Anthropic()

TOOLS = [{
    "name": "calculator",
    "description": "Evaluate a simple arithmetic expression. Input: a string like '2 + 3 * 4'. Returns a numeric result. Do not use for non-arithmetic text.",
    "input_schema": {
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
}]

def run_tool(name: str, args: dict) -> str:
    if name == "calculator":
        # SAFE subset: only digits and + - * / ( ) . and spaces
        expr = args["expression"]
        allowed = set("0123456789+-*/(). ")
        if not set(expr).issubset(allowed):
            return "ERROR: expression contains disallowed characters"
        try:
            return str(eval(expr, {"__builtins__": {}}))  # sandboxed eval
        except Exception as e:
            return f"ERROR: {e}"
    return f"ERROR: unknown tool {name}"

def agent(user_prompt: str, max_iterations: int = 10) -> str:
    messages = [{"role": "user", "content": user_prompt}]
    for i in range(max_iterations):
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        print(f"--- turn {i} stop_reason={resp.stop_reason} ---")

        if resp.stop_reason == "end_turn":
            # collect final text
            texts = [b.text for b in resp.content if b.type == "text"]
            return "\n".join(texts)

        if resp.stop_reason == "max_tokens":
            raise RuntimeError("Model hit max_tokens mid-turn — raise ceiling or split task")

        if resp.stop_reason == "tool_use":
            # append the assistant turn VERBATIM so tool_use IDs match
            messages.append({"role": "assistant", "content": resp.content})
            # run every tool_use block in this turn
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    print(f"   tool {block.name}({block.input}) -> {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"Unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError(f"Exceeded max_iterations={max_iterations}")

if __name__ == "__main__":
    answer = agent("What is 17 * 23 + 5? Show your work.")
    print("\n=== FINAL ===")
    print(answer)
```

---

## How to run

**Setup (one-time):**

```bash
pip install anthropic
```

**Set your API key (Windows PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Set your API key (bash / WSL):**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Run:**
```bash
python agent_loop.py
```

**Expected output:** you should see 2 turns — turn 0 ends with `stop_reason=tool_use` (the model calls `calculator`), turn 1 ends with `stop_reason=end_turn` and prints the final answer (396).

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| `anthropic.AuthenticationError` | `ANTHROPIC_API_KEY` not set or invalid | Re-export; verify with `echo $env:ANTHROPIC_API_KEY` (Windows) |
| Loop runs forever / hits `max_iterations` | Tool result is garbage so model keeps trying | Print `tool_results` each turn; check tool output format |
| `stop_reason=max_tokens` immediately | `max_tokens=1024` too small for the task | Raise to 4096; or reduce task scope |
| Model ignores tool and answers in prose | Tool description is weak | Add concrete examples, input format, and boundaries to description |
| `ValidationError: tool_use_id mismatch` | You didn't append `resp.content` verbatim as assistant turn | Copy the `content` list exactly — don't rebuild it |
| Model calls tool with weird input | Schema too loose | Tighten `input_schema` with stricter `pattern` / `enum` |

**Inspect raw response for any bug:**
```python
import json
print(json.dumps(resp.model_dump(), indent=2, default=str))
```

**Print every message before sending for loop-state bugs:**
```python
for m in messages:
    print(m["role"], "->", str(m["content"])[:200])
```

---

## Exam connection

- Every exam question that says "parse the response text for 'done'" is the **wrong** answer — this example shows why `stop_reason` is the contract.
- Any answer choice using `role: "tool"` is wrong — Claude uses `tool_result` blocks inside a `user` message, as above.
- `max_tokens` handling (raise, don't treat as success) is directly testable.
