# W03 APIs — Claude APIs for this week

> APIs relevant to **hooks, sessions, and workflows**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Claude Code `settings.json` hooks** | Register `PreToolUse` / `PostToolUse` scripts the harness runs around tool calls | Deterministic gates (refund threshold, path allowlist) |
| **Hook JSON contract** — stdin event → stdout `{"decision": "block"/"approve"}` | How the hook talks to Claude Code | Every hook invocation |
| **Claude Code CLI** — `--resume <name>`, `--session-id`, `/compact` | Manage long-running sessions | Coherent continuation; lossy compression |
| **Session fork** — `--fork-session` / Agent SDK `fork_session` | Branched exploration from a checkpoint | Exploratory or poison-recovery |

---

## Hook JSON contract

**Input (stdin):**
```json
{
  "tool_name": "issue_refund",
  "tool_input": {"customer_id": "C123", "amount": 750},
  "session_id": "...",
  "cwd": "..."
}
```

**Output (stdout):**
```json
{"decision": "block", "reason": "Refunds over $500 require manager approval"}
```

Other decisions: `"approve"` (explicit allow; rare), or omit `decision` to pass through.

---

## Working example — refund-gate PreToolUse hook

### 1. The hook script — `refund_gate.py`

Save in the project at `.claude/hooks/refund_gate.py`:

```python
"""
PreToolUse hook: block issue_refund when amount > $500.
Reads event JSON from stdin, writes decision JSON to stdout.
"""
import json, sys

THRESHOLD = 500

def main():
    event = json.loads(sys.stdin.read())
    if event.get("tool_name") != "issue_refund":
        # not our concern — pass through
        print("{}")
        return
    amount = event.get("tool_input", {}).get("amount", 0)
    if amount > THRESHOLD:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"Refund of ${amount} exceeds ${THRESHOLD} threshold. "
                "Route to manager escalation with ticket number."
            ),
        }))
    else:
        print("{}")

if __name__ == "__main__":
    main()
```

### 2. Wire it in `.claude/settings.json`

Create or edit `.claude/settings.json` at the project root:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "issue_refund",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/refund_gate.py"
          }
        ]
      }
    ]
  }
}
```

### 3. Test the hook standalone (no Claude required)

```bash
echo '{"tool_name":"issue_refund","tool_input":{"amount":750}}' | python .claude/hooks/refund_gate.py
# Expect: {"decision": "block", "reason": "Refund of $750 exceeds $500 threshold. ..."}

echo '{"tool_name":"issue_refund","tool_input":{"amount":200}}' | python .claude/hooks/refund_gate.py
# Expect: {}

echo '{"tool_name":"other_tool","tool_input":{}}' | python .claude/hooks/refund_gate.py
# Expect: {}
```

On Windows PowerShell:
```powershell
'{"tool_name":"issue_refund","tool_input":{"amount":750}}' | python .claude/hooks/refund_gate.py
```

---

## Session management — CLI examples

### Resume coherently
```bash
# Resume a named session
claude --resume my-investigation

# Or by ID (from `claude --list-sessions`)
claude --session-id 9f3...
```

### Fork from a checkpoint
```bash
# Branch off `main-investigation` without modifying it
claude --fork-session main-investigation --name experiment-1
```

### Compact (inside Claude Code)
Inside a running Claude Code session, type:
```
/compact
```
Collapses history into a summary. **Lossy** — flush critical facts to a scratchpad file first.

---

## How to run the full hook example

**Setup:**
1. In your project root, create the folders: `.claude/hooks/`.
2. Save the Python script as `.claude/hooks/refund_gate.py`.
3. Save the settings file as `.claude/settings.json`.
4. Verify the standalone test from step 3 above works.

**Test with Claude Code:**
1. Launch Claude Code in the project directory: `claude`.
2. Register a mock tool `issue_refund` (via MCP or Agent SDK — see W04).
3. Ask Claude to "issue a refund of $750 to customer C123."
4. The hook fires; Claude receives the block reason and routes to escalation.

**Test without a real refund tool — dry run:**
Use Claude Code's Bash tool with a fake refund command; wire the hook to match `"matcher": "Bash"` and inspect the arguments. Replace `"matcher": "issue_refund"` with `"matcher": "Bash"` and the script to parse for `issue_refund` in the command string.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| Hook never fires | `matcher` doesn't match the tool name exactly | Run `claude --debug` to see which matchers are tested; fix matcher |
| Hook fires but Claude ignores the block | Script wrote malformed JSON or non-JSON to stdout | Test script standalone with `echo ... \|` pipe; verify stdout is **only** the JSON object |
| Hook crashes silently | Unhandled exception in script | Add `try/except` around `main()`; log to a file: `open(".claude/hooks/hook.log","a").write(traceback.format_exc())` |
| Block reason not shown to the model | Used `"approve"` instead of `"block"` | `decision` must be exactly `"block"` to halt execution |
| Works standalone, fails via Claude Code | Python not on PATH | Use absolute path: `"command": "C:/Python312/python.exe .claude/hooks/refund_gate.py"` |

**Enable Claude Code debug logging:**
```bash
claude --debug
```
Shows each hook invocation, matcher result, stdin/stdout exchange.

---

## Exam connection

- PreToolUse blocks the call *before* side effects → correct for gates.
- PostToolUse fires *after* execution → correct for output shaping (redaction, trimming), **wrong** for gates.
- Prompt-only "please never refund over $500" is probabilistic → exam distractor.
- `--resume` vs `fork_session`: resume for continuity, fork for exploration / poison recovery. Exam tests this distinction directly.
