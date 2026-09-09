"""Milestone 1 eval runner: the three Orphaned fixtures, graded automatically.

Pure Python, no model call - Orphaned is deterministic (eval-cases.md's
Tier 1, ADR-0006). Not the real eval harness yet (that's evals/cases/ in
full, later milestones) - this is the seed of it: run each fixture, diff
findings against expected.json, per SPEC.md's grading approach.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CASES = [
    "orphaned-clean-flag",
    "orphaned-clean-no-flag",
    "orphaned-contractor-scope-boundary",
]


def findings_set(findings: list[dict]) -> set[tuple]:
    return {
        (f["category"], f["system_name"], f["employee_id"])
        for f in findings
    }


def run_case(case_name: str) -> bool:
    from access_review_agent.detection.orphaned import detect_orphaned
    from access_review_agent.grounding import GroundingError, validate_finding

    case_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / case_name
    expected = json.loads((case_dir / "expected.json").read_text())

    actual = detect_orphaned(case_dir)
    claimed_findings = actual["findings"]

    # Grounding check: even deterministic code can have bugs. Independently
    # re-verifying every claimed finding against source data is cheap here
    # and applies uniformly whether a finding came from Python or a model.
    for finding in claimed_findings:
        try:
            validate_finding(finding, case_dir)
        except GroundingError as e:
            print(f"[FAIL] {case_name} — UNGROUNDED FINDING: {e}")
            return False

    expected_set = findings_set(expected["findings"])
    actual_set = findings_set(claimed_findings)

    passed = expected_set == actual_set
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {case_name} — {expected['description']}")
    if not passed:
        print(f"         expected: {expected_set}")
        print(f"         actual:   {actual_set}")
    return passed


def main() -> None:
    results = [run_case(case) for case in CASES]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
