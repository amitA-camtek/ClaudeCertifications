"""
W02 — Real-world multi-agent system: product risk research pipeline.

Scenario:
    A product manager asks: "We're considering deploying an LLM-powered
    medical-triage chatbot. Give me the top risks and one mitigation for each."

    A naive single agent would produce a vague list. A good multi-agent system:

        COORDINATOR
          ├── spawn_subagent(type="technical_risk_researcher", ...)
          ├── spawn_subagent(type="regulatory_risk_researcher", ...)
          └── spawn_subagent(type="operational_risk_researcher", ...)
        (all three dispatched IN PARALLEL — they are independent)
          ↓
        Coordinator synthesizes ONE unified report with cross-risk analysis.

Why this exercise:
    - Exercises PARALLEL subagent dispatch (the #1 W02 concept).
    - Each subagent has an isolated context and a SCOPED tool set.
    - Shows realistic context isolation: the technical researcher never sees
      the regulatory researcher's context, and vice versa.
    - Coordinator has a real SYNTHESIS step at the end, not just concatenation.

Data is a fake in-memory "knowledge base" so the example runs without any
real web search or external API. The structure maps 1:1 to what you'd build
in production with web search / MCP tools wired in.

Run: ANTHROPIC_API_KEY=... python real_world_research_pipeline.py
"""

from __future__ import annotations
import json

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# Fake knowledge base (stands in for web search / MCP tools in production)
# =============================================================================

KNOWLEDGE_BASE = {
    "technical": [
        {
            "topic": "hallucination in clinical context",
            "summary": (
                "LLMs can fabricate symptoms, dosages, or conditions when "
                "confidence is miscalibrated. In a triage setting, a single "
                "hallucinated symptom can mis-route a patient."
            ),
            "source": "arxiv:2024.medllm-eval",
        },
        {
            "topic": "context length degradation",
            "summary": (
                "Attention quality drops on long conversations; earlier patient "
                "statements get lost in the middle of the context window."
            ),
            "source": "anthropic:long-context-report-2024",
        },
        {
            "topic": "prompt injection via user input",
            "summary": (
                "Patient-supplied text can contain adversarial instructions "
                "that override the system prompt (e.g., jailbreaks)."
            ),
            "source": "owasp:llm-top-10-2024",
        },
    ],
    "regulatory": [
        {
            "topic": "FDA SaMD classification",
            "summary": (
                "A triage chatbot that recommends clinical action is likely "
                "Software as a Medical Device (SaMD), requiring FDA review "
                "depending on risk class."
            ),
            "source": "fda.gov:samd-framework",
        },
        {
            "topic": "HIPAA data handling",
            "summary": (
                "Patient conversations are PHI. Model training, logging, and "
                "third-party API calls must meet HIPAA Business Associate "
                "Agreement requirements."
            ),
            "source": "hhs.gov:hipaa-ai-guidance-2024",
        },
        {
            "topic": "EU AI Act high-risk classification",
            "summary": (
                "Medical AI systems are classified 'high-risk' under the EU "
                "AI Act, requiring conformity assessment, post-market "
                "monitoring, and human oversight."
            ),
            "source": "eur-lex:ai-act-annex-iii",
        },
    ],
    "operational": [
        {
            "topic": "escalation to clinician",
            "summary": (
                "Unclear thresholds for handing off to a human clinician lead "
                "to either over-escalation (clinicians overwhelmed) or "
                "under-escalation (patient harm)."
            ),
            "source": "jama:2024-triage-bots",
        },
        {
            "topic": "monitoring model drift",
            "summary": (
                "Model behavior shifts as patient language, disease prevalence, "
                "and seasonal factors change. Without drift monitoring, accuracy "
                "silently degrades."
            ),
            "source": "nature-digital-med:2024-drift",
        },
        {
            "topic": "incident response playbook",
            "summary": (
                "No agreed-upon runbook for 'chatbot gave harmful advice' "
                "incidents — legal, medical, and engineering each own a piece "
                "with no consolidated owner."
            ),
            "source": "internal:sre-maturity-model",
        },
    ],
}


def _tool_search_kb(domain: str, query: str) -> str:
    """Return entries in the fake KB for a given domain, lightly filtered by query."""
    entries = KNOWLEDGE_BASE.get(domain, [])
    # The filter is intentionally loose — the model will see all entries for
    # that domain. In a real system this would be semantic search.
    _ = query  # unused in the stub
    return json.dumps(entries, indent=2)


# =============================================================================
# Subagent definitions
# =============================================================================

def _researcher_definition(domain: str, human_label: str):
    return {
        "description": f"Researches {human_label} risks for deploying LLM systems.",
        "system": (
            f"You are a {human_label} risk researcher. You receive a product "
            f"description. Use the search_kb tool (domain='{domain}') to gather "
            f"evidence. Then return a structured JSON object:\n"
            f"  {{\n"
            f"    \"risks\": [\n"
            f"      {{\"risk\": \"...\", \"evidence\": \"...\", \"source\": \"...\", \"mitigation\": \"...\"}},\n"
            f"      ...\n"
            f"    ]\n"
            f"  }}\n"
            f"Return ONLY the JSON (no prose before/after). Include 2-3 risks maximum, "
            f"each with a concrete mitigation."
        ),
        "tools": [
            {
                "name": "search_kb",
                "description": (
                    f"Search the {human_label} risk knowledge base. "
                    f"Input: a short query string. Returns a list of relevant "
                    f"evidence entries with topic, summary, and source."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ],
        "tool_dispatch": {
            "search_kb": lambda query, domain=domain: _tool_search_kb(domain, query),
        },
    }


SUBAGENTS = {
    "technical_risk_researcher": _researcher_definition("technical", "technical"),
    "regulatory_risk_researcher": _researcher_definition("regulatory", "regulatory"),
    "operational_risk_researcher": _researcher_definition("operational", "operational"),
}


# =============================================================================
# Generic agentic loop (shared by coordinator and subagents)
# =============================================================================

def run_agent_loop(system, tools, tool_dispatch, user_input, label, safety_fuse=15, verbose=True):
    messages = [{"role": "user", "content": user_input}]

    for i in range(safety_fuse):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if verbose:
            print(f"\n[{label} iter={i} stop={resp.stop_reason}]")
            for b in resp.content:
                if b.type == "text":
                    print(f"  text: {b.text[:200]}{'...' if len(b.text) > 200 else ''}")
                elif b.type == "tool_use":
                    print(f"  tool_use: {b.name}({b.input})")

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text")

        if resp.stop_reason == "tool_use":
            tool_results = []
            for b in resp.content:
                if b.type == "tool_use":
                    r = tool_dispatch[b.name](**b.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": b.id, "content": r}
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"{label}: unexpected stop_reason {resp.stop_reason}")
    raise RuntimeError(f"{label}: safety fuse tripped")


# =============================================================================
# Coordinator
# =============================================================================

COORDINATOR_SYSTEM = (
    "You are a research coordinator. For any question about deploying LLM "
    "systems, DECOMPOSE into parallel specialist subagents across technical, "
    "regulatory, and operational risk domains. Call spawn_subagent multiple "
    "times IN THE SAME TURN so they run in parallel. Each subagent returns a "
    "JSON object; collect all three, then produce a single consolidated "
    "markdown report grouped by risk category, with the PM's decision "
    "highlights at the top. Use only information the subagents returned."
)

COORDINATOR_TOOLS = [
    {
        "name": "spawn_subagent",
        "description": (
            "Spawn a specialist risk researcher in an isolated context. Available "
            "subagent_type values:\n"
            "  - technical_risk_researcher\n"
            "  - regulatory_risk_researcher\n"
            "  - operational_risk_researcher\n"
            "The subagent sees ONLY the prompt you pass — include the full "
            "product description. Returns a JSON string with the subagent's findings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subagent_type": {"type": "string", "enum": list(SUBAGENTS.keys())},
                "prompt": {"type": "string"},
            },
            "required": ["subagent_type", "prompt"],
        },
    }
]


def coordinator_spawn(subagent_type: str, prompt: str) -> str:
    cfg = SUBAGENTS[subagent_type]
    print(f"\n>>>>> COORDINATOR SPAWNING '{subagent_type}' <<<<<")
    final = run_agent_loop(
        system=cfg["system"],
        tools=cfg["tools"],
        tool_dispatch=cfg["tool_dispatch"],
        user_input=prompt,
        label=subagent_type,
    )
    print(f"<<<<< '{subagent_type}' RETURNED {len(final)} chars >>>>>")
    return final


COORDINATOR_TOOL_DISPATCH = {"spawn_subagent": coordinator_spawn}


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    pm_question = (
        "We're considering deploying an LLM-powered medical triage chatbot that "
        "takes patient-described symptoms and recommends self-care, PCP visit, "
        "or ER. Give me the top risks grouped by technical / regulatory / "
        "operational, with one mitigation each, and a bottom-line "
        "go/no-go/conditional recommendation."
    )

    final = run_agent_loop(
        system=COORDINATOR_SYSTEM,
        tools=COORDINATOR_TOOLS,
        tool_dispatch=COORDINATOR_TOOL_DISPATCH,
        user_input=pm_question,
        label="coordinator",
    )

    print("\n\n===== FINAL REPORT =====\n")
    print(final)
