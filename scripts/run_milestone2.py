"""Milestone 2 eval runner: open_issue's format correctness and its
grounding gate, both exercised in dry-run mode — no GitHub credentials,
no network call, no cost. Real-mode writing was verified once by hand
against the scratch repo (see docs/adr/0007-local-vs-remote-dry-run-adapter.md);
this script is the repeatable, CI-safe check that runs on every PR.

Covers:
- eval-cases.md Tier 3 case 41 (Issue formatting): a grounded finding
  produces the exact title/labels SPEC.md §4 specifies, and a body
  containing every required field.
- eval-cases.md Tier 3 case 37 (Grounding/citation), routed through
  open_issue() itself rather than validate_finding() in isolation, which
  is what "rejected before becoming an Issue" actually describes.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def case_issue_format() -> bool:
    """Case 41: a grounded finding's dry-run Issue matches SPEC.md §4."""
    from access_review_agent.detection.orphaned import detect_orphaned
    from access_review_agent.github.issues import open_issue

    case_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / "orphaned-clean-flag"
    expected = json.loads((case_dir / "expected_issue.json").read_text())

    findings = detect_orphaned(case_dir)["findings"]
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
    print(f"[{status}] issue-format-orphaned — {expected['description']}")
    for p in problems:
        print(f"         {p}")
    return not problems


def case_grounding_gate_blocks_open_issue() -> bool:
    """Case 37 (via open_issue): an ungrounded finding is rejected before
    it ever reaches the adapter — no Issue, dry-run or otherwise.
    """
    from access_review_agent.github.issues import open_issue
    from access_review_agent.grounding import GroundingError

    case_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / "orphaned-clean-flag"
    ungrounded_finding = {
        "category": "orphaned",
        "system_name": "aws",
        "employee_id": "E9999-DOES-NOT-EXIST",
        "employee_name": "Nobody Real",
        "access_level": "admin",
        "expected_per_policy": "None (terminated 2026-01-01)",
        "date_detected": "2026-09-08",
        "source_record": {"file": "access_aws.csv", "employee_id": "E9999-DOES-NOT-EXIST"},
    }

    try:
        open_issue(ungrounded_finding, "dotMR/access-review-agent-scratch", case_dir)
        print("[FAIL] grounding-gate-blocks-open-issue — UNGROUNDED FINDING WAS NOT REJECTED")
        return False
    except GroundingError:
        print("[PASS] grounding-gate-blocks-open-issue — ungrounded finding rejected before open_issue's adapter call")
        return True


def main() -> None:
    results = [case_issue_format(), case_grounding_gate_blocks_open_issue()]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
