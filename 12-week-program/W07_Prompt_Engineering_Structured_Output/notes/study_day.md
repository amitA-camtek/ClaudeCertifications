# W07 Study Day — Prompt Engineering & Structured Output (Domain 4.1–4.3)

## The one thing to internalize

**Deterministic mechanisms beat prompt instructions — and in this domain the deterministic mechanisms are: categorical criteria, forced `tool_choice`, JSON Schema with nullable fields, and enums with `"other"` + detail.**

If a question's correct answer looks like "tell the model more forcefully", it's wrong. The correct answer always adds a concrete rule, a specific threshold, a schema constraint, or a forced tool call.

## Four levers, in order of what to reach for first

1. **Categorical criteria** — replace "important" / "confident" / "unsure" with checkable conditions. E.g., `TIER_1 if severity=blocker AND impact>=100`.
2. **Few-shot (2–4 examples)** — only for ambiguous edge cases. Show reasoning, not just answers. Don't waste shots on canonical cases.
3. **Structured output via `tool_use` + `input_schema`** — never ask for JSON in natural language. That produces syntax errors.
4. **`tool_choice = {"type": "tool", "name": "..."}`** — for extraction, force the specific tool. Never leave it `auto` for mandatory extraction.

## The schema-compliance truth

> **JSON Schema eliminates SYNTAX errors. It does NOT eliminate SEMANTIC errors.**

- Syntax / shape / types / enum membership → guaranteed.
- `vendor_name` is actually the vendor and not the customer → **not** guaranteed.

An exam distractor that says "enforce a JSON Schema to eliminate extraction errors" is half right and therefore wrong. Semantic validation needs Pydantic validators, second passes, or human review.

## Nullable fields are the anti-hallucination lever

If a field is `required: true, type: "string"` and the source doesn't contain the value, the model fabricates one. It has no legal "absent" answer.

Fix: `type: ["string", "null"]` + system prompt rule "return null when the field is not present in the source."

This is the #1 practical fix for hallucinated extraction fields. It shows up on the exam as "pipeline hallucinates due_date when missing — what's the fix?"

## Enum + `"other"` + detail

Closed enums break on novel inputs. Always add `"other"` + a string detail field for any enum whose input domain might evolve. Example:

```json
"payment_terms":        {"enum": ["net_30","net_60","due_on_receipt","other"]},
"payment_terms_detail": {"type": ["string","null"]}
```

And tell the model: if not in the enum, use `"other"` and put the verbatim phrase in `payment_terms_detail`.

## `tool_choice` cheat sheet

| Value | Behavior | Use for |
|---|---|---|
| `{"type": "auto"}` | Model decides | General agent loops |
| `{"type": "any"}` | Must call *some* tool | Must classify but you have multiple tools |
| `{"type": "tool", "name": "X"}` | Must call X | **Extraction tasks — this is the right default** |
| `{"type": "none"}` | Cannot call any tool | Rare, text-only forced reply |

## Anti-patterns that appear as distractors on the exam

| Wrong answer | Why it's wrong |
|---|---|
| "Ask Claude to output JSON in the text reply" | Syntax errors, markdown fences, commentary. Use `tool_use`. |
| "JSON Schema eliminates extraction errors" | Only shape; semantics unguarded. |
| "`tool_choice: auto` for mandatory extraction" | Model may skip the tool and reply in prose. |
| "No nullable fields — all fields required non-null" | Hallucination pressure on absent data. |
| "Closed enum, no `other`" | Breaks on novel values. Silently miscategorizes. |
| "`flag high-confidence findings only`" | Vague; miscalibrated. Needs categorical rule. |
| "Have the model self-rate confidence 1–10" | Self-reported confidence is miscalibrated, worst on hard cases. |
| "Add a prompt rule 'you must call the tool'" | Probabilistic. Use `tool_choice`. |
| "One canonical few-shot example" | One example is not a pattern. Use 2–4. |
| "Twelve few-shot examples covering every case" | Bloat + over-fit. 2–4, only for ambiguous cases. |

## The canonical extraction prompt shape

```python
# Schema
EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": "Record structured invoice fields.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
            "total_usd":   {"type": "number"},
            "due_date":    {"type": ["string", "null"]},   # nullable
            "payment_terms": {"enum": ["net_30","net_60","due_on_receipt","other"]},
            "payment_terms_detail": {"type": ["string", "null"]},
        },
        "required": ["vendor_name","total_usd","due_date",
                     "payment_terms","payment_terms_detail"],
    },
}

# System: categorical rules + 2-3 few-shot on ambiguous cases
SYSTEM = (
    "Extract invoice fields. If a field is not in the source, return null. "
    "For payment_terms not in the enum, use 'other' and put the verbatim phrase "
    "in payment_terms_detail.\n"
    "Examples:\n"
    "  'Net 30' -> payment_terms='net_30', payment_terms_detail=null\n"
    "  'Net 45' -> payment_terms='other',  payment_terms_detail='Net 45'\n"
    "  'due upon receipt' -> payment_terms='due_on_receipt', detail=null\n"
)

resp = client.messages.create(
    model="claude-sonnet-4-6",
    system=SYSTEM,
    tools=[EXTRACT_TOOL],
    tool_choice={"type": "tool", "name": "extract_invoice"},   # FORCE
    messages=[{"role": "user", "content": invoice_text}],
)
```

Every piece is load-bearing: forced tool_choice guarantees the call, schema guarantees shape, nullable + null-when-absent suppresses hallucination, enum+other+detail handles novel cases, few-shot covers the edge cases.

## 3-bullet recap

- **Categorical criteria + forced `tool_choice` + nullable fields + enum-with-other** — these four levers fix ~90% of extraction prompt problems.
- **Schema guarantees SHAPE, not MEANING.** Semantic errors need downstream validation or human review; the schema cannot catch them.
- **Few-shot is for ambiguous cases only.** 2–4 examples, with reasoning shown, covering the edges — not the canonical inputs.
