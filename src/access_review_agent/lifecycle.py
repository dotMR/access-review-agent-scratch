"""Issue lifecycle mechanics: Escalation, Accepted Risk, and Remediation
re-check (SPEC.md §4/§8, ADR-0005, Milestones 9 and 12).

Escalation and Accepted Risk both act on already-open Issues via
list_issues alone - re-checking existing Issue state (labels, dates),
not detecting anything new. Run unconditionally across every open Issue
on every trigger (push or monthly), never scoped to just the systems a
given push touched - Escalation's same-day SLA timing shouldn't depend
on which system happened to get a commit today, and this cross-system
bookkeeping is exactly what the main agent (the sole holder of GitHub
write tools, SPEC.md §3) is for, not something detection units do.

Remediation re-check (close_remediated_issues) is different in kind: it
needs to know whether a finding is STILL true, which only this run's own
fresh detection for that one system can answer - unlike the other two,
it's necessarily scoped to one system per call, using that system's own
just-computed findings, not list_issues alone.
"""

from datetime import date
from typing import Any

from access_review_agent.github.adapter import GitHubAdapter, IssueInfo
from access_review_agent.reports import CATEGORY_DISPLAY, category_of, source_employee_id, system_of
from access_review_agent.tools.policy import DEFAULT_POLICY_CONFIG_PATH, read_policy


def close_accepted_risk_issues(
    adapter: GitHubAdapter, repo_full_name: str, issues: list[IssueInfo]
) -> list[int]:
    """Close every open Issue carrying the accepted-risk label. The label
    is what distinguishes "fixed" from "formally accepted as an
    acceptable risk" on an otherwise identical closed state
    (CONTEXT.md, ADR-0005) — closing is a mechanical consequence of a
    human applying the label, not something the agent decides.
    """
    closed = []
    for issue in issues:
        if issue.state == "open" and "accepted-risk" in issue.labels:
            adapter.close_issue(repo_full_name, issue.number)
            closed.append(issue.number)
    return closed


def escalate_overdue_issues(
    adapter: GitHubAdapter,
    repo_full_name: str,
    issues: list[IssueInfo],
    as_of: date | None = None,
) -> list[int]:
    """Escalate every open Issue whose category has its own Operational-
    cadence SLA (policy-config.yaml's escalation section — only Orphaned
    has one in v1, access-control-policy.md's Unremediated findings
    Principle) and isn't already escalated. Fires at most once per
    Finding: an Issue already carrying the escalated label is skipped
    unconditionally, never re-escalated or re-commented.
    """
    as_of = as_of or date.today()
    sla_config = read_policy(DEFAULT_POLICY_CONFIG_PATH)["escalation"]

    escalated = []
    for issue in issues:
        if issue.state != "open" or "escalated" in issue.labels:
            continue
        category = category_of(issue)
        if category is None:
            continue
        sla_key = f"{category.replace('-', '_')}_sla_days"
        if sla_key not in sla_config:
            continue  # this category has no Operational cadence to escalate against

        created = date.fromisoformat(issue.created_at[:10])
        days_open = (as_of - created).days
        sla_days = sla_config[sla_key]
        if days_open <= sla_days:
            continue

        adapter.apply_label(repo_full_name, issue.number, "escalated")
        adapter.add_comment(
            repo_full_name,
            issue.number,
            f"**Escalated:** the same-day SLA for {CATEGORY_DISPLAY[category]} was missed "
            f"(opened {created.isoformat()}, still open {days_open} day(s) later) — per "
            "access-control-policy.md's Unremediated findings Principle.",
        )
        escalated.append(issue.number)
    return escalated


def close_remediated_issues(
    adapter: GitHubAdapter,
    repo_full_name: str,
    system_name: str,
    current_findings: list[dict[str, Any]],
    open_issues: list[IssueInfo],
) -> list[int]:
    """Close every open Issue for `system_name` whose finding is no longer
    present in `current_findings` - iam-review-agent-design.md's "Closing
    the loop" section, SPEC.md §8's "remediation re-check/auto-close":
    "each run compares currently-open findings/Issues against the current
    data; anything no longer present...gets its Issue closed with a note,
    not left dangling." A real, previously-missing capability - found live
    during Milestone 12's scratch-repo trial (an Orphaned Issue stayed
    open after the underlying access was genuinely revoked in the data),
    not designed in speculatively; SPEC.md §8 already listed this as v1
    Core scope, Milestone 9 built Escalation and Accepted Risk but never
    this third lifecycle mechanic.

    Deliberately scoped to one system per call, using that system's own
    just-computed `current_findings` - unlike close_accepted_risk_issues/
    escalate_overdue_issues above, this needs to know whether a finding
    is STILL true, which only fresh detection for that one system can
    answer, not Issue metadata alone. Call once per system inside the
    same per-system loop that already computed `current_findings`, not
    unconditionally across every system regardless of push scope.

    Skips any Issue carrying the accepted-risk label unconditionally -
    that's close_accepted_risk_issues' exclusive path (a human decision,
    not a re-detection outcome); closing it here too, with a "remediated"
    comment, would misrepresent why it's actually closed.
    """
    current_keys = {
        (f["category"], f["system_name"], f["source_record"]["employee_id"]) for f in current_findings
    }
    closed = []
    for issue in open_issues:
        if issue.state != "open" or "accepted-risk" in issue.labels:
            continue
        category = category_of(issue)
        employee_id = source_employee_id(issue)
        if category is None or system_of(issue) != system_name or employee_id is None:
            continue
        if (category, system_name, employee_id) in current_keys:
            continue  # still an open finding this run - not remediated

        adapter.close_issue(repo_full_name, issue.number)
        adapter.add_comment(
            repo_full_name,
            issue.number,
            f"**Remediated:** {CATEGORY_DISPLAY[category]} is no longer present as of this "
            "run's detection pass — closing automatically.",
        )
        closed.append(issue.number)
    return closed
