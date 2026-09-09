"""Issue formatting and creation: SPEC.md §4's Issue format, gated by the
grounding guardrail.

open_issue() is the function Milestone 2 proved: a real Issue opens with
the correct title/body/labels, and an ungrounded finding does not open
one. A category is wired up here only once grounding.py has its own
validator for it - adding a new category means adding its grounding
check first, not the other way around (Milestone 3 added the four
Tier 1 categories that came after Orphaned; Identity resolution and
Drift's Tier 2 reasoning-based cousins are not in scope until
Milestone 6 onward).
"""

from pathlib import Path
from typing import Any

from access_review_agent.github.adapter import GitHubAdapter, IssueResult, get_adapter
from access_review_agent.grounding import validate_finding

CATEGORY_TITLES = {
    "orphaned": "Orphaned access",
    "dormant-admin": "Dormant admin-level access",
    "dormant-ad-hoc": "Dormant ad-hoc access",
    "unapproved": "Unapproved access",
    "drift": "Drift",
    "identity-resolution": "Identity resolution",
}

SYSTEM_DISPLAY_NAMES = {
    "aws": "AWS",
    "github": "GitHub",
    "salesforce": "Salesforce",
    "finance_erp": "Finance ERP",
    "vpn": "VPN",
}


def _as_literal(value: str) -> str:
    """Render a CSV/HRIS-sourced free-text value as an inert Markdown code
    span rather than resumed prose. GitHub's Issue body renderer parses
    @mentions, #issue-references, and every other bit of markdown syntax
    from ordinary text but not from inside a code span - the same
    protection the Source record line already relies on for the source
    filename and employee_id. Fields like access_level, approved_by, and
    role names are free text from external CSV data with no enforced
    enum on the raw cell value (only the mapped/looked-up side is
    validated), so a crafted value could otherwise trigger real
    notifications or cross-issue links when the Issue is opened. A
    literal backtick in the value itself would prematurely close the
    span, so any backticks in the value are neutralized first.
    """
    return f"`{value.replace('`', chr(0x27))}`"


def _format_title(finding: dict[str, Any]) -> str:
    category = finding["category"]
    system_name = finding["system_name"]
    identity = finding.get("employee_name") or finding["employee_id"]
    category_display = CATEGORY_TITLES.get(category, category)
    system_display = SYSTEM_DISPLAY_NAMES.get(system_name, system_name)
    return f"{category_display} — {identity} ({system_display})"


def _format_body(finding: dict[str, Any], repo_full_name: str, commit_sha: str | None) -> str:
    source = finding["source_record"]
    lines = [
        f"**Access detail:** {_as_literal(finding['access_level'])} access to {finding['system_name']}",
        f"**Expected per policy:** {finding['expected_per_policy']}",
    ]

    category = finding["category"]
    if category == "orphaned":
        lines.append(f"**Date detected:** {finding['date_detected']}")
        lines.append(
            "**Time to revoke:** same day as detection (Orphaned SLA — "
            "access-control-policy.md, Operational review)"
        )
    elif category in ("dormant-admin", "dormant-ad-hoc"):
        lines.append(f"**Last used:** {finding['last_used_date']}")
        lines.append(f"**Days dormant:** {finding['days_dormant']}")
    elif category == "unapproved":
        lines.append(f"**Date granted:** {finding['granted_date']}")
        approved_by = finding["approved_by"]
        lines.append(f"**Approved by:** {_as_literal(approved_by) if approved_by else 'none on file'}")
    elif category == "drift":
        for change in finding["role_change_history"]:
            lines.append(
                f"**Role change ({_as_literal(change['date'])}):** "
                f"{_as_literal(change['old_role'])} → {_as_literal(change['new_role'])}"
            )
    elif category == "identity-resolution":
        lines.append(f"**Date detected:** {finding['date_detected']}")
        lines.append(f"**Resolution outcome:** {_as_literal(finding['resolution_outcome'])}")
        lines.append(f"**Evidence:** {_as_literal(finding['evidence'])}")
        if finding.get("claimed_owner_employee_id"):
            lines.append(
                f"**Claimed owner (now terminated):** "
                f"{_as_literal(finding['claimed_owner_employee_id'])}"
            )

    if commit_sha:
        # data/ is production's fixed DATA_DIR convention (scripts/run_production.py) -
        # the only caller that ever supplies commit_sha, so this coupling is narrow
        # and documented rather than inferred. Eval/dry-run callers pass no SHA and
        # get the plain bare-filename citation instead, matching their data_dir
        # (evals/cases/<case>/, not data/) - a permalink there would point nowhere.
        blob_url = f"https://github.com/{repo_full_name}/blob/{commit_sha}/data/{source['file']}"
        lines.append(
            f"**Source record:** [`{source['file']}`]({blob_url}), row matching "
            f"`employee_id={source['employee_id']}`"
        )
    else:
        lines.append(
            f"**Source record:** `{source['file']}`, row matching "
            f"`employee_id={source['employee_id']}`"
        )
    return "\n\n".join(lines)


def _format_labels(finding: dict[str, Any]) -> list[str]:
    category_label = finding["category"]
    system_label = finding["system_name"].replace("_", "-")
    return [category_label, system_label]


def open_issue(
    finding: dict[str, Any],
    repo_full_name: str,
    data_dir: Path,
    commit_sha: str | None = None,
    skip_reopen_keys: set[tuple[str, str, str]] | None = None,
) -> IssueResult | None:
    """Validate `finding` against source data (the grounding gate), then
    open a GitHub Issue for it via the dry-run-capable adapter.

    `commit_sha`, when given, upgrades the Issue body's Source record
    citation from a bare file path to a clickable GitHub blob permalink
    (Milestone 5) - only the real production entrypoint ever has a real
    triggering commit SHA to supply; eval/dry-run callers leave it unset.

    `skip_reopen_keys`, when given, is the set of (category, system_name,
    employee_id) - the finding's own genuine unique key, not its
    rendered title - for every OPEN Issue plus every CLOSED
    accepted-risk Issue. A finding whose key is in this set returns None
    rather than opening a duplicate. Found live during Milestone 12's
    scratch-repo trial, in two stages:

    1. A push touching system_hr.csv/policy-config.yaml/role-access-
       mapping.yaml fans out to all five systems (dispatch.py) and
       re-detects every already-known, still-open finding right along
       with anything genuinely new - with nothing to recognize "already
       open," every such push duplicated every one of them, indefinitely.
    2. Open-only wasn't enough either: once a formally accepted-risk
       finding's Issue is closed (Milestone 9), the underlying condition
       is still genuinely detected every run (accepted risk isn't
       remediation - nothing about the data changed), and with only
       OPEN Issues checked, the very next run re-opened it as if brand
       new - directly contradicting iam-review-agent-design.md's
       Accepted Risk section ("No expiry in v1: the underlying condition
       is never periodically re-reviewed or re-surfaced once accepted").
       A REMEDIATED closure is deliberately excluded from this set - a
       fixed-then-later-recurring finding is a genuinely new instance of
       the problem, not something to suppress forever.

    Deliberately NOT keyed on the rendered title (SPEC.md §4's "{Category}
    — {identity} ({System})"), even though that's this system's usual
    display key: `identity` is employee_name, a human display name, not
    guaranteed unique the way employee_id is - two different employees
    sharing a name would collide on title, silently swallowing a second,
    genuinely distinct finding as "already reported." employee_id is
    HRIS's actual primary key, so it's what dedup keys on instead.

    None (the default) skips this check entirely - every caller before
    this fix, and every credential-free eval suite, behaves exactly as
    before; only run_full_reconciliation, which already has a real
    list_issues read whenever check_lifecycle=True, passes a real set.

    Raises GroundingError (from grounding.py) without opening anything if
    the finding doesn't hold up against data_dir's source records.
    """
    validate_finding(finding, data_dir)
    title = _format_title(finding)
    key = (finding["category"], finding["system_name"], finding["source_record"]["employee_id"])
    if skip_reopen_keys is not None and key in skip_reopen_keys:
        return None

    adapter: GitHubAdapter = get_adapter()
    return adapter.create_issue(
        repo_full_name=repo_full_name,
        title=title,
        body=_format_body(finding, repo_full_name, commit_sha),
        labels=_format_labels(finding),
    )
