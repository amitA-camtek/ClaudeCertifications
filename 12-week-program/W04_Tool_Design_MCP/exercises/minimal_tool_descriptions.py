"""
W04 — Tool description quality: BAD vs GOOD, side by side.

Goal of this file:
    Show the same two tools declared twice — once with terse/ambiguous
    descriptions, once with rich/explicit descriptions — and explain how
    the quality of the description drives tool selection.

Why this matters for the exam:
    The model picks a tool by reading its `description`. Not by reading
    your system prompt. Not by reading the tool name. The description is
    THE selector. Terse descriptions that "save tokens" are the single
    most common W04 distractor.

You do NOT need the Anthropic SDK to read this file — it's a side-by-side
comparison with commentary. Run it to see the two catalogs printed.
"""

from __future__ import annotations
import json

# =============================================================================
# SCENARIO
# =============================================================================
#
# The agent has two tools in an inventory/order domain:
#
#   1. A tool that looks up STATIC product metadata by SKU (name, price,
#      category). This is cheap, cacheable, always returns the same thing
#      for the same SKU.
#
#   2. A tool that checks REAL-TIME stock levels across warehouses. This
#      hits a live system, can time out, varies minute-to-minute.
#
# These two tools are EASY to confuse if you describe them badly — they
# both "look stuff up about a product". The model's only way to tell them
# apart is what you write in the `description` field.


# =============================================================================
# BAD TOOL CATALOG — terse, ambiguous, no examples, no boundaries
# =============================================================================

BAD_TOOLS = [
    {
        "name": "lookup_sku",
        "description": "Looks up a product.",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    },
    {
        "name": "check_stock",
        "description": "Checks stock.",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    },
]

# What's wrong with BAD_TOOLS:
#
#   * No input format. The model doesn't know if `sku` is a number, an
#     alphanumeric code, a product name. It will guess — badly — when the
#     user says "the blue headphones" instead of a SKU.
#
#   * No examples. The model has never seen a well-formed call.
#
#   * No return format. The model doesn't know what keys it will see back,
#     so it can't compose follow-up tool calls that depend on those keys.
#
#   * No positive boundary. When does `lookup_sku` apply vs `check_stock`?
#     The descriptions overlap.
#
#   * No negative boundary — the single highest-leverage addition. Without
#     "Do NOT use this for X, use Y instead", the model has to guess which
#     of the two overlapping tools is right.
#
#   * No error behavior. On a bad SKU, what does the tool return? The
#     model doesn't know whether to retry, apologize, or escalate.
#
# Observed failure modes when you run an agent against this catalog:
#
#   - User asks "is SKU ABX-0042 in stock?" and the model calls
#     `lookup_sku` (wrong — needs `check_stock`).
#   - User asks "how much is SKU ABX-0042?" and the model calls
#     `check_stock` (wrong — needs `lookup_sku`).
#   - User asks a free-text question ("do you have blue headphones?") —
#     the model invents a SKU string and calls `lookup_sku` with it.
#   - On errors, the model retries blindly or gives up entirely — no
#     structured signal to branch on.


# =============================================================================
# GOOD TOOL CATALOG — explicit input format, examples, boundaries, returns
# =============================================================================

GOOD_TOOLS = [
    {
        "name": "lookup_sku",
        "description": (
            # 1. What it does
            "Look up STATIC product metadata by SKU. "
            # 2. Input format + concrete example
            "Input: `sku`, a 7-character alphanumeric code like 'ABX-0042' "
            "or 'USB-1199'. Must be an exact SKU — do NOT pass product "
            "names or free-text descriptions here. "
            # 3. Return format — so the model can chain follow-ups
            "Returns: {sku, name, category, unit_price_usd, "
            "is_discontinued}. All fields always present except "
            "`is_discontinued` may be null for very old products. "
            # 4. Positive boundary — when this tool IS right
            "Use this when the user mentions a SKU directly and you "
            "need name / price / category. This call is cheap and "
            "cacheable. "
            # 5. Negative boundary — when this tool is NOT right
            "Do NOT use this to check current stock levels or warehouse "
            "availability — use `check_stock` for that. Do NOT use this "
            "when the user gives a free-text product name rather than a "
            "SKU; ask them for the SKU first. "
            # 6. Error shape — so retry logic can branch
            "On unknown SKU returns {isError: true, errorCategory: "
            "'not_found', isRetryable: false, message: ...}."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "7-char alphanumeric SKU, e.g. 'ABX-0042'",
                }
            },
            "required": ["sku"],
        },
    },
    {
        "name": "check_stock",
        "description": (
            # 1. What it does
            "Check REAL-TIME stock levels for a SKU across warehouses. "
            # 2. Input format + example
            "Input: `sku`, a 7-character alphanumeric code like "
            "'ABX-0042'. "
            # 3. Return format
            "Returns: {sku, total_units_available, per_warehouse: "
            "[{warehouse_id, units}], checked_at_iso}. "
            "`total_units_available` may be 0 (legitimate out-of-stock). "
            # 4. Positive boundary
            "Use this when the user asks about availability, 'is X in "
            "stock', 'how many left', or before attempting to place an "
            "order. This call hits a live system and can time out. "
            # 5. Negative boundary
            "Do NOT use this to fetch product name, price, or category — "
            "use `lookup_sku` for those. Do NOT use this to place an "
            "order — this is read-only. "
            # 6. Error shape
            "On upstream timeout returns {isError: true, errorCategory: "
            "'timeout', isRetryable: true, retry_after_seconds: 2, "
            "message: ...}. On unknown SKU returns {isError: true, "
            "errorCategory: 'not_found', isRetryable: false, ...}."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "7-char alphanumeric SKU, e.g. 'ABX-0042'",
                }
            },
            "required": ["sku"],
        },
    },
]

# Why GOOD_TOOLS changes tool-selection quality:
#
#   * Six clauses per description: what / input format+example / return /
#     positive boundary / negative boundary / error shape. Each one kills
#     a specific failure mode that BAD_TOOLS exhibited.
#
#   * The negative boundary ("Do NOT use this for ..., use `other_tool`
#     instead") is the single biggest improvement. For near-similar tool
#     pairs, this clause is what makes the selector deterministic.
#
#   * Explicit return format lets the model chain — after `lookup_sku`,
#     it KNOWS the response has `unit_price_usd` and can use it in the
#     next reasoning turn without hallucinating field names.
#
#   * Error shape in the description means the model can READ the return
#     and act correctly. On `isRetryable: false`, it stops retrying and
#     asks the user. On `isRetryable: true`, your loop retries.
#
#   * Cost: ~8x more tokens than BAD_TOOLS. This is the correct trade.
#     Tokens spent on descriptions are the best-spent tokens in the whole
#     prompt — they are read on every single turn and they directly
#     determine which tool fires.


# =============================================================================
# EXAM-STYLE TAKEAWAYS
# =============================================================================
#
# 1. "Terse descriptions save tokens and speed the agent up" is a
#    distractor. Selection quality collapses; you pay far more in wrong
#    tool calls than you save in description tokens.
#
# 2. If the model keeps picking the wrong tool between two overlapping
#    tools, the fix is almost ALWAYS the description's negative boundary
#    — not a system-prompt rule, not `tool_choice`.
#
# 3. If you can't write a clean negative boundary ("Do NOT use this for
#    X; use Y instead") without contorting it, the two tools probably
#    shouldn't both exist. Consolidate.
#
# 4. Descriptions should also describe the ERROR shape, not just the
#    success shape, so the model's reasoning on the next turn can branch
#    correctly.


def _pretty(catalog: list[dict]) -> str:
    return json.dumps(catalog, indent=2)


if __name__ == "__main__":
    print("=" * 72)
    print("BAD CATALOG — terse, ambiguous, no boundaries")
    print("=" * 72)
    print(_pretty(BAD_TOOLS))
    print()
    print("=" * 72)
    print("GOOD CATALOG — explicit input format, boundaries, return, errors")
    print("=" * 72)
    print(_pretty(GOOD_TOOLS))
    print()
    print("Token-count sketch (characters are a rough proxy):")
    bad_len = sum(len(t["description"]) for t in BAD_TOOLS)
    good_len = sum(len(t["description"]) for t in GOOD_TOOLS)
    print(f"  BAD  total description chars: {bad_len}")
    print(f"  GOOD total description chars: {good_len}")
    print(f"  ratio: {good_len / max(bad_len, 1):.1f}x")
    print()
    print("That ratio is the right trade. Selection quality dominates.")
