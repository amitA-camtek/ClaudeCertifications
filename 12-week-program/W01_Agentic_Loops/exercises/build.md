# Build — Agentic Loops & Core API

**Time:** 40 min · **Goal:** Write a raw-Messages-API agentic loop that calls a single tool and terminates on `stop_reason == "end_turn"`.

## What you'll have at the end
- A runnable `exercises/my_loop.py` that answers "What's the weather in Berlin?" by calling a `get_weather` tool and returning final text.
- A loop that terminates on `end_turn` (not on text-parsing, not on a tight iteration cap).

## Prereqs
- Python 3.10+, `pip install anthropic`, `ANTHROPIC_API_KEY` exported.
- Finished reading [reference.md](../reference.md) §1–§4 (agentic loop, `stop_reason`, message-history contract, canonical loop).
- Target file: `exercises/my_loop.py` (peek at [minimal_agentic_loop.py](minimal_agentic_loop.py) only if stuck).

## Steps

### 1. Scaffold the file + client (~3 min)
Create the file and get an API client instantiated before any loop logic.

- [ ] Create `exercises/my_loop.py`.
- [ ] `import anthropic`; instantiate `client = anthropic.Anthropic()`.
- [ ] Set `MODEL = "claude-sonnet-4-6"` as a module constant.

**Why:** §1 — the model is stateless; every iteration will be one `client.messages.create` call, so the client must be reusable across iterations.
**Checkpoint:** `python my_loop.py` runs without error (file imports cleanly, even though it does nothing yet).

### 2. Define the `TOOLS` list (~5 min)
One tool, three-field JSON schema. The description is the load-bearing part — it's what the model reads to decide when to call it.

- [ ] Define a `TOOLS` list with one entry named `get_weather`.
- [ ] Write a description that states: what it does, input format ("plain city name like 'Berlin'"), return format ("short human-readable string").
- [ ] `input_schema`: `type: "object"`, one property `city: {type: "string"}`, `required: ["city"]`.

**Why:** §5 — tool description is the primary signal for tool selection; `input_schema` is validated by the API.
**Checkpoint:** You can state out loud: "name, description, input_schema — those are the three required fields."

### 3. Implement `run_tool` (~3 min)
The *model* requests tools; *your code* executes them. This function is that executor.

- [ ] Define `run_tool(name: str, tool_input: dict) -> str`.
- [ ] If `name == "get_weather"`: return a hardcoded dict lookup for `"Berlin"` and `"Tel Aviv"`, fallback string otherwise.
- [ ] Raise `ValueError` on unknown tool names.

**Why:** §1 — "The API does not execute tools — it only requests them." This function is the bridge.
**Checkpoint:** `run_tool("get_weather", {"city": "Berlin"})` returns a string when called directly.

### 4. Loop skeleton + initial message (~4 min)
Set up the `messages` list and the outer `for` with a safety fuse. No branching logic yet.

- [ ] Define `agentic_loop(user_input: str, safety_fuse: int = 25) -> str`.
- [ ] Initialize `messages = [{"role": "user", "content": user_input}]`.
- [ ] `for _ in range(safety_fuse):` — inside, call `client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages)` and append `{"role": "assistant", "content": resp.content}` to `messages`.

**Why:** §4 invariant 1 — every iteration appends an `assistant` message. §4 "Why safety_fuse" — high cap, not a tight termination.
**Checkpoint:** If you run it now it will loop 25 times (no termination yet) — that's expected. Ctrl-C is fine.

### 5. Handle `end_turn` — the exit condition (~5 min)
The *only* correct termination signal. Return the final joined text.

- [ ] After the append, add: `if resp.stop_reason == "end_turn":` return the concatenated text of all `text`-type blocks in `resp.content`.
- [ ] Do **not** check the text content for "done" / "finished" / etc.

**Why:** §2 and §7 — `stop_reason == "end_turn"` is the only valid terminator; text-parsing is an exam distractor.
**Checkpoint:** You can answer: "Why not check the text?" → *"Phrasing is probabilistic; `stop_reason` is deterministic."*

### 6. Handle `tool_use` — execute, pair, append (~8 min)
Walk the assistant content, run each `tool_use` block, bundle all `tool_result` blocks into **one** `user` message.

- [ ] `if resp.stop_reason == "tool_use":` — build `tool_results = []`.
- [ ] For each `block` in `resp.content` where `block.type == "tool_use"`: call `run_tool(block.name, block.input)`, append a `tool_result` block keyed by `block.id`:

```python
{"type": "tool_result", "tool_use_id": block.id, "content": result}
```

- [ ] After the inner loop: `messages.append({"role": "user", "content": tool_results})` then `continue`.

**Why:** §3 — tool_results go in a `user` message (no `"tool"` role exists); N `tool_use` blocks → N `tool_result` blocks in ONE user turn, each keyed by matching `tool_use_id`.
**Checkpoint:** If the assistant emitted 2 tool_use blocks, your next appended message has role `user` and a content list of length 2.

### 7. Unexpected stop_reason + fuse exit (~2 min)
Don't silently treat `max_tokens` / `refusal` / `pause_turn` as success.

- [ ] After the two `if` branches: `raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")`.
- [ ] After the `for` loop (fuse exhausted): `raise RuntimeError("safety fuse tripped")`.

**Why:** §2 — `max_tokens` must not be silently converted to `end_turn`; §4 invariant 3 — fuse is a bug-catcher, not a task limit.
**Checkpoint:** `grep stop_reason my_loop.py` shows exactly two branches plus one fallthrough `raise`.

## Verify
Add `if __name__ == "__main__": print(agentic_loop("What's the weather in Berlin?"))` and run.

You should see:
- Exactly **2 iterations**: turn 1 returns `stop_reason="tool_use"`; turn 2 returns `stop_reason="end_turn"` with text like *"The weather in Berlin is 12°C, rainy."*
- Final `messages` list has 4 entries in order: `user` (prompt), `assistant` (tool_use), `user` (tool_result), `assistant` (final text).

**Common mistakes to check:**
- Loop exits after 1 iteration → you're returning on `tool_use` instead of `end_turn`. (§2)
- API 400 error about tool_result → you sent tool_results as a separate turn per block, or used `"role": "tool"`, or forgot `tool_use_id`. (§3)
- Loop runs forever → you forgot to `continue` / you overwrite `messages` instead of appending. (§4 invariant 1)
- Looks fine but truncates mid-thought and "succeeds" → you treated `max_tokens` as `end_turn`. (§7)

## Stretch — Polish block (30 min on Practice Day)
Finish any leftover steps, then add a second tool so the model has to choose between them.

- [ ] Add a second tool `get_time(city)` to `TOOLS` with the same 3-field schema shape.
- [ ] Extend `run_tool` to dispatch on `name` for both tools.
- [ ] Test with a prompt that requires both tools in parallel, e.g. *"What's the weather and current time in Berlin?"* — confirm a single assistant turn emits **two** `tool_use` blocks and your next `user` turn bundles **two** `tool_result` blocks (§3 parallel tool calls).
- [ ] Test with a prompt that needs neither tool, e.g. *"Say hi."* — confirm `end_turn` on iteration 1 with no tool calls (§7: re-prompting when no tool was called is an anti-pattern).

## If stuck
Compare with [minimal_agentic_loop.py](minimal_agentic_loop.py). Read → close it → rewrite from memory. Don't copy-paste.
