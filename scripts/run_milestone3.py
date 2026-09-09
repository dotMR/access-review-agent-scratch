"""Milestone 3 eval runner: Tier 1 cases 4-16 (Dormant admin-level, Dormant
ad-hoc, Unapproved, Drift), graded automatically. Same pattern as
scripts/run_milestone1.py - pure Python, no model call (ADR-0006), every
claimed finding independently re-verified via grounding.validate_finding()
before being counted, not just pattern-matched against expected.json.

The two dormancy categories are threshold checks relative to "today," so
their fixtures pin an explicit `as_of` reference date in expected.json
rather than relying on date.today() - otherwise a 89/90/91-day boundary
case would silently start failing as real wall-clock time moves past the
date the fixture was authored on.

Also extends case 41 (Issue formatting, introduced in Milestone 2 for
Orphaned only) to the four categories this milestone adds - same dry-run,
no-credentials check as scripts/run_milestone2.py, just parameterized
over more categories now that issues.py knows how to format them.
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CASES = [
    "dormant-admin-clean-flag",
    "dormant-admin-boundary-no-flag",
    "dormant-admin-boundary-flag",
    "dormant-admin-exact-threshold-no-flag",
    "dormant-ad-hoc-clean-flag",
    "dormant-ad-hoc-boundary-no-flag",
    "dormant-ad-hoc-category-boundary-no-flag",
    "unapproved-clean-flag",
    "unapproved-clean-no-flag-auto",
    "unapproved-clean-no-flag-owner",
    "drift-clean-flag",
    "drift-clean-no-flag",
    "drift-category-boundary-no-flag",
]


def findings_set(findings: list[dict]) -> set[tuple]:
    return {(f["category"], f["system_name"], f["employee_id"]) for f in findings}


def run_case(case_name: str) -> bool:
    from access_review_agent.detection.dormant_admin import detect_dormant_admin
    from access_review_agent.detection.dormant_ad_hoc import detect_dormant_ad_hoc
    from access_review_agent.detection.drift import detect_drift
    from access_review_agent.detection.unapproved import detect_unapproved
    from access_review_agent.grounding import GroundingError, validate_finding

    case_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / case_name
    expected = json.loads((case_dir / "expected.json").read_text())

    if case_name.startswith("dormant-admin"):
        actual = detect_dormant_admin(case_dir, as_of=date.fromisoformat(expected["as_of"]))
    elif case_name.startswith("dormant-ad-hoc"):
        actual = detect_dormant_ad_hoc(case_dir, as_of=date.fromisoformat(expected["as_of"]))
    elif case_name.startswith("unapproved"):
        actual = detect_unapproved(case_dir)
    elif case_name.startswith("drift"):
        actual = detect_drift(case_dir)
    else:
        raise ValueError(f"Unrecognized case name (no detector mapped): {case_name}")

    claimed_findings = actual["findings"]

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


ISSUE_FORMAT_CASES = [
    "dormant-admin-clean-flag",
    "dormant-ad-hoc-clean-flag",
    "unapproved-clean-flag",
    "drift-clean-flag",
]


def run_issue_format_case(case_name: str) -> bool:
    """Case 41 (Issue formatting), one per category this milestone adds -
    dry-run only, no GitHub credentials, no network call.
    """
    from access_review_agent.detection.dormant_admin import detect_dormant_admin
    from access_review_agent.detection.dormant_ad_hoc import detect_dormant_ad_hoc
    from access_review_agent.detection.drift import detect_drift
    from access_review_agent.detection.unapproved import detect_unapproved
    from access_review_agent.github.issues import open_issue

    case_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / case_name
    expected = json.loads((case_dir / "expected_issue.json").read_text())
    expected_findings = json.loads((case_dir / "expected.json").read_text())
    as_of = date.fromisoformat(expected_findings["as_of"]) if "as_of" in expected_findings else None

    if case_name.startswith("dormant-admin"):
        findings = detect_dormant_admin(case_dir, as_of=as_of)["findings"]
    elif case_name.startswith("dormant-ad-hoc"):
        findings = detect_dormant_ad_hoc(case_dir, as_of=as_of)["findings"]
    elif case_name.startswith("unapproved"):
        findings = detect_unapproved(case_dir)["findings"]
    elif case_name.startswith("drift"):
        findings = detect_drift(case_dir)["findings"]
    else:
        raise ValueError(f"Unrecognized case name (no detector mapped): {case_name}")

    result = open_issue(findings[0], "dotMR/access-review-agent-scratch", case_dir)

    problems = []
    if result.title != expected["title"]:
        problems.append(f"title: expected {expected['title']!r}, got {result.title!r}")
    if sorted(result.labels) != sorted(expected["labels"]):
        problems.append(f"labels: expected {expected['labels']!r}, got {result.labels!r}")
    for required in expected["body_must_contain"]:
        if required not in result.body:
            problems.append(f"body missing required text: {required!r}")
    if not result.dry_run:
        problems.append("expected dry_run=True (GITHUB_WRITE_MODE unset in this runner)")

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] issue-format-{case_name} — {expected['description']}")
    for p in problems:
        print(f"         {p}")
    return not problems


def main() -> None:
    results = [run_case(case) for case in CASES]
    results += [run_issue_format_case(case) for case in ISSUE_FORMAT_CASES]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
