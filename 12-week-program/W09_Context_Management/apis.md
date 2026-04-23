# W09 APIs — Claude APIs for this week

> APIs relevant to **context management and reliability**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Messages API** with explicit `case_facts` section in prompt | Persistent structured facts that survive summarization | Long-session support |
| **`client.messages.count_tokens()`** | Measure prompt size before sending | Decide when to trim / split |
| **Tool-output trimming** at the wrapper layer | Reduce verbose tool returns to the 3–5 fields the model needs | Every tool call |
| **Structured error return from tools/subagents** | Let callers branch on category, preserve partial results | Error propagation |

---

## API snippets

### Count tokens before sending
```python
count = client.messages.count_tokens(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "..."}],
)
print(count.input_tokens)
```

### Trim a verbose tool result
```python
def trim_customer(full: dict) -> dict:
    # keep only what the model needs to answer the user
    return {
        "id": full["id"],
        "name": full["name"],
        "tier": full["tier"],
        "open_tickets": len(full.get("tickets", [])),
    }
```

### Structured error with partial results
```python
return {
    "isError": True,
    "errorCategory": "timeout",
    "isRetryable": True,
    "attempted_query": {"customer_id": "C123", "date_range": "30d"},
    "partial_results": partial,  # what we DID get
    "alternatives": ["Retry with date_range='7d'", "Ask user for more specific ID"],
    "message": "DB read timeout after 30s",
}
```

---

## Working example — multi-turn support agent with `case_facts` block + trimmed tool output + structured errors

Save as `support_agent.py`:

```python
"""
Customer-support agent with:
- Persistent `case_facts` block (survives summarization)
- Tool output trimming at the wrapper
- Structured error returns with partial results
- Valid escalation triggers (explicit / policy / inability) - NOT sentiment
"""
import anthropic, json, random, time

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5"

# --- mock "database" and tool wrappers ---
CUSTOMERS = {
    "C100": {"id": "C100", "name": "Alice Garcia", "tier": "gold",
             "email": "alice@example.com", "phone": "+1-555-0100",
             "tickets": [{"id": "T1", "status": "open"}, {"id": "T2", "status": "closed"}],
             "purchase_history": [{"id": f"P{i}", "amount": random.randint(10,500)} for i in range(40)]},
}

def tool_lookup_customer(customer_id: str) -> dict:
    # Simulate 10% timeout
    if random.random() < 0.10:
        return {
            "isError": True, "errorCategory": "timeout", "isRetryable": True,
            "attempted_query": {"customer_id": customer_id},
            "partial_results": None,
            "alternatives": ["Retry in 5s", "Ask user to provide order number instead"],
            "message": "CRM DB timeout",
        }
    row = CUSTOMERS.get(customer_id)
    if row is None:
        return {
            "isError": True, "errorCategory": "not_found", "isRetryable": False,
            "attempted_query": {"customer_id": customer_id},
            "partial_results": None,
            "alternatives": ["Ask user to verify the ID or provide email"],
            "message": f"No customer with id {customer_id}",
        }
    # TRIM: the DB row has 40 purchases + 5 fields per ticket. Model only needs summary.
    return {
        "id": row["id"],
        "name": row["name"],
        "tier": row["tier"],
        "email": row["email"],
        "open_tickets": sum(1 for t in row["tickets"] if t["status"] == "open"),
        "total_purchases": len(row["purchase_history"]),
    }

TOOLS = [{
    "name": "lookup_customer",
    "description": (
        "Look up a customer by exact ID (e.g., 'C100'). "
        "Returns a trimmed customer summary OR a structured error. "
        "On errors, check errorCategory: 'timeout' is retryable, 'not_found' is not."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"],
    },
}]

# --- case_facts block: persistent, structured, re-injected each turn ---
case_facts = {
    "session_id": "sess-001",
    "customer_id": None,
    "customer_name": None,
    "customer_tier": None,
    "agreed_actions": [],
    "escalation_reason": None,
}

SYSTEM_TEMPLATE = """You are a customer support agent.

## Case facts (authoritative — use these over conversation history)
{case_facts_json}

## Rules
- If the customer explicitly asks for a manager, set escalation_reason='explicit_request' and escalate.
- If the request is outside policy (refund > $500), set escalation_reason='policy_gap' and escalate.
- If you cannot progress after 2 tool attempts, set escalation_reason='inability' and escalate.
- DO NOT escalate based on the customer's tone or apparent frustration.
- If a tool returns isError, branch on errorCategory — retry if isRetryable, otherwise inform user.
- If multiple matches: ASK for an identifier; do not guess.
"""

def build_system() -> str:
    return SYSTEM_TEMPLATE.format(case_facts_json=json.dumps(case_facts, indent=2))

def chat_turn(messages: list[dict]) -> tuple[list[dict], str]:
    """Run one Claude turn, handling any tool calls, return updated messages + final text."""
    while True:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=build_system(),
            tools=TOOLS,
            messages=messages,
        )
        if resp.stop_reason == "end_turn":
            text = "\n".join(b.text for b in resp.content if b.type == "text")
            return messages, text
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    if block.name == "lookup_customer":
                        result = tool_lookup_customer(block.input["customer_id"])
                        # update case_facts on a successful lookup
                        if not result.get("isError"):
                            case_facts["customer_id"] = result["id"]
                            case_facts["customer_name"] = result["name"]
                            case_facts["customer_tier"] = result["tier"]
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
            messages.append({"role": "user", "content": tool_results})
            continue
        raise RuntimeError(f"Unexpected stop_reason: {resp.stop_reason}")

def main():
    # Turn 1
    messages = [{"role": "user", "content":
                 "Hi, my customer ID is C100. Can you confirm my tier and open tickets?"}]
    messages, reply = chat_turn(messages)
    print("\n[customer] Hi, my customer ID is C100...")
    print(f"[agent] {reply}")
    messages.append({"role": "assistant", "content": reply})

    # Turn 2 — tests whether case_facts persists the customer ID even after tool trimming
    messages.append({"role": "user", "content":
                     "Actually, I want to speak to a manager about my last ticket."})
    messages, reply = chat_turn(messages)
    print("\n[customer] I want to speak to a manager...")
    print(f"[agent] {reply}")

    print("\n=== Final case_facts ===")
    print(json.dumps(case_facts, indent=2))

if __name__ == "__main__":
    main()
```

---

## How to run

**Setup:**
```bash
pip install anthropic
```

**Set API key (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Run:**
```bash
python support_agent.py
```

**Expected behavior:**
- Turn 1: agent calls `lookup_customer("C100")`, receives trimmed summary, answers about tier and open tickets. `case_facts` updates with `customer_id`, `name`, `tier`.
- Turn 2: customer explicitly asks for manager → agent sets `escalation_reason="explicit_request"` and escalates. Does NOT re-lookup (case_facts has the info).

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| Agent re-calls `lookup_customer` every turn | Not re-injecting `case_facts` via `system` | Rebuild system prompt each call with latest case_facts (shown in example) |
| Agent escalates on tone ("customer seems upset") | System prompt not explicit enough | Add the "NOT on tone" rule emphatically; test with a frustrated-but-simple request |
| Tool errors crash loop | Wrapper raises instead of returning structured error | Always return the `isError` dict; never `raise` from a tool wrapper |
| `case_facts` block too large (>2k tokens) | Storing full tool output instead of extracting | Store only 5–10 fields; if the block grows, trim it |
| Lost-in-the-middle: agent misses a fact stated 20 turns ago | Fact was in conversation history, not in case_facts | Move it into case_facts |

**Measure the prompt size:**
```python
count = client.messages.count_tokens(model=MODEL, system=build_system(), messages=messages)
print(f"Current input_tokens = {count.input_tokens}")
```
If growing linearly with turns, you're not trimming. Should stay roughly flat once case_facts stabilizes.

**Test escalation triggers individually:**
- Explicit request: "I want a manager" → should escalate with `explicit_request`.
- Policy gap: "Refund me $5000" (beyond authority) → should escalate with `policy_gap`.
- Inability: after 2 failed lookups → should escalate with `inability`.
- Sentiment: "I'm furious!!!" with a trivial request → should NOT escalate.

---

## Exam connection

- **Trimmed tool output at the wrapper** is what "don't overwhelm the model with 40 fields" looks like in code.
- **`case_facts` persistent block** fixes the lost-in-the-middle + summarization-loses-numbers failure mode.
- **Structured errors with `attempted_query`, `partial_results`, `alternatives`** is exactly the exam's "correct error propagation" answer.
- **Escalation rules**: explicit / policy / inability — the exam distractors propose sentiment or self-confidence.
- **Ask for disambiguator on multiple matches** — explicit rule in the system prompt.
