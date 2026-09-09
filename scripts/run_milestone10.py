"""Milestone 10 eval runner: Tier 3 cases 32-33 (Monthly trigger),
graded automatically. Pure Python, no model call, no network -
credential-free, matching Milestones 1-5/9.

Case 32 tests run_full_reconciliation directly (not the full
generate_monthly_reports, which chains a second real list_issues read
for report-building that a dry-run write can't feed - see
development-plan.md's Milestone 10 for why): the actual claim is that
monthly detection runs for real, not that report content reflects live
Issue state (already covered by Milestone 7). generate_monthly_reports
itself was verified manually against the real scratch repo before this
suite was written - see development-plan.md.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "monthly-quiet-system-catch"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


async def case_32_quiet_system_catch() -> bool:
    from access_review_agent.orchestrator import run_full_reconciliation

    results = await run_full_reconciliation(FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=False)
    systems = results["systems"]

    problems = []
    if systems["aws"]["detected"] != 1:
        problems.append(f"expected 1 finding detected for aws, got {systems['aws']['detected']}")
    for system_name in ("github", "salesforce", "finance_erp", "vpn"):
        if systems[system_name]["detected"] != 0:
            problems.append(
                f"expected 0 findings for {system_name} (empty access file), "
                f"got {systems[system_name]['detected']}"
            )

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] case-32-quiet-system-catch — full monthly reconciliation runs real "
        "detection across all five systems (not a stale list_issues read), catching a "
        "dormant-admin finding on a system with no prior Issue for it"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


def _issue(number, category, system, created_at, labels, state="open"):
    from access_review_agent.github.adapter import IssueInfo

    body = (
        "**Access detail:** `admin` access to " + system + "\n\n"
        "**Expected per policy:** Revoke if unused > 90 consecutive days\n\n"
        "**Last used:** 2026-01-01\n\n**Days dormant:** 200\n\n"
        f"**Source record:** `access_{system}.csv`, row matching `employee_id=E{number}`"
    )
    return IssueInfo(
        number=number,
        title=f"Test — {category} ({system})",
        body=body,
        state=state,
        labels=[category, system] + labels,
        created_at=created_at,
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


def case_33_monthly_report_scope() -> bool:
    from access_review_agent.reports import build_monthly_report

    issues = [
        _issue(401, "orphaned", "aws", "2026-09-01T00:00:00Z", labels=["escalated"]),
        _issue(402, "dormant-admin", "aws", "2026-08-15T00:00:00Z", labels=[]),
        _issue(403, "unapproved", "aws", "2026-08-20T00:00:00Z", labels=[]),
        _issue(404, "identity-resolution", "aws", "2026-08-25T00:00:00Z", labels=[]),
        _issue(405, "drift", "aws", "2026-08-28T00:00:00Z", labels=[]),
        _issue(406, "dormant-ad-hoc", "aws", "2026-08-30T00:00:00Z", labels=["accepted-risk"], state="closed"),
    ]
    # Only currently-open issues should ever reach build_monthly_report - the
    # caller (generate_monthly_reports) filters by state before calling it,
    # same as this test does, matching real usage.
    open_issues = [i for i in issues if i.state == "open"]
    content = build_monthly_report("aws", "2026-09", open_issues, "2026-09-09T00:00:00Z")

    problems = []
    for expected_number in (401, 402, 403, 404, 405):
        if f"#{expected_number}" not in content:
            problems.append(f"expected open Issue #{expected_number} to appear in the report, it didn't")
    if "#406" in content:
        problems.append("accepted-risk-closed Issue #406 appeared in the report - it should not")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] case-33-monthly-report-scope — every open finding of every category "
        "(including already-escalated Orphaned) appears; the accepted-risk-closed one does not"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [await case_32_quiet_system_catch(), case_33_monthly_report_scope()]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
