"""Regression guard: confirms run_full_reconciliation doesn't re-open a
new Issue for a finding that's still present but already has an open
Issue from a prior run.

Why this exists: found live during Milestone 12's scratch-repo trial,
not designed in speculatively. A push touching system_hr.csv (or
policy-config.yaml/role-access-mapping.yaml) fans out to all five
systems (dispatch.py) - so a run that re-detects an already-known,
still-open finding (nothing about it changed) had nothing to recognize
"there's already an open Issue for this" and opened a brand new
duplicate every time. Every eval fixture before this test was a
single-shot detection check against fresh data, so none of them ever
exercised running detection twice against unchanged data - the exact
shape of run that triggered this live.

Mocks list_issues (the one call run_full_reconciliation makes that's
never dry-run-gated - always a real API call per its own docstring) so
this stays credential-free; create_issue/close_issue/apply_label/
add_comment all go through the default DryRunAdapter already, no
mocking needed there.

Keys on (category, system_name, employee_id) - the finding's own real
unique key, parsed back out of the mocked Issue's Source record line via
reports.py's source_employee_id() - not the rendered title. Also found
during the same review: title alone (employee_name, a human display
name) isn't a safe dedup key, since two different employees could share
a name and collide on it, silently swallowing a second, genuinely
distinct finding. Case two proves this directly: an identical title with
a DIFFERENT employee_id in its Source record must NOT be treated as a
duplicate.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "partial-failure-isolation"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


def _mock_issue(number, title, employee_id, labels):
    from access_review_agent.github.adapter import IssueInfo

    return IssueInfo(
        number=number,
        title=title,
        body=(
            "**Access detail:** `write` access to github\n\n"
            "**Expected per policy:** A recorded approval (auto or Asset Owner) on file\n\n"
            f"**Source record:** `access_github.csv`, row matching `employee_id={employee_id}`"
        ),
        state="open",
        labels=labels,
        created_at=datetime.now(timezone.utc).isoformat(),
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


async def case_duplicate_issue_skipped() -> bool:
    from access_review_agent.orchestrator import run_full_reconciliation

    # Same (category, system, employee_id) as the fixture's own GitHub
    # Unapproved finding (Github Employee, E9202) - a prior run's Issue
    # for the SAME finding, still open, nothing about it changed.
    already_open = _mock_issue(101, "Unapproved access — Github Employee (GitHub)", "E9202", ["unapproved", "github"])

    with patch("access_review_agent.orchestrator.list_issues", return_value=[already_open]):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=True
        )

    problems = []
    github_result = results["systems"]["github"]
    if github_result["detected"] != 1:
        problems.append(f"expected 1 finding detected for github, got {github_result['detected']}")
    if len(github_result["opened"]) != 0:
        problems.append(f"expected 0 Issues opened for github (already open) - got {len(github_result['opened'])}")
    if len(github_result["skipped_existing"]) != 1:
        problems.append(
            f"expected the github finding to be recorded as skipped_existing - got {github_result['skipped_existing']}"
        )

    # A different system's genuinely-new finding (no matching open Issue
    # in the mock) must still open normally - dedup isn't a blanket freeze.
    salesforce_result = results["systems"]["salesforce"]
    if len(salesforce_result["opened"]) != 1:
        problems.append(
            f"expected salesforce's finding (no existing Issue for it) to open normally - "
            f"got {len(salesforce_result['opened'])} opened"
        )

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] duplicate-issue-prevention — a finding whose key matches an already-open "
        "Issue is skipped, not re-opened, while genuinely new findings still open normally"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def case_name_collision_not_deduped() -> bool:
    """The fix keys on employee_id, not the rendered title (employee_name)
    - proves it directly: an Issue with the IDENTICAL title text but a
    DIFFERENT employee_id in its own Source record must NOT be treated
    as the same finding. Title-only matching would have wrongly skipped
    this and silently swallowed a genuinely distinct violation.
    """
    from access_review_agent.orchestrator import run_full_reconciliation

    same_title_different_person = _mock_issue(
        202, "Unapproved access — Github Employee (GitHub)", "E-someone-else", ["unapproved", "github"]
    )

    with patch("access_review_agent.orchestrator.list_issues", return_value=[same_title_different_person]):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=True
        )

    github_result = results["systems"]["github"]
    problems = []
    if len(github_result["opened"]) != 1:
        problems.append(
            f"expected the fixture's E9202 finding to open despite the title-alike Issue for a "
            f"different employee_id - got {len(github_result['opened'])} opened"
        )
    if github_result["skipped_existing"]:
        problems.append(f"expected nothing skipped (different employee_id) - got {github_result['skipped_existing']}")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] duplicate-issue-prevention-employee-id-not-title — an Issue with an "
        "identical title but a different employee_id is NOT treated as a duplicate"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def case_extra_label_does_not_break_system_matching() -> bool:
    """Found live during Milestone 12's scratch-repo trial, a genuine
    duplicate produced in production: an already-open Issue that ALSO
    carries accepted-risk (three labels total, not _format_labels' usual
    two) must still be recognized correctly - system_of() previously
    picked "whichever label isn't the category", which meant an Issue
    with accepted-risk present could return "accepted-risk" as if it
    were the system, producing a wrong dedup key and letting a real
    duplicate Issue open right alongside the original.
    """
    from access_review_agent.orchestrator import run_full_reconciliation

    already_open_with_extra_label = _mock_issue(
        401, "Unapproved access — Github Employee (GitHub)", "E9202",
        ["accepted-risk", "unapproved", "github"],  # accepted-risk listed FIRST, same order as the live bug
    )

    with patch(
        "access_review_agent.orchestrator.list_issues", return_value=[already_open_with_extra_label]
    ):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=True
        )

    github_result = results["systems"]["github"]
    problems = []
    if len(github_result["opened"]) != 0:
        problems.append(
            f"expected 0 Issues opened for github (already open, despite the extra accepted-risk "
            f"label) - got {len(github_result['opened'])}"
        )
    if len(github_result["skipped_existing"]) != 1:
        problems.append(
            f"expected the github finding to be recognized as already open despite the extra label "
            f"- got {github_result['skipped_existing']}"
        )

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] duplicate-issue-prevention-extra-label — an Issue with a THIRD label "
        "(accepted-risk) is still matched correctly, not mistaken for a different system"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        await case_duplicate_issue_skipped(),
        await case_name_collision_not_deduped(),
        await case_extra_label_does_not_break_system_matching(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
