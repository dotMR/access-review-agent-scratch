"""Milestone 4 eval runner: the isolation boundary, proven structurally.

Not a numbered eval-cases.md case — development-plan.md's Milestone 4
gate is explicit that this is "a registry-inspection test, not a
data-fixture one." Three checks, all against evals/cases/milestone4-all-
systems/ (one finding per system, five different categories):

1. Isolation by absence: each SystemDetectionUnit is run twice - once
   against the full five-system fixture, once against a data_dir holding
   *only* that unit's own access file plus HRIS (the other four systems'
   files aren't present at all). If a unit's code ever referenced another
   system's file, the isolated run would raise FileNotFoundError, not
   just "happen not to" read it - so identical success and identical
   findings in both runs is real evidence, not a coincidence.

2. Cross-contamination: every finding a unit produces is attributed to
   that unit's own system_name, never another's.

3. Full reconciliation: the orchestrator (the "main agent") runs all five
   units and opens an Issue - dry-run, no credentials - for every
   grounded finding, matching expected.json exactly.
"""

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "milestone4-all-systems"


def findings_set(findings: list[dict]) -> set[tuple]:
    return {(f["category"], f["system_name"], f["employee_id"]) for f in findings}


def isolated_data_dir(tmp_root: Path, system_name: str) -> Path:
    """A data_dir holding only `system_name`'s access file plus HRIS -
    every other system's access file is absent, not merely unused.
    """
    d = tmp_root / system_name
    d.mkdir()
    shutil.copy(FIXTURE_DIR / "system_hr.csv", d / "system_hr.csv")
    shutil.copy(FIXTURE_DIR / f"access_{system_name}.csv", d / f"access_{system_name}.csv")
    return d


def run_isolation_check() -> bool:
    from access_review_agent.units import SYSTEMS, SystemDetectionUnit

    expected = json.loads((FIXTURE_DIR / "expected.json").read_text())
    all_ok = True

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for system_name in SYSTEMS:
            full_findings = SystemDetectionUnit(system_name, FIXTURE_DIR).detect_all()

            iso_dir = isolated_data_dir(tmp_root, system_name)
            try:
                iso_findings = SystemDetectionUnit(system_name, iso_dir).detect_all()
            except Exception as e:
                print(f"[FAIL] isolation/{system_name} — detect_all() failed with only its own file present: {e}")
                all_ok = False
                continue

            if findings_set(full_findings) != findings_set(iso_findings):
                print(f"[FAIL] isolation/{system_name} — findings differ between full and isolated data_dir")
                print(f"         full:     {findings_set(full_findings)}")
                print(f"         isolated: {findings_set(iso_findings)}")
                all_ok = False
                continue

            expected_for_system = {
                (f["category"], f["system_name"], f["employee_id"])
                for f in expected["findings"]
                if f["system_name"] == system_name
            }
            if findings_set(full_findings) != expected_for_system:
                print(f"[FAIL] isolation/{system_name} — findings don't match expected.json")
                print(f"         expected: {expected_for_system}")
                print(f"         actual:   {findings_set(full_findings)}")
                all_ok = False
                continue

            print(
                f"[PASS] isolation/{system_name} — detect_all() identical with and "
                "without the other four systems' files present"
            )

    return all_ok


def run_cross_contamination_check() -> bool:
    from access_review_agent.units import SYSTEMS, SystemDetectionUnit

    all_ok = True
    for system_name in SYSTEMS:
        findings = SystemDetectionUnit(system_name, FIXTURE_DIR).detect_all()
        for f in findings:
            if f["system_name"] != system_name:
                print(
                    f"[FAIL] cross-contamination — {system_name}'s unit produced a "
                    f"finding for system_name={f['system_name']!r}"
                )
                all_ok = False

    status = "PASS" if all_ok else "FAIL"
    print(f"[{status}] cross-contamination — every unit's findings are attributed to its own system only")
    return all_ok


async def run_orchestrator_check() -> bool:
    from access_review_agent.orchestrator import run_full_reconciliation

    expected = json.loads((FIXTURE_DIR / "expected.json").read_text())
    expected_set = findings_set(expected["findings"])

    # check_lifecycle=False: this suite tests detection/orchestration
    # correctness, not lifecycle mechanics (Milestone 9's own
    # scripts/run_milestone9.py already covers those, credential-free).
    # list_issues is a real read that needs a valid token even against a
    # private repo - CI runs this suite with none, by design.
    results = await run_full_reconciliation(
        FIXTURE_DIR, "dotMR/access-review-agent-scratch", check_lifecycle=False
    )

    opened_set = set()
    total_rejected = 0
    for system_name, summary in results["systems"].items():
        for issue_result in summary["opened"]:
            # Recover (category, system_name, employee_id) from the title/labels
            # the same way an external reviewer would - not from internal state.
            category_label = next(l for l in issue_result.labels if l != system_name)
            employee_id = issue_result.body.split("employee_id=")[1].rstrip("`")
            opened_set.add((category_label, system_name, employee_id))
        total_rejected += len(summary["rejected"])

    problems = []
    if opened_set != expected_set:
        problems.append(f"opened Issues don't match expected.json: {opened_set} != {expected_set}")
    if total_rejected != 0:
        problems.append(f"{total_rejected} finding(s) were rejected by the grounding gate unexpectedly")

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] orchestrator — full five-system reconciliation opens exactly the expected Issues")
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        run_isolation_check(),
        run_cross_contamination_check(),
        await run_orchestrator_check(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
