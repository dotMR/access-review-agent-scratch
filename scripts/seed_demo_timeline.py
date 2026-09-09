"""Milestone 12 seeding/scenario-generation tool (iam-review-agent-design.md,
"Demo timeline"; concrete sequence in demo-timeline.md).

Produces demo-timeline.md's 14 numbered data commits against a real target
repo checkout's `data/` directory (SPEC.md §2's DATA_DIR default), one git
commit per step, in order. Distinct from both the eval fixtures (which
exist to fail on purpose, isolating one behavior each) and this repo's own
source - this is a separate demo *data* repo's history.

**Why some steps aren't just "commit N's own data change".** Three of
demo-timeline.md's narrative beats depend on a threshold being crossed by
elapsed time (GitHub's dormant-admin thread going quiet for "months",
Todd's VPN approval being corrected "before Q2's audit", Cecilia Tisio's
own AWS access being revoked "within the same-day SLA" right after her
termination) - but every detection function's `as_of` defaults to real
`date.today()` (dormant_admin.py, dormant_ad_hoc.py), and this tool has no
way to make real calendar time pass between two git commits made minutes
apart. The resolution, already established practice everywhere else in
this codebase (every eval fixture with a "185 days dormant" record):
pre-age the DATA field (`last_used_date`) to already be past-threshold at
the moment detection is meant to catch it, rather than waiting for real
elapsed time. That's a property of the CSV content, not of git commit
timestamps - "Git commits...get their real dates, whenever they're
actually made" (demo-timeline.md) is a promise about commit metadata, not
about how old a `last_used_date` value is allowed to already be, and
commits 1 and 2 already rely on exactly this (records "already past
threshold", "idle since well before day 0"). So the three auxiliary
steps below (3b, 10b, 14b) are real, separate data-changing commits, not
folded into their parent commit's own step - each is its own honest git
commit, dated whenever it's actually made, same as the 14 numbered ones.

**What this tool does NOT do**, because they aren't data changes: the SLA
escalation check (commit 9's follow-up), the monthly/quarterly workflow
triggers, and commit 13's accepted-risk labeling (a human GitHub Issue
action, deliberately - see CONTEXT.md, Accepted Risk) are all real-run
orchestration, not something a seeding tool should fabricate. `--list`
shows where each belongs in the sequence; `--step` on one of them prints
what to actually run instead of writing data.
"""

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

ACCESS_COLUMNS = [
    "employee_id",
    "system_name",
    "access_level",
    "granted_date",
    "approved_by",
    "last_used_date",
    "status",
    "provisioning_note",
]
HR_COLUMNS = ["employee_id", "name", "role", "start_date", "end_date", "status", "role_change_history"]
SYSTEMS = ["aws", "github", "salesforce", "finance_erp", "vpn"]

AUTO_APPROVED = "auto (granted per role policy)"


@dataclass
class State:
    hr: dict[str, dict[str, str]] = field(default_factory=dict)
    access: dict[str, dict[str, dict[str, str]]] = field(
        default_factory=lambda: {s: {} for s in SYSTEMS}
    )

    def set_hr(self, employee_id, **fields):
        row = self.hr.setdefault(
            employee_id,
            {"employee_id": employee_id, "end_date": "", "status": "active", "role_change_history": "[]"},
        )
        row.update(fields)

    def set_access(self, system, local_id, **fields):
        row = self.access[system].setdefault(
            local_id,
            {"employee_id": local_id, "system_name": system, "approved_by": "", "provisioning_note": ""},
        )
        row.update(fields)


def hire_baseline(state: State, employee_id: str, name: str, role: str, start_date: str, grants: dict) -> None:
    """A clean, fully-baseline hire: one row per system in `grants`
    ({system: (access_level, last_used_date)}), all auto-approved - the
    "happy path" every commit-1/commit-6 employee needs, distinct from
    the deliberately-planted violation each commit also seeds.
    """
    state.set_hr(employee_id, name=name, role=role, start_date=start_date)
    for system, (level, last_used) in grants.items():
        state.set_access(
            system,
            employee_id,
            access_level=level,
            granted_date=start_date,
            approved_by=AUTO_APPROVED,
            last_used_date=last_used,
            status="active",
        )


# ---------------------------------------------------------------------------
# Pre-Q1 / Day 0
# ---------------------------------------------------------------------------


def step_01(state: State, today: date) -> str:
    """Commit 1 - Seed baseline: several employees, clean baseline access,
    plus Dana Whitfield's pre-aged Dormant admin-level Finance ERP record
    (Critical criticality, admin-level, idle since well before day 0).
    """
    # Single-system personal access only, deliberately - commit 14 later
    # revokes exactly "their own access" (singular) same-day via step_14b;
    # a second system's grant would silently survive that revocation and
    # produce an unintended second Orphaned finding.
    hire_baseline(state, "E9301", "Cecilia Tisio", "Software Engineer", "2023-02-01",
                  {"aws": ("write", today.isoformat())})
    hire_baseline(state, "E9302", "Kelly Jack", "Software Engineer", "2023-03-14",
                  {"aws": ("write", today.isoformat())})
    hire_baseline(state, "E9304", "Bobson Dugnutt", "Engineering Manager", "2022-11-01",
                  {"aws": ("write", today.isoformat())})
    hire_baseline(state, "E9306", "Ronnis Pawgood", "Software Engineer", "2021-08-09",
                  {"aws": ("write", today.isoformat())})
    hire_baseline(state, "E9308", "Mike Truk", "Sales Rep", "2022-05-19",
                  {"salesforce": ("write", today.isoformat())})
    hire_baseline(state, "E9309", "Karl Dandleton", "Software Engineer", "2021-01-11",
                  {"aws": ("write", today.isoformat())})

    dormant_since = (today - timedelta(days=140)).isoformat()
    state.set_hr("E9305", name="Dana Whitfield", role="Finance Analyst", start_date="2020-06-15")
    state.set_access(
        "finance_erp", "E9305", access_level="admin", granted_date="2020-09-01",
        approved_by="Asset Owner: E9304 (Bobson Dugnutt)", last_used_date=dormant_since, status="active",
    )
    return "Seed baseline: several employees, clean access, plus one pre-aged Dormant admin-level record (Finance ERP)"


def step_02(state: State, today: date) -> str:
    """Commit 2 - Sleve McDichael's pre-aged Dormant ad-hoc Salesforce
    record (their baseline is none - individually approved, idle since
    well before day 0, past the 180-day threshold).
    """
    state.set_hr("E9303", name="Sleve McDichael", role="Engineering Manager", start_date="2022-01-10")
    dormant_since = (today - timedelta(days=210)).isoformat()
    state.set_access(
        "salesforce", "E9303", access_level="read", granted_date="2022-02-01",
        approved_by="Asset Owner: cross-functional project grant", last_used_date=dormant_since, status="active",
    )
    return "Seed a pre-aged Dormant ad-hoc access record (Salesforce) - Sleve McDichael"


def step_03(state: State, today: date) -> str:
    """Commit 3 - Bobson Dugnutt's baseline GitHub admin grant, currently
    compliant (legitimate, recently used as of day 0). No finding yet -
    the setup half of the quiet-system scenario; step 3b ages this past
    the dormant-admin threshold once the mid-Q2 monthly beat needs it.
    """
    state.set_access(
        "github", "E9304", access_level="admin", granted_date=today.isoformat(),
        approved_by=AUTO_APPROVED, last_used_date=today.isoformat(), status="active",
    )
    return "Seed a GitHub admin-level grant, currently compliant - Bobson Dugnutt"


def step_04(state: State, today: date) -> str:
    """Commit 4 - Clean Identity resolution case (stale-ownership happy
    path): a CI/CD service account naming Cecilia Tisio as accountable
    owner, currently active. No finding - resolves to a documented
    non-individual exception. This is the record commit 14 reactivates.
    """
    state.set_access(
        "github", "svc-cicd-deploy", access_level="write", granted_date="2025-11-02",
        approved_by=AUTO_APPROVED, last_used_date=today.isoformat(), status="active",
        provisioning_note=(
            "Provisioned for CI/CD pipeline automation, 2025-11-02. Accountable owner: "
            "Cecilia Tisio (Platform Engineering), contact for renewal or decommission."
        ),
    )
    return "Seed a clean Identity resolution case (stale-ownership, happy path) - svc-cicd-deploy"


def step_05(state: State, today: date) -> str:
    """Commit 5 - SSO-gap Identity resolution case (name-similarity,
    happy path): a VPN record under a local identifier not matching any
    HRIS employee_id, resolving via name similarity to Kelly Jack.
    """
    state.set_access(
        "vpn", "kjack_vpn", access_level="granted", granted_date="2024-07-22",
        approved_by="IT Helpdesk (ticket #4821)", last_used_date=today.isoformat(), status="active",
        provisioning_note="VPN access requested by K. Jack, IT ticket #4821.",
    )
    return "Seed an SSO-gap Identity resolution case (name-similarity, happy path) - kjack_vpn"


# ---------------------------------------------------------------------------
# Q1 2026
# ---------------------------------------------------------------------------


def step_06(state: State, today: date) -> str:
    """Commit 6 - Hire. Willie Dustice joins, baseline access auto-granted
    across systems. Clean event, no finding - the happy path works too.
    """
    hire_baseline(
        state, "E9307", "Willie Dustice", "Software Engineer", today.isoformat(),
        {"aws": ("write", today.isoformat()), "github": ("write", today.isoformat()),
         "vpn": ("granted", today.isoformat())},
    )
    return "Hire: Willie Dustice, baseline access auto-granted"


def step_07(state: State, today: date) -> str:
    """Commit 7 - Ad-hoc access, unapproved (AWS, write-level). Mike Truk
    (Sales Rep, AWS baseline none) granted AWS write with approved_by left
    null. The instance that persists as a recurring signal into Q2/Q3.
    """
    state.set_access(
        "aws", "E9308", access_level="write", granted_date=today.isoformat(),
        approved_by="", last_used_date=today.isoformat(), status="active",
    )
    return "Ad-hoc access, unapproved (AWS, write-level) - Mike Truk"


def step_08(state: State, today: date) -> str:
    """Commit 8 - Identity resolution, unresolved case. A leftover VPN
    access record matching no HR record, no provisioning_note at all -
    correctly resolves to unresolved rather than a guess.
    """
    state.set_access(
        "vpn", "vpn-legacy-4402", access_level="granted", granted_date="2019-04-30",
        approved_by="legacy grant, pre-dates current approval process",
        last_used_date=today.isoformat(), status="active", provisioning_note="",
    )
    return "Identity resolution, unresolved case - vpn-legacy-4402 (no HR match, no provisioning note)"


def step_09(state: State, today: date) -> str:
    """Commit 9 - Termination. Ronnis Pawgood leaves; AWS access not yet
    revoked. Sets up Orphaned access - the same-day SLA miss and
    Escalation are a live re-check afterward, not this commit itself
    (see the "9-sla-check" checkpoint).
    """
    state.set_hr("E9306", status="terminated", end_date=today.isoformat())
    return "Termination: Ronnis Pawgood leaves, AWS access not yet revoked"


# ---------------------------------------------------------------------------
# Q2 2026
# ---------------------------------------------------------------------------


def step_10(state: State, today: date) -> str:
    """Commit 10 - Isolated, low-risk Unapproved access (VPN). A one-off
    ad-hoc-feeling VPN grant for Todd Bonzalez, approved_by left null;
    corrected before Q2's audit by step 10b, never carrying into a second
    audit - the Risk Assessment contrast case (Likelihood=Low, Impact=Low
    on Low-criticality VPN).
    """
    state.set_hr("E9310", name="Todd Bonzalez", role="Sales Rep", start_date=today.isoformat())
    state.set_access(
        "vpn", "E9310", access_level="granted", granted_date=today.isoformat(),
        approved_by="", last_used_date=today.isoformat(), status="active",
    )
    return "Isolated, low-risk Unapproved access (VPN) - Todd Bonzalez"


def step_10b(state: State, today: date) -> str:
    """Auxiliary (not one of the 14): the Asset Owner corrects Todd's
    missing VPN approval before Q2's audit runs, per demo-timeline.md's
    commit 10 note - a real, separate data-changing commit, not folded
    into commit 10 itself, since the correction happens later in the
    quarter, not at the moment of the original grant.
    """
    state.set_access("vpn", "E9310", approved_by="Asset Owner: E9304 (Bobson Dugnutt)")
    return "Correct Todd Bonzalez's missing VPN approval (remediated within Q2, before the quarterly audit)"


def step_11(state: State, today: date) -> str:
    """Commit 11 - Role change (mover). Karl Dandleton: Software Engineer
    -> Asset Owner; AWS access stays at the old baseline (write), now
    mismatching the new role's baseline (admin). Feeds Drift-Evidentiary.
    """
    state.set_hr(
        "E9309", role="Asset Owner",
        role_change_history=json.dumps(
            [{"date": today.isoformat(), "old_role": "Software Engineer", "new_role": "Asset Owner"}]
        ),
    )
    return "Role change (mover): Karl Dandleton, Software Engineer -> Asset Owner"


def step_12(state: State, today: date) -> str:
    """Commit 12 - Remediation. Asset Owner revokes Ronnis Pawgood's Q1
    orphaned AWS access, acting alone (Orphaned itself never
    re-escalates once Unremediated findings already fired).
    """
    state.set_access("aws", "E9306", status="revoked")
    return "Remediation: Ronnis Pawgood's orphaned AWS access revoked"


def step_14b(state: State, today: date) -> str:
    """Auxiliary, run right after commit 14 (see below): Cecilia Tisio's
    own AWS access revoked within the same-day SLA - a deliberate
    contrast with Q1's missed SLA, meant to be applied the same day
    commit 14 lands, before the next SLA re-check run.
    """
    state.set_access("aws", "E9301", status="revoked")
    return "Remediation: Cecilia Tisio's own AWS access revoked same-day (SLA met, contrast with Q1)"


def step_13_note() -> str:
    return (
        "Commit 13 is a human GitHub Issue action, not a data commit - the "
        "Reviewer labels the Q1 Identity-resolution Issue (from commit 8) "
        "accepted-risk with a justification comment. Run for real once that "
        "Issue's number is known:\n"
        "  gh issue edit <issue-number> --add-label accepted-risk --repo <repo>\n"
        '  gh issue comment <issue-number> --repo <repo> --body '
        '"Investigated by hand: this is a legitimate documented shared '
        'account. Evidence exists outside the system and wasn\'t available '
        'to the agent. Accepted as risk, not remediated."'
    )


# ---------------------------------------------------------------------------
# Q3 2026
# ---------------------------------------------------------------------------


def step_03b(state: State, today: date) -> str:
    """Auxiliary: age Bobson Dugnutt's GitHub admin grant (commit 3) past
    the 90-day dormant-admin threshold for the mid-Q2 monthly beat - no
    further GitHub commits occur on their own, so nothing push-triggered
    would catch this; only the monthly cadence's own full-detection run
    does (ADR-0003).
    """
    state.set_access("github", "E9304", last_used_date=(today - timedelta(days=95)).isoformat())
    return "Age Bobson Dugnutt's GitHub admin grant past the Dormant admin-level threshold (mid-Q2 monthly beat)"


def step_14(state: State, today: date) -> str:
    """Commit 14 - Second termination, doubling as the sharpest Identity
    resolution case. Cecilia Tisio (the documented owner of commit 4's
    service account) leaves. Nothing on the service-account record
    itself changes - only re-validating her current HR status on this
    run surfaces the newly-stale ownership. Her own AWS access is
    revoked same-day by step_14b, a deliberate contrast with Q1's miss.
    """
    state.set_hr("E9301", status="terminated", end_date=today.isoformat())
    return "Second termination: Cecilia Tisio leaves (also the owner of record from commit 4)"


# ---------------------------------------------------------------------------
# The full sequence
# ---------------------------------------------------------------------------


@dataclass
class Step:
    id: str
    title: str
    kind: str  # "data" | "checkpoint" | "manual"
    fn: Callable[[State, date], str] | None = None


STEPS: list[Step] = [
    Step("1", "Seed baseline + Dana Whitfield's pre-aged Dormant admin-level (Finance ERP)", "data", step_01),
    Step("2", "Seed Sleve McDichael's pre-aged Dormant ad-hoc (Salesforce)", "data", step_02),
    Step("3", "Seed Bobson Dugnutt's compliant GitHub admin grant", "data", step_03),
    Step("4", "Seed clean Identity resolution: svc-cicd-deploy (stale-ownership happy path)", "data", step_04),
    Step("5", "Seed clean Identity resolution: kjack_vpn (SSO-gap happy path)", "data", step_05),
    Step("q1-push-1", "Trigger production workflow (push touching data/) to run detection on steps 1-5", "checkpoint"),
    Step("6", "Hire: Willie Dustice", "data", step_06),
    Step("7", "Ad-hoc unapproved AWS access: Mike Truk", "data", step_07),
    Step("8", "Identity resolution unresolved: vpn-legacy-4402", "data", step_08),
    Step("9", "Termination: Ronnis Pawgood (sets up Orphaned)", "data", step_09),
    Step("q1-push-2", "Trigger production workflow to run detection on steps 6-9 (opens Issues #6-9-ish)", "checkpoint"),
    Step("9-sla-check", "Re-run production/lifecycle check after same-day SLA passes - escalates the Orphaned Issue", "checkpoint"),
    Step("q1-quarterly", "Trigger quarterly-audit.yml, period=2026-Q1 (approve the create-release gate)", "checkpoint"),
    Step("10", "Isolated low-risk Unapproved (VPN): Todd Bonzalez", "data", step_10),
    Step("11", "Role change (mover): Karl Dandleton, Software Engineer -> Asset Owner (Drift)", "data", step_11),
    Step("12", "Remediation: Ronnis Pawgood's orphaned AWS access revoked", "data", step_12),
    Step("10b", "[auxiliary] Correct Todd Bonzalez's VPN approval before Q2's audit", "data", step_10b),
    Step("3b", "[auxiliary] Age Bobson Dugnutt's GitHub grant past the Dormant admin-level threshold", "data", step_03b),
    Step("q2-push", "Trigger production workflow to run detection on steps 10-12 + 10b", "checkpoint"),
    Step("q2-monthly", "Trigger monthly-report.yml, period=2026-05 - catches GitHub's dormant admin (step 3b)", "checkpoint"),
    Step("13", "Accepted risk: label the Q1 Identity-resolution Issue (from commit 8) - human action", "manual"),
    Step("q2-quarterly", "Trigger quarterly-audit.yml, period=2026-Q2 (approve the create-release gate)", "checkpoint"),
    Step("14", "Second termination: Cecilia Tisio (sharpest Identity resolution case)", "data", step_14),
    Step("14b", "[auxiliary] Revoke Cecilia Tisio's own AWS access same-day (SLA met, contrast with Q1)", "data", step_14b),
    Step("q3-push", "Trigger production workflow to run detection on step 14 + 14b", "checkpoint"),
    Step("q3-quarterly", "Trigger quarterly-audit.yml, period=2026-Q3 (approve the create-release gate)", "checkpoint"),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def replay(upto: str) -> tuple[State, date]:
    """Rebuild state by replaying every data step up to and including
    `upto`, in order - deterministic, no state file needed since there
    are only ~20 steps total. `today` is captured once per replay so an
    --upto run applies every step "as of" the same moment.
    """
    today = date.today()
    state = State()
    for step in STEPS:
        if step.kind == "data":
            step.fn(state, today)
        if step.id == upto:
            break
    else:
        raise ValueError(f"Unknown step id: {upto!r}")
    return state, today


MARKER_FILE = ".demo-timeline-seed"


def check_target_is_safe(target_dir: Path, force: bool) -> None:
    """Refuse to overwrite a data/ directory this tool didn't create -
    write_csvs() opens every file in "w" mode (full overwrite) and
    git_commit() immediately commits, with no confirmation prompt in
    between. Today that's harmless (this repo has no data/ directory
    yet - no live data), but a mistyped --target-dir pointed at the real
    checkout instead of a scratch/demo one would otherwise silently
    destroy and commit over real access data once production is live.
    The marker file records that THIS tool already owns target_dir;
    --force is an explicit, deliberate opt-out, not the default.
    """
    if force:
        return
    marker = target_dir / MARKER_FILE
    data_dir = target_dir / "data"
    if data_dir.exists() and not marker.exists():
        raise SystemExit(
            f"Refusing to write: {data_dir} already exists and wasn't created by this "
            f"tool (no {MARKER_FILE} marker found). If this is genuinely the intended "
            "demo/scratch repo, pass --force."
        )
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()


def write_csvs(state: State, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "system_hr.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HR_COLUMNS)
        writer.writeheader()
        for row in state.hr.values():
            writer.writerow(row)
    for system in SYSTEMS:
        with (data_dir / f"access_{system}.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ACCESS_COLUMNS)
            writer.writeheader()
            for row in state.access[system].values():
                writer.writerow(row)


def git_commit(target_dir: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(target_dir), "add", "data"], check=True)
    subprocess.run(["git", "-C", str(target_dir), "commit", "-m", message], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print the full step sequence and exit")
    parser.add_argument("--step", help="Apply exactly this step id")
    parser.add_argument("--target-dir", type=Path, help="Demo data repo checkout root")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, don't write or commit")
    parser.add_argument(
        "--force", action="store_true",
        help="Skip the check that target-dir's data/ was created by this tool (see check_target_is_safe)",
    )
    args = parser.parse_args()

    if args.list:
        for step in STEPS:
            print(f"[{step.kind:>10}] {step.id:<12} {step.title}")
        return

    if not args.step:
        parser.error("--step is required (or use --list)")

    matches = [s for s in STEPS if s.id == args.step]
    if not matches:
        parser.error(f"Unknown step id: {args.step!r} (see --list)")
    target = matches[0]

    if target.kind == "checkpoint":
        print(f"[checkpoint] {target.title}")
        print("Nothing to seed here - this is a real workflow trigger, not a data commit.")
        return

    if target.kind == "manual":
        print(step_13_note())
        return

    if not args.target_dir:
        parser.error("--target-dir is required for a data step")

    state, today = replay(args.step)
    message = f"[demo-timeline] {args.step}: {target.title}"

    if args.dry_run:
        print(f"Would write data/ under {args.target_dir} and commit:\n  {message}")
        print(f"HR records: {len(state.hr)}")
        for system in SYSTEMS:
            print(f"  {system}: {len(state.access[system])} access record(s)")
        return

    check_target_is_safe(args.target_dir, args.force)
    write_csvs(state, args.target_dir / "data")
    git_commit(args.target_dir, message)
    print(f"Committed: {message}")


if __name__ == "__main__":
    main()
