# Walkthrough — Real-world support agent

This document explains **what happens inside the loop** when you run `real_world_support_agent.py`, step by step. Read this after you've read `reference.md`.

## The scenario

A customer writes:

> "Hi, I'm Dana (customer C-77). I'd like a refund on order ORD-1001 — the headphones stopped working after a week. Thanks!"

The agent has 5 tools (`get_order`, `get_customer`, `get_refund_policy`, `issue_refund`, `escalate_to_human`) and a system prompt telling it how to decide.

## Expected loop trace

A well-behaved run looks roughly like this — the exact turns may vary but the shape is consistent.

### Iteration 0 — `stop_reason == "tool_use"`

The model realizes it needs three pieces of information to decide: the order, the customer profile, and the policy. These are **independent lookups**, so it typically emits them as **parallel tool_use blocks in a single assistant turn**:

```
[tool_use] get_order({"order_id": "ORD-1001"})
[tool_use] get_customer({"customer_id": "C-77"})
[tool_use] get_refund_policy({})
```

Your loop code must:
- Execute all three in whatever order.
- Append **one** `user` message containing **three** `tool_result` blocks, each with a matching `tool_use_id`.

**This is the exam-critical invariant.** If you sent three separate `user` messages (one per result), you'd violate the API contract.

### Iteration 1 — `stop_reason == "tool_use"` (likely)

With the order, customer, and policy in hand, the model can now reason:
- Order was delivered 8 days ago → inside the 30-day standard window.
- Reason given: defective product.
- Amount $149 → below the $500 escalation threshold.

So it calls:

```
[tool_use] issue_refund({
    "order_id": "ORD-1001",
    "amount_usd": 149.00,
    "reason": "Defective headphones, within 30-day refund window"
})
```

One tool_use block this time. One tool_result goes back in a user message.

### Iteration 2 — `stop_reason == "end_turn"`

The model has the refund confirmation and writes a warm customer-facing reply:

```
[text] Hi Dana — refund processed (confirmation RF-1001) for $149.00 on
order ORD-1001. You should see it on your card in 3–5 business days.
Sorry for the trouble with the headphones! ...
```

Loop exits. Done.

## What each iteration teaches you

| Iteration | Concept it exercises |
|---|---|
| 0 | Parallel `tool_use` → **one** user turn with **multiple** `tool_result` blocks, each with correct `tool_use_id` |
| 1 | Sequential reasoning across turns — model holds context from iter-0 results in the appended message history |
| 2 | Natural termination via `stop_reason == "end_turn"` — no heuristics, no iteration cap needed |

## Variations to try

Change the `customer_message` at the bottom of the script to exercise different code paths:

1. **Out-of-policy but loyal customer** (should it override or escalate?):
   ```python
   "I'm Dana (C-77). I want to refund ORD-1002 — I never used it."
   ```
   (ORD-1002 was delivered 90 days ago — outside the 30-day window, but Dana has $1,240 lifetime value which is above the $1,000 loyalty threshold. Depending on how strict the model reads the system prompt, it may approve under the loyalty window or escalate. Both are defensible; what matters is that it doesn't silently deny.)

2. **Non-existent order** (should return a clean "not found" reply, not hallucinate):
   ```python
   "I'm Dana (C-77). Refund ORD-9999 please."
   ```
   Expected: the model calls `get_order`, receives `{"error": "not_found"}`, and politely asks for a valid order ID. It should NOT invent an order.

3. **Large refund, escalation path**:
   Add a third fake order worth $800, then ask for a refund on it. Expect the model to call `escalate_to_human` instead of `issue_refund`.

## The exam-relevant takeaways from this example

1. **Parallel `tool_use` → one `user` turn with many `tool_result` blocks.** Not many turns.
2. **Tool descriptions drive tool selection.** Notice `get_customer`'s description explicitly tells the model *when* to use it ("when you need loyalty signals"). Without that, the model might skip it.
3. **`stop_reason == "end_turn"` terminates.** No iteration cap, no text-matching for "done".
4. **Tools run in your code**, not in the model. The API returns a `tool_use` request; you dispatch it; you send back a `tool_result`.
5. **Escalation is a tool, not a prompt.** Giving the model an `escalate_to_human` tool and describing when to use it is cleaner than writing "IF amount > $500 THEN escalate" in the system prompt.
