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
    list_issues,
)
from access_review_agent.detection.identity_resolution import detect_identity_resolution
from access_review_agent.github.issues import open_issue
from access_review_agent.grounding import GroundingError
from access_review_agent.lifecycle import close_accepted_risk_issues, escalate_overdue_issues
from access_review_agent.narrative import synthesize_narrative
from access_review_agent.pdf_export import render_pdf
from access_review_agent.reports import (
    SYSTEM_DISPLAY,
    SYSTEM_LABEL,
    SYSTEM_ORDER,
    build_aggregate_report,
    build_monthly_report,
    build_per_system_report,
    summary_counts,
)
from access_review_agent.risk_assessment import build_risk_assessment_entries
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
    SystemDetectionUnit.detect_all() stays Tier-1-only and synchronous by
    design (ADR-0006's split point), so this async function is what adds
    Identity resolution's findings on top, not the unit itself. Cheap when
    there's nothing to resolve: find_unresolved_candidates() is plain
    Python and detect_identity_resolution() returns immediately with no
    Agent SDK call at all if it finds zero candidates - the eval fixtures
    every CI-wired milestone script runs against have none, so this
    doesn't turn any of those free/local suites into a paid one.

    Also runs Escalation/Accepted-Risk lifecycle checks (Milestone 9,
    ADR-0005) over EVERY currently-open Issue, unconditionally - never
    scoped to just `systems`. Escalation's same-day SLA timing shouldn't
    depend on which system happened to get a commit today, and this
    cross-system bookkeeping is what the main agent (the sole holder of
    GitHub write tools) is for, not something detection units do.

    `check_lifecycle=False` skips that pass entirely - list_issues is a
    real read that needs a valid token even against a private repo
    (unauthenticated reads 404, they don't just see less), unlike
    open_issue's write side, which dry-run mode already makes network-
    free. Milestones 1-5's eval suites run credential-free in CI by
    design; they pass False here since Milestone 9's lifecycle logic
    already has its own dedicated, credential-free test coverage
    (scripts/run_milestone9.py) and doesn't need re-exercising through
    every other milestone's detection tests too.

    Per-system failure isolation (SPEC.md §7's fail-loud completeness,
    Milestone 11): a malformed source file for one system (missing
    columns, same-file consistency mismatch, a missing file entirely)
    doesn't abort the whole run - that system's entry gets "failed" set
    to a loud, specific reason, and every other system still completes
    and reports normally. Only FileNotFoundError/ValueError are caught
    here (the two real "bad source data" exceptions read_and_validate
    raises) - anything else is a genuine bug, not a data problem, and
    should still crash loudly rather than being silently absorbed.

    Returns {"systems": {<system_name>: {detected, opened, rejected,
    failed}}, "lifecycle": {accepted_risk_closed, escalated} | None} -
    two clearly separate shapes under their own keys, not flattened
    together, so a caller iterating per-system results can't accidentally
    trip over the differently-shaped lifecycle entry.
    """
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
                "failed": str(e),
            }
            continue

        try:
            identity_result = await detect_identity_resolution(data_dir, system_name)
            findings = findings + identity_result["findings"]
        except Exception as e:
            # Deliberately broader than the FileNotFoundError/ValueError
            # catch above: Identity resolution's failure surface is a live
            # Agent SDK call, not just local file parsing, so a transient
            # network/API error is a realistic, non-"genuine bug" failure
            # mode here in a way it isn't for Tier 1 - and it shouldn't
            # crash the whole run any more than a malformed file does.
            # Isolated at the same system granularity Milestone 11 already
            # established, not partial-credited against the Tier 1
            # findings just computed above - same all-or-nothing-per-
            # system semantics as the block above, just a second cause.
            systems_results[system_name] = {
                "detected": 0,
                "opened": [],
                "rejected": [],
                "failed": f"Identity resolution failed: {e}",
            }
            continue

        opened: list[IssueResult] = []
        rejected: list[dict[str, Any]] = []
        for finding in findings:
            try:
                opened.append(open_issue(finding, repo_full_name, data_dir, commit_sha))
            except GroundingError as e:
                rejected.append({"finding": finding, "reason": str(e)})

        systems_results[system_name] = {
            "detected": len(findings),
            "opened": opened,
            "rejected": rejected,
            "failed": None,
        }

    lifecycle_results = None
    if check_lifecycle:
        adapter = get_adapter()
        all_issues = list_issues(repo_full_name)
        lifecycle_results = {
            "accepted_risk_closed": close_accepted_risk_issues(adapter, repo_full_name, all_issues),
            "escalated": escalate_overdue_issues(adapter, repo_full_name, all_issues),
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
    shared by generate_quarterly_reports (single-shot, no gate - manual/
    testing use) and create_quarterly_release (the real two-job,
    human-in-the-loop path, Milestone 11), so the two can't drift apart.
    `report_contents` must have all five system names plus "aggregate".
    """
    year, quarter = period.split("-Q")
    counts = summary_counts(all_issues)
    report_links = "\n".join(f"- [{SYSTEM_DISPLAY[s]}](reports/{period}/{s}.md)" for s in SYSTEM_ORDER)
    body = (
        f"{counts['total']} findings identified this quarter. {counts['remediated']} "
        f"remediated, {counts['open']} open, {counts['accepted_risk']} accepted as risk. "
        f"{counts['escalated']} escalation(s) this period.\n\n"
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

    Tags whatever commit `checkout_dir` is currently at - the caller
    (scripts/create_quarterly_release.py) resolves that via `git
    rev-parse HEAD` after its own checkout, since the workflow-trigger-
    time `github.sha` context value predates the report-generation job's
    commits and would tag the wrong commit.
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
    all six via commit_report — the sole caller of commit_report, same
    "main agent only" pattern as open_issue.

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

    aggregate_content = build_aggregate_report(
        period, per_system_issues, generated_at, risk_assessment_rows=risk_assessment_rows
    )
    report_contents["aggregate"] = aggregate_content
    results["aggregate"] = adapter.commit_report(
        repo_full_name,
        f"reports/{period}/aggregate.md",
        aggregate_content,
        f"Aggregate report: {period}",
    )

    return results
