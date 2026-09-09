"""Milestone 6 eval runner: Tier 2 cases 17-22 (Identity resolution's four
outcomes plus the two restraint cases) and case 38 (input safety),
graded automatically.

Unlike Milestones 1-5, this one costs real money - each case is one real
Agent SDK call (Haiku 4.5, per the milestone's model decision). Every
claimed finding is independently re-verified via grounding.validate_finding()
before being counted, same discipline as every prior milestone; total
cost is printed at the end so a run's real price is never a surprise.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _load_dotenv() -> None:
    """Load .env locally (gitignored) so ANTHROPIC_API_KEY is set without
    ever sourcing it in a shell command - same pattern as
    scripts/smoke_test.py. CI sets the env var directly; this is a no-op
    there since there's no .env file to find.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

CASES = [
    "identity-resolution-documented-exception",
    "identity-resolution-sso-gap",
    "identity-resolution-unresolved-no-evidence",
    "identity-resolution-stale-ownership",
    "identity-resolution-restraint-insufficient-evidence",
    "identity-resolution-restraint-ambiguous-match",
    "identity-resolution-input-safety",
    "identity-resolution-input-safety-identifier-vector",
]


def _check_issue_format(finding: dict, case_dir: Path, repo_full_name: str) -> list[str]:
    """Issue-format correctness (case 41's pattern, extended to Identity
    resolution) - dry-run only, reusing the finding this case already
    paid for rather than a second API call. Checks structure, not the
    model-generated evidence text verbatim (that varies run to run).
    """
    from access_review_agent.github.issues import open_issue

    result = open_issue(finding, repo_full_name, case_dir)
    problems = []
    if not result.title.startswith("Identity resolution — ") or not result.title.endswith("(VPN)"):
        problems.append(f"unexpected title format: {result.title!r}")
    if sorted(result.labels) != ["identity-resolution", "vpn"]:
        problems.append(f"unexpected labels: {result.labels!r}")
    for required in ("**Resolution outcome:**", "**Evidence:**", "**Source record:**"):
        if required not in result.body:
            problems.append(f"body missing required field: {required!r}")
    if not result.dry_run:
        problems.append("expected dry_run=True (GITHUB_WRITE_MODE unset in this runner)")
    return problems


async def run_case(case_name: str) -> tuple[bool, float]:
    from access_review_agent.detection.identity_resolution import (
        build_options,
        find_unresolved_candidates,
        resolve_identity,
    )
    from access_review_agent.grounding import GroundingError, validate_finding

    case_dir = Path(__file__).resolve().parent.parent / "evals" / "cases" / case_name
    expected = json.loads((case_dir / "expected.json").read_text())

    candidates = find_unresolved_candidates(case_dir, "vpn")
    if len(candidates) != 1:
        print(f"[FAIL] {case_name} — expected exactly 1 candidate, found {len(candidates)}")
        return False, 0.0
    candidate = candidates[0]
    if candidate["employee_id"] != expected["identifier"]:
        print(
            f"[FAIL] {case_name} — candidate identifier {candidate['employee_id']!r} != "
            f"expected {expected['identifier']!r}"
        )
        return False, 0.0

    options = build_options("vpn", case_dir)
    finding, cost = await resolve_identity(options, "vpn", candidate)

    problems = []
    actual_outcome = finding["resolution_outcome"] if finding else None
    # Map the no-finding outcomes back from "no finding produced" - resolve_identity
    # only tells us the Finding, not which of the two no-finding outcomes it was,
    # so for those two expected outcomes we only assert "no finding" here.
    if expected["expected_outcome"] in ("documented-exception", "resolved-individual"):
        if finding is not None:
            problems.append(
                f"expected no finding ({expected['expected_outcome']}), got a "
                f"{actual_outcome} finding: {finding}"
            )
    else:
        if finding is None:
            problems.append(f"expected a {expected['expected_outcome']} finding, got none")
        elif actual_outcome != expected["expected_outcome"]:
            problems.append(f"expected outcome={expected['expected_outcome']!r}, got {actual_outcome!r}")
        else:
            try:
                validate_finding(finding, case_dir)
            except GroundingError as e:
                problems.append(f"UNGROUNDED FINDING: {e}")
            else:
                problems.extend(
                    _check_issue_format(finding, case_dir, "dotMR/access-review-agent-scratch")
                )
            if expected.get("claimed_owner_employee_id") and finding is not None:
                claimed = finding.get("claimed_owner_employee_id")
                if claimed != expected["claimed_owner_employee_id"]:
                    problems.append(
                        f"claimed_owner_employee_id={claimed!r} != "
                        f"expected {expected['claimed_owner_employee_id']!r}"
                    )

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] {case_name} — {expected['description']} (${cost:.4f})")
    for p in problems:
        print(f"         {p}")
        print(f"         evidence given: {finding['evidence'] if finding else '(none - no finding produced)'}")
    return not problems, cost


async def main() -> None:
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("FAIL: ANTHROPIC_API_KEY not set (checked .env and environment)")
        sys.exit(1)

    results = []
    total_cost = 0.0
    for case in CASES:
        passed, cost = await run_case(case)
        results.append(passed)
        total_cost += cost

    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed — total cost ${total_cost:.4f}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
