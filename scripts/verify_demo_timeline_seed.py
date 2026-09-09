"""Regression check for scripts/seed_demo_timeline.py: replays the full
step sequence into a throwaway git repo and asserts the Tier 1 detection
functions produce exactly the findings demo-timeline.md describes, at
both the Q1 checkpoint (five categories, no Drift yet, GitHub's dormant
thread not yet crossed) and the final Q3 state (seven findings, both
Orphaned instances already closed by their own same-run remediation).

Pure Python, no model call, no network - credential-free, matching
Milestones 1-5/9/10/11. Doesn't touch Identity resolution's LLM-resolved
outcome (that's Milestone 6's own eval suite's job) - only that the right
*candidates* reach that stage, which is deterministic.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed_demo_timeline.py"


def make_repo(tmp: Path, name: str, steps: list[str]) -> Path:
    target = tmp / name
    target.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=target, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=target, check=True)
    for step in steps:
        subprocess.run(
            [sys.executable, str(SEED_SCRIPT), "--step", step, "--target-dir", str(target)],
            check=True,
            capture_output=True,
        )
    return target / "data"


def check(label: str, actual: set[tuple[str, str]], expected: set[tuple[str, str]]) -> list[str]:
    problems = []
    if actual != expected:
        problems.append(f"{label}: expected {expected}, got {actual}")
    return problems


def case_q1_checkpoint(tmp: Path) -> bool:
    from access_review_agent.detection.dormant_admin import detect_dormant_admin
    from access_review_agent.detection.dormant_ad_hoc import detect_dormant_ad_hoc
    from access_review_agent.detection.drift import detect_drift
    from access_review_agent.detection.identity_resolution import find_unresolved_candidates
    from access_review_agent.detection.orphaned import detect_orphaned
    from access_review_agent.detection.unapproved import detect_unapproved

    data_dir = make_repo(tmp, "q1-repo", ["1", "2", "3", "4", "5", "6", "7", "8", "9"])
    systems = ["aws", "github", "salesforce", "finance_erp", "vpn"]

    problems = []
    problems += check(
        "Q1 Orphaned",
        {(s, f["employee_name"]) for s in systems for f in detect_orphaned(data_dir, s)["findings"]},
        {("aws", "Ronnis Pawgood")},
    )
    problems += check(
        "Q1 Dormant admin-level",
        {(s, f["employee_name"]) for s in systems for f in detect_dormant_admin(data_dir, s)["findings"]},
        {("finance_erp", "Dana Whitfield")},  # GitHub's thread hasn't crossed threshold yet
    )
    problems += check(
        "Q1 Dormant ad-hoc",
        {(s, f["employee_name"]) for s in systems for f in detect_dormant_ad_hoc(data_dir, s)["findings"]},
        {("salesforce", "Sleve McDichael")},
    )
    problems += check(
        "Q1 Unapproved",
        {(s, f["employee_name"]) for s in systems for f in detect_unapproved(data_dir, s)["findings"]},
        {("aws", "Mike Truk")},
    )
    problems += check(
        "Q1 Drift",
        {(s, f["employee_name"]) for s in systems for f in detect_drift(data_dir, s)["findings"]},
        set(),  # Karl's role change (commit 11) hasn't happened yet
    )
    problems += check(
        "Q1 Identity resolution candidates",
        {(s, c["employee_id"]) for s in systems for c in find_unresolved_candidates(data_dir, s)},
        {("github", "svc-cicd-deploy"), ("vpn", "kjack_vpn"), ("vpn", "vpn-legacy-4402")},
    )

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] q1-checkpoint — five categories with findings, Drift and GitHub's dormant thread both absent")
    for p in problems:
        print(f"         {p}")
    return not problems


def case_q3_final_state(tmp: Path) -> bool:
    from access_review_agent.detection.dormant_admin import detect_dormant_admin
    from access_review_agent.detection.dormant_ad_hoc import detect_dormant_ad_hoc
    from access_review_agent.detection.drift import detect_drift
    from access_review_agent.detection.identity_resolution import find_unresolved_candidates
    from access_review_agent.detection.orphaned import detect_orphaned
    from access_review_agent.detection.unapproved import detect_unapproved

    data_dir = make_repo(
        tmp, "q3-repo",
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "10b", "3b", "14", "14b"],
    )
    systems = ["aws", "github", "salesforce", "finance_erp", "vpn"]

    problems = []
    problems += check(
        "Q3 Orphaned",
        {(s, f["employee_name"]) for s in systems for f in detect_orphaned(data_dir, s)["findings"]},
        set(),  # both instances (commits 9, 14) already revoked same-run
    )
    problems += check(
        "Q3 Dormant admin-level",
        {(s, f["employee_name"]) for s in systems for f in detect_dormant_admin(data_dir, s)["findings"]},
        {("github", "Bobson Dugnutt"), ("finance_erp", "Dana Whitfield")},
    )
    problems += check(
        "Q3 Dormant ad-hoc",
        {(s, f["employee_name"]) for s in systems for f in detect_dormant_ad_hoc(data_dir, s)["findings"]},
        {("salesforce", "Sleve McDichael")},
    )
    problems += check(
        "Q3 Unapproved",
        {(s, f["employee_name"]) for s in systems for f in detect_unapproved(data_dir, s)["findings"]},
        {("aws", "Mike Truk")},  # Todd's VPN grant was corrected by step 10b
    )
    problems += check(
        "Q3 Drift",
        {(s, f["employee_name"]) for s in systems for f in detect_drift(data_dir, s)["findings"]},
        {("aws", "Karl Dandleton")},
    )
    problems += check(
        "Q3 Identity resolution candidates",
        {(s, c["employee_id"]) for s in systems for c in find_unresolved_candidates(data_dir, s)},
        {("github", "svc-cicd-deploy"), ("vpn", "kjack_vpn"), ("vpn", "vpn-legacy-4402")},
    )

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] q3-final-state — seven findings across five categories, both Orphaned instances closed")
    for p in problems:
        print(f"         {p}")
    return not problems


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        results = [case_q1_checkpoint(tmp), case_q3_final_state(tmp)]

    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
