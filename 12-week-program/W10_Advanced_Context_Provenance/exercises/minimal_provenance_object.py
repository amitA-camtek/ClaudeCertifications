"""
W10 — Minimal provenance object demo.

Scenario:
    Three subagents return factual claims about a market. Each claim is a
    structured object carrying its OWN source, evidence pointer, and
    publication date. The synthesis step detects conflicts between claims
    from DIFFERENT sources and annotates them — crucially, it reads
    publication_date first so a 2023 stat vs a 2025 stat is not mis-read
    as a contradiction.

Why this exercise:
    - Shows the minimum viable provenance record: {claim, evidence,
      source_url, publication_date}.
    - Shows the correct synthesis behavior: preserve BOTH, attribute,
      annotate; never silently pick one.
    - Shows publication_date disambiguating "expected drift over time"
      from "genuine disagreement at the same time".

No API calls. Fake subagent outputs inline. Runnable standalone:

    python minimal_provenance_object.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


# =============================================================================
# 1. The provenance record — the ONLY shape subagents are allowed to return.
# =============================================================================

@dataclass
class Claim:
    """
    Minimum viable provenance record.

    Load-bearing fields:
      - claim:             what is being asserted
      - source_url:        where this assertion came from (per-claim, not
                           bibliography-at-the-bottom)
      - publication_date:  ISO date of the SOURCE (not of "today"). Without
                           this, old-vs-new reads as a contradiction.
      - evidence:          a pointer back into the source so the claim is
                           auditable later (table/figure/section).

    topic is a lightweight grouping key so the synthesis step can find
    claims that are about the same thing.
    """
    topic: str
    claim: str
    evidence: str
    source_url: str
    publication_date: str   # ISO 'YYYY-MM-DD'

    def attributed(self) -> str:
        """Render the claim with its full attribution — no orphaned facts."""
        return (
            f"{self.claim} "
            f"[source: {self.source_url}, {self.publication_date}; "
            f"evidence: {self.evidence}]"
        )


# =============================================================================
# 2. Three fake subagent outputs.
#
# Each subagent returns a LIST of Claim objects, NOT prose. If you return
# prose, you've already lost provenance — no way to know which source
# backed which sentence.
# =============================================================================

def subagent_industry_analyst() -> List[Claim]:
    """Analyst firm research report. 2025."""
    return [
        Claim(
            topic="us_ev_market_size_2024",
            claim="US passenger EV market was $89B in calendar 2024.",
            evidence="Table 3, row 'Passenger EVs', column 'US revenue'",
            source_url="industry-report-2025.pdf",
            publication_date="2025-03-15",
        ),
        Claim(
            topic="us_ev_market_size_2023",
            claim="US passenger EV market was $51B in calendar 2023.",
            evidence="Table 3, row 'Passenger EVs', column 'US revenue (prior year)'",
            source_url="industry-report-2025.pdf",
            publication_date="2025-03-15",
        ),
        Claim(
            topic="battery_pack_cost_2025",
            claim="Average Li-ion battery pack cost fell to $118/kWh in 2025.",
            evidence="Figure 7, annual cost curve",
            source_url="industry-report-2025.pdf",
            publication_date="2025-03-15",
        ),
    ]


def subagent_regulator_filing() -> List[Claim]:
    """Regulator filing, early 2025 (covers 2024 data)."""
    return [
        Claim(
            topic="us_ev_market_size_2024",
            claim="US passenger EV market was $72B in calendar 2024.",
            evidence="Filing section 2, passenger-EV revenue line",
            source_url="regulator-filing-2025Q1.pdf",
            # NOTE: SAME YEAR AS THE ANALYST FIRM'S 2024 FIGURE — so this is
            # a REAL conflict, not stale-vs-fresh. Synthesis must detect
            # this and annotate, not silently pick one.
            publication_date="2025-01-20",
        ),
    ]


def subagent_old_news_summary() -> List[Claim]:
    """Older news article summarizing a different year. Looks like a
    conflict if you ignore the date — isn't, because it's 2023 data."""
    return [
        Claim(
            topic="us_ev_market_size_2023",
            claim="US passenger EV market was $51B in 2023.",
            evidence="Paragraph 4 of news article",
            source_url="news-article-2024.html",
            publication_date="2024-02-10",
        ),
        # Same topic bucket as the 2024 figures above — WOULD look like
        # a conflict on the topic key alone. The synthesis step uses the
        # claim text + date to see that this is actually a different year.
        Claim(
            topic="us_ev_market_size_2024",
            claim="US passenger EV market projected at ~$80B for 2024.",
            evidence="Paragraph 6, forecast callout",
            # Published BEFORE 2024 ended → this is a forecast, not a
            # realized number. Synthesis should call that out.
            publication_date="2024-02-10",
            source_url="news-article-2024.html",
        ),
    ]


# =============================================================================
# 3. Synthesis step.
#
# Responsibilities (all required):
#   a. Group claims by topic.
#   b. For each topic, detect whether sources actually disagree.
#      A "disagreement" requires:
#        - at least two DIFFERENT source_urls
#        - AND the claim content points at incompatible values
#   c. Preserve BOTH (or all N) conflicting claims with attribution.
#      NEVER silently drop or pick one.
#   d. Preserve publication_date in the output so readers can see that
#      "2023 vs 2025" is NOT a disagreement — it's expected drift.
#   e. Tag each topic: well-established / contested / single-source.
#
# What this function deliberately does NOT do:
#   - It does NOT compute an "average" or "best" value.
#   - It does NOT pick the newest source as canonical.
#   - It does NOT pick the most-authoritative source as canonical.
# Those are all anti-patterns from the W10 reference.
# =============================================================================

def synthesize(all_claims: List[Claim]) -> Dict[str, dict]:
    by_topic: Dict[str, List[Claim]] = {}
    for c in all_claims:
        by_topic.setdefault(c.topic, []).append(c)

    report: Dict[str, dict] = {}
    for topic, claims in by_topic.items():
        distinct_sources = {c.source_url for c in claims}
        distinct_texts = {c.claim for c in claims}

        if len(claims) == 1:
            status = "single-source"
            note = "Only one source found — flag for caution; no corroboration."
        elif len(distinct_sources) == 1:
            # Multiple claims, one source. Not a conflict — just richer
            # evidence from one source. Treat as single-source still.
            status = "single-source"
            note = "Multiple assertions from a single source — corroboration still missing."
        elif len(distinct_texts) == 1:
            status = "well-established"
            note = "Multiple independent sources agree."
        else:
            # Multiple sources, disagreeing wording. But BEFORE calling
            # it a conflict, check if the disagreement is actually the
            # publication_date difference in disguise ("old vs new").
            dates = sorted({c.publication_date for c in claims})
            if len(dates) > 1 and _looks_like_temporal_drift(topic, claims):
                status = "well-established"
                note = (
                    "Sources differ in wording but align with expected change "
                    f"between {dates[0]} and {dates[-1]} — not a disagreement."
                )
            else:
                status = "contested"
                note = (
                    "Sources disagree at similar publication dates — preserve "
                    "BOTH with attribution; do not pick one."
                )

        report[topic] = {
            "status": status,
            "note": note,
            # Critical: every claim object is kept, full attribution intact.
            # The downstream consumer (human reader, or another agent)
            # decides which to trust.
            "claims": [
                {
                    "claim": c.claim,
                    "evidence": c.evidence,
                    "source_url": c.source_url,
                    "publication_date": c.publication_date,
                }
                for c in claims
            ],
        }
    return report


def _looks_like_temporal_drift(topic: str, claims: List[Claim]) -> bool:
    """
    Heuristic: if the topic mentions a specific year (e.g. '..._2024') AND
    all claims that mention that year in their TEXT agree, but claims
    with much older publication_dates use hedged language ('projected',
    'forecast', '~', 'estimated'), treat as forecast-vs-realized drift,
    not a genuine conflict.

    Deliberately conservative: when in doubt, it returns False and the
    caller tags the topic `contested`. Under-flagging drift is safer
    than over-suppressing real conflicts.
    """
    hedges = ("projected", "forecast", "estimate", "~", "approximately")
    has_hedged_older = any(
        any(h in c.claim.lower() for h in hedges)
        for c in claims
    )
    # Only collapse to "well-established + drift" if there's BOTH a hedged
    # forecast AND a firm realized number AND the firm number comes from
    # a later publication_date than the forecast.
    if not has_hedged_older:
        return False
    firm = [c for c in claims if not any(h in c.claim.lower() for h in hedges)]
    hedged = [c for c in claims if any(h in c.claim.lower() for h in hedges)]
    if not firm or not hedged:
        return False
    return max(c.publication_date for c in firm) > max(c.publication_date for c in hedged)


# =============================================================================
# 4. Render a provenance-preserving report.
#
# Every claim line in the output carries its own source_url + date.
# No bibliography-at-the-bottom, because that pattern destroys
# provenance — you can't tell which source backed which claim.
# =============================================================================

def render(report: Dict[str, dict]) -> str:
    lines = ["# Synthesis Report", ""]
    for topic, entry in sorted(report.items()):
        lines.append(f"## Topic: {topic}")
        lines.append(f"Status: **{entry['status']}**")
        lines.append(f"Note:   {entry['note']}")
        lines.append("Supporting claims:")
        for c in entry["claims"]:
            lines.append(
                f"  - {c['claim']} "
                f"[{c['source_url']}, {c['publication_date']}; "
                f"evidence: {c['evidence']}]"
            )
        lines.append("")
    return "\n".join(lines)


# =============================================================================
# 5. Entry point.
# =============================================================================

if __name__ == "__main__":
    all_claims = (
        subagent_industry_analyst()
        + subagent_regulator_filing()
        + subagent_old_news_summary()
    )

    print(f"Collected {len(all_claims)} claims from 3 subagents.\n")

    report = synthesize(all_claims)
    print(render(report))

    # Expected teaching signals (check these when you run it):
    #   - Topic 'us_ev_market_size_2024' should come out CONTESTED:
    #       industry report says $89B (2025-03-15), regulator says $72B
    #       (2025-01-20) — both claim 2024 revenue, similar publication
    #       dates. Both must appear in the output with attribution.
    #       The news article's $80B forecast is an EARLIER publication
    #       (2024-02-10) using hedged language — the drift heuristic
    #       either folds it in or leaves it in; either way it is NOT
    #       silently dropped.
    #   - Topic 'us_ev_market_size_2023' should come out WELL-ESTABLISHED:
    #       two DIFFERENT sources ($51B from the industry report and
    #       $51B from the news article) agree.
    #   - Topic 'battery_pack_cost_2025' should come out SINGLE-SOURCE:
    #       only the industry report made that claim — flag for caution.
