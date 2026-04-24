# Operational Topics — Cross-Domain Reference

The 12-week plan covers every task statement in the exam guide at least once. These four topics cut across multiple weeks and are under-weighted relative to their likely exam surface. Read this before Practice Exam 1 at the end of W11.

- **§1. Prompt caching** — likely 2–4 questions (Domain 4, sometimes Domain 3 for Claude Code)
- **§2. Extended thinking** — likely 1–2 questions (Domain 1 loop interaction; Domain 4 output quality)
- **§3. Model selection** — likely 1–2 questions (any scenario asks "which model for this step?")
- **§4. Cost / token economics** — 0–2 questions directly, but underlies answers in Domain 3 (CI/CD) and Domain 4 (batch)

---

## 1. Prompt caching

### What it is

Prompt caching lets you mark a prefix of your request as **cacheable**. Subsequent requests that send the same cached prefix hit the cache instead of re-processing the tokens. Cache reads are ~**10% of input cost** and dramatically lower latency on long prefixes.

### Where `cache_control` lives

`cache_control: {"type": "ephemeral"}` is a block-level attribute you attach to **content blocks** in `system`, `tools`, or `messages`. Everything **before and including** the marked block is cached as one unit.

```python
client.messages.create(
    model="claude-sonnet-4-6",
    system=[
        {"type": "text", "text": LONG_STYLE_GUIDE,
         "cache_control": {"type": "ephemeral"}},   # cached prefix
        {"type": "text", "text": "Now do: " + user_request},
    ],
    tools=[...],
    messages=[...],
)
```

### The 5-minute TTL (ephemeral)

The default `"ephemeral"` cache has a **5-minute sliding TTL** — each hit refreshes it. If 5 minutes elapse with no hit, the cached prefix is evicted. Plan cadence around this: a poll every 6 minutes always misses; every 4 minutes always hits. There's also a 1-hour cache tier (`cache_control: {"type": "ephemeral", "ttl": "1h"}`) with slightly different pricing — use when you know you'll hit the cache at a low frequency.

### What to cache

Good candidates (large, stable across requests):
- System prompt (style guide, persona, agent instructions)
- Tool definitions (JSON schemas can be kilobytes)
- Retrieved context (large doc you're asking questions about)
- Few-shot examples (especially 2–4 multi-turn ones)

Bad candidates:
- The actual user question (changes each request — not reusable)
- Anything after the last `cache_control` breakpoint (not cached)

### Cache breakpoints — you can have up to 4

You can place up to 4 `cache_control` markers per request. Common pattern: one on system prompt, one on tools, one on a retrieved document, one on a stable multi-turn history. Each marker defines a cache segment; shorter shared prefixes hit even if the longer ones don't.

### Exam framing

Typical distractors:
- "Use prompt caching to save cost on the user's message" — **wrong**, the user message varies per turn; only cache stable prefixes.
- "Move the system prompt to a file to save tokens" — **wrong**, loading from a file doesn't reduce token count; caching reduces *recomputation* cost, not token count.
- "Caching reduces output tokens" — **wrong**, caching only affects **input** tokens. Output is computed fresh each time.
- "Enable caching via a model parameter" — **wrong**, it's via `cache_control` on content blocks, not a top-level param.

**Discriminator:** cache stable **prefixes** that are **reused across requests**. Output is never cached.

---

## 2. Extended thinking

### What it is

Extended thinking lets Claude produce internal reasoning tokens before emitting its user-visible response. You control the token budget; the model decides how much to use up to that budget.

```python
client.messages.create(
    model="claude-opus-4-7",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "..."}],
)
```

Reasoning tokens are billed at **output token rate**. The response includes `thinking` content blocks (model's reasoning) plus `text` content blocks (the visible answer).

### When it helps

- **Complex multi-step planning** — the model actually thinks through constraints before acting.
- **Math / logic** — reduces arithmetic errors and hallucinated intermediate steps.
- **Structured-output accuracy** — thinking can verify the extraction before emitting it.

### When it doesn't

- Simple lookups, chit-chat, known-shape transformations — pure cost with no quality gain.
- Agent loops with cheap, fast tool calls — thinking on every turn multiplies latency.

### Interaction with tool use

During extended thinking + tool use, the model can emit `tool_use` blocks **after** thinking. The thinking block is preserved in history; downstream turns can see prior reasoning. This is useful (model doesn't re-think from scratch) and dangerous (poisoned reasoning sticks).

### Interleaved thinking

With `interleaved_thinking`, the model can think again **between** tool calls within a single turn. Good for tasks where the next tool choice depends on the previous result. Cost scales per thinking block.

### Exam framing

Typical distractors:
- "Enable extended thinking to speed up the agent" — **wrong**, it adds latency. It improves quality, not speed.
- "Thinking tokens are free / uncounted" — **wrong**, billed at output rate.
- "Thinking replaces tool use" — **wrong**, they compose; thinking helps the model decide which tool to call.
- "Always enable thinking for structured extraction" — mostly **wrong**; quality gain exists but at 3-10x cost. Enable selectively on hard inputs.

**Discriminator:** extended thinking is a **quality-for-cost-and-latency** trade, scoped per-request.

---

## 3. Model selection — Opus / Sonnet / Haiku

Claude 4.x family (as of late 2025):

| Model | Strengths | Trade-offs | Typical use |
|---|---|---|---|
| **Opus 4.7** | Highest capability, best reasoning, largest context (1M token variant) | Slowest, most expensive | Hard reasoning, novel synthesis, final-pass review, agent coordinator in complex systems |
| **Sonnet 4.6** | Strong capability, good speed, solid tool use | Mid-tier cost | **Default choice** for most production work — agents, extraction, code |
| **Haiku 4.5** | Fastest, cheapest, good enough for many focused tasks | Lower ceiling on novel reasoning, less nuanced | High-volume routing, simple classification, cheap tool-calling subagents, cost-sensitive bulk |

### Mixing models in one pipeline

A **coordinator + subagents** pattern often uses different models per role:
- Coordinator: Opus (needs judgment)
- Each subagent: Sonnet (solid tool use at moderate cost)
- A classification-only subagent: Haiku (fast, cheap)

### Decision framework

Ask, in order:
1. **Is a task at hand where Sonnet has failed noticeably in testing?** → Opus. Otherwise skip to 2.
2. **Is this high-volume with tight latency or cost budget, and the task is narrow?** → Haiku. Otherwise skip to 3.
3. **Default:** Sonnet.

### Exam framing

Typical distractors:
- "Always use the largest model for best quality" — **wrong** for cost/latency-sensitive pipelines; Sonnet is the default.
- "Always use the smallest model to save cost" — **wrong** when capability matters; false economy if Haiku fails quality gates.
- "Use Opus for every subagent in a multi-agent system" — **wrong**, cost explodes linearly with subagent count; mix models per role.

**Discriminator:** start with Sonnet; upgrade to Opus when Sonnet demonstrably fails; downgrade to Haiku when the task is narrow and volume matters.

---

## 4. Cost / token economics

### The four lines on your bill

1. **Input tokens** — what you sent (system + tools + messages). Biggest line for agent loops with long histories.
2. **Output tokens** — what the model generated. Includes thinking tokens when extended thinking is on.
3. **Cache-write tokens** — first time a cached prefix is written (slightly *more* than input rate).
4. **Cache-read tokens** — subsequent hits (~10% of input rate).

### Message Batches API — 50% off

Send up to 10,000 requests in a single batch. Each completes asynchronously within a **24 h window** (no SLA). Pricing is **50% of sync**. Correlate results via `custom_id` you set per request. Batches **do not** support multi-turn tool use within one request — each request is single-shot.

**Use for:** overnight scoring of 10k docs, weekly report generation, bulk extraction pipelines with no deadline, evaluation runs.

**Don't use for:** CI pre-merge checks, user-facing latency, anything where a human is waiting.

### Prompt caching economics

Cache savings kick in when:
- The cached prefix is **large enough** (rule of thumb: ≥ 1024 tokens; shorter prefixes may not amortize the cache-write overhead).
- The prefix is **reused** (the 5-minute TTL means steady traffic benefits; sporadic access doesn't).

A 10k-token system prompt + tools sent at 10 req/sec = dramatic savings. Same 10k-token prefix sent once every 10 minutes = cache misses and pays the write penalty each time.

### Agent-loop cost compounds

Every turn in an agent loop re-sends the **full message history**. A 20-turn loop with a 5k-token system prompt re-sends 100k system tokens (once cached, ~10k effective) plus growing history. Without caching, cost scales quadratically-ish with turn count. With caching, it scales closer to linearly.

### Exam framing

Typical distractors:
- "Batches are always cheaper so use them when possible" — **wrong** when latency matters.
- "Caching is always on" — **wrong**, opt-in via `cache_control`.
- "Cost is proportional to turn count" — **wrong**, proportional to total tokens processed; caching changes the effective shape.
- "Shorter prompts are always cheaper" — **wrong** when a well-cached long prompt is cheaper than a short uncached one at scale.

**Discriminator:** think in tokens × processing-state, not in "requests" or "characters".

---

## How to use this reference

- **End of W11:** read end-to-end once, then re-examine your exercise code (W11 exercises 1–4). Note where you'd now enable caching, switch models, or flip to batches.
- **Before Practice Exam 1:** skim the "Exam framing" boxes in each section.
- **If you see a question that mentions any of**: `cache_control`, `ephemeral`, `thinking`, `budget_tokens`, `custom_id`, "Haiku/Sonnet/Opus", "50% cheaper", "24 h window" — this doc has the answer.
