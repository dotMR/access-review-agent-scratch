"""Main agent: the sole orchestrator and Issue-writer, per SPEC.md §3.

Constructs one SystemDetectionUnit per Information System and aggregates
each unit's already-detected findings — it never re-derives them by
combining raw per-system data against HRIS itself (SPEC.md §3). Then runs
open_issue (which itself gates on validate_finding, per ADR-0007) on
every finding. Units never call open_issue themselves; this module is the
only caller in the whole detection path, matching the tool registry's
"open_issue — held by: Main agent only."

Milestone 4 always ran all five systems (manually/locally triggered, no
dispatch yet). Milestone 5 adds `systems`, so a real push-triggered run
can scope to exactly what `dispatch.determine_dispatch()` decided — a
single-system commit runs one unit, not all five.
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from access_review_agent.github.adapter import (
    IssueResult,
    ReleaseResult,
    ReportCommitResult,
    get_adapter,
    get_escalation_comment_date,
    list_issues,
)
from access_review_agent.detection.identity_resolution import detect_identity_resolution
from access_review_agent.github.issues import open_issue
from access_review_agent.grounding import GroundingError
from access_review_agent.lifecycle import (
    close_accepted_risk_issues,
    close_remediated_issues,
    escalate_overdue_issues,
)
from access_review_agent.narrative import synthesize_narrative
from access_review_agent.pdf_export import render_pdf
from access_review_agent.reports import (
    SYSTEM_DISPLAY,
    SYSTEM_LABEL,
    SYSTEM_ORDER,
    build_aggregate_report,
    build_monthly_report,
    build_per_system_report,
    category_of,
    count_escalations_this_period,
    parse_issue_title,
    source_employee_id,
    summary_counts,
    system_of,
)
from access_review_agent.risk_assessment import (
    build_risk_assessment_entries,
    period_bounds,
    read_prior_aggregate_total,
)
from access_review_agent.tools.policy import DEFAULT_ROLE_ACCESS_MAPPING_PATH, read_policy
from access_review_agent.units import SYSTEMS, SystemDetectionUnit


async def run_full_reconciliation(
    data_dir: Path,
    repo_full_name: str,
    systems: set[str] | None = None,
    commit_sha: str | None = None,
    check_lifecycle: bool = True,
) -> dict[str, Any]:
    """Reconciliation across `systems` (default: all five), every Tier 1
    (deterministic) category plus Identity resolution (Tier 2, Milestone 6
    - the one category needing an Agent SDK call): detect, then open an
    Issue for every grounded finding. `commit_sha`, when given, upgrades
    every Issue's Source record citation to a clickable GitHub blob
    permalink (Milestone 5) - passed straight through to open_issue.

    Identity resolution runs per system, same as every Tier 1 category -
    SystemDetectionUnit.detect_all() stays Tier-1-only and synchronous
    (ADR-0006's split point); this async function adds Identity
    resolution's findings on top. Cheap when there's nothing to resolve:
    detect_identity_resolution() makes no Agent SDK call at all if it
    finds zero candidates, so the credential-free eval fixtures stay free.

    check_lifecycle gates three things on one `list_issues` read, all
    needing real Issue data a credential-free eval run can't provide:
    Escalation/Accepted-Risk lifecycle checks (Milestone 9, ADR-0005, run
    unconditionally over every open Issue, never scoped to `systems` -
    Escalation's same-day SLA shouldn't depend on which system got a
    commit today); duplicate-Issue prevention (passed to open_issue as
    `skip_reopen_keys` - see its own docstring for the key and why);
    and Remediation re-check (SPEC.md §8's "remediation re-check/
    auto-close," iam-review-agent-design.md's "Closing the loop" -
    close_remediated_issues, called once per system with that system's
    own just-detected `findings`, since only fresh per-system detection
    can know whether a finding is still true - unlike the other two
    checks, which only need Issue metadata). False skips all three;
    every CI-wired eval suite passes False and is unaffected.

    Per-system failure isolation (SPEC.md §7, Milestone 11): a malformed
    source file for one system doesn't abort the run - that system's
    entry gets "failed" set to a loud, specific reason, every other
    system still completes. Only FileNotFoundError/ValueError are caught
    for detection (the two real "bad source data" exceptions
    read_and_validate raises); Identity resolution's own try/except below
    is deliberately broader, since a live Agent SDK call's failure
    surface isn't just bad data - anything uncaught is a genuine bug and
    should still crash loudly.

    The write path gets the same isolation, at finding granularity: a
    real GitHub failure (rate limit, network, 5xx, auth) opening one
    Issue is caught and recorded in "write_failed" rather than aborting
    the rest of that system's findings - previously only GroundingError
    was caught here, so a transient API blip had a bigger blast radius
    than a malformed input file did. lifecycle.py's own write loops
    (close_accepted_risk_issues, escalate_overdue_issues,
    close_remediated_issues) isolate the same way, per Issue.

    Returns {"systems": {<system_name>: {detected, opened, rejected,
    skipped_existing, remediated_closed, write_failed, failed}},
    "lifecycle": {accepted_risk_closed, escalated} | None} - kept as two
    separate shapes so a caller can't conflate a per-system result with
    the cross-system lifecycle one.
    """
    all_issues = list_issues(repo_full_name) if check_lifecycle else None
    skip_reopen_keys = None
    if all_issues is not None:
        # Every OPEN Issue's key, plus every CLOSED accepted-risk Issue's -
        # accepted risk has no expiry (iam-review-agent-design.md), so a
        # still-detected finding whose Issue was formally accepted must
        # stay suppressed even after closing. A REMEDIATED closure is
        # deliberately excluded: a fixed-then-later-recurring finding is
        # a new instance of the problem, not something to suppress
        # forever. An Issue that doesn't parse cleanly (unrecognized
        # category, or a body predating a format change) is just left
        # out - risks one future duplicate, not a crash.
        skip_reopen_keys = {
            (category_of(i), system_of(i), source_employee_id(i))
            for i in all_issues
            if (i.state == "open" or "accepted-risk" in i.labels)
            and category_of(i) and system_of(i) and source_employee_id(i)
        }

    systems_results: dict[str, Any] = {}
    for system_name in (systems if systems is not None else SYSTEMS):
        try:
            unit = SystemDetectionUnit(system_name, data_dir)
            findings = unit.detect_all()
        except (FileNotFoundError, ValueError) as e:
            systems_results[system_name] = {
                "detected": 0,
                "opened": [],
                "rejected": [],
                "skipped_existing": [],
                "remediated_closed": [],
                "write_failed": [],
                "failed": str(e),
            }
            continue

        try:
            identity_result = await detect_identity_resolution(data_dir, system_name)
            findings = findings + identity_result["findings"]
        except Exception as e:
            # Broader catch than above on purpose - a live Agent SDK call's
            # failure surface isn't just bad data. Same all-or-nothing
            # per-system isolation, a second possible cause.
            systems_results[system_name] = {
                "detected": 0,
                "opened": [],
                "rejected": [],
                "skipped_existing": [],
                "remediated_closed": [],
                "write_failed": [],
                "failed": f"Identity resolution failed: {e}",
            }
            continue

        opened: list[IssueResult] = []
        rejected: list[dict[str, Any]] = []
        skipped_existing: list[dict[str, Any]] = []
        write_failed: list[dict[str, Any]] = []
        for finding in findings:
            try:
                result = open_issue(
                    finding, repo_full_name, data_dir, commit_sha,
                    skip_reopen_keys=skip_reopen_keys,
                )
            except GroundingError as e:
                rejected.append({"finding": finding, "reason": str(e)})
                continue
            except Exception as e:
                # A real write failure, isolated to this one finding - see
                # this function's own docstring.
                print(f"::error::{system_name} failed to open Issue for a finding: {e}")
                write_failed.append({"finding": finding, "reason": str(e)})
                continue
            if result is None:
                skipped_existing.append(finding)
            else:
                opened.append(result)

        remediated_closed: list[int] = []
        if all_issues is not None:
            remediated_closed = close_remediated_issues(
                get_adapter(), repo_full_name, system_name, findings, all_issues
            )

        systems_results[system_name] = {
            "detected": len(findings),
            "opened": opened,
            "rejected": rejected,
            "skipped_existing": skipped_existing,
            "remediated_closed": remediated_closed,
            "write_failed": write_failed,
            "failed": None,
        }

    lifecycle_results = None
    if check_lifecycle:
        adapter = get_adapter()
        # all_issues predates the per-system loop above, so an Issue
        # close_remediated_issues just closed this run still reads "open"
        # here - filter it out, or escalate_overdue_issues could apply an
        # escalated label to something already closed moments ago (e.g.
        # an Orphaned Issue a few days old, not yet escalated, whose
        # access got revoked in this same run).
        remediated_this_run = {
            number for summary in systems_results.values() for number in summary["remediated_closed"]
        }
        remaining_issues = [i for i in all_issues if i.number not in remediated_this_run]
        lifecycle_results = {
            "accepted_risk_closed": close_accepted_risk_issues(adapter, repo_full_name, remaining_issues),
            "escalated": escalate_overdue_issues(adapter, repo_full_name, remaining_issues),
        }
    return {"systems": systems_results, "lifecycle": lifecycle_results}


_MONTH_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


async def generate_monthly_reports(
    data_dir: Path, repo_full_name: str, period: str, commit_sha: str | None = None
) -> dict[str, ReportCommitResult]:
    """Monthly Operational Flags (SPEC.md §2/§6, ADR-0003, Milestone 10):
    the same full-reconciliation mechanism as a push-triggered run — real
    detection across all five systems, not just a list_issues read - so a
    system with no recent commits still gets a fresh look. Then commits
    one report per system listing every currently-open Finding, any
    category including Orphaned. Informational only: no sign-off, no
    SLA, doesn't gate Escalation (the reconciliation call above still
    runs Escalation/Accepted-Risk lifecycle checks as always, per
    Milestone 9 - that's independent of, and unaffected by, this report).

    `period` (YYYY-MM) becomes part of every committed file's path
    (`reports/monthly/{period}/...`) - validated strictly before it ever
    reaches a path, same discipline as generate_quarterly_reports's
    period validation and for the same reason.
    """
    if not _MONTH_PERIOD_RE.match(period):
        raise ValueError(f"period must match YYYY-MM (e.g. 2026-02), got: {period!r}")

    reconciliation = await run_full_reconciliation(data_dir, repo_full_name, systems=None, commit_sha=commit_sha)
    for system_name, summary in reconciliation["systems"].items():
        if summary["failed"]:
            # Per-system failure isolation (SPEC.md §7, Milestone 11): loud
            # and visible, but the monthly report for every OTHER system
            # still gets built and committed below regardless.
            print(f"::error::{system_name} FAILED: {summary['failed']}")
        for failure in summary["write_failed"]:
            print(f"::error::{system_name} failed to open Issue for a finding: {failure['reason']}")

    all_issues = list_issues(repo_full_name)
    generated_at = datetime.now(timezone.utc).isoformat()
    adapter = get_adapter()
    results: dict[str, ReportCommitResult] = {}

    for system_name in SYSTEM_ORDER:
        open_issues = [
            i for i in all_issues if SYSTEM_LABEL[system_name] in i.labels and i.state == "open"
        ]
        content = build_monthly_report(system_name, period, open_issues, generated_at)
        path = f"reports/monthly/{period}/{system_name}.md"
        results[system_name] = adapter.commit_report(
            repo_full_name, path, content, f"Monthly Operational Flags: {system_name}, {period}"
        )
    return results


_PERIOD_RE = re.compile(r"^\d{4}-Q[1-4]$")

NARRATIVE_DISABLED_NOTE = (
    "_(narrative synthesis disabled for this run — set generate_narrative=True / "
    "ENABLE_RISK_ASSESSMENT_NARRATIVE=true to generate; Likelihood/Impact/Risk Rating "
    "above are still real, computed values)_"
)


def _build_release_payload(
    period: str, report_contents: dict[str, str], all_issues: list
) -> tuple[str, str, dict[str, bytes]]:
    """(title, body, assets) for the quarterly Release (SPEC.md §6) -
    used by create_quarterly_release, kept as its own function so the
    payload-building logic stays separate from that function's own
    file-reading/tagging concerns. `report_contents` must have all five
    system names plus "aggregate".

    The body's escalation count comes from count_escalations_this_period
    on the aggregate report content itself, NOT summary_counts(all_issues)
    - that whole-tracker count can't express "this period" (the escalated
    label persists for an Issue's whole remaining life once applied,
    ADR-0005), and would drift from what the report's own Escalations
    table shows.
    """
    year, quarter = period.split("-Q")
    counts = summary_counts(all_issues)
    escalated_count = count_escalations_this_period(report_contents["aggregate"])
    report_links = "\n".join(f"- [{SYSTEM_DISPLAY[s]}](reports/{period}/{s}.md)" for s in SYSTEM_ORDER)
    body = (
        f"{counts['total']} findings identified this quarter. {counts['remediated']} "
        f"remediated, {counts['open']} open, {counts['accepted_risk']} accepted as risk. "
        f"{escalated_count} escalation(s) this period.\n\n"
        f"**Reports:**\n{report_links}\n- [Aggregate](reports/{period}/aggregate.md)"
    )
    assets = {f"{name}.md": content.encode("utf-8") for name, content in report_contents.items()}
    assets["aggregate.pdf"] = render_pdf(report_contents["aggregate"])
    title = f"Q{quarter} {year} Quarterly Access Review Audit"
    return title, body, assets


def create_quarterly_release(repo_full_name: str, period: str, checkout_dir: Path) -> ReleaseResult:
    """The Release-creation half of SPEC.md §6, deliberately split from
    generate_quarterly_reports (Milestone 11) so it can run as its own
    job, gated behind a GitHub Actions environment protection rule (the
    human-in-the-loop publish gate, SPEC.md §7) - AFTER the report-
    generation job's commits have already landed. Reads the six just-
    committed report files from the LOCAL checkout (which, by the time
    this job's own checkout step runs, already includes the previous
    job's commits) rather than re-deriving them, avoiding a second,
    redundant set of commit_report calls that would otherwise create
    duplicate no-op commits.

    Tags whatever commit `checkout_dir` is currently at, resolved here
    via `git rev-parse HEAD` against that checkout, since the workflow-
    trigger-time `github.sha` context value predates the report-
    generation job's commits and would tag the wrong commit.
    """
    if not _PERIOD_RE.match(period):
        raise ValueError(f"period must match YYYY-Qn (e.g. 2026-Q1), got: {period!r}")

    report_dir = checkout_dir / "reports" / period
    report_contents = {name: (report_dir / f"{name}.md").read_text() for name in SYSTEM_ORDER}
    report_contents["aggregate"] = (report_dir / "aggregate.md").read_text()

    all_issues = list_issues(repo_full_name)
    title, body, assets = _build_release_payload(period, report_contents, all_issues)

    commit_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=checkout_dir, capture_output=True, text=True, check=True
    ).stdout.strip()

    adapter = get_adapter()
    return adapter.create_release(
        repo_full_name, tag=period, title=title, body=body, target_commitish=commit_sha, assets=assets
    )


async def generate_quarterly_reports(
    repo_full_name: str,
    period: str,
    checkout_dir: Path,
    generate_narrative: bool = False,
) -> dict[str, ReportCommitResult]:
    """Roll up the quarter's already-existing Issue-tracker state (SPEC.md
    §2 — detection already happened via push-triggered runs throughout
    the quarter; this just reads and renders, no fresh detection) into
    the two evidentiary reports per system plus the aggregate, committing
    all six via commit_report - restricted to this module the same
    "main agent only" way open_issue is (generate_monthly_reports is the
    other caller, for the monthly report path).

    `period` becomes part of every committed file's path
    (`reports/{period}/...`) - validated strictly (YYYY-Qn) before it
    ever reaches a path, since workflow_dispatch's `period` input is
    free-form text a caller controls, not something safe to trust as a
    path segment unvalidated (path traversal via `../`, or worse).

    `checkout_dir` is the local repo checkout Risk Assessment's
    read_prior_report needs (SPEC.md §3 - a local file read, not a
    GitHub API call) for quarterly-recurrence Likelihood.

    `generate_narrative` gates the one real per-run cost this function
    can incur: narrative synthesis is a real Anthropic API call, made
    regardless of GITHUB_WRITE_MODE (that flag only gates GitHub writes,
    not this). Defaults to False - the deterministic Likelihood/Impact/
    Risk Rating scores are still computed and shown either way (free,
    local); only the narrative text itself is skipped when False, with
    an explicit placeholder rather than a silent gap.

    Also computes the aggregate report's "Escalations this period" table:
    every Issue with the escalated label whose escalation comment (posted
    by lifecycle.py's escalate_overdue_issues) falls within this period's
    own date range (risk_assessment.period_bounds) - not just "currently
    carries the label," since that label persists for an Issue's whole
    remaining life once applied (ADR-0005's "fires once") and would
    otherwise re-appear in every subsequent quarter's report forever.

    Also computes the Executive Summary's trend line: this period's total
    findings vs. the prior period's (risk_assessment.read_prior_aggregate_total,
    a local file read of the prior aggregate report - same "reuse what's
    already there" discipline as the Escalations table above). "N/A, no
    prior period" only for a genuine first quarter.

    Does NOT create the Release - see create_quarterly_release for that
    (Milestone 11 split it out deliberately so the human-in-the-loop
    publish gate can sit in front of release creation specifically,
    without also re-running detection/report generation).
    """
    if not _PERIOD_RE.match(period):
        raise ValueError(f"period must match YYYY-Qn (e.g. 2026-Q1), got: {period!r}")

    all_issues = list_issues(repo_full_name)
    per_system_issues = {
        system_name: [i for i in all_issues if SYSTEM_LABEL[system_name] in i.labels]
        for system_name in SYSTEM_ORDER
    }

    system_criticality = read_policy(DEFAULT_ROLE_ACCESS_MAPPING_PATH)["system_criticality"]
    risk_assessment_rows: list[dict[str, Any]] = []
    for system_name in SYSTEM_ORDER:
        entries = build_risk_assessment_entries(
            system_name, per_system_issues[system_name], period, checkout_dir, system_criticality[system_name]
        )
        for entry in entries:
            if generate_narrative:
                narrative, _cost = await synthesize_narrative(entry)
            else:
                narrative = NARRATIVE_DISABLED_NOTE
            risk_assessment_rows.append(
                {
                    "category": entry.category,
                    "system_name": entry.system_name,
                    "likelihood": entry.likelihood,
                    "impact": entry.impact,
                    "risk_rating": entry.risk_rating,
                    "narrative": narrative,
                }
            )

    period_start, period_end = period_bounds(period)
    escalated_rows: list[dict[str, Any]] = []
    for system_name in SYSTEM_ORDER:
        for issue in per_system_issues[system_name]:
            if "escalated" not in issue.labels:
                continue
            escalated_at = get_escalation_comment_date(repo_full_name, issue.number)
            if escalated_at is None or not (period_start <= escalated_at < period_end):
                continue  # escalated in a different period, or (shouldn't happen) no comment found
            escalated_rows.append(
                {
                    "finding": parse_issue_title(issue.title),
                    "system_name": system_name,
                    "category": category_of(issue),
                    "open_since": issue.created_at,
                    "escalated_at": escalated_at,
                    "issue_number": issue.number,
                    "issue_url": issue.html_url,
                }
            )

    generated_at = datetime.now(timezone.utc).isoformat()
    adapter = get_adapter()
    results: dict[str, ReportCommitResult] = {}
    report_contents: dict[str, str] = {}

    for system_name in SYSTEM_ORDER:
        content = build_per_system_report(
            system_name, period, per_system_issues[system_name], generated_at
        )
        report_contents[system_name] = content
        path = f"reports/{period}/{system_name}.md"
        results[system_name] = adapter.commit_report(
            repo_full_name, path, content, f"Per-system report: {system_name}, {period}"
        )

    prior_total = read_prior_aggregate_total(checkout_dir, period)
    if prior_total is None:
        trend_note = "N/A, no prior period"
    else:
        this_total = sum(len(issues) for issues in per_system_issues.values())
        delta = this_total - prior_total
        trend_note = (
            f"{this_total} finding(s) this quarter vs. {prior_total} last quarter "
            f"({'+' if delta >= 0 else ''}{delta})"
        )

    aggregate_content = build_aggregate_report(
        period,
        per_system_issues,
        generated_at,
        trend_note=trend_note,
        risk_assessment_rows=risk_assessment_rows,
        escalated_rows=escalated_rows,
    )
    report_contents["aggregate"] = aggregate_content
    results["aggregate"] = adapter.commit_report(
        repo_full_name,
        f"reports/{period}/aggregate.md",
        aggregate_content,
        f"Aggregate report: {period}",
    )

    return results
