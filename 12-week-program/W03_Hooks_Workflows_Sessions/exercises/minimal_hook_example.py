"""
W03 — Minimal PreToolUse hook example.

This is the smallest possible hook that demonstrates the Claude Code hook
contract:

    1. Harness pipes a JSON tool-call context to the hook's stdin.
    2. Hook prints a JSON decision to stdout and exits 0.
    3. On `decision: "block"`, the tool does NOT run; the `reason` string is
       returned to the model as if it were the tool_result, so the model can
       see WHY and recover (typically by calling a different tool).

Run it standalone for a sanity check:

    echo '{"tool_name":"issue_refund","tool_input":{"amount_usd":742}}' \
        | python minimal_hook_example.py

You should see:
    {"decision": "block", "reason": "Refund amount $742.00 ..."}

-----------------------------------------------------------------------------
Wiring into Claude Code's settings.json
-----------------------------------------------------------------------------

Place this file at `.claude/hooks/minimal_hook_example.py` in your project.
Then add the following to `.claude/settings.json`:

    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "issue_refund",
            "hooks": [
              {
                "type": "command",
                "command": "python .claude/hooks/minimal_hook_example.py"
              }
            ]
          }
        ]
      }
    }

Notes on the config shape:
    * `matcher` is matched against `tool_name`. Use `"*"` to match every tool,
      an exact string for one tool, or a regex for a pattern.
    * `type: "command"` = external shell command. The harness pipes JSON to
      stdin, reads JSON from stdout.
    * Multiple entries under `PreToolUse` can coexist; every matching entry
      fires for each tool call.

-----------------------------------------------------------------------------
Why this is the exam-correct way to enforce "no refunds over $500"
-----------------------------------------------------------------------------

The alternative is to write "NEVER issue refunds over $500" in the system
prompt. That works *most* of the time. Hooks work *every* time — they are
code, executed by the harness, and the model cannot bypass them.

Deterministic enforcement beats probabilistic guidance. Burn that in — it's
the W03 exam theme.
"""

from __future__ import annotations
import json
import sys


# The threshold above which refunds must be blocked and escalated to a human.
# In production this would live in a config file or policy service. Hardcoded
# here for pedagogical clarity.
REFUND_CAP_USD = 500.00


def decide(event: dict) -> dict:
    """
    Given the hook event from stdin, return the decision dict to write to
    stdout. Pure function so it's trivial to unit-test.
    """
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}

    # We only care about the `issue_refund` tool. Anything else falls through.
    # (In practice the settings.json `matcher` already filters by tool_name,
    # so this guard is defensive — but cheap and explicit.)
    if tool_name != "issue_refund":
        return {"decision": "approve"}

    # Defensive extraction — tool_input could be missing fields or have wrong
    # types if the model hallucinates. Treat unparseable as "block" (fail-safe).
    try:
        amount = float(tool_input.get("amount_usd", 0))
    except (TypeError, ValueError):
        return {
            "decision": "block",
            "reason": (
                "issue_refund was called with a non-numeric amount_usd. "
                "Refusing to run. Re-check the input and try again, or "
                "escalate_to_human if the amount is unknown."
            ),
        }

    if amount > REFUND_CAP_USD:
        return {
            "decision": "block",
            "reason": (
                f"Refund amount ${amount:.2f} exceeds the ${REFUND_CAP_USD:.2f} "
                f"auto-approve cap. Do NOT retry issue_refund; call "
                f"escalate_to_human with a brief reason instead."
            ),
        }

    # Under the cap — let the refund proceed.
    return {"decision": "approve"}


def main() -> int:
    # Read the full stdin payload. Claude Code's hook harness pipes one JSON
    # object per invocation.
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as e:
        # If we can't parse stdin, fail-safe: block the call and surface the
        # parse error so the user sees what went wrong. An alternative is to
        # approve (fail-open) — correct choice depends on your threat model.
        # For a refund gate, fail-closed is the right call.
        print(json.dumps({
            "decision": "block",
            "reason": f"Hook received malformed JSON on stdin: {e}",
        }))
        return 0

    decision = decide(event)
    print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
