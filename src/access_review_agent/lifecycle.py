"""Issue lifecycle mechanics: Escalation and Accepted Risk (SPEC.md §4,
ADR-0005, Milestone 9). Both act on already-open Issues via list_issues —
re-checking existing state, not detecting anything new (that's
detection/'s job). Run unconditionally across every open Issue on every
trigger (push or monthly), never scoped to just the systems a given push
touched — Escalation's same-day SLA timing shouldn't depend on which
system happened to get a commit today, and this cross-system bookkeeping
is exactly what the main agent (the sole holder of GitHub write tools,
SPEC.md §3) is for, not something detection units do.
"""

from datetime import date

from access_review_agent.github.adapter import GitHubAdapter, IssueInfo
from access_review_agent.reports import CATEGORY_DISPLAY, category_of
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
