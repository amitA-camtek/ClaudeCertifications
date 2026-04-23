"""
W02 — Minimal hub-and-spoke multi-agent system (raw Messages API).

Architecture:
    Coordinator (one agentic loop)
      ├── has ONE coordinator-level tool: `spawn_subagent(subagent_type, prompt)`
      │      — this is our didactic equivalent of the Agent SDK's `Task` tool
      └── delegates to two subagent types, each running its own isolated
          agentic loop in a fresh `messages` list:
            - `math_expert`  (scoped tools: `calculate`)
            - `date_expert`  (scoped tools: `days_between`)

Why build it raw instead of using the SDK's `Task` tool?
    Because seeing the isolation boundary implemented by hand is what makes
    the exam questions click. In production you'd use the SDK. Here, we
    want the mechanics visible.

Key things this example demonstrates:
    1. COORDINATOR must have `spawn_subagent` ("Task" analogue) in its tool list.
       Without it, the coordinator can only try to do things itself.
    2. Each subagent runs a FRESH agentic loop with its own `messages` list.
       It does NOT see the coordinator's messages, the user's original input,
       or other subagents' work.
    3. Subagents have SCOPED tool sets — math_expert doesn't get `days_between`.
    4. Only the subagent's FINAL TEXT comes back to the coordinator as a
       tool_result. All the subagent's intermediate tool_use / tool_result
       turns stay inside the subagent's isolated loop.

Run: ANTHROPIC_API_KEY=... python minimal_multi_agent.py
"""

from __future__ import annotations
import json
from datetime import date

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# Subagent definitions (the AgentDefinition analogue)
# =============================================================================

SUBAGENTS = {
    "math_expert": {
        "description": "Performs arithmetic calculations accurately.",
        "system": (
            "You are a math specialist. Use the calculate tool for any "
            "arithmetic. Give a short, direct final answer when done."
        ),
        "tools": [
            {
                "name": "calculate",
                "description": "Evaluate a Python arithmetic expression like '3 * (4 + 5)'. Returns the numeric result.",
                "input_schema": {
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
            }
        ],
    },
    "date_expert": {
        "description": "Computes differences and arithmetic on calendar dates.",
        "system": (
            "You are a date specialist. Use the days_between tool for any "
            "date-math. Give a short, direct final answer when done."
        ),
        "tools": [
            {
                "name": "days_between",
                "description": "Return the number of days between two ISO-format dates (YYYY-MM-DD).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                    },
                    "required": ["start", "end"],
                },
            }
        ],
    },
}


# =============================================================================
# Tool implementations (split by subagent so scoping is explicit)
# =============================================================================

def _tool_calculate(expression: str) -> str:
    # Deliberately narrow eval — no names/builtins.
    return str(eval(expression, {"__builtins__": {}}, {}))


def _tool_days_between(start: str, end: str) -> str:
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    return str((e - s).days)


SUBAGENT_TOOL_DISPATCH = {
    "math_expert": {"calculate": _tool_calculate},
    "date_expert": {"days_between": _tool_days_between},
}


# =============================================================================
# Generic agentic loop (same shape as W01)
# =============================================================================

def run_agent_loop(
    system: str,
    tools: list,
    tool_dispatch: dict,
    user_input: str,
    label: str = "agent",
    safety_fuse: int = 15,
    verbose: bool = True,
) -> str:
    """W01-style agentic loop. Used for BOTH the coordinator and each subagent."""
    messages = [{"role": "user", "content": user_input}]

    for i in range(safety_fuse):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if verbose:
            print(f"\n[{label} iter={i} stop_reason={resp.stop_reason}]")
            for block in resp.content:
                if block.type == "text":
                    print(f"  text: {block.text}")
                elif block.type == "tool_use":
                    print(f"  tool_use: {block.name}({block.input})")

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = tool_dispatch[block.name](**block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
                    if verbose:
                        print(f"  tool_result({block.id}): {result}")
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"{label}: unexpected stop_reason {resp.stop_reason}")

    raise RuntimeError(f"{label}: safety fuse tripped")


# =============================================================================
# Coordinator — knows how to spawn subagents
# =============================================================================

COORDINATOR_SYSTEM = (
    "You are a coordinator. For any specialist task, delegate to the correct "
    "subagent via the spawn_subagent tool. Subagent types available:\n"
    "  - math_expert: arithmetic\n"
    "  - date_expert: calendar date math\n"
    "After all subagent results are in, synthesize ONE final answer for the user."
)

COORDINATOR_TOOLS = [
    {
        # This is our hand-rolled equivalent of the Agent SDK's "Task" tool.
        # Same role: the coordinator's ONLY way to delegate to a subagent.
        "name": "spawn_subagent",
        "description": (
            "Spawn a specialist subagent in an isolated context. The subagent "
            "will only see the prompt you provide — it cannot see the user's "
            "original message or any other subagent's work. Returns the "
            "subagent's final text synthesis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subagent_type": {
                    "type": "string",
                    "enum": list(SUBAGENTS.keys()),
                },
                "prompt": {
                    "type": "string",
                    "description": "Self-contained task description. Include ALL data the subagent needs — it sees nothing else.",
                },
            },
            "required": ["subagent_type", "prompt"],
        },
    }
]


def coordinator_dispatch_spawn(subagent_type: str, prompt: str) -> str:
    """Run the chosen subagent's own agentic loop in an isolated context."""
    cfg = SUBAGENTS[subagent_type]
    print(f"\n>>>>> COORDINATOR SPAWNING SUBAGENT '{subagent_type}' <<<<<")
    print(f"  subagent sees ONLY this prompt: {prompt!r}")
    final = run_agent_loop(
        system=cfg["system"],
        tools=cfg["tools"],
        tool_dispatch=SUBAGENT_TOOL_DISPATCH[subagent_type],
        user_input=prompt,
        label=subagent_type,
    )
    print(f"<<<<< SUBAGENT '{subagent_type}' RETURNED: {final!r} >>>>>")
    return final


COORDINATOR_TOOL_DISPATCH = {"spawn_subagent": coordinator_dispatch_spawn}


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    user_question = (
        "I was born on 1995-06-14. How many days old was I on 2025-01-01? "
        "Then compute (that number × 24 × 60) to get total minutes."
    )

    # Note: this question needs BOTH subagents. The coordinator should:
    #   1. spawn date_expert to get days between the two dates.
    #   2. spawn math_expert to multiply by 24*60.
    # These two subagent calls have a data dependency (#2 needs #1's result),
    # so the coordinator should dispatch them SEQUENTIALLY, not in parallel.

    final = run_agent_loop(
        system=COORDINATOR_SYSTEM,
        tools=COORDINATOR_TOOLS,
        tool_dispatch=COORDINATOR_TOOL_DISPATCH,
        user_input=user_question,
        label="coordinator",
    )

    print("\n===== FINAL ANSWER =====")
    print(final)
