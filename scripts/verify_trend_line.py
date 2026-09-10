"""Regression guard for the aggregate quarterly report's Executive
Summary trend line (SPEC.md §5/§6; demo-timeline.md's "First real trend
line, comparing against Q1" / "Trend line continues" narrative beats).

Why this exists: found during Milestone 12's live-trial review of a
freshly-generated Q3 report - every quarter's Executive Summary said
"N/A, no prior period," even Q3, because build_aggregate_report's
trend_note parameter was never supplied by any caller. The finer-grained
per-category recurrence narrative (risk_assessment.py's
count_consecutive_periods, already used in the Risk Assessment table)
worked correctly and independently of this - the gap was specifically at
the Executive Summary's own summary-line level, a third instance of the
same "field that looks real but nothing ever wires it" pattern as the
Escalations-this-period table and the Release body's escalation count
(both fixed earlier this same milestone).

Fixed via risk_assessment.read_prior_aggregate_total - a local file read
of the prior period's own aggregate report (same "reuse what's already
there" discipline read_prior_report already applies one level down, at
the per-system report level).

Mocks list_issues (real-API-only, never dry-run-gated); get_adapter is
mocked with a small recording adapter so the committed aggregate content
can be inspected directly, since generate_quarterly_reports returns
ReportCommitResult objects (paths), not report text. checkout_dir is a
real temp directory with a hand-written prior-period aggregate.md, since
read_prior_aggregate_total is a local file read, not a GitHub call.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

SCRATCH_REPO = "dotMR/access-review-agent-scratch"


class _RecordingAdapter:
    def __init__(self):
        self.committed: dict[str, str] = {}

    def commit_report(self, repo_full_name, path, content, message):
        from access_review_agent.github.adapter import ReportCommitResult

        self.committed[path] = content
        return ReportCommitResult(path=path, commit_sha="fake", html_url=None, dry_run=False)


def _mock_issue(number, category, system):
    from datetime import datetime, timezone

    from access_review_agent.github.adapter import IssueInfo

    return IssueInfo(
        number=number,
        title=f"{category.replace('-', ' ').title()} access — Someone {number} ({system})",
        body=(
            f"**Access detail:** `write` access to {system}\n\n"
            "**Expected per policy:** N/A\n\n"
            f"**Source record:** `access_{system}.csv`, row matching `employee_id=E{number}`"
        ),
        state="open",
        labels=[category, system.replace("_", "-")],
        created_at=datetime.now(timezone.utc).isoformat(),
        closed_at=None,
        html_url=f"https://example.com/issues/{number}",
    )


async def case_trend_line_compares_against_prior_period() -> bool:
    from access_review_agent.orchestrator import generate_quarterly_reports

    with tempfile.TemporaryDirectory() as tmp:
        checkout_dir = Path(tmp)
        prior_dir = checkout_dir / "reports" / "2026-Q1"
        prior_dir.mkdir(parents=True)
        (prior_dir / "aggregate.md").write_text(
            "# Quarterly Access Review Audit Report — 2026-Q1\n\n"
            "## Executive summary\n\n"
            "8 findings identified this quarter across 6 finding categories "
            "and 5 Information Systems. 6 remediated, 0 open, 2 accepted as "
            "risk. N/A, no prior period\n"
        )

        issues = [_mock_issue(101, "unapproved", "aws"), _mock_issue(102, "unapproved", "github")]
        with (
            patch("access_review_agent.orchestrator.list_issues", return_value=issues),
            patch("access_review_agent.orchestrator.get_adapter", return_value=_RecordingAdapter()) as get_adapter,
        ):
            await generate_quarterly_reports(SCRATCH_REPO, "2026-Q2", checkout_dir, generate_narrative=False)
            aggregate_content = get_adapter.return_value.committed["reports/2026-Q2/aggregate.md"]

    problems = []
    if "N/A, no prior period" in aggregate_content:
        problems.append("Q2 (a real prior period exists) still renders the 'no prior period' placeholder")
    if "2 finding(s) this quarter vs. 8 last quarter (-6)" not in aggregate_content:
        problems.append("expected a real trend line comparing this quarter's 2 findings against Q1's 8 (-6)")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] trend-line-real-comparison — a quarter with a real prior period's aggregate "
        "report on disk gets an actual finding-count comparison, not the placeholder"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def case_first_quarter_still_shows_placeholder() -> bool:
    """No prior period's report exists at all - must still render the
    honest "no prior period" placeholder, not a bogus 0-vs-something
    comparison.
    """
    from access_review_agent.orchestrator import generate_quarterly_reports

    with tempfile.TemporaryDirectory() as tmp:
        checkout_dir = Path(tmp)
        issues = [_mock_issue(201, "orphaned", "vpn")]
        with (
            patch("access_review_agent.orchestrator.list_issues", return_value=issues),
            patch("access_review_agent.orchestrator.get_adapter", return_value=_RecordingAdapter()) as get_adapter,
        ):
            await generate_quarterly_reports(SCRATCH_REPO, "2026-Q1", checkout_dir, generate_narrative=False)
            aggregate_content = get_adapter.return_value.committed["reports/2026-Q1/aggregate.md"]

    problems = []
    if "N/A, no prior period" not in aggregate_content:
        problems.append("a genuine first quarter (no prior aggregate report on disk) should still say 'no prior period'")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] trend-line-first-quarter — a quarter with no prior aggregate report on disk "
        "still renders the honest 'no prior period' result, not a fabricated comparison"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        await case_trend_line_compares_against_prior_period(),
        await case_first_quarter_still_shows_placeholder(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
