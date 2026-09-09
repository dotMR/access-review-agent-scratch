"""Milestone 8 eval runner: Tier 3 cases 29-31 (Risk Assessment scoring,
deterministic, free) and Tier 2 cases 23-24 (narrative, LLM-as-judge,
real cost), graded automatically.

Cases 29-31 need no credentials and cost nothing - pure lookups and a
local multi-period fixture (evals/cases/risk-assessment-recurrence/).
Cases 23-24 are the first use of LLM-as-judge grading in this project:
one real narrative-synthesis call, then one real judge call per
criterion, both Haiku 4.5 per the milestone's model decision. Total cost
is printed at the end so a run's real price is never a surprise.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def case_29_impact_table() -> bool:
    from access_review_agent.risk_assessment import compute_impact

    result = compute_impact("Medium", "write")
    passed = result == "Medium"
    print(f"[{'PASS' if passed else 'FAIL'}] case-29-impact-table — System Criticality=Medium + "
          f"access_level=write -> Impact={result} (expected Medium)")
    return passed


def case_30_risk_rating_table() -> bool:
    from access_review_agent.risk_assessment import compute_risk_rating

    result = compute_risk_rating("Medium", "High")
    passed = result == "High"
    print(f"[{'PASS' if passed else 'FAIL'}] case-30-risk-rating-table — Likelihood=Medium x "
          f"Impact=High -> Rating={result} (expected High)")
    return passed


def case_31_recurrence_counting() -> bool:
    from access_review_agent.risk_assessment import count_consecutive_periods, likelihood_from_consecutive_periods

    checkout_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / "risk-assessment-recurrence"
    all_ok = True
    for issue_num, expected_count, expected_likelihood in [(101, 1, "Low"), (102, 2, "Medium"), (103, 3, "High")]:
        count = count_consecutive_periods(issue_num, "orphaned", "2026-Q2", checkout_dir, "aws")
        likelihood = likelihood_from_consecutive_periods(count)
        ok = count == expected_count and likelihood == expected_likelihood
        all_ok = all_ok and ok
        print(
            f"[{'PASS' if ok else 'FAIL'}] case-31-recurrence-counting (issue #{issue_num}) — "
            f"count={count} (expected {expected_count}), likelihood={likelihood} (expected {expected_likelihood})"
        )
    return all_ok


async def case_23_and_24_narrative() -> tuple[bool, bool, float]:
    from access_review_agent.narrative import judge_narrative, synthesize_narrative
    from access_review_agent.risk_assessment import FindingSummary, RiskAssessmentEntry

    entry = RiskAssessmentEntry(
        category="orphaned",
        system_name="aws",
        likelihood="High",
        impact="High",
        risk_rating="Critical",
        findings=[
            FindingSummary(issue_number=201, identity="svc-legacy-etl", status="Open", consecutive_periods=3),
            FindingSummary(issue_number=202, identity="Jamie Rivera", status="Remediated", consecutive_periods=1),
        ],
    )
    narrative, cost = await synthesize_narrative(entry)
    total_cost = cost

    facts = (
        f"Category: {entry.category}\nSystem: {entry.system_name}\nLikelihood: {entry.likelihood}\n"
        f"Impact: {entry.impact}\nRisk Rating: {entry.risk_rating}\nFindings:\n"
        + "\n".join(
            f"- Issue #{f.issue_number} ({f.identity}): status={f.status}, "
            f"open across {f.consecutive_periods} consecutive audit(s) including this one"
            for f in entry.findings
        )
    )

    ok23, reason23, cost23 = await judge_narrative(
        facts,
        narrative,
        "The narrative correctly identifies which specific Issue number is recurring (open 2+ "
        "consecutive audits) and which is isolated (open only 1 audit and already closed), citing "
        "both by their Issue numbers.",
    )
    total_cost += cost23
    print(f"[{'PASS' if ok23 else 'FAIL'}] case-23-discriminates-isolated-vs-recurring — {reason23}")

    ok24, reason24, cost24 = await judge_narrative(
        facts,
        narrative,
        "The narrative recommends a process-level treatment action ONLY for the recurring finding "
        "(#201), and does NOT recommend any treatment action for the isolated, already-closed "
        "finding (#202).",
    )
    total_cost += cost24
    print(f"[{'PASS' if ok24 else 'FAIL'}] case-24-discriminates-treatment-necessity — {reason24}")

    print(f"         narrative: {narrative}")
    return ok23, ok24, total_cost


async def main() -> None:
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("FAIL: ANTHROPIC_API_KEY not set (checked .env and environment)")
        sys.exit(1)

    results = [case_29_impact_table(), case_30_risk_rating_table(), case_31_recurrence_counting()]
    ok23, ok24, cost = await case_23_and_24_narrative()
    results += [ok23, ok24]

    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed — total cost ${cost:.4f}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
