# Build — Hooks, Workflows & Sessions

**Time:** 40 min · **Goal:** Build a PreToolUse hook that deterministically blocks `issue_refund` calls over $500 and redirects the model to `escalate_to_human`.

## What you'll have at the end
- Working `exercises/hooks/block_refund.py` that reads hook-event JSON from stdin and emits an `approve`/`block` decision to stdout
- `.claude/settings.json` snippet wiring the hook to `PreToolUse` with `matcher: "issue_refund"`
- A manual test showing a $600 refund attempt is blocked with a helpful `reason` string

## Prereqs
- Python 3 on PATH, Claude Code installed, a project with `.claude/` folder writable
- Finished reading [reference.md](../reference.md) §2–§4, §6, §10
- Target files: `exercises/hooks/block_refund.py` and `.claude/settings.json` snippet (peek at [minimal_hook_example.py](minimal_hook_example.py) only if stuck)

## Steps

### 1. Scaffold the hook script (~5 min)
Create `exercises/hooks/block_refund.py`. Import `json` and `sys`; add a `main()` that reads all of stdin, parses it as JSON, and for now prints `{"decision": "approve"}` and exits 0.
- [ ] Create the file and stub `main()`
- [ ] Wrap `json.loads` in try/except; on parse error emit `{"decision": "block", "reason": "..."}` (fail-closed)

**Why:** §3 — the hook contract is "JSON in on stdin, one JSON object out on stdout, exit 0." Fail-closed on bad input because this is a money gate.
**Checkpoint:** `echo '{}' | python exercises/hooks/block_refund.py` prints `{"decision": "approve"}`.

### 2. Extract `tool_name` and `amount_usd` (~5 min)
Pull the fields you need from the event dict. Guard every access — `tool_input` may be missing, `amount_usd` may not parse as a float.
- [ ] Read `event.get("tool_name", "")` and `event.get("tool_input", {}) or {}`
- [ ] `float(tool_input.get("amount_usd", 0))` inside try/except; on failure, return `block` with a "non-numeric amount" reason

**Why:** §3 — the stdin event shape has `tool_name` at the top and `amount_usd` nested under `tool_input`. Reference shape:

```
{"tool_name": "issue_refund", "tool_input": {"amount_usd": 742.00, ...}}
```

**Checkpoint:** piping a malformed payload yields a `block` decision, not a crash.

### 3. Implement the >$500 threshold (~8 min)
If `tool_name == "issue_refund"` AND `amount > 500`, emit `block` with a `reason` telling the model to call `escalate_to_human` instead. Otherwise emit `approve`.
- [ ] Add the threshold branch; include the dollar amount in the `reason` string
- [ ] Tell the model *which tool to call next* (`escalate_to_human`) — the reason is its only feedback

**Why:** §10 — the canonical refund scenario. The `reason` becomes the `tool_result` the model sees, so make it actionable: "exceeds $500 cap; call escalate_to_human instead." §5 — this is the deterministic answer, not a prompt rule.
**Checkpoint:** piping `{"tool_name":"issue_refund","tool_input":{"amount_usd":600}}` prints a `block` decision with `escalate_to_human` in the reason.

### 4. Wire it in `.claude/settings.json` (~7 min)
Create (or edit) `.claude/settings.json` at the project root and register the hook under `PreToolUse` with `matcher: "issue_refund"` and a `command` that invokes your script.
- [ ] Add the `hooks.PreToolUse` array with a single entry
- [ ] Use `"type": "command"` and `"command": "python exercises/hooks/block_refund.py"` (relative to project root)

**Why:** §4 — hooks live in `settings.json`, keyed by event name, filtered by `matcher` on `tool_name`. **Must be `PreToolUse`, not `PostToolUse`** — PostToolUse fires after the refund already ran (§2, §11).
**Checkpoint:** `settings.json` parses as valid JSON and your hook entry is under `hooks.PreToolUse[0]`.

### 5. Approve the under-$500 case (~3 min)
Make sure a $50 refund still passes through. A hook that blocks everything is a broken hook.
- [ ] Pipe `{"tool_name":"issue_refund","tool_input":{"amount_usd":50}}`; verify `{"decision": "approve"}`
- [ ] Pipe a non-`issue_refund` tool name; verify `approve` (defense-in-depth even though `matcher` filters)

**Why:** §3 — `approve` lets the tool run normally; the matcher already filters by name, but the script should still do the right thing if invoked standalone.
**Checkpoint:** both invocations print `approve`.

### 6. End-to-end test against Claude Code (~7 min)
Start Claude Code in the project. Simulate a support scenario where the model would call `issue_refund(amount_usd=600, ...)`.
- [ ] Prompt: "Issue a $600 refund to order ORD-1001 for a damaged item."
- [ ] Watch the tool call get intercepted; the model should receive the `reason` and pivot to `escalate_to_human`

**Why:** §10 — end-to-end, the hook blocks, the model reads the `reason`, and it recovers by calling the escalation path. That recovery loop is the whole point.
**Checkpoint:** no refund is issued; the model's next tool call is `escalate_to_human` (or it asks the user how to escalate).

## Verify
Trigger the `issue_refund` tool with a $600 amount. Expected:
- Hook emits `{"decision": "block", "reason": "Refund amount $600.00 exceeds the $500.00 auto-approve cap. Call escalate_to_human instead."}`
- The model does **not** retry `issue_refund`; it calls `escalate_to_human` or surfaces the block to the user
- A $50 refund still executes normally (sanity: hook doesn't over-block)

**Common mistakes:**
- Registering under `PostToolUse` instead of `PreToolUse` — the refund already ran; money is gone (§2, §11)
- Exiting non-zero to "block" — non-zero is a hook *failure*, not a structured block; use exit 0 with `decision: "block"` (§3)
- Empty or punitive `reason` — the model has nothing to recover with and will loop or give up (§3, §10)
- Matching on `"*"` instead of `"issue_refund"` — your hook now fires on every tool and slows everything down (§4)

## Stretch — Polish block (30 min on Practice Day)
Finish the refund hook and verify trigger conditions end-to-end.
- [ ] Add a unit test: feed 4 stdin payloads ($50, $500, $501, malformed) and assert the decision for each
- [ ] Add a `PostToolUse` audit hook on `issue_refund` that appends `{session_id, amount, decision, timestamp}` to `exercises/hooks/audit.log` (§6)
- [ ] Try the "poisoned session" drill: after a blocked refund, `fork_session` instead of `--resume` and confirm the fork starts clean (§7)
- [ ] Add one deny-list regex case to the hook (e.g., `reason` field containing "test"/"fraud") and verify it blocks independent of amount

## If stuck
Compare with [minimal_hook_example.py](minimal_hook_example.py). Read → close → rewrite.
