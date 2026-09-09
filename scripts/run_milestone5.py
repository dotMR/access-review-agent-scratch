"""Milestone 5 eval runner: Tier 3 cases 25-28 (dispatch), graded
automatically, dry-run only, no credentials.

Two things per case: the dispatch *decision* (determine_dispatch, a pure
function over changed-file paths - the same one the real
.github/workflows/production.yml calls), and, where the decision is
non-empty, that a dispatch-scoped orchestrator run genuinely only ever
touches the dispatched systems' data - reusing Milestone 4's isolation-by-
absence technique: case 25's single-system run executes against a data_dir
holding *only* AWS's access file plus HRIS, so "the other four systems'
data is untouched this run" (eval-cases.md's own wording for case 25) is
structural, not just an assertion about the returned results.
"""

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "milestone4-all-systems"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


def findings_set(findings: list[dict]) -> set[tuple]:
    return {(f["category"], f["system_name"], f["employee_id"]) for f in findings}


async def case_25_single_system_scope() -> bool:
    from access_review_agent.dispatch import determine_dispatch
    from access_review_agent.orchestrator import run_full_reconciliation

    dispatch = determine_dispatch(["data/access_aws.csv"])
    if dispatch != {"aws"}:
        print(f"[FAIL] case-25-single-system-scope — dispatch={dispatch}, expected {{'aws'}}")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        aws_only_dir = Path(tmp) / "aws-only"
        aws_only_dir.mkdir()
        shutil.copy(FIXTURE_DIR / "system_hr.csv", aws_only_dir / "system_hr.csv")
        shutil.copy(FIXTURE_DIR / "access_aws.csv", aws_only_dir / "access_aws.csv")

        try:
            # check_lifecycle=False - see the identical note in run_milestone4.py
            results = await run_full_reconciliation(
                aws_only_dir, SCRATCH_REPO, systems=dispatch, check_lifecycle=False
            )
        except Exception as e:
            print(f"[FAIL] case-25-single-system-scope — run failed with only AWS's file present: {e}")
            return False

    if set(results["systems"].keys()) != {"aws"}:
        print(
            f"[FAIL] case-25-single-system-scope — orchestrator touched "
            f"{set(results['systems'].keys())}, expected {{'aws'}}"
        )
        return False

    opened = {
        (next(l for l in r.labels if l != "aws"), "aws", r.body.split("employee_id=")[1].rstrip("`"))
        for r in results["systems"]["aws"]["opened"]
    }
    expected = {("orphaned", "aws", "E9001")}
    if opened != expected:
        print(f"[FAIL] case-25-single-system-scope — opened={opened}, expected {expected}")
        return False

    print(
        "[PASS] case-25-single-system-scope — a commit touching only access_aws.csv "
        "dispatches to AWS alone, and the run succeeds with the other four systems' "
        "files entirely absent"
    )
    return True


async def _all_systems_fan_out(case_name: str, changed_files: list[str]) -> bool:
    from access_review_agent.dispatch import determine_dispatch
    from access_review_agent.orchestrator import run_full_reconciliation
    from access_review_agent.units import SYSTEMS

    dispatch = determine_dispatch(changed_files)
    if dispatch != set(SYSTEMS):
        print(f"[FAIL] {case_name} — dispatch={dispatch}, expected all five: {set(SYSTEMS)}")
        return False

    expected = json.loads((FIXTURE_DIR / "expected.json").read_text())
    expected_set = findings_set(expected["findings"])

    # check_lifecycle=False - see the identical note in run_milestone4.py
    results = await run_full_reconciliation(FIXTURE_DIR, SCRATCH_REPO, systems=dispatch, check_lifecycle=False)
    opened = {
        (
            next(l for l in r.labels if l != system_name),
            system_name,
            r.body.split("employee_id=")[1].rstrip("`"),
        )
        for system_name, summary in results["systems"].items()
        for r in summary["opened"]
    }
    if opened != expected_set:
        print(f"[FAIL] {case_name} — opened={opened}, expected {expected_set}")
        return False

    print(f"[PASS] {case_name} — fans out to all five systems")
    return True


async def case_26_hris_fan_out() -> bool:
    return await _all_systems_fan_out("case-26-hris-fan-out", ["data/system_hr.csv"])


async def case_27_policy_fan_out() -> bool:
    ok1 = await _all_systems_fan_out("case-27-policy-fan-out (policy-config.yaml)", ["policy-config.yaml"])
    ok2 = await _all_systems_fan_out(
        "case-27-policy-fan-out (role-access-mapping.yaml)", ["role-access-mapping.yaml"]
    )
    return ok1 and ok2


def case_28_no_trigger() -> bool:
    from access_review_agent.dispatch import determine_dispatch

    dispatch = determine_dispatch(["access-control-policy.md"])
    status = "PASS" if dispatch == set() else "FAIL"
    print(f"[{status}] case-28-no-trigger — a commit touching only access-control-policy.md dispatches nothing")
    return dispatch == set()


async def main() -> None:
    results = [
        await case_25_single_system_scope(),
        await case_26_hris_fan_out(),
        await case_27_policy_fan_out(),
        case_28_no_trigger(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
