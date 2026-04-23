"""
W10 — Real-world research synthesis with provenance, conflict annotation,
scratchpad/crash-recovery, and stratified confidence reporting.

Scenario:
    A strategy lead asks: "How big was the US passenger EV market in 2024,
    how fast is it growing, and how reliable are these numbers?"

    Three subagents each research the question from a different source and
    return claims WITH PROVENANCE:

        COORDINATOR
          ├── subagent_industry_analyst         (industry report, 2025-03)
          ├── subagent_regulator_filing         (regulator filing, 2025-01)
          └── subagent_academic_paper           (peer-reviewed paper, 2025-02)

    Crucially:
      - Two of the three subagents CONFLICT on the 2024 market-size number
        (different methodology; both sources were published in early 2025
        so this is a REAL conflict, not stale-vs-fresh).
      - The synthesis step does NOT silently pick one. It preserves BOTH
        with attribution, annotates the likely cause, and tags the claim
        `contested`.
      - Every claim record carries publication_date so the synthesis step
        can distinguish "old vs new" drift from genuine disagreement.
      - The pipeline writes a scratchpad.json after every step so a crash
        halfway through does not destroy collected work.
      - Final confidence is reported BY source_type AND BY field, not as
        a single aggregate — per the W10 stratified-reporting rule.

Why this exercise is structured this way:
    - Extends the W02 real_world_research_pipeline pattern (parallel
      subagents, hub-and-spoke) with the W10 provenance layer on top.
    - Every piece maps to a specific exam concept; see the walkthrough.
    - No API calls. Subagent outputs are fake, inline. Runnable:

        python real_world_research_synthesis.py
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
import os
import hashlib
import datetime


SCRATCHPAD_PATH = "scratchpad.json"


# =============================================================================
# 1. Provenance record — full W10 shape.
#
# Compared to minimal_provenance_object.py, this adds:
#   - source_type: primary / peer_reviewed / regulator_filing /
#                  industry_report / news / derivative
#   - author_credibility: a cheap signal for the synthesis tagger
#   - field: which field of the topic this claim is asserting (lets us
#            report accuracy BY FIELD, not just in aggregate)
#   - confidence_stratum: subagent's self-stated confidence band; used
#                         as a stratification axis, NOT as a replacement
#                         for actual QA
# =============================================================================

@dataclass
class Claim:
    topic: str                  # grouping key, e.g. 'us_ev_market_2024'
    field: str                  # sub-attribute, e.g. 'size_usd_billion'
    claim: str                  # the assertion in prose
    value: Optional[float]      # the numeric value when applicable
    unit: Optional[str]         # '$B', '%', 'kWh', etc.
    evidence: str               # pointer back into the source
    source_url: str
    source_type: str            # industry_report | regulator_filing | ...
    publication_date: str       # ISO 'YYYY-MM-DD'
    author_credibility: str     # established_firm | peer_reviewed | regulator | self_published | unknown
    confidence_stratum: str     # 'high' | 'medium' | 'low'


# =============================================================================
# 2. Three fake subagents.
#
# Each is a pure function: given the research question, returns a list
# of Claim objects. No shared state; each subagent is conceptually running
# in its OWN isolated context (W02 rule), just simulated in-process here.
# =============================================================================

def subagent_industry_analyst(question: str) -> List[Claim]:
    """Industry research firm. Counts light commercial vehicles in 'passenger EV'."""
    _ = question  # subagent has its own isolated scope; question is used here only to satisfy the signature
    return [
        Claim(
            topic="us_ev_market_2024",
            field="size_usd_billion",
            claim="US passenger EV market was $89B in calendar 2024.",
            value=89.0, unit="$B",
            evidence="Table 3, row 'Passenger EVs', column 'US revenue'",
            source_url="industry-report-2025.pdf",
            source_type="industry_report",
            publication_date="2025-03-15",
            author_credibility="established_firm",
            confidence_stratum="high",
        ),
        Claim(
            topic="us_ev_market_2024",
            field="yoy_growth_pct",
            claim="US passenger EV market grew ~75% YoY from 2023 to 2024.",
            value=75.0, unit="%",
            evidence="Table 3, YoY growth column",
            source_url="industry-report-2025.pdf",
            source_type="industry_report",
            publication_date="2025-03-15",
            author_credibility="established_firm",
            confidence_stratum="medium",
        ),
        Claim(
            topic="battery_pack_cost_2025",
            field="usd_per_kwh",
            claim="Average Li-ion battery pack cost fell to $118/kWh in 2025.",
            value=118.0, unit="$/kWh",
            evidence="Figure 7, annual cost curve",
            source_url="industry-report-2025.pdf",
            source_type="industry_report",
            publication_date="2025-03-15",
            author_credibility="established_firm",
            confidence_stratum="medium",
        ),
    ]


def subagent_regulator_filing(question: str) -> List[Claim]:
    """Regulator filing, published early 2025, covering 2024 realized data.
    DOES NOT include light commercial vehicles in 'passenger EV'."""
    _ = question
    return [
        Claim(
            topic="us_ev_market_2024",
            field="size_usd_billion",
            # Same topic+field as the industry analyst — DIFFERENT NUMBER.
            # Both publications are early 2025, both cover 2024. This is
            # a REAL conflict, not stale-vs-fresh drift.
            claim="US passenger EV market was $72B in calendar 2024.",
            value=72.0, unit="$B",
            evidence="Filing §2, passenger-EV revenue line",
            source_url="regulator-filing-2025Q1.pdf",
            source_type="regulator_filing",
            publication_date="2025-01-20",
            author_credibility="regulator",
            confidence_stratum="high",
        ),
        Claim(
            topic="us_ev_market_2024",
            field="yoy_growth_pct",
            claim="US passenger EV market grew ~41% YoY from 2023 to 2024.",
            value=41.0, unit="%",
            evidence="Filing §2, calculated YoY",
            source_url="regulator-filing-2025Q1.pdf",
            source_type="regulator_filing",
            publication_date="2025-01-20",
            author_credibility="regulator",
            confidence_stratum="high",
        ),
    ]


def subagent_academic_paper(question: str) -> List[Claim]:
    """Peer-reviewed paper, mid-range number."""
    _ = question
    return [
        Claim(
            topic="us_ev_market_2024",
            field="size_usd_billion",
            claim="US passenger EV market was ~$80B in calendar 2024 by authors' own tally.",
            value=80.0, unit="$B",
            evidence="Table 1, 'US passenger EV revenue'",
            source_url="jpubpol-ev-2025.pdf",
            source_type="peer_reviewed",
            publication_date="2025-02-05",
            author_credibility="peer_reviewed",
            confidence_stratum="medium",
        ),
        Claim(
            topic="battery_pack_cost_2025",
            field="usd_per_kwh",
            # Agrees with the industry report (both say $118/kWh) → this
            # moves `battery_pack_cost_2025` from single-source toward
            # well-established via an independent source.
            claim="Li-ion pack cost ~$118/kWh in early 2025.",
            value=118.0, unit="$/kWh",
            evidence="Figure 4",
            source_url="jpubpol-ev-2025.pdf",
            source_type="peer_reviewed",
            publication_date="2025-02-05",
            author_credibility="peer_reviewed",
            confidence_stratum="medium",
        ),
    ]


SUBAGENTS = {
    "industry_analyst": subagent_industry_analyst,
    "regulator_filing": subagent_regulator_filing,
    "academic_paper":    subagent_academic_paper,
}


# =============================================================================
# 3. Scratchpad + crash-recovery manifest.
#
# After every step (every subagent return, plus the synthesis result),
# we write the whole collected state to scratchpad.json. If the process
# crashes mid-pipeline, restarting reads the scratchpad and picks up
# from the next step.
#
# The manifest includes:
#   - session_id:        which run this is
#   - step_index:        last completed step
#   - completed_subagents: dict of subagent_name -> their claims
#   - pending_subagents: ones dispatched but not yet returned (in a real
#                        async system this matters; here we keep the slot
#                        for demonstration)
#   - scratchpad_hash:   SHA256 of the serialized state, so a reader can
#                        detect a partial/truncated write
#   - timestamp:         for staleness checks
#
# On crash recovery, compare the manifest's step_index to the plan and
# skip already-completed steps. Do NOT resume a manifest that contains a
# destructive-error marker; fork from an earlier clean step instead
# (W03 rule applied to durability).
# =============================================================================

def _hash_state(state: Dict[str, Any]) -> str:
    payload = json.dumps(state, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def write_scratchpad(state: Dict[str, Any]) -> None:
    # Compute hash over the state MINUS any previous hash field and MINUS
    # the timestamp so it's stable across reads/writes (the re-read path
    # strips both before rehashing).
    state["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    state_for_hash = {k: v for k, v in state.items() if k not in ("scratchpad_hash", "timestamp")}
    state["scratchpad_hash"] = _hash_state(state_for_hash)
    tmp_path = SCRATCHPAD_PATH + ".tmp"
    # Write-then-rename: an interrupted write never leaves a corrupt
    # scratchpad.json behind. This is the same pattern a real crash-
    # recovery manifest uses.
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(tmp_path, SCRATCHPAD_PATH)


def read_scratchpad() -> Optional[Dict[str, Any]]:
    if not os.path.exists(SCRATCHPAD_PATH):
        return None
    with open(SCRATCHPAD_PATH) as f:
        state = json.load(f)
    # Integrity check — a mismatched hash means the file is partial or
    # tampered. In a real system you'd refuse to resume and fork fresh.
    stored_hash = state.get("scratchpad_hash")
    state_without_hash = {k: v for k, v in state.items() if k not in ("scratchpad_hash", "timestamp")}
    if stored_hash and stored_hash != _hash_state(state_without_hash):
        print("! scratchpad hash mismatch — refusing to resume; starting clean.")
        return None
    return state


# =============================================================================
# 4. Synthesis step.
#
# Per W10, synthesis must:
#   a. Group claims by (topic, field).
#   b. For each group, detect whether DIFFERENT sources disagree on the
#      value — but only after checking publication_date. A difference
#      that lines up with a large date gap and hedged language is
#      labeled drift, not conflict.
#   c. Preserve BOTH/ALL conflicting claims with full attribution. Never
#      silently pick one. Never average them.
#   d. Tag each group:
#        well-established — multiple independent sources agree
#        contested        — sources disagree at similar dates
#        single-source    — only one source
#   e. For `contested`, emit a human-readable annotation naming the
#      likely cause when identifiable (e.g. methodology).
# =============================================================================

METHODOLOGY_HINTS = {
    ("us_ev_market_2024", "size_usd_billion"): (
        "Industry reports often include light commercial vehicles in 'passenger EV'; "
        "regulator filings typically exclude them. Definitional, not factual."
    ),
    ("us_ev_market_2024", "yoy_growth_pct"): (
        "Growth rate is derived from the market-size figure above; the disagreement "
        "propagates from the size-definition choice."
    ),
}


def synthesize(all_claims: List[Claim]) -> Dict[str, dict]:
    groups: Dict[tuple, List[Claim]] = {}
    for c in all_claims:
        groups.setdefault((c.topic, c.field), []).append(c)

    synthesized: Dict[str, dict] = {}
    for (topic, field), claims in groups.items():
        key = f"{topic}::{field}"
        distinct_sources = {c.source_url for c in claims}
        distinct_values = {c.value for c in claims if c.value is not None}

        if len(distinct_sources) == 1:
            status = "single-source"
            annotation = "Only one source; no independent corroboration — flag for caution."
        elif len(distinct_values) <= 1:
            status = "well-established"
            annotation = f"{len(distinct_sources)} independent sources agree."
        else:
            # Multiple sources, multiple values. Check dates before calling
            # it a conflict. If the spread of publication_date is > 18
            # months AND the numbers plausibly drift upward over time,
            # treat as temporal drift (expected change), NOT a disagreement.
            dates = sorted(c.publication_date for c in claims)
            spread_days = _date_spread_days(dates)
            if spread_days > 540:   # >~18 months
                status = "well-established"
                annotation = (
                    f"Numbers differ but publication dates span {spread_days} days — "
                    "treating as expected drift over time, not disagreement. "
                    "(Audit if surprising.)"
                )
            else:
                status = "contested"
                hint = METHODOLOGY_HINTS.get((topic, field), "Likely methodology difference.")
                annotation = (
                    "Sources disagree at similar publication dates. "
                    "Preserving BOTH with attribution; not picking one. "
                    f"Likely cause: {hint}"
                )

        synthesized[key] = {
            "topic": topic,
            "field": field,
            "status": status,
            "annotation": annotation,
            "claims": [asdict(c) for c in claims],
        }
    return synthesized


def _date_spread_days(iso_dates: List[str]) -> int:
    if len(iso_dates) < 2:
        return 0
    parsed = [datetime.date.fromisoformat(d) for d in iso_dates]
    return (max(parsed) - min(parsed)).days


# =============================================================================
# 5. Stratified confidence reporting.
#
# "93% accurate overall" is the exam trap. Report accuracy broken down by:
#   - source_type (industry_report / regulator_filing / peer_reviewed)
#   - field       (size_usd_billion / yoy_growth_pct / usd_per_kwh)
#
# In a production pipeline, you'd compare each claim against ground-truth
# labels. Here we simulate it with a tiny ground-truth table and count
# matches per stratum. The point is the SHAPE of the report, not the
# specific percentages.
# =============================================================================

# Imaginary ground truth. In practice this comes from human QA of
# stratified samples (see W10 §6). Stratified, not random.
GROUND_TRUTH = {
    ("us_ev_market_2024",   "size_usd_billion"): {"accepted_range": (70, 92)},
    ("us_ev_market_2024",   "yoy_growth_pct"):   {"accepted_range": (40, 80)},
    ("battery_pack_cost_2025", "usd_per_kwh"):   {"accepted_range": (115, 125)},
}


def score_claims(all_claims: List[Claim]) -> Dict[str, dict]:
    """
    Build the (source_type × field) accuracy matrix. A claim 'passes' if
    its numeric value falls within the ground-truth accepted range.

    The matrix is the exam's correct reporting shape. One aggregate
    number would HIDE per-field collapses (see the reference's
    'due_date 45%' example).
    """
    matrix: Dict[str, Dict[str, Dict[str, int]]] = {}
    for c in all_claims:
        truth = GROUND_TRUTH.get((c.topic, c.field))
        if truth is None or c.value is None:
            continue
        lo, hi = truth["accepted_range"]
        ok = lo <= c.value <= hi
        matrix.setdefault(c.source_type, {}).setdefault(c.field, {"pass": 0, "total": 0})
        matrix[c.source_type][c.field]["total"] += 1
        matrix[c.source_type][c.field]["pass"] += (1 if ok else 0)
    return matrix


def render_matrix(matrix: Dict[str, dict]) -> str:
    lines = ["## Confidence matrix (BY source_type × BY field)", ""]
    for src_type, fields in sorted(matrix.items()):
        lines.append(f"- {src_type}:")
        for field, counts in sorted(fields.items()):
            pct = 100.0 * counts["pass"] / counts["total"] if counts["total"] else 0.0
            lines.append(f"    - {field}: {counts['pass']}/{counts['total']} ({pct:.0f}%)")
    lines.append("")
    lines.append(
        "Aggregate accuracy is DELIBERATELY NOT REPORTED here. "
        "Per W10: one number hides per-field collapses. Read the matrix."
    )
    return "\n".join(lines)


# =============================================================================
# 6. Render final report — every claim keeps its source on the same line.
# =============================================================================

def render_report(synth: Dict[str, dict]) -> str:
    lines = ["# Market Research Synthesis", ""]
    for key in sorted(synth.keys()):
        entry = synth[key]
        lines.append(f"## {entry['topic']} — {entry['field']}")
        lines.append(f"Status: **{entry['status']}**")
        lines.append(f"Annotation: {entry['annotation']}")
        lines.append("Supporting claims:")
        for c in entry["claims"]:
            lines.append(
                f"  - {c['claim']} "
                f"[{c['source_type']}, {c['publication_date']}, "
                f"cred={c['author_credibility']}, "
                f"confidence={c['confidence_stratum']}; "
                f"evidence: {c['evidence']}; "
                f"src: {c['source_url']}]"
            )
        lines.append("")
    return "\n".join(lines)


# =============================================================================
# 7. Pipeline with crash-recovery resume.
# =============================================================================

def run_pipeline(question: str, session_id: str = "w10-demo-01") -> str:
    # Attempt to resume from scratchpad.
    state = read_scratchpad() or {
        "session_id": session_id,
        "step_index": 0,
        "completed_subagents": {},   # name -> list[dict-of-Claim]
        "pending_subagents": list(SUBAGENTS.keys()),
        "question": question,
    }

    if state.get("session_id") != session_id:
        print(f"! scratchpad belongs to {state['session_id']}, not {session_id}; starting fresh.")
        state = {
            "session_id": session_id,
            "step_index": 0,
            "completed_subagents": {},
            "pending_subagents": list(SUBAGENTS.keys()),
            "question": question,
        }

    # Dispatch each remaining subagent. In a real system these run in
    # parallel (W02 rule). Here we run sequentially and write the
    # scratchpad after EACH completion — that's what would let us resume
    # after a crash halfway through the list.
    for name in list(state["pending_subagents"]):
        print(f"> dispatching subagent: {name}")
        claims = SUBAGENTS[name](state["question"])
        state["completed_subagents"][name] = [asdict(c) for c in claims]
        state["pending_subagents"].remove(name)
        state["step_index"] += 1
        write_scratchpad(state)   # durable checkpoint after every step

    # Flatten everything back into Claim objects for synthesis.
    all_claims: List[Claim] = []
    for name, raw_claims in state["completed_subagents"].items():
        for rc in raw_claims:
            all_claims.append(Claim(**rc))

    synth = synthesize(all_claims)
    matrix = score_claims(all_claims)

    state["synthesis"] = synth
    state["confidence_matrix"] = matrix
    state["step_index"] += 1
    write_scratchpad(state)

    report = render_report(synth) + "\n\n" + render_matrix(matrix)
    return report


# =============================================================================
# 8. Entry point.
# =============================================================================

if __name__ == "__main__":
    question = (
        "How big was the US passenger EV market in 2024, how fast is it "
        "growing, and how reliable are these numbers?"
    )

    # First run — may crash at any point, scratchpad is written after
    # every step. A hypothetical re-run would pick up where it left off.
    print("=== FIRST RUN ===\n")
    report = run_pipeline(question)
    print(report)

    # Demonstrate that the scratchpad survives and can be re-read.
    print("\n\n=== INSPECTING SCRATCHPAD ===\n")
    state = read_scratchpad()
    if state is not None:
        print(f"session_id:      {state['session_id']}")
        print(f"step_index:      {state['step_index']}")
        print(f"completed:       {list(state['completed_subagents'].keys())}")
        print(f"pending:         {state['pending_subagents']}")
        print(f"timestamp:       {state.get('timestamp')}")
        print(f"scratchpad_hash: {state.get('scratchpad_hash')[:16]}...")

    # Expected teaching signals:
    #
    #   - us_ev_market_2024::size_usd_billion should come out CONTESTED:
    #     industry_report=$89B, regulator_filing=$72B, peer_reviewed=$80B
    #     all published within ~60 days of each other → NOT temporal
    #     drift; real disagreement; annotated with the methodology hint.
    #     All three claims appear in the output with full attribution.
    #     No silent pick. No average.
    #
    #   - us_ev_market_2024::yoy_growth_pct should come out CONTESTED:
    #     75% vs 41%, at similar dates; annotation notes it's derived
    #     from the size disagreement above.
    #
    #   - battery_pack_cost_2025::usd_per_kwh should come out
    #     WELL-ESTABLISHED: industry_report and peer_reviewed both say
    #     $118/kWh — two independent sources agreeing.
    #
    #   - Confidence matrix shows pass/total BY source_type × BY field.
    #     NO aggregate number. Per W10, aggregate accuracy reporting is
    #     an anti-pattern because it hides per-field collapses.
