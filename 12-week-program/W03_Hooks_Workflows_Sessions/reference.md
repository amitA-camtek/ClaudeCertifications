# W03 Reference — Hooks, Workflows & Sessions (Domain 1.4–1.7)

Complete, self-contained study material for Week 3. Read this end-to-end. Every concept the exam tests for task statements 1.4–1.7 is included here.

Prerequisites: W01 (agentic loop + `stop_reason`) and W02 (hub-and-spoke + `Task` tool). Hooks sit on top of the loop; sessions wrap around multiple loops. You need both mental models before this makes sense.

---

## 1. The central idea for this week

> **Deterministic enforcement (hooks) beats probabilistic guidance (prompt instructions). Every single time.**

If the exam gives you two candidate fixes — *"add 'never do X' to the system prompt"* vs *"register a PreToolUse hook that blocks X"* — the hook wins. Full stop.

A prompt rule says "please don't"; the model obeys it 98% of the time. A hook is code that runs outside the model, inspects the tool call, and **cannot be talked out of it.** On a production surface with real money / PHI / destructive filesystem actions, 98% is a catastrophe. 100% is the job.

This single theme drives 3–5 exam questions. Burn it in now.

---

## 2. Where hooks fit in the agentic loop

Recall the W01 loop:

```
model → tool_use request → YOUR CODE runs the tool → tool_result → model → ...
```

Hooks are interceptors you attach to the *"YOUR CODE runs the tool"* step. The Claude Code / Agent SDK harness invokes them automatically around tool execution. The model does not know they exist; they are enforced by the runtime, not the prompt.

```
model emits tool_use block
        │
        ▼
┌───────────────────┐
│   PreToolUse hook │  ← inspects tool_name + tool_input, can BLOCK or APPROVE
└───────────────────┘
        │ (if not blocked)
        ▼
   tool actually runs
        │
        ▼
┌────────────────────┐
│  PostToolUse hook  │  ← inspects raw result, can NORMALIZE / REDACT / LOG
└────────────────────┘
        │
        ▼
  tool_result returned to model
```

### The two hook types

| Hook | Fires | Can do | Cannot do |
|---|---|---|---|
| **PreToolUse** | *Before* the tool runs | Block the call, approve it, or let it pass through | Actually execute the tool itself |
| **PostToolUse** | *After* the tool returns, *before* the model sees the result | Rewrite/redact/normalize the result, write audit logs | Prevent the tool from having already run |

**Exam-critical distinction:** if your goal is to **stop something from happening**, you need **PreToolUse**. PostToolUse fires too late — the side effect already occurred. Refunds, deletions, emails sent, database writes — all PreToolUse territory.

PostToolUse is for **shaping what the model sees next**: redact PII before it hits the context, trim bloated results, attach audit metadata, normalize a messy API response.

There are other Claude Code hook events (`UserPromptSubmit`, `Stop`, `SubagentStop`, `SessionStart`, `Notification`, `PreCompact`) — they exist, but the exam overwhelmingly tests PreToolUse vs PostToolUse. Know those two cold.

---

## 3. The hook script interface

A hook is an external script (Python, bash, Node, whatever — the harness runs it via a shell command). The contract is stdin/stdout JSON:

### Input (stdin)

The harness pipes a JSON object to the script's stdin. The fields depend on the hook event, but for tool hooks the shape is roughly:

```json
{
  "session_id": "sess_abc123",
  "hook_event_name": "PreToolUse",
  "tool_name": "issue_refund",
  "tool_input": {
    "order_id": "ORD-1001",
    "amount_usd": 742.00,
    "reason": "customer requested"
  },
  "cwd": "/path/to/project"
}
```

For `PostToolUse`, the same object also contains a `tool_response` field with the raw tool result.

### Output (stdout)

The script prints a single JSON object to stdout and exits 0. The shape:

```json
{
  "decision": "block",
  "reason": "Refund amount $742.00 exceeds $500 auto-approve cap. Escalate to tier-2."
}
```

| `decision` value | Effect |
|---|---|
| `"approve"` | Tool runs (PreToolUse) or result is passed through unmodified (PostToolUse). |
| `"block"` | Tool does **not** run. The `reason` string is fed back to the model as the `tool_result`, so the model sees *why* and can recover. |
| *(omitted)* | Harness uses its default (usually pass-through). |

### Exit codes matter

- **Exit 0, no `decision` field** → pass-through.
- **Exit 0, `decision: "block"`** → block, feed `reason` to the model.
- **Exit non-zero** → treated as a hook failure; behavior depends on config, but typically blocks defensively and surfaces the error.

### Why stdin/stdout JSON?

It's language-agnostic. Your hook can be a 30-line Python file, a shell one-liner, a Go binary — the harness doesn't care. That portability is part of why hooks are a platform feature rather than a prompt concept.

---

## 4. Wiring a hook in `settings.json`

Hooks are registered in Claude Code's `settings.json` (project: `.claude/settings.json`; user-global: `~/.claude/settings.json`). The shape is a map keyed by hook event name, containing matcher + command entries:

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
    ],
    "PostToolUse": [
      {
        "matcher": "get_customer",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/redact_pii.py"
          }
        ]
      }
    ]
  }
}
```

Field notes:

- **`matcher`** — a pattern matched against `tool_name`. Exact name like `"issue_refund"`, a regex, or `"*"` for every tool. Multiple matchers can coexist; they all fire for matching calls.
- **`type: "command"`** — the hook is an external shell command. The harness spawns it, pipes JSON to stdin, reads JSON from stdout.
- **`command`** — the exact command string. Relative paths resolve from the project root.

**Exam distractor pattern:** a config where the hook is registered under `PostToolUse` but the stated goal is "prevent refunds over $500 from executing." Wrong — PostToolUse fires after the refund already ran. The money is out. Move it to `PreToolUse`.

---

## 5. Deterministic vs probabilistic — the canonical comparison

Put this table in front of you for the exam. Every hook question is some variant of it.

| Concern | Probabilistic approach (prompt) | Deterministic approach (hook / config) |
|---|---|---|
| Stop refunds > $500 | "NEVER issue refunds over $500 without escalation." in system prompt | PreToolUse hook on `issue_refund` that blocks when `amount_usd > 500` |
| Redact PHI before logging | "Redact patient names before logging." in system prompt | PostToolUse hook that runs a regex over `tool_response` and replaces matches |
| Prevent `rm -rf /` | "Never run destructive shell commands." | PreToolUse hook on `Bash` that blocks commands matching a deny-list regex |
| Require a specific tool for structured output | "Always call `extract_invoice`." | `tool_choice: {"type": "tool", "name": "extract_invoice"}` (from W07) |
| Force delegation to a subagent | "You must use the research subagent." | `allowedTools` excludes direct web tools, so the coordinator *has* to delegate |

Prompt instructions are the right tool for **style, tone, reasoning guidance** — things that are naturally fuzzy. Hooks are the right tool for **policy, safety, compliance, audit** — things that must not fail.

### Why the exam harps on this

Distractors almost always include the "add a rule to the system prompt" option because it *looks* like it should work, and in casual testing it usually does. The exam rewards recognizing that "usually" is not an acceptable failure mode for a $10k refund button. Pick the deterministic answer every time.

---

## 6. PostToolUse as a shaping tool

PostToolUse doesn't just do audit logging. Common production uses:

| Use case | What the hook does |
|---|---|
| **Redaction** | Scan the tool result for SSN / email / credit-card patterns; replace with `[REDACTED]` before it enters the model's context |
| **Normalization** | The API returns 40 fields; the hook returns only the 5 the model needs. Keeps context compact (W05 / W09 theme). |
| **Audit logging** | Append `{tool_name, input, output, timestamp, session_id}` to an audit file. The model never sees this; the logging is a side effect. |
| **PII stripping for training** | If you capture sessions for fine-tuning / replay, strip PHI here so raw PHI never hits disk. |
| **Schema enforcement on output** | If a tool sometimes returns malformed JSON, the hook can sanity-check and wrap it before the model sees it. |

**Exam nuance:** PostToolUse sees the tool's real output. Whatever it writes to stdout becomes what the *model* sees. The model cannot tell you ran a hook — only that the result looks clean.

---

## 7. Sessions: `--resume`, named sessions, `fork_session`

A **session** is the persisted conversation state — the message history, system prompt, tool definitions, and any agent-level state. Claude Code sessions are stored per project so you can come back tomorrow and continue.

### `--resume <name>`

`claude --resume my-refactor` re-opens an existing session by name. You get back the entire message history. The model continues where you left off, with full context.

Use when:
- You're continuing the *same* task (e.g., a multi-day refactor).
- The context is still coherent and relevant.
- You want the model to remember decisions you've already made together.

Do **not** use when:
- The last turn ended in a destructive failure (botched file write, corrupted commit). The session history now contains the broken state and the model's rationale for it — that context will poison the next turn. **Fork instead.** (This is a recurring distractor.)
- The session is long and stale and the current task is different. Start fresh.

### Named sessions

You can create a session with an explicit name (e.g., `claude --session-name frontend-audit`). Naming makes them easy to list, resume, and distinguish — otherwise you end up with a pile of timestamp-named sessions you can't tell apart.

### `fork_session`

Creates a divergent copy of the current session at its current state. Both the original and the fork share the history up to the fork point; after that they evolve independently.

Use when:
- You want to **explore a hypothesis** without contaminating the main thread. "Try migrating this one file to the new API; if it works I'll apply the same pattern elsewhere." Trial migration goes in a fork.
- **Recovery from a poisoned session.** The main session hit a destructive failure. Fork to a clean branch point (or start fresh); do **not** resume into the poisoned history.
- **Branched research** (W02 theme) — one fork per hypothesis.

### Resume vs fork — the decision rule

| State of last session | Next move |
|---|---|
| Clean, task continuing | `--resume` |
| Clean, different task | Start fresh |
| Last turn crashed / wrote bad data / model got confused | **Fork** from a clean point (or start fresh) — **never resume** |
| Want to try something risky without losing current progress | **Fork** |
| Session is very long and attention is degrading | `/compact` or fork a new summary-seeded session |

---

## 8. Stale context and `/compact`

Sessions get stale. Symptoms:
- Model refers to decisions made 80 turns ago that have since been reversed.
- Tool descriptions and CLAUDE.md rules start getting ignored (crowded out by noise).
- Latency creeps up (more tokens in, more tokens out).
- Model repeats itself or loses track of the current subtask.

### Mitigation options (roughly in order of preference)

1. **`/compact`** — asks Claude to produce a compact summary of the session so far, then continues with that summary as the new history. Cheapest, usually sufficient.
2. **Fork + seed** — fork a fresh session, paste in a hand-written summary of the relevant state. Best when `/compact` is too lossy.
3. **Scratchpad file** — dump structured state (decisions, open questions, current step) to a file the model reads each session. Survives crashes. (W10 theme.)
4. **Start fresh** — sometimes the right answer. Accept the loss of conversational history.

### Exam distractor pattern

"The session is slow and confused. Increase the context window / upgrade to a larger model." — **wrong.** Bigger windows don't fix stale context; attention degrades regardless of cap (lost-in-the-middle effect, W09). The fix is structural: compact, fork, or start fresh.

---

## 9. Workflow enforcement: prompt chains vs adaptive decomposition

(Restating from the W02 lens because the exam conflates these with hook questions.)

| Pattern | Mechanism | When right |
|---|---|---|
| **Fixed prompt chain** | Predefined sequence of steps, often via separate API calls: classify → look-up → act → confirm. Each step's output feeds the next step's input deterministically. | Well-understood tasks with a known shape. Predictable latency, easy to debug, easy to add hooks/validation between steps. |
| **Adaptive decomposition** | Coordinator agent inspects the input and dynamically decides how many subagents to spawn and of what type (W02). | Open-ended or multi-concern inputs where the shape isn't known in advance. |

Hooks integrate cleanly with both:
- In a **fixed chain**, register a PreToolUse hook on each stage's action tool; failures surface as structured errors between stages.
- In **adaptive decomposition**, the hook enforces the same policy regardless of which subagent tries to call the guarded tool. One hook, uniform policy.

### Exam-critical gotcha

A question may describe a task where the steps are known and ask whether to use adaptive decomposition. If the steps are fixed, adaptive is overkill — it adds a reasoning turn (and a failure mode) for no benefit. Prefer the simpler pattern.

---

## 10. Worked example: the refund scenario

This is the canonical W03 exam scenario. Memorize the shape.

**Setup:** customer support agent with an `issue_refund` tool. Policy says refunds over $500 must be escalated to a human.

**Probabilistic (wrong) fix:**

```
SYSTEM PROMPT: "NEVER issue refunds over $500. If the amount is higher, call escalate_to_human."
```

The model usually obeys. Sometimes — when the customer is insistent, when the reasoning chain gets tangled, when a prompt injection overrides the system prompt — it doesn't. You've issued a $9,000 refund you shouldn't have.

**Deterministic (correct) fix:** register a PreToolUse hook on `issue_refund`:

```python
# .claude/hooks/refund_gate.py
import json, sys
evt = json.load(sys.stdin)
amt = float(evt["tool_input"].get("amount_usd", 0))
if evt["tool_name"] == "issue_refund" and amt > 500:
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"Refund amount ${amt:.2f} exceeds the $500 auto-approve cap. "
            "Call escalate_to_human instead."
        ),
    }))
else:
    print(json.dumps({"decision": "approve"}))
```

Wired via `.claude/settings.json` under `PreToolUse` with `matcher: "issue_refund"`. Now:

- The model *tries* to call `issue_refund(amount_usd=742, ...)`.
- The harness runs the hook.
- The hook writes `decision: "block"` with a helpful `reason`.
- The model gets the `reason` as the tool result. It sees "exceeds $500 cap — call escalate_to_human instead" and does so.
- **No refund was issued.** The safety is enforced in code, not in prose.

You keep the prompt rule too (belt + suspenders — the prompt lets the model pick the right path on the first try, the hook is the hard stop). But the prompt rule is not *load-bearing* anymore.

---

## 11. Anti-patterns (these ARE the exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| "Add 'NEVER issue refunds over $500' to the system prompt" | Probabilistic; model can be talked out of it | PreToolUse hook with `decision: "block"` |
| Hooks and prompts are interchangeable | They aren't — one is deterministic, one is not | Reach for prompts for tone/reasoning, hooks for policy/safety |
| Use PostToolUse to prevent a destructive action | PostToolUse fires *after* the tool ran; damage is done | PreToolUse is the only option for "prevent" |
| Resume a session after a failed destructive operation | The poisoned history will mis-steer the next turn | **Fork** from a clean point, or start fresh |
| Let the model decide when to escalate using sentiment | Sentiment ≠ complexity; this fails on polite edge cases | Hook + explicit policy thresholds |
| Rely on "max iterations" to stop runaway tool use | Truncates legitimate work | Hook that blocks the specific abusive pattern + high safety fuse |
| "Increase context window" to fix stale session | Attention doesn't scale with window size | `/compact`, fork + seed, or start fresh |
| Log PHI in a PostToolUse hook that returns the data unchanged | Data hit the model context before redaction | Redact *in* the PostToolUse hook before returning |
| One hook registered under `PostToolUse` to "block" the tool | Wrong event — it already ran | Register under `PreToolUse` |
| Register the hook only on the subagent's tool list | Hooks are harness-level, registered in `settings.json`; they aren't part of `AgentDefinition` | Register in `settings.json`, applies wherever the tool is called |
| Adaptive decomposition for a task with a known fixed sequence | Adds a reasoning turn + failure mode for no benefit | Fixed prompt chain |
| Start a new session every turn to avoid staleness | Throws away all useful context | Use `--resume` when coherent; `/compact` or fork when stale |

---

## 12. What the exam will probe

Based on task statements 1.4–1.7:

- **1.4 (Hooks):** given a scenario with a hard policy requirement ("refunds must never exceed X without human approval"), pick the correct mechanism. Expect PreToolUse-vs-PostToolUse distractors and "just add it to the prompt" distractors.
- **1.5 (Deterministic enforcement):** given two candidate fixes, pick the one that gives *100%* compliance rather than *usually*. Prompt rules are the trap answer.
- **1.6 (Sessions):** given a session in a specific state (long-running, crashed, just finished a task), pick `--resume`, `fork_session`, `/compact`, or start-fresh. Resume-after-crash is the canonical distractor.
- **1.7 (Workflows):** given a task shape, pick fixed prompt chain vs adaptive decomposition. Adaptive-for-a-fixed-task is the canonical distractor.

Expect at least one question that combines all four: a broken multi-agent refund workflow where you need to (a) add a hook, (b) fork instead of resume, and (c) switch from adaptive back to a fixed chain.

---

## 13. Fast recap

- **PreToolUse blocks; PostToolUse shapes.** If you need to prevent a side effect, only PreToolUse works.
- **Hook script contract:** JSON on stdin, JSON on stdout with `decision: "approve" | "block"` + optional `reason`. Wired via `settings.json` with a `matcher` and a `command`.
- **Deterministic enforcement (hooks, `tool_choice`, schemas) beats probabilistic guidance (prompt rules).** This is THE theme.
- **Sessions:** `--resume` for coherent continuation, `fork_session` for risky exploration or recovery from a poisoned session, `/compact` for staleness, start fresh when history is worthless.
- **Never resume into a poisoned context.** Fork.
- **Fixed chain vs adaptive decomposition** — fixed for known steps, adaptive for open-ended / multi-concern inputs.
- **Bigger context window does not fix stale context.** Structural fixes only.

When you can explain each of those seven bullets out loud in ~20 seconds each, you're ready for the W03 test.
