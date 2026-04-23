# W03 Study Day — Hooks, Workflows & Sessions (Domain 1.4–1.7)

## The one thing to internalize

**Deterministic enforcement (hooks) beats probabilistic guidance (prompt rules). Always.**

A prompt rule that says "NEVER issue refunds over $500" is advice the model usually follows. A PreToolUse hook that blocks `issue_refund` when `amount_usd > 500` is code the model physically cannot bypass. On safety-critical paths the exam always picks the hook.

## The two hooks, in one line each

- **PreToolUse** fires *before* the tool runs. It can **block**. Use it to prevent side effects (refunds, deletions, emails, writes).
- **PostToolUse** fires *after* the tool runs but *before* the result reaches the model. It can **rewrite/redact**. Use it to shape what the model sees next (strip PII, trim verbose output, audit-log).

If the goal is "stop it from happening," it is PreToolUse. PostToolUse is too late — the action already occurred.

## Hook script contract (memorize this shape)

Hook scripts are language-agnostic. Stdin in, stdout out.

**Stdin** (harness gives you):
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "issue_refund",
  "tool_input": {"order_id": "ORD-1001", "amount_usd": 742.00, "reason": "..."}
}
```

**Stdout** (you write back):
```json
{"decision": "block", "reason": "Amount $742 > $500 cap. Escalate instead."}
```

`decision` is `"approve"` or `"block"`. A blocked call never executes; the `reason` string becomes the `tool_result` the model sees — so the model can recover.

## Wiring it in `settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "issue_refund",
        "hooks": [
          {"type": "command", "command": "python .claude/hooks/refund_gate.py"}
        ]
      }
    ]
  }
}
```

- `matcher` matches against `tool_name` (exact string, regex, or `"*"`).
- `type: "command"` = external shell command, stdin/stdout JSON.

## Anti-patterns that appear as distractors on the exam

| Wrong answer | Why it's wrong |
|---|---|
| "Add 'never do X' to the system prompt" | Probabilistic — model can be talked out of it. Use a hook. |
| "Register the hook under PostToolUse" (when goal is prevention) | PostToolUse is too late. Use PreToolUse. |
| "Hooks and prompts are interchangeable" | They are not. Prompts = tone/reasoning. Hooks = policy/safety. |
| "Resume the session after a destructive failure" | History is poisoned; it will mis-steer the next turn. **Fork** instead. |
| "Increase the context window to fix a stale session" | Attention doesn't scale with window size. Use `/compact`, fork, or start fresh. |
| "Run sentiment analysis to decide escalation" | Sentiment ≠ complexity. Use explicit policy thresholds enforced by a hook. |
| "Use adaptive decomposition for a fixed sequence" | Adds a reasoning turn + failure mode for nothing. Fixed chain is correct. |
| "Hooks belong in the AgentDefinition's tool list" | Hooks are harness-level, registered in `settings.json`, not tied to a subagent definition. |

## Sessions: the decision rule

| Session state | Right move |
|---|---|
| Clean, continuing same task | `--resume <name>` |
| Clean, different task now | Start fresh |
| Last turn crashed / destructive failure | **Fork** from a clean point (never resume) |
| Want to try something risky | **Fork** |
| Long + stale + losing coherence | `/compact`, or fork + seed summary |

**Resume-after-crash is the canonical distractor.** The poisoned history (bad file write, corrupted state, model's wrong-rationale chain) will mis-steer every subsequent turn. Fork out of it.

## Fixed chain vs adaptive decomposition (W02 lens, relevant here)

- **Fixed chain** — predefined steps, deterministic order, easy to insert hooks between stages. Right for well-understood tasks.
- **Adaptive decomposition** — coordinator inspects input, decides subagents dynamically (W02). Right for open-ended / multi-concern inputs.

Adaptive on a fixed-shape task is overkill and introduces a reasoning failure mode for no gain.

## The refund scenario in one breath

Policy: "no refunds over $500 without human approval." **Wrong fix:** system prompt rule. **Right fix:** PreToolUse hook on `issue_refund` matching `amount_usd > 500`, returns `decision: "block"` with a `reason` telling the model to call `escalate_to_human`. The model gets the reason as a tool result and picks the escalation path. Zero failures. Zero exceptions.

## 3-bullet recap

- **PreToolUse blocks; PostToolUse shapes.** Deterministic hook beats probabilistic prompt rule every time. JSON-on-stdin, JSON-on-stdout with `decision` + `reason`, wired in `settings.json` with a `matcher`.
- **Never resume a poisoned session.** Fork for recovery and for speculative exploration. `/compact` or start fresh for staleness — bigger windows do not fix it.
- **Fixed chain vs adaptive decomposition:** fixed when the steps are known, adaptive when the input's shape is open-ended. Adaptive on a fixed-shape task is the trap answer.
