"""Regression guard: a real GitHub write failure (rate limit, network,
5xx, auth) on one Issue doesn't abort the rest of the batch.

Why this exists: an EM-level code review of the codebase found that
every read/detection-side failure this project has found and fixed
(malformed source data, Agent SDK errors, duplicate Issues, the missing
remediation re-check) got real per-item isolation - but the write path
never did. Only GroundingError was ever caught around open_issue; any
other exception propagated uncaught and aborted the entire
run_full_reconciliation call, and lifecycle.py's three write loops had
no exception handling anywhere. A transient API blip while writing had
a bigger blast radius than a bad input file did.

Mocks the adapter layer only (create_issue/close_issue/apply_label/
add_comment) - detection and grounding run for real against the
partial-failure-isolation fixture, same as the other verify_*.py
scripts.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "partial-failure-isolation"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


class _FlakyAdapter:
    """A fake adapter whose create_issue raises for exactly one system
    (github) and behaves normally (records the call, returns a fake
    result) for everyone else - proving one write failure doesn't stop
    the rest of the batch, in either direction (systems before AND
    after it in iteration order).
    """

    def __init__(self):
        self.created = []
        self.closed = []
        self.labeled = []
        self.commented = []

    def create_issue(self, repo_full_name, title, body, labels):
        from access_review_agent.github.adapter import IssueResult

        if "GitHub" in title:
            raise RuntimeError("simulated GitHub API 502")
        self.created.append(title)
        return IssueResult(
            number=len(self.created), title=title, body=body, labels=labels,
            html_url=f"https://example.com/issues/{len(self.created)}", dry_run=False,
        )

    def close_issue(self, repo_full_name, issue_number):
        if issue_number == 999:
            raise RuntimeError("simulated GitHub API 502")
        self.closed.append(issue_number)

    def apply_label(self, repo_full_name, issue_number, label):
        if issue_number == 999:
            raise RuntimeError("simulated GitHub API 502")
        self.labeled.append((issue_number, label))

    def add_comment(self, repo_full_name, issue_number, body):
        self.commented.append((issue_number, body))


async def case_open_issue_write_failure_isolated() -> bool:
    """One system's Issue-creation failing must not abort the other
    systems' - and the fixture's own real findings (salesforce,
    finance_erp, vpn) must still open normally around it.
    """
    from access_review_agent.orchestrator import run_full_reconciliation

    flaky = _FlakyAdapter()
    with (
        patch("access_review_agent.orchestrator.list_issues", return_value=[]),
        patch("access_review_agent.github.issues.get_adapter", return_value=flaky),
        patch("access_review_agent.orchestrator.get_adapter", return_value=flaky),
    ):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=True
        )

    problems = []
    github_result = results["systems"]["github"]
    if len(github_result["write_failed"]) != 1:
        problems.append(f"expected github's finding to be recorded as write_failed - got {github_result['write_failed']}")
    if github_result["opened"]:
        problems.append(f"expected 0 Issues opened for github (write failed) - got {github_result['opened']}")

    for system_name in ("salesforce", "finance_erp", "vpn"):
        summary = results["systems"][system_name]
        if len(summary["opened"]) != 1:
            problems.append(
                f"expected {system_name}'s finding to open normally despite github's write "
                f"failure - got {len(summary['opened'])} opened"
            )
        if summary["write_failed"]:
            problems.append(f"expected no write failures for {system_name} - got {summary['write_failed']}")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] write-failure-isolation-open-issue — one system's Issue-creation failure "
        "doesn't abort the run; every other system's real findings still open"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


def _mock_issue(number, category, employee_id, system, escalation_eligible=False):
    from access_review_agent.github.adapter import IssueInfo

    created = "2020-01-01T00:00:00Z" if escalation_eligible else datetime.now(timezone.utc).isoformat()
    return IssueInfo(
        number=number,
        title=f"{category} — Someone ({system})",
        body=f"**Source record:** `access_{system}.csv`, row matching `employee_id={employee_id}`",
        state="open",
        labels=[category, system],
        created_at=created,
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


def case_lifecycle_write_failures_isolated() -> bool:
    """close_accepted_risk_issues and escalate_overdue_issues must both
    isolate a single Issue's write failure from the rest of the batch -
    Issue #999 always raises in _FlakyAdapter, everything else succeeds.
    """
    from access_review_agent.lifecycle import close_accepted_risk_issues, escalate_overdue_issues

    # Built directly rather than via _mock_issue - need the accepted-risk
    # label added on top, which that helper doesn't carry.
    from access_review_agent.github.adapter import IssueInfo

    accepted_risk_issues = [
        IssueInfo(
            number=999, title="Unapproved access — A (GitHub)", body="",
            state="open", labels=["unapproved", "github", "accepted-risk"],
            created_at=datetime.now(timezone.utc).isoformat(), closed_at=None,
            html_url="https://example.com/issues/999",
        ),
        IssueInfo(
            number=1000, title="Unapproved access — B (VPN)", body="",
            state="open", labels=["unapproved", "vpn", "accepted-risk"],
            created_at=datetime.now(timezone.utc).isoformat(), closed_at=None,
            html_url="https://example.com/issues/1000",
        ),
    ]
    flaky = _FlakyAdapter()
    closed = close_accepted_risk_issues(flaky, SCRATCH_REPO, accepted_risk_issues)

    escalation_issues = [
        _mock_issue(999, "orphaned", "E1", "aws", escalation_eligible=True),
        _mock_issue(1001, "orphaned", "E2", "aws", escalation_eligible=True),
    ]
    escalated = escalate_overdue_issues(flaky, SCRATCH_REPO, escalation_issues)

    problems = []
    if 999 in closed:
        problems.append("expected Issue #999's close to fail (simulated), it didn't")
    if 1000 not in closed:
        problems.append(f"expected Issue #1000 to close despite #999's failure - got {closed}")
    if 999 in escalated:
        problems.append("expected Issue #999's escalation to fail (simulated), it didn't")
    if 1001 not in escalated:
        problems.append(f"expected Issue #1001 to escalate despite #999's failure - got {escalated}")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] write-failure-isolation-lifecycle — one Issue's write failure in "
        "close_accepted_risk_issues/escalate_overdue_issues doesn't abort the rest of the batch"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        await case_open_issue_write_failure_isolated(),
        case_lifecycle_write_failures_isolated(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
