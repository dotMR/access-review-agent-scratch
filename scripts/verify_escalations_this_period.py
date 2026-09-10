"""Regression guard for the aggregate quarterly report's "Escalations
this period" table (SPEC.md §4's Escalation mechanism section, ADR-0005).

Why this exists: found during Milestone 12's live-trial review of a
freshly-generated Q2 report - the table was hardcoded to a "Not yet
implemented - lands in Milestone 9" placeholder with an always-empty
row set, even though Milestone 9 (Escalation) shipped long ago and
summary_counts() right there in reports.py already computed a real
escalated count that was simply never wired through. Fixed by filtering
on the escalation comment's own timestamp (get_escalation_comment_date),
not just "currently carries the escalated label" - that label persists
for an Issue's whole remaining life once applied (ADR-0005's "fires
once"), so a naive label check would re-report the same escalation in
every subsequent quarter forever.

Also covers the quarterly Release body's own escalation count
(_build_release_payload, orchestrator.py) - found to have the same class
of bug one level up: it used summary_counts(all_issues)["escalated"], a
whole-tracker label count that can't express "this period" either, so
the Release body and the report's own table could disagree even after
the first fix. Now parsed back from the report's own rendered table
(count_escalations_this_period) instead.

Mocks list_issues and get_escalation_comment_date (both real-API-only,
never dry-run-gated); get_adapter is mocked with a small recording
adapter so the committed aggregate content can be inspected directly,
since generate_quarterly_reports returns ReportCommitResult objects
(paths), not report text.
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


class _RecordingAdapter:
    def __init__(self):
        self.committed: dict[str, str] = {}

    def commit_report(self, repo_full_name, path, content, message):
        from access_review_agent.github.adapter import ReportCommitResult

        self.committed[path] = content
        return ReportCommitResult(path=path, commit_sha="fake", html_url=None, dry_run=False)


def _mock_issue(number, category, system, created_at, escalated=False):
    from access_review_agent.github.adapter import IssueInfo

    labels = [category, system.replace("_", "-")]
    if escalated:
        labels.append("escalated")
    return IssueInfo(
        number=number,
        title=f"{category.replace('-', ' ').title()} access — Someone {number} ({system})",
        body=(
            f"**Access detail:** `write` access to {system}\n\n"
            "**Expected per policy:** N/A\n\n"
            f"**Source record:** `access_{system}.csv`, row matching `employee_id=E{number}`"
        ),
        state="open",
        labels=labels,
        created_at=created_at,
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


async def case_only_this_periods_escalations_appear() -> bool:
    from access_review_agent.orchestrator import generate_quarterly_reports

    # Escalated label present, but the escalation comment itself landed in
    # Q1 - a naive "label present" check would wrongly re-report this in
    # every later quarter (ADR-0005's "fires once").
    stale_escalation = _mock_issue(101, "orphaned", "aws", "2026-01-05T00:00:00+00:00", escalated=True)
    # Escalated label present, comment lands inside Q2 - must appear.
    this_period_escalation = _mock_issue(102, "orphaned", "aws", "2026-05-01T00:00:00+00:00", escalated=True)
    # A normal open finding, never escalated at all - must never appear.
    never_escalated = _mock_issue(103, "unapproved", "github", "2026-05-01T00:00:00+00:00", escalated=False)

    def fake_escalation_date(repo_full_name, issue_number):
        return {101: "2026-01-06T00:00:00+00:00", 102: "2026-05-02T00:00:00+00:00"}[issue_number]

    with (
        patch(
            "access_review_agent.orchestrator.list_issues",
            return_value=[stale_escalation, this_period_escalation, never_escalated],
        ),
        patch(
            "access_review_agent.orchestrator.get_escalation_comment_date",
            side_effect=fake_escalation_date,
        ),
        patch("access_review_agent.orchestrator.get_adapter", return_value=_RecordingAdapter()) as get_adapter,
    ):
        await generate_quarterly_reports(SCRATCH_REPO, "2026-Q2", REPO_ROOT, generate_narrative=False)
        aggregate_content = get_adapter.return_value.committed["reports/2026-Q2/aggregate.md"]

    problems = []
    if "Not yet implemented" in aggregate_content:
        problems.append("aggregate report still renders the stale 'Not yet implemented' placeholder")
    if "#102" not in aggregate_content.split("## Escalations this period")[1].split("## Reviewer")[0]:
        problems.append("expected #102 (escalated within Q2) in the Escalations this period table")
    escalations_section = aggregate_content.split("## Escalations this period")[1].split("## Reviewer")[0]
    if "#101" in escalations_section:
        problems.append("#101 (escalated in Q1, not Q2) incorrectly appears in Q2's Escalations this period table")
    if "#103" in escalations_section:
        problems.append("#103 (never escalated) incorrectly appears in the Escalations this period table")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] escalations-this-period — the aggregate report's Escalations table shows "
        "only Issues that escalated within THIS period, not every Issue that ever carried the label"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def case_no_escalations_renders_real_empty_result() -> bool:
    """No escalated Issues at all this quarter must render as a real
    computed "none" result, not the old placeholder - the whole point of
    the fix is that this table is now a real computation either way.
    """
    from access_review_agent.orchestrator import generate_quarterly_reports

    with (
        patch("access_review_agent.orchestrator.list_issues", return_value=[]),
        patch("access_review_agent.orchestrator.get_adapter", return_value=_RecordingAdapter()) as get_adapter,
    ):
        await generate_quarterly_reports(SCRATCH_REPO, "2026-Q3", REPO_ROOT, generate_narrative=False)
        aggregate_content = get_adapter.return_value.committed["reports/2026-Q3/aggregate.md"]

    problems = []
    if "Not yet implemented" in aggregate_content:
        problems.append("empty-quarter aggregate report still renders the stale placeholder")
    if "No escalations this period" not in aggregate_content:
        problems.append("expected an explicit 'No escalations this period' row for a quarter with none")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] escalations-this-period-empty — a quarter with zero escalations renders a real "
        "'none' result, not the old 'not yet implemented' placeholder"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


def case_release_body_escalation_count_matches_report() -> bool:
    """The Release body's escalation count must come from the same
    period-filtered computation as the report's own Escalations table,
    not a separate whole-tracker label count that can drift from it -
    the real bug found in Q2's actual Release body (a stray Issue,
    escalated during unrelated earlier testing, inflated the body's
    count to 1 when the report's own table correctly showed 0 for the
    period).
    """
    from access_review_agent.orchestrator import _build_release_payload
    from access_review_agent.reports import build_aggregate_report

    aggregate_content = build_aggregate_report(
        "2026-Q2", {}, "2026-01-01T00:00:00Z", risk_assessment_rows=[], escalated_rows=[]
    )
    report_contents = {s: f"# fake {s} report" for s in ["aws", "github", "salesforce", "finance_erp", "vpn"]}
    report_contents["aggregate"] = aggregate_content

    _title, body, _assets = _build_release_payload("2026-Q2", report_contents, all_issues=[])

    problems = []
    if "0 escalation(s) this period" not in body:
        problems.append(
            "expected the Release body to show 0 escalations (matching the report's real "
            f"'none' result) - got: {body.splitlines()[0]}"
        )

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] release-body-escalation-count — the Release body's escalation count is "
        "parsed from the report's own period-filtered table, not a separate whole-tracker label count"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        await case_only_this_periods_escalations_appear(),
        await case_no_escalations_renders_real_empty_result(),
        case_release_body_escalation_count_matches_report(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
