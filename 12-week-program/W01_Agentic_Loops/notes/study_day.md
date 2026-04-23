# W01 Study Day — Agentic Loops & Core API (Domain 1.1)

## The one thing to internalize

**The agentic loop is driven by `stop_reason`. Nothing else.**

- `stop_reason == "tool_use"` → model asked for a tool; run it, append `tool_result`, call API again.
- `stop_reason == "end_turn"` → model is done; exit loop, return final message.
- `stop_reason == "max_tokens"` → hit token cap mid-response; not a normal termination.

Everything in this domain is "did you build the loop correctly, or did you cheat it with heuristics."

## Anti-patterns that appear as distractors on the exam

| Wrong answer | Why it's wrong |
|---|---|
| "Parse the model's text for phrases like 'I'm done'" | Natural language is probabilistic. `stop_reason` is deterministic. Always use `stop_reason`. |
| "Cap iterations at 5 and exit" | Arbitrary caps truncate valid multi-step work. Let `stop_reason == "end_turn"` terminate naturally. A safety fuse (say, 50) is fine; a low task-level cap is not. |
| "If the model didn't call a tool, re-prompt it" | If `stop_reason == "end_turn"` and no tool was called, the model is legitimately done. |
| "Run tools inside the model call" | Tools run in *your* code. The API returns a `tool_use` block; you execute, then send `tool_result` back. |
| "Feed only the latest `tool_result` back" | You must maintain the full `messages` history — every prior `assistant` (with tool_use) and `user` (with tool_result) turn. |

## The loop skeleton (memorize this shape)

```python
messages = [{"role": "user", "content": user_input}]
while True:
    resp = client.messages.create(model=..., tools=tools, messages=messages)
    messages.append({"role": "assistant", "content": resp.content})

    if resp.stop_reason == "end_turn":
        return resp  # done

    if resp.stop_reason == "tool_use":
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                result = run_tool(block.name, block.input)  # YOUR code
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})
        continue

    # max_tokens / other — handle explicitly, don't silently retry
    raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")
```

Three invariants:
1. **Every `tool_use` block gets exactly one `tool_result` block with the matching `tool_use_id`.** If the model made 3 parallel tool calls, send one `user` turn with 3 tool_result blocks — not 3 separate turns.
2. **Append, don't overwrite.** Message history grows monotonically within one loop.
3. **Tool results are passed as a `user` role message**, even though *you* produced them. That's the API convention.

## Agent SDK vs raw Messages API

- **Raw Messages API** (`anthropic` SDK) — you write the loop yourself. This is what the exam tests you on conceptually.
- **Agent SDK** (`claude-agent-sdk`) — the loop is wrapped for you; you define tools and hand it a prompt. Good for real work, but on the exam you must still be able to reason about the underlying loop.

Know both. Expect questions about the raw loop mechanics.

## 3-bullet recap

- **Termination is `stop_reason`, never text-matching.** `tool_use` → execute + continue; `end_turn` → exit.
- **Tool execution happens in your code**, results go back as a `user` message with `tool_result` blocks keyed by `tool_use_id`.
- **Don't cap iterations artificially**; a high safety fuse is fine, but the natural terminator is `end_turn`.
