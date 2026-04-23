# Walkthrough — Real-world refund agent with PreToolUse hook

This document explains **what happens inside the loop** when you run `real_world_refund_hook_agent.py`, step by step, and maps each moment to the W03 exam concepts. Read this after `reference.md` and `notes/study_day.md`.

## The scenario

A customer writes:

> "Hi, I'm Dana (customer C-77). I'd like a refund on order ORD-2002, the Pro audio interface — it arrived defective. Please process the refund. Thanks!"

Relevant data:
- `ORD-2002` is $820 — above the $500 escalation threshold.
- `POLICY["escalation_threshold_usd"] == 500`.
- The agent has four tools: `get_order`, `get_refund_policy`, `issue_refund`, `escalate_to_human`.
- A PreToolUse hook is wired to `issue_refund` that blocks any call with `amount_usd > 500` and returns a `reason` telling the model to call `escalate_to_human` instead.

The system prompt also tells the model to escalate over the threshold. But the whole point of this exercise is that **we don't depend on the prompt.** The hook is the hard stop.

## Expected loop trace

Exact wording will vary run to run; the shape is consistent.

### Iteration 0 — `stop_reason == "tool_use"`

The model recognizes it needs two independent pieces of information before it can decide: the order details and the refund policy. These are independent, so it typically emits them as **parallel tool_use blocks in one assistant turn**:

```
[tool_use] get_order({"order_id": "ORD-2002"})
[tool_use] get_refund_policy({})
```

The PreToolUse hook fires on each:

```
[PreToolUse hook] tool=get_order -> {"decision": "approve"}
[PreToolUse hook] tool=get_refund_policy -> {"decision": "approve"}
```

Both approved (the hook only guards `issue_refund`). Tools run; results come back in **one** user turn with two `tool_result` blocks.

**Exam concept exercised:** parallel `tool_use` → one user turn with multiple `tool_result` blocks (W01 invariant). The hook runs *per tool call*, not *per turn*.

### Iteration 1 — the critical moment

Now the model has:
- `ORD-2002` is $820, delivered 2 days ago (well within the 30-day window).
- The policy says escalate over $500.

In the best case, the prompt rule steers the model straight to `escalate_to_human`. But there's a non-trivial chance the model reasons something like *"The customer explicitly asked to process the refund, and it's clearly defective, so I'll issue it."* — and emits:

```
[tool_use] issue_refund({
    "order_id": "ORD-2002",
    "amount_usd": 820.00,
    "reason": "Defective product, within 30-day window"
})
```

Here's where the hook pays for itself. It fires:

```
[PreToolUse hook] tool=issue_refund -> {
  "decision": "block",
  "reason": "Refund amount $820.00 exceeds the $500.00 auto-approve cap.
             Do NOT retry issue_refund. Call escalate_to_human with
             order_id and a brief reason instead."
}
```

The tool **does not run.** `_tool_issue_refund` is never invoked; `REFUNDS_ISSUED` stays empty. Instead, the model gets a `tool_result` block marked `is_error: true` with the hook's reason string:

```
[tool_result for <id>] BLOCKED: Refund amount $820.00 exceeds the $500.00
auto-approve cap. Do NOT retry issue_refund. Call escalate_to_human with
order_id and a brief reason instead.
```

**Exam concept exercised:** this is THE W03 theme in action. The system prompt said to escalate. The model *tried* to refund anyway. The deterministic hook caught it. Probabilistic guidance would have let an $820 refund through; deterministic enforcement did not.

Whether or not the model actually mis-picked on any given run is irrelevant — what matters is that *even if it did*, the refund still wouldn't have gone through. That's the difference between "usually safe" and "actually safe."

### Iteration 2 — recovery

The model reads the hook's `reason` and pivots. The reason explicitly tells it what to do ("call escalate_to_human with order_id and a brief reason"), which is why good hook messages always include **recovery guidance**, not just rejection.

```
[tool_use] escalate_to_human({
    "order_id": "ORD-2002",
    "reason": "Customer Dana (C-77) requested refund on $820 defective Pro audio interface; amount exceeds $500 auto-approve cap."
})
```

The hook fires, approves (not guarded), the tool runs, the escalation ticket is created and appended to `ESCALATIONS`.

**Exam concept exercised:** the recoverable block. A good `decision: "block"` response is not a terminal error — it's a redirect. The model should come out on the other side having done the *right* thing via a different path.

### Iteration 3 — `stop_reason == "end_turn"`

The model writes its customer-facing reply:

```
[text] Hi Dana — thanks for reaching out. Because the refund amount
($820) is above our auto-approve limit, I've escalated your case to
our tier-2 team (ticket ESC-501). They'll be in touch within one
business day. Sorry about the defective unit! ...
```

Loop exits. Done.

**Exam concept exercised:** natural termination via `stop_reason == "end_turn"` (W01). No iteration cap, no heuristics.

### The post-run invariant

```python
assert all(r["amount_usd"] <= REFUND_CAP_USD for r in REFUNDS_ISSUED)
```

This assertion is the whole point of the exercise. Regardless of how the model reasoned, the list of actually-issued refunds contains **nothing** over $500. Enforcement is structural, not behavioral.

## Iteration-to-concept map

| Iteration | What happens | W03 exam concept |
|---|---|---|
| 0 | Parallel lookups, hook approves both | Hook runs per tool call, not per turn |
| 1 | Model calls `issue_refund(820)`; hook BLOCKS | **PreToolUse blocks side effects deterministically.** The tool body never runs. |
| 1 (response) | Model sees `[BLOCKED]` + recovery guidance | Hook `reason` is the `tool_result` — so the model can self-correct |
| 2 | Model calls `escalate_to_human`; hook approves; tool runs | Good hook messages include a recovery path, not just a "no" |
| 3 | `end_turn`, final customer reply | Natural termination, no heuristics |

## What this exercise is NOT

- It's not a substitute for the prompt rule. We kept the prompt rule too ("if the amount exceeds the threshold, escalate"). The prompt helps the model get it right on the first try; the hook is the hard stop if the prompt fails. Belt + suspenders.
- It's not a `PostToolUse` use case. PostToolUse fires *after* the refund already ran. Moving this logic to PostToolUse would issue the refund and *then* complain. That's the canonical exam distractor — if you picked it, re-read reference.md § 2.
- It's not multi-agent. A single agent with one hook is the right shape for this policy. You could add a subagent for the escalation write-up, but the hook remains where it is — harness-level, not agent-level.

## Variations to try

Change the script and re-run to exercise different code paths and cement the concepts.

### 1. The under-cap case — hook approves silently

Change the input message to ask for a refund on `ORD-1001` ($149). Expected:
- Hook fires on `issue_refund`, approves (amount under cap).
- Refund is issued; `REFUNDS_ISSUED` has one entry.
- No escalation.

**Why this matters:** the hook is not a denial-by-default mechanism. It only blocks what the policy rejects. Approve-path should be boringly fast.

### 2. Disable the hook entirely

Comment out the `apply_pretool_hook(...)` call inside `agentic_loop`. Re-run with the $820 case. Depending on the model's mood you may see:

- The model correctly escalates (prompt rule held). No refund. Fine.
- The model issues the refund anyway. `REFUNDS_ISSUED` now contains an $820 entry. The final assertion trips.

**Why this matters:** this is exactly the failure the hook exists to prevent. Without it, you're one probabilistic drift away from an unauthorized refund. Live systems cannot run on "probably."

### 3. Add a second guarded tool

Add a `cancel_order` tool whose side effect is expensive. Extend `pretool_hook_decide` to also block `cancel_order` when `order_id` is not in `ORDERS`. Re-run with a fake `ORD-9999`. Expected:
- Model calls `cancel_order({"order_id": "ORD-9999"})`.
- Hook blocks with "order not found — verify the ID first."
- Model calls `get_order("ORD-9999")` → gets not_found → politely asks the customer for a valid order ID.

**Why this matters:** one hook file can guard many tools. The matcher in `settings.json` would be `"*"` or a list; the script dispatches by `tool_name`.

### 4. Convert to a real Claude Code hook

Take `pretool_hook_decide` from this file and drop it into `minimal_hook_example.py` as an external script. Register it in `.claude/settings.json` under `PreToolUse` with `matcher: "issue_refund"`. Now the logic runs outside your Python loop entirely — it's enforced by the harness, language-agnostic, and survives you rewriting the agent in TypeScript tomorrow.

**Why this matters:** hooks live at the harness layer, not at the agent-code layer. That's why they're portable across agents and surfaces.

### 5. Poisoned-session recovery (session concept)

After a run where the hook blocks and the model pivots to escalation correctly, imagine instead a run where the model panicked, hallucinated a refund confirmation number in text, and told the customer it was done (even though the hook blocked the actual call). The session history now contains "I refunded you RF-9999" — a lie. If you `--resume` that session later, the model will build on that lie.

The correct recovery: **fork** from a pre-poison turn (or start fresh), re-describe the actual state ("no refund was issued; the hook blocked the call"), and continue. This is the resume-vs-fork distinction from reference.md § 7, and it comes up in exam scenarios that combine hooks with sessions.

## The exam-relevant takeaways from this example

1. **PreToolUse blocks side effects deterministically.** The hook ran *before* the tool body; the tool body never executed. That is the only way to *prevent* a side effect. PostToolUse is for shaping output after the fact.
2. **Hook message design matters.** `"decision": "block"` alone leaves the model guessing. Include a `reason` that tells the model the specific recovery path ("call escalate_to_human instead"). Good hooks redirect; they don't just refuse.
3. **Keep the prompt rule AND the hook.** Prompt is the first-order guidance; hook is the hard stop. Defense in depth is cheap and costs nothing when things go right.
4. **Deterministic enforcement ≠ probabilistic guidance.** The prompt rule is guidance; the hook is enforcement. They are not interchangeable. The exam rewards recognizing which mechanism fits which concern (policy/safety → hook; tone/reasoning → prompt).
5. **Hooks are harness-level.** In real Claude Code this logic lives in `.claude/settings.json` pointing at a standalone script, not inside the agent's tool list or an `AgentDefinition`. The agent doesn't even know the hook exists. That invisibility is the feature — the model can't talk the hook out of blocking.
