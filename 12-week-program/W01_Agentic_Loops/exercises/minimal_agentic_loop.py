"""
W01 — Minimal agentic loop against the raw Messages API.

Tool: get_weather(city) — fake, deterministic, just returns a string.

Run: ANTHROPIC_API_KEY=... python minimal_agentic_loop.py
"""

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

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


def run_tool(name: str, tool_input: dict) -> str:
    if name == "get_weather":
        city = tool_input["city"]
        fake = {"Tel Aviv": "28°C, sunny", "Berlin": "12°C, rainy"}
        return fake.get(city, f"No data for {city}")
    raise ValueError(f"unknown tool: {name}")


def agentic_loop(user_input: str, safety_fuse: int = 25) -> str:
    messages = [{"role": "user", "content": user_input}]

    for _ in range(safety_fuse):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            # natural termination — pull out the final text
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")

    raise RuntimeError("safety fuse tripped — loop did not terminate naturally")


if __name__ == "__main__":
    print(agentic_loop("What's the weather in Tel Aviv and Berlin right now?"))
