"""
W11 Exercise 4 — Multi-Agent Research Pipeline with Provenance, Conflicts,
                 and Coverage-Gap Reporting.

Integrates:
    W02 — Coordinator + 2 subagents; hub-and-spoke; context isolation;
          coordinator's allowedTools MUST include "Task"; parallel subagent
          dispatch in ONE coordinator turn.
    W09 — Structured inter-agent messages (claim objects with provenance);
          structured error propagation when a subagent fails; partial-results
          reporting.
    W10 — Claim→source→date mapping preserved through synthesis; conflicting
          sources retained with attribution (never coin-flipped); coverage
          gap annotation when a subagent fails.

Scenario:
    A strategy team asks: "How is the remote-work share of the US software-
    engineering workforce trending?" The coordinator spawns TWO subagents:

      market_trend_researcher   — surveys market reports.
      labor_stats_researcher    — surveys public labor statistics.

    In parallel. Each subagent returns a list of claim objects with
    {claim, evidence, source, source_url, publication_date, confidence}.

    ONE of the subagents' searches is INTENTIONALLY forced to time out. The
    coordinator must NOT silently drop the gap — it must annotate a "coverage
    gap" in the final report.

    The two sources also return CONFLICTING numbers on the same question
    (one cites 2022 data, the other 2024). The synthesis must KEEP BOTH with
    attribution and publication dates — not pick one arbitrarily.

Why this exercise:
    Almost every wrong answer in Domain 5 is "silently collapse the problem":
    silent conflict resolution, silent timeout, silent lost dates. The right
    pattern is always "structured, attributed, preserved." This exercise
    literally codes the right pattern end to end.

Run: ANTHROPIC_API_KEY=... python exercise_4_multi_agent_research_pipeline.py

Variations to try: make BOTH subagents time out; add a third subagent with a
directly contradicting claim; strip publication_date and watch conflicts become
indistinguishable from "two sources disagreeing about the same moment".
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass
from typing import Any

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# Fake evidence sources (stand in for web search / MCP tools)
# =============================================================================
#
# Each source is a list of "findings" the subagent will see. Notice:
#   - Two findings conflict: 22% (market 2022) vs 38% (labor 2024).
#   - The labor subagent's tool will be forced to TIME OUT on this run, so we
#     simulate the error branch (not a successful data return).
# =============================================================================

MARKET_SOURCE = [
    {
        "claim": "Fully remote share of US software engineers was ~22% in 2022.",
        "evidence": "Based on a survey of 4,800 engineers at 120 US companies.",
        "source": "ExampleMarket 2022 Developer Survey",
        "source_url": "(fake) example-market-2022",
        "publication_date": "2022-11-15",
    },
    {
        "claim": "Hybrid (1–4 days/week remote) rose from 35% in 2020 to 52% in 2023.",
        "evidence": "Longitudinal panel of 2,000 engineers tracked annually.",
        "source": "ExampleMarket Panel Report",
        "source_url": "(fake) example-market-panel",
        "publication_date": "2023-09-01",
    },
]

LABOR_SOURCE = [
    # If the labor subagent successfully runs, it would report these. But in
    # this exercise run, we simulate a TIMEOUT on the labor source so it never
    # does — the coordinator must notice and annotate.
    {
        "claim": "Fully remote share of US software engineers was ~38% as of Q1 2024.",
        "evidence": "Monthly labor flow statistics from a national survey (n≈60k).",
        "source": "ExampleBLS Remote Work Monthly",
        "source_url": "(fake) example-bls-2024-q1",
        "publication_date": "2024-04-01",
    },
]

# Toggle for variations. Default: labor subagent times out.
SIMULATE_LABOR_TIMEOUT = True


# =============================================================================
# Subagent tool: search the fake source
# =============================================================================

def _tool_search_market(query: str) -> str:
    _ = query
    return json.dumps(MARKET_SOURCE, indent=2)


def _tool_search_labor(query: str) -> str:
    _ = query
    if SIMULATE_LABOR_TIMEOUT:
        # W09 — structured error, not bare empty string. The coordinator (via
        # the subagent's structured return) must be able to distinguish
        # "no data found" from "the tool failed to respond in time".
        raise TimeoutError("labor_stats search timed out after 30s")
    return json.dumps(LABOR_SOURCE, indent=2)


# =============================================================================
# Subagent definition factory
# =============================================================================

def subagent_definition(kind: str):
    if kind == "market_trend_researcher":
        domain_label = "market survey reports"
        tool_name = "search_market"
        tool_fn = _tool_search_market
    elif kind == "labor_stats_researcher":
        domain_label = "public labor statistics"
        tool_name = "search_labor"
        tool_fn = _tool_search_labor
    else:
        raise ValueError(f"unknown subagent kind: {kind}")

    system = (
        f"You are a research specialist for {domain_label}. You receive a "
        f"question. Call {tool_name} ONCE with a short query; you will receive "
        f"a JSON list of findings. Return a SINGLE JSON object of this exact "
        f"shape, nothing else:\n"
        f"  {{\n"
        f'    "status": "ok",\n'
        f'    "claims": [\n'
        f'      {{"claim": "...", "evidence": "...",\n'
        f'        "source": "...", "source_url": "...",\n'
        f'        "publication_date": "YYYY-MM-DD",\n'
        f'        "confidence": "high" | "medium" | "low"}},\n'
        f"      ...\n"
        f"    ]\n"
        f"  }}\n"
        f"Preserve source and publication_date EXACTLY as given. Never fabricate "
        f"a claim that is not supported by a returned finding."
    )

    tools = [{
        "name": tool_name,
        "description": (
            f"Search {domain_label} for evidence relevant to a short query. "
            f"Returns a list of finding objects with claim, evidence, source, "
            f"source_url, and publication_date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    }]

    return {"system": system, "tools": tools,
            "tool_dispatch": {tool_name: tool_fn}}


# =============================================================================
# Subagent loop — same skeleton as W02, with structured error return on timeout.
# =============================================================================

@dataclass
class SubagentReturn:
    subagent_type: str
    status: str                 # "ok" | "timeout" | "error"
    duration_s: float
    content: str                # JSON string the coordinator sees
    attempted_query: str | None = None


def run_subagent(subagent_type: str, prompt: str, safety_fuse: int = 8) -> SubagentReturn:
    cfg = subagent_definition(subagent_type)
    messages = [{"role": "user", "content": prompt}]
    started = time.time()
    attempted_query: str | None = None

    print(f"\n>>>>> SPAWNING {subagent_type} <<<<<")
    for i in range(safety_fuse):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=cfg["system"],
            tools=cfg["tools"],
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        for b in resp.content:
            if b.type == "text":
                print(f"  [{subagent_type} text] {b.text[:200]}")
            elif b.type == "tool_use":
                print(f"  [{subagent_type} tool_use] {b.name}({b.input})")

        if resp.stop_reason == "end_turn":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return SubagentReturn(
                subagent_type=subagent_type, status="ok",
                duration_s=time.time() - started, content=text,
                attempted_query=attempted_query,
            )

        if resp.stop_reason == "tool_use":
            tool_results = []
            for b in resp.content:
                if b.type == "tool_use":
                    attempted_query = str(b.input.get("query", ""))
                    try:
                        r = cfg["tool_dispatch"][b.name](**b.input)
                        tool_results.append(
                            {"type": "tool_result", "tool_use_id": b.id, "content": r}
                        )
                    except TimeoutError as e:
                        # W09 — the subagent short-circuits and returns a STRUCTURED
                        # error to the coordinator. No silent empty string.
                        print(f"  [{subagent_type}] TOOL TIMEOUT: {e}")
                        err = {
                            "status": "timeout",
                            "error_message": str(e),
                            "attempted_query": attempted_query,
                            "partial_results": [],
                        }
                        return SubagentReturn(
                            subagent_type=subagent_type, status="timeout",
                            duration_s=time.time() - started,
                            content=json.dumps(err),
                            attempted_query=attempted_query,
                        )
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"{subagent_type}: unexpected stop_reason {resp.stop_reason}")

    return SubagentReturn(
        subagent_type=subagent_type, status="error",
        duration_s=time.time() - started,
        content=json.dumps({"status": "error",
                            "error_message": "safety fuse tripped"}),
        attempted_query=attempted_query,
    )


# =============================================================================
# Coordinator — spawns subagents in PARALLEL (one turn, two Task calls)
# =============================================================================

COORDINATOR_SYSTEM = (
    "You are a research coordinator. For any research question, decompose the "
    "work and call spawn_subagent MULTIPLE TIMES IN THE SAME TURN so they run "
    "in parallel. Available subagent_type values:\n"
    "  - market_trend_researcher\n"
    "  - labor_stats_researcher\n"
    "Each subagent returns a JSON object with a 'status' field. If status=='ok', "
    "its 'claims' array has structured evidence. If status=='timeout' or 'error', "
    "you MUST annotate the coverage gap in your final report (do not silently "
    "drop it, do not retry more than once).\n"
    "\n"
    "In the final report:\n"
    "  - Cite every claim with (source, publication_date).\n"
    "  - If two claims conflict (different numbers on the same question), keep "
    "    BOTH with attribution — do NOT pick one arbitrarily, do NOT average.\n"
    "  - Mark any domain where a subagent failed as a 'coverage gap' with "
    "    the attempted query and the error reason.\n"
    "End your turn with a markdown report only after you have synthesized."
)

COORDINATOR_TOOLS = [
    {
        "name": "spawn_subagent",
        "description": (
            "Spawn a specialist research subagent in an isolated context. "
            "The subagent sees ONLY the prompt you pass — include the full "
            "question. Returns a JSON string. Call multiple times IN THE "
            "SAME TURN to parallelize."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subagent_type": {
                    "type": "string",
                    "enum": ["market_trend_researcher", "labor_stats_researcher"],
                },
                "prompt": {"type": "string"},
            },
            "required": ["subagent_type", "prompt"],
        },
    }
]


def coordinator_loop(question: str, parallel: bool = True) -> tuple[str, float, list[SubagentReturn]]:
    """Run the coordinator. Returns (final_text, wall_clock_seconds, subagent_returns)."""
    messages = [{"role": "user", "content": question}]
    subagent_returns: list[SubagentReturn] = []
    started = time.time()

    for i in range(8):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=COORDINATOR_SYSTEM,
            tools=COORDINATOR_TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        print(f"\n--- coordinator iter {i} stop={resp.stop_reason} ---")
        for b in resp.content:
            if b.type == "text":
                print(f"  [coord text] {b.text[:250]}")
            elif b.type == "tool_use":
                print(f"  [coord tool_use] {b.name}(subagent_type={b.input.get('subagent_type')})")

        if resp.stop_reason == "end_turn":
            final = "".join(b.text for b in resp.content if b.type == "text")
            return final, time.time() - started, subagent_returns

        if resp.stop_reason == "tool_use":
            # Collect all spawn_subagent calls in this turn and execute.
            # parallel=True → run them concurrently (simulated with sequential
            # but we measure wall-clock around them so the cost model is real).
            spawn_blocks = [b for b in resp.content if b.type == "tool_use"]
            tool_results = []

            if parallel:
                # Use a thread pool to actually overlap the API calls.
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=len(spawn_blocks)) as ex:
                    futures = {
                        ex.submit(run_subagent,
                                  b.input["subagent_type"], b.input["prompt"]): b
                        for b in spawn_blocks
                    }
                    for fut, b in list(futures.items()):
                        ret = fut.result()
                        subagent_returns.append(ret)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": b.id,
                            "content": ret.content,
                        })
            else:
                for b in spawn_blocks:
                    ret = run_subagent(b.input["subagent_type"], b.input["prompt"])
                    subagent_returns.append(ret)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": ret.content,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"coordinator: unexpected stop_reason {resp.stop_reason}")

    raise RuntimeError("coordinator: safety fuse tripped")


# =============================================================================
# Entry point — run once in parallel, once sequential, compare latency.
# =============================================================================

if __name__ == "__main__":
    question = (
        "How is the remote-work share of the US software-engineering workforce "
        "trending? Give me the numbers with sources and publication dates. "
        "If the domains you consult disagree, present BOTH views with attribution."
    )

    print("\n\n" + "#" * 70)
    print("# RUN 1 — PARALLEL subagent dispatch")
    print("#" * 70)
    final_parallel, wall_par, rets_par = coordinator_loop(question, parallel=True)

    print("\n\n" + "#" * 70)
    print("# RUN 2 — SEQUENTIAL subagent dispatch (for latency comparison)")
    print("#" * 70)
    final_seq, wall_seq, rets_seq = coordinator_loop(question, parallel=False)

    print("\n\n" + "=" * 70)
    print("LATENCY COMPARISON (wall-clock for the whole coordinator loop)")
    print("=" * 70)
    print(f"  Parallel:   {wall_par:6.2f}s")
    print(f"  Sequential: {wall_seq:6.2f}s")
    print(f"  Speedup:    {wall_seq / wall_par:.2f}x  (subagents are independent → parallel wins)")

    print("\n\n" + "=" * 70)
    print("SUBAGENT OUTCOMES (parallel run)")
    print("=" * 70)
    for r in rets_par:
        print(f"  {r.subagent_type:30s} status={r.status:10s} duration={r.duration_s:5.2f}s "
              f"attempted_query={r.attempted_query!r}")

    print("\n\n" + "=" * 70)
    print("FINAL SYNTHESIZED REPORT (parallel run)")
    print("=" * 70)
    print(final_parallel)

    # Validation: the final report MUST mention the coverage gap (labor timeout).
    lowered = final_parallel.lower()
    assert (
        "coverage" in lowered or "gap" in lowered
        or "timeout" in lowered or "unavailable" in lowered
    ), "FAIL: final report does not annotate the labor subagent coverage gap."
    print("\n[CHECK] coverage gap annotated in final report ✓")


# =============================================================================
# Variations to try
# =============================================================================
#
# V1. Set SIMULATE_LABOR_TIMEOUT = False. Now both subagents succeed and the
#     coordinator will see the conflict (22% in 2022 vs 38% in 2024). Verify
#     the final report preserves BOTH with dates, not an average.
#     (Exam task 5.6 — preserve conflicts with attribution.)
#
# V2. Remove "Task" / spawn_subagent from COORDINATOR_TOOLS. The coordinator
#     now has no way to delegate. Watch it either end_turn with a refusal or
#     (worse) hallucinate stats directly. That's the W02 allowedTools rule.
#     "Add a prompt line telling it to delegate" — does not fix this.
#     (Exam task 1.3.)
#
# V3. Replace the structured timeout error with an empty string return. Watch
#     the coordinator silently produce a report that appears complete but is
#     missing the labor domain — with no annotation. Silent failure is
#     precisely the failure mode Domain 5.4 tests for.
#
# V4. Strip publication_date from the claim objects. Now the 22% and 38% look
#     like two sources disagreeing about the same moment. With dates preserved,
#     the model correctly frames it as "22% in 2022, 38% in 2024, consistent
#     with growth." Losing temporal metadata loses interpretability.
#     (Exam task 5.6 — temporal data.)
#
# V5. Add a third subagent (e.g. "job_postings_researcher") and see whether the
#     coordinator still parallelizes all three in one turn. If decomposition
#     is working, you should see three spawn_subagent blocks in ONE coordinator
#     assistant turn, not three separate turns.
