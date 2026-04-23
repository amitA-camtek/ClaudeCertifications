# W01 Reference — Agentic Loops & Core API (Domain 1.1)

Complete, self-contained study material for Week 1. Read this end-to-end. Every concept the exam tests for task statement 1.1 is included here.

---

## 1. What an "agentic loop" actually is

An **agentic loop** is the code you (the developer) write around the Claude Messages API so that Claude can use tools to accomplish a multi-step task.

The model itself is stateless. Each API call:
- takes the full conversation history (`messages`) + tool definitions (`tools`)
- returns one response (`content` blocks + `stop_reason`)
- does **not** execute tools — it only requests them

Your loop code:
1. Sends the messages to the API
2. Inspects `stop_reason`
3. If tools were requested, runs them in your code and appends the results
4. Calls the API again with the updated history
5. Repeats until `stop_reason == "end_turn"`

This is why it's called a loop: the same API call pattern repeats. The model decides when to stop by emitting `stop_reason == "end_turn"`.

### Why this matters for the exam

Many distractors on the exam describe "agent frameworks" that are wrong in subtle ways — e.g., parsing the model's text for "I'm done", or capping at N iterations, or running tools inline. The correct answer almost always routes through `stop_reason`.

---

## 2. The `stop_reason` enumeration

The API returns one of these values on every response. You must handle each explicitly:

| `stop_reason` | Meaning | What your loop does |
|---|---|---|
| `"tool_use"` | Model wants to call one or more tools | Execute the tools, append `tool_result` blocks, call API again |
| `"end_turn"` | Model finished its response naturally | **Exit the loop.** Return the final text. |
| `"max_tokens"` | Response was truncated by the `max_tokens` cap | Not a normal terminator. Either raise, or continue with a larger cap. Don't silently treat as `end_turn`. |
| `"stop_sequence"` | A custom `stop_sequences` string was hit | Rare in agent loops. Treat like `end_turn` unless you set them deliberately. |
| `"pause_turn"` / `"refusal"` | Model paused or refused | Handle explicitly; don't ignore. |

**Exam rule:** if a distractor says "check the text" or "check if the model called a tool" to decide termination, it's wrong. Only `stop_reason` decides.

---

## 3. The message-history contract

You must maintain the full message history inside the loop. Every iteration **appends** to `messages`. Never overwrite it.

### Role conventions

- **`user`** — input from the user **or** `tool_result` blocks you produced after executing tools.
- **`assistant`** — the full `resp.content` from the previous API response (may include `text` blocks, `tool_use` blocks, or both).

Yes — tool results are sent as a `user` message. That's the API's convention, even though *you* produced them. Do not invent a `"tool"` role; it doesn't exist in this API.

### Tool-use ↔ tool-result pairing

If the assistant turn contained N `tool_use` blocks, the very next `user` turn must contain N `tool_result` blocks, each with a `tool_use_id` that matches the corresponding `tool_use.id`.

```python
# assistant turn emitted 2 tool_use blocks with ids "a1" and "a2"
# next user turn MUST look like this (one message, two blocks):
{
    "role": "user",
    "content": [
        {"type": "tool_result", "tool_use_id": "a1", "content": "..."},
        {"type": "tool_result", "tool_use_id": "a2", "content": "..."},
    ],
}
```

Common wrong answers on the exam:
- Sending each `tool_result` as its own separate `user` turn → **wrong**, API will error or misbehave.
- Omitting `tool_use_id` → **wrong**, required field.
- Using `"role": "tool"` → **wrong**, no such role.

### Parallel tool calls

A single assistant turn can contain multiple `tool_use` blocks ("parallel tool use"). You run them all (in parallel if you like), then return one `user` turn with all the `tool_result` blocks together. Do not feed them one at a time across multiple turns.

---

## 4. The canonical loop (this is the shape to memorize)

```python
import anthropic
client = anthropic.Anthropic()

def agentic_loop(user_input: str, tools: list, safety_fuse: int = 25) -> str:
    messages = [{"role": "user", "content": user_input}]

    for _ in range(safety_fuse):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError("safety fuse tripped")
```

### Invariants

1. Every iteration appends an `assistant` message.
2. On `tool_use`, the next append is a `user` message with **all** `tool_result` blocks for that turn.
3. `safety_fuse` is a crash-prevention cap, **not** a task-level iteration limit. It should be high (25, 50, 100) — high enough that real tasks never hit it.

### Why `safety_fuse` and not a tight cap?

An exam-style distractor: *"To prevent runaway loops, exit after 5 iterations."* — wrong. Real multi-tool tasks routinely need 10+ steps. A tight cap truncates correct work. A high cap exists only to catch bugs (infinite loop, model stuck calling the same broken tool forever).

---

## 5. Tool definitions

Tools are declared in the `tools=` argument to `messages.create`. Each tool needs:

- `name` — the identifier the model will use
- `description` — **plain English**, describes what the tool does, when to use it, input format, return format. This is the primary signal the model uses to choose a tool. Bad descriptions → wrong tool choices.
- `input_schema` — JSON Schema for the tool's input

```python
TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "Look up the current weather for a city. "
            "Input: a plain city name like 'Tel Aviv' or 'Berlin'. "
            "Returns: a short human-readable weather string."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]
```

**Rule of thumb:** if the model keeps picking the wrong tool, the fix is almost never "add a rule to the system prompt" — it's "write a better description." More on this in W04.

---

## 6. `tool_choice`

Controls whether the model must call a tool or can end the turn directly.

| `tool_choice` | Behavior |
|---|---|
| `{"type": "auto"}` (default) | Model decides. May call a tool, may end turn immediately. |
| `{"type": "any"}` | Model **must** call *some* tool this turn. Cannot end turn without a tool call. |
| `{"type": "tool", "name": "get_weather"}` | Model **must** call *this specific* tool this turn. |
| `{"type": "none"}` | Model **cannot** call any tool this turn (even if tools are in the list). |

Use `"any"` when you have a structured-output extraction task and need to force the model through a tool (more in W07). Use forced-specific when you're scripting a known step. Default to `"auto"` for general agent loops.

---

## 7. Anti-patterns (these ARE the exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| Parsing `resp.content` text for "done" / "finished" | Probabilistic, model phrasing varies | Use `stop_reason == "end_turn"` |
| Iteration cap of 3–5 as termination | Truncates valid multi-step tasks | High safety fuse + natural `end_turn` |
| Re-prompt if no tool was called | `end_turn` with no tool is valid completion | Trust `end_turn` |
| Running tools "inside" the model call | API doesn't execute tools | Execute in your code, send `tool_result` back |
| Feeding only the latest tool result | Breaks history, model loses context | Append every turn; never overwrite |
| Separate `user` turn per `tool_result` | Violates API contract | Bundle all `tool_result`s for a turn into one `user` message |
| Using `"role": "tool"` | No such role in this API | Tool results go in a `user` message |
| Silently converting `max_tokens` to `end_turn` | Returns truncated output as if complete | Raise or continue with larger `max_tokens` |
| Adding "you must always call tool X" to the system prompt to enforce compliance | Probabilistic — model will sometimes skip | Use `tool_choice` (deterministic) or a programmatic gate |

The last row is a recurring exam theme across **all** domains: *deterministic mechanisms (hooks, tool_choice, schemas) beat prompt instructions*. Burn it in.

---

## 8. Agent SDK vs raw Messages API

The `claude-agent-sdk` wraps the loop for you. You declare tools, hand it a prompt, and it runs the loop until `end_turn`. In real work, prefer the SDK. On the exam, be able to reason about the raw loop mechanics — questions probe the underlying API semantics.

Agent SDK adds (you'll cover these in later weeks, not here):
- Subagents via `Task` tool (W02)
- Hooks: `PreToolUse`, `PostToolUse` (W03)
- Sessions, `--resume`, `fork_session` (W03)
- MCP server integration (W04)

For W01, stick with the raw loop. You need to see the mechanics before the SDK abstracts them.

---

## 9. What this week's exam questions will probe

Based on the exam guide task statement 1.1, expect questions that:

- Show broken loop code, ask which line/logic is wrong.
- Describe a scenario ("the agent keeps terminating too early / too late") and ask for the fix.
- Give two candidate termination conditions and ask which is correct.
- Test whether you'd route a specific failure mode through prompt changes vs. `tool_choice` vs. hooks (hooks come in W03; for W01, the answer is usually `tool_choice` or loop logic).
- Test that you understand message-history contract (pairing `tool_use_id`, `user` role for tool_result, bundling).

---

## 10. Fast recap

- The loop runs until `stop_reason == "end_turn"`.
- Tools run in **your** code; results come back as a `user` message with `tool_result` blocks keyed by `tool_use_id`.
- Full history appended every turn. Never overwrite, never drop old turns.
- High safety fuse, not a tight iteration cap.
- Deterministic mechanism (tool_choice, loop logic) beats prompt instruction every time.

When you can explain each of those five bullets out loud in ~20 seconds each, you're ready for the W01 test.
