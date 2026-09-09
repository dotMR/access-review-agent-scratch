"""Milestone 9 eval runner: Tier 3 cases 34-36 (Escalation mechanism,
fires-once, Accepted-risk closure), graded automatically.

Pure Python, no model call, no network - uses synthetic IssueInfo objects
and the DryRunAdapter directly, since these are mechanism-correctness
checks (does the right label/comment/close action fire under the right
conditions), not detection or reasoning correctness. Real-mode behavior
(does GITHUB_WRITE_MODE=real actually reach the GitHub API correctly)
was verified once by hand against the scratch repo - see
docs/adr/0007-local-vs-remote-dry-run-adapter.md's precedent and
development-plan.md's Milestone 9 for that verification.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _issue(number, category, system, created_at, labels, state="open"):
    from access_review_agent.github.adapter import IssueInfo

    return IssueInfo(
        number=number,
        title=f"Test — {category} ({system})",
        body="",
        state=state,
        labels=[category, system] + labels,
        created_at=created_at,
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


def case_34_escalation_mechanism() -> bool:
    from access_review_agent.github.adapter import DryRunAdapter
    from access_review_agent.lifecycle import escalate_overdue_issues

    issue = _issue(301, "orphaned", "aws", "2026-09-08T00:00:00Z", labels=[])
    escalated = escalate_overdue_issues(DryRunAdapter(), "dotMR/access-review-agent", [issue], as_of=date(2026, 9, 9))
    passed = escalated == [301]
    print(f"[{'PASS' if passed else 'FAIL'}] case-34-escalation-mechanism — orphaned Issue open 1 day "
          f"past same-day SLA -> escalated={escalated} (expected [301])")
    return passed


def case_35_escalation_fires_once() -> bool:
    from access_review_agent.github.adapter import DryRunAdapter
    from access_review_agent.lifecycle import escalate_overdue_issues

    issue = _issue(302, "orphaned", "aws", "2026-09-01T00:00:00Z", labels=["escalated"])
    escalated = escalate_overdue_issues(DryRunAdapter(), "dotMR/access-review-agent", [issue], as_of=date(2026, 9, 9))
    passed = escalated == []
    print(f"[{'PASS' if passed else 'FAIL'}] case-35-escalation-fires-once — already-escalated Issue, "
          f"still open -> escalated={escalated} (expected [], no re-escalation)")
    return passed


def case_36_accepted_risk_closes() -> bool:
    from access_review_agent.github.adapter import DryRunAdapter
    from access_review_agent.lifecycle import close_accepted_risk_issues

    issue = _issue(303, "dormant-admin", "aws", "2026-09-01T00:00:00Z", labels=["accepted-risk"])
    closed = close_accepted_risk_issues(DryRunAdapter(), "dotMR/access-review-agent", [issue])
    passed = closed == [303]
    print(f"[{'PASS' if passed else 'FAIL'}] case-36-accepted-risk-closes — accepted-risk label applied "
          f"-> closed={closed} (expected [303])")
    return passed


def case_boundary_not_yet_overdue() -> bool:
    """Not a numbered eval case, but the natural boundary check for
    case 34's own condition (same-day SLA = 0 days, so an Issue opened
    today - not yet overdue - must NOT escalate, matching the `>`, not
    `>=`, threshold discipline used throughout this project.
    """
    from access_review_agent.github.adapter import DryRunAdapter
    from access_review_agent.lifecycle import escalate_overdue_issues

    issue = _issue(304, "orphaned", "aws", "2026-09-09T00:00:00Z", labels=[])
    escalated = escalate_overdue_issues(DryRunAdapter(), "dotMR/access-review-agent", [issue], as_of=date(2026, 9, 9))
    passed = escalated == []
    print(f"[{'PASS' if passed else 'FAIL'}] case-boundary-not-yet-overdue — orphaned Issue opened "
          f"today, same-day SLA not yet missed -> escalated={escalated} (expected [])")
    return passed


def main() -> None:
    results = [
        case_34_escalation_mechanism(),
        case_35_escalation_fires_once(),
        case_36_accepted_risk_closes(),
        case_boundary_not_yet_overdue(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
