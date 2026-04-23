# Walkthrough — Real-world multi-agent research pipeline

Read this after `reference.md`. Explains what happens inside the pipeline in `real_world_research_pipeline.py`.

## The scenario

A product manager asks: *"We're considering deploying an LLM-powered medical triage chatbot... Give me the top risks grouped by technical / regulatory / operational, with one mitigation each, and a go/no-go/conditional recommendation."*

The coordinator has access to three subagent types and nothing else:
- `technical_risk_researcher`
- `regulatory_risk_researcher`
- `operational_risk_researcher`

Each subagent has one scoped tool: `search_kb` filtered to its domain.

## Expected loop trace

### Coordinator — iteration 0 (`stop_reason == "tool_use"`)

The coordinator recognizes three independent sub-problems (technical, regulatory, operational risks). They're independent, so it dispatches them **in parallel** — one assistant turn with three `spawn_subagent` tool_use blocks:

```
[coordinator iter=0 stop=tool_use]
  tool_use: spawn_subagent({subagent_type: "technical_risk_researcher",  prompt: "Research technical risks for the following product: ..."})
  tool_use: spawn_subagent({subagent_type: "regulatory_risk_researcher", prompt: "Research regulatory risks for the following product: ..."})
  tool_use: spawn_subagent({subagent_type: "operational_risk_researcher", prompt: "Research operational risks for the following product: ..."})
```

**Each subagent now runs its OWN agentic loop, completely isolated.** It sees only the `prompt` the coordinator passed. It does not see:
- The original PM question
- The coordinator's reasoning
- The other two subagents' work or results

### Inside a subagent (e.g. technical_risk_researcher)

```
[technical_risk_researcher iter=0 stop=tool_use]
  tool_use: search_kb({query: "LLM medical triage technical risks"})
  tool_result: [... fake KB entries ...]

[technical_risk_researcher iter=1 stop=end_turn]
  text: {"risks": [{"risk": "hallucination of symptoms...", "mitigation": "..."}, ...]}
```

The subagent's final JSON comes back to the coordinator as the tool_result for its `spawn_subagent` call. **All 2+ turns inside the subagent's loop are invisible to the coordinator.** That's the isolation boundary doing its job.

### Coordinator — iteration 1 (after all three subagents return)

All three `tool_result` blocks come back **in one `user` turn** (per the API contract — one user turn per assistant turn, bundled). The coordinator now has three JSON reports in its context and synthesizes:

```
[coordinator iter=1 stop=end_turn]
  text:
    # LLM Medical Triage Chatbot — Risk Assessment
    **Recommendation: conditional go** — deploy in limited pilot with...

    ## Technical risks
    1. **Hallucination of symptoms** — ... Mitigation: ...
    ...

    ## Regulatory risks
    ...

    ## Operational risks
    ...
```

Loop exits. Done.

## What this run teaches you — mapped to exam concepts

| Loop moment | W02 concept exercised |
|---|---|
| Coordinator emits 3 `spawn_subagent` in one turn | **Parallel subagent dispatch** — independent tasks run concurrently |
| 3 tool_result blocks come back in ONE `user` turn | API contract (same as W01 parallel tool use, applied at the agent layer) |
| Subagent sees only its prompt, not the PM's original question | **Context isolation** — the core reason hub-and-spoke scales |
| Each subagent has a scoped tool (`search_kb` filtered to its domain) | **Scoped tool sets per subagent** |
| Coordinator has `spawn_subagent` ("Task" analogue) in its tool list | **`allowedTools` must include `Task`** for delegation to be possible |
| Coordinator produces a unified report, not concatenated JSON | **Real synthesis step**, not just join-and-ship |

## Variations to try

1. **Make tasks sequential by adding a data dependency.** Change the PM question to: *"What technical risks does the FDA classification imply for us?"* Now the technical subagent needs the regulatory subagent's output first. The coordinator should dispatch regulatory in turn-0, then technical in turn-1 with the regulatory result embedded in its prompt. Parallel would be wrong — technical would run blind.

2. **Over-narrow decomposition pitfall.** Split `technical_risk_researcher` into five hyper-specific subagents (hallucination, injection, drift, latency, cost). Notice how the coordinator's synthesis gets worse, not better — too granular means no subagent has enough context to judge relative importance.

3. **Subagent without `search_kb`.** Remove `search_kb` from `technical_risk_researcher`'s `tools`. Watch the subagent try to answer from general knowledge and either hallucinate or refuse. This is the "scoped tools matter" lesson — a tool-less subagent is near-useless for research tasks.

4. **Forget `spawn_subagent` in the coordinator's tools.** Comment out `COORDINATOR_TOOLS`. The coordinator will try to answer the PM question from its own general knowledge in one pass — no delegation happens. This is the "Task must be in allowedTools" exam pattern, made concrete.

## Exam-critical takeaways

1. **Parallel subagents when independent** — don't serialize for safety if tasks don't share data dependencies.
2. **Each subagent's context is a fresh `messages[]`** — nothing is shared except the prompt in and the final result out.
3. **Subagents get SCOPED tools** — the technical researcher doesn't need (and shouldn't have) regulatory search.
4. **The coordinator's delegation mechanism (`Task` / `spawn_subagent`) must be in its allowed tools.** Without that tool, no amount of prompt engineering will make it delegate.
5. **A real synthesis step at the end is what distinguishes multi-agent from round-robin concatenation.** If your coordinator's last turn is just glueing JSON together, you've decomposed without a plan for re-integration.
