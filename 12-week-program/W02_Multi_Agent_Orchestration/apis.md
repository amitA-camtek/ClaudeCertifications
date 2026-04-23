# W02 APIs — Claude APIs for this week

> APIs relevant to **multi-agent orchestration**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Messages API** (`client.messages.create()`) | Each agent (coordinator, subagent) is its own Messages API call | Every turn of every agent |
| **Parallel execution** via `asyncio` + `anthropic.AsyncAnthropic` | Run subagents in parallel inside a single coordinator turn | Spawning N subagents simultaneously |
| **Task-style subagent pattern** | Manual hub-and-spoke: coordinator hands off with minimal context, receives a synthesized string back | Agent SDK `Task` tool conceptual equivalent |
| **Session fork / resume** (CLI and Agent SDK) | `--resume <name>` and `fork_session` for branched exploration | Discussed conceptually; CLI examples below |

---

## API snippets

### Async Messages API
```python
import anthropic, asyncio

aclient = anthropic.AsyncAnthropic()

async def call_model(prompt: str) -> str:
    resp = await aclient.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text
```

### Parallel subagent spawn
```python
results = await asyncio.gather(
    call_model("Research topic A"),
    call_model("Research topic B"),
    call_model("Research topic C"),
)
```

### Session fork (Claude Code CLI)
```bash
# branch from a named session without polluting it
claude --fork-session main-investigation --name experiment-1
```

---

## Working example — coordinator + 2 parallel subagents

Save as `multi_agent.py`:

```python
"""
Hub-and-spoke multi-agent: coordinator spawns 2 subagents in PARALLEL,
each with its own isolated context, then synthesizes their outputs.
"""
import anthropic, asyncio, time

aclient = anthropic.AsyncAnthropic()

SUBAGENT_SYSTEM = (
    "You are a focused research subagent. You receive one narrow question "
    "and return a short answer (2-3 sentences) with any relevant facts. "
    "Do not ask clarifying questions — answer from general knowledge."
)

COORDINATOR_SYSTEM = (
    "You are a coordinator. You will be given several subagent findings "
    "and asked to synthesize them into a single structured answer. "
    "Preserve attribution: mark which finding came from which subagent."
)

async def subagent(name: str, question: str) -> dict:
    """One subagent call in isolation. Returns {name, question, finding}."""
    t0 = time.time()
    resp = await aclient.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        system=SUBAGENT_SYSTEM,
        messages=[{"role": "user", "content": question}],
    )
    finding = resp.content[0].text
    print(f"[subagent {name}] {time.time()-t0:.1f}s: {finding[:80]}...")
    return {"name": name, "question": question, "finding": finding}

async def coordinator(user_prompt: str) -> str:
    # Step 1: decompose (hard-coded here; in practice the coordinator itself decides)
    subtasks = [
        ("historian", "When was the Anthropic company founded and by whom?"),
        ("product", "What is Model Context Protocol (MCP) and why was it introduced?"),
    ]

    # Step 2: parallel spawn
    findings = await asyncio.gather(*[subagent(name, q) for name, q in subtasks])

    # Step 3: coordinator synthesizes
    synthesis_prompt = (
        f"User asked: {user_prompt}\n\n"
        "Subagent findings:\n"
        + "\n".join(
            f"- [{f['name']}] Q: {f['question']}\n  A: {f['finding']}"
            for f in findings
        )
        + "\n\nSynthesize a single answer that preserves attribution."
    )
    resp = await aclient.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": synthesis_prompt}],
    )
    return resp.content[0].text

if __name__ == "__main__":
    t0 = time.time()
    final = asyncio.run(coordinator(
        "Give me a brief on Anthropic's company history and their MCP standard."
    ))
    print(f"\n=== FINAL ({time.time()-t0:.1f}s total) ===\n{final}")
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
python multi_agent.py
```

**Expected behavior:**
- Both subagent lines print *roughly at the same time* (not sequentially). If the total wall-clock is ~2× the slower subagent, parallelism is broken.
- Coordinator synthesis comes last.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| Subagents run sequentially (total time = sum) | Used `await subagent(...)` in a loop instead of `asyncio.gather()` | Use `gather(*[...])` |
| Coordinator output loses attribution | Didn't structure the synthesis prompt with the `[name]` tags | Keep the `- [{name}] Q:... A:...` bullet structure |
| Subagent context pollution | Passed coordinator history into subagent `messages` | Subagents get only the narrow question — verify with a print before each `.create()` |
| High cost / slow | Passing all N findings as a mega-prompt | Trim each finding to its 2-3 sentence summary before synthesis |
| `anthropic.APIError: rate_limit` | Burst of parallel calls exceeds tier limit | Add `asyncio.Semaphore(4)` around subagent calls |

**Semaphore pattern for rate-limit safety:**
```python
sem = asyncio.Semaphore(4)
async def subagent(...):
    async with sem:
        resp = await aclient.messages.create(...)
```

**Measure parallelism:**
```python
# Wrap gather in time.time() before/after. If sum of individual times >> wall time,
# parallelism works. If ≈ equal, it doesn't.
```

---

## Exam connection

- The hub-and-spoke structure here matches what "How we built our multi-agent research system" describes — subagents do not see each other's context.
- `asyncio.gather` is the portable equivalent of `Task` parallelism — both spawn concurrent isolated contexts.
- If you replaced `SUBAGENT_SYSTEM` with the coordinator's full history, you'd kill context isolation — that's the distractor on the exam.
