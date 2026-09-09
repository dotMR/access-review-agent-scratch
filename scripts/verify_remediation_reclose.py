"""Regression guard for lifecycle.py's close_remediated_issues (SPEC.md
§8, iam-review-agent-design.md's "Closing the loop"): confirms
run_full_reconciliation actually closes an open Issue once its finding
is genuinely gone from a system's own current detection.

Why this exists: found live during Milestone 12's scratch-repo trial -
an Orphaned Issue stayed open even after step 12's data commit revoked
the underlying AWS access for real. Investigation found there was no
code anywhere that re-checked an open Issue against current data and
closed it - "remediated" was only ever an inferred report LABEL (a
closed, non-accepted-risk Issue), never something the system actually
did. SPEC.md §8 already listed "remediation re-check/auto-close" as v1
Core scope; Milestone 9 built Escalation and Accepted Risk but never
this third lifecycle mechanic.

Mocks list_issues only (the one call that's never dry-run-gated);
close_issue/add_comment already go through the credential-free
DryRunAdapter.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "partial-failure-isolation"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


def _mock_issue(number, title, employee_id, labels, system="github"):
    from access_review_agent.github.adapter import IssueInfo

    return IssueInfo(
        number=number,
        title=title,
        body=(
            f"**Access detail:** `write` access to {system}\n\n"
            "**Expected per policy:** A recorded approval (auto or Asset Owner) on file\n\n"
            f"**Source record:** `access_{system}.csv`, row matching `employee_id={employee_id}`"
        ),
        state="open",
        labels=labels,
        created_at=datetime.now(timezone.utc).isoformat(),
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


async def case_remediated_finding_closes() -> bool:
    from access_review_agent.orchestrator import run_full_reconciliation

    # No employee_id=E-long-gone row exists in the fixture's
    # access_github.csv at all - the access was genuinely revoked/removed,
    # this Issue should close as remediated.
    stale = _mock_issue(301, "Unapproved access — Someone Gone (GitHub)", "E-long-gone", ["unapproved", "github"])
    # Still genuinely present (the fixture's real E9202 finding) - must
    # NOT be closed.
    still_open = _mock_issue(302, "Unapproved access — Github Employee (GitHub)", "E9202", ["unapproved", "github"])
    # Carries accepted-risk - must NOT be touched by remediation re-check
    # even though its finding is also gone; that's close_accepted_risk_issues'
    # job, not this one's.
    accepted_risk = _mock_issue(
        303, "Unapproved access — Also Gone (GitHub)", "E-also-gone",
        ["unapproved", "github", "accepted-risk"],
    )

    with patch(
        "access_review_agent.orchestrator.list_issues",
        return_value=[stale, still_open, accepted_risk],
    ):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=True
        )

    github_result = results["systems"]["github"]
    problems = []
    if 301 not in github_result["remediated_closed"]:
        problems.append(f"expected Issue #301 (finding gone) to be closed as remediated - got {github_result['remediated_closed']}")
    if 302 in github_result["remediated_closed"]:
        problems.append("Issue #302 (finding still present) was incorrectly closed as remediated")
    if 303 in github_result["remediated_closed"]:
        problems.append("Issue #303 (accepted-risk) was incorrectly closed by remediation re-check, not its own path")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] remediation-reclose — an Issue whose finding is genuinely gone closes "
        "automatically; a still-present finding and an accepted-risk Issue are both left alone"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def case_remediated_and_escalation_overlap_handled() -> bool:
    """Overlap scenario, found during this fix's own security review: an
    Orphaned Issue, 2 days old, not yet escalated, whose access has ALSO
    been genuinely revoked (gone from current_findings) in this same run.
    Must close as remediated and must NOT also receive the escalated
    label/comment - escalate_overdue_issues reads a snapshot fetched
    before remediation closing ran, so without filtering it would act on
    something already closed moments earlier in the very same run.
    """
    from datetime import timedelta

    from access_review_agent.github.adapter import IssueInfo
    from access_review_agent.orchestrator import run_full_reconciliation

    old_orphaned = IssueInfo(
        number=401,
        title="Orphaned access — Someone Departed (GitHub)",
        body=(
            "**Access detail:** `write` access to github\n\n"
            "**Expected per policy:** None (terminated 2026-01-01)\n\n"
            "**Date detected:** 2026-01-01\n\n"
            "**Time to revoke:** same day as detection\n\n"
            "**Source record:** `access_github.csv`, row matching `employee_id=E-departed`"
        ),
        state="open",
        labels=["orphaned", "github"],
        created_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        closed_at=None,
        html_url="https://example.com/issues/401",
    )

    with patch("access_review_agent.orchestrator.list_issues", return_value=[old_orphaned]):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=True
        )

    github_result = results["systems"]["github"]
    problems = []
    if 401 not in github_result["remediated_closed"]:
        problems.append(f"expected #401 to close as remediated - got {github_result['remediated_closed']}")
    if 401 in results["lifecycle"]["escalated"]:
        problems.append("expected #401 to NOT also be escalated in the same run - it was already closed as remediated")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] remediation-escalation-overlap — an Issue remediated and escalation-eligible "
        "in the same run closes as remediated, and is not also escalated"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        await case_remediated_finding_closes(),
        await case_remediated_and_escalation_overlap_handled(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
