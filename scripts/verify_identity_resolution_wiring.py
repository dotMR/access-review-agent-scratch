"""Regression guard: confirms run_full_reconciliation actually merges
Identity resolution's findings into a system's results and opens an
Issue for them, not just that SystemDetectionUnit's five Tier 1 checks
still work.

Why this exists: units.py's SystemDetectionUnit.detect_all() was always
deliberately Tier-1-only (ADR-0006's split point), but nothing wired
Identity resolution (Milestone 6, Tier 2) into run_full_reconciliation
either - the routine push/monthly/quarterly path never called it at all,
silently, until this was found during Milestone 12 prep. Every other
eval suite exercises run_full_reconciliation against fixtures with zero
identity-resolution candidates (deliberately, to stay free/credential-
free), so none of them would have caught a regression here even after
the fix - this test mocks detect_identity_resolution instead of making a
real Agent SDK call, so it can assert the merge actually happens without
real network/API cost.

A second case guards a related fix found in the same review: Identity
resolution's own failures (a live Agent SDK call) were originally caught
by the same narrow FileNotFoundError/ValueError clause as Tier 1's local
file parsing, so an unrelated network/API error would have propagated
out of run_full_reconciliation entirely, aborting every other system's
processing too - reintroducing the exact class of problem Milestone 11's
fail-loud-completeness guardrail was built to prevent. Identity
resolution now gets its own, broader isolation boundary.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "partial-failure-isolation"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"

FAKE_FINDING = {
    "category": "identity-resolution",
    "system_name": "github",
    "employee_id": "svc-fake-deploy",
    "access_level": "write",
    "expected_per_policy": "Individual Usage - access must be assigned to a specific employee, or a documented Service Account",
    "date_detected": "2026-09-09",
    "resolution_outcome": "unresolved",
    "evidence": "No provisioning_note, no HRIS match - insufficient evidence to resolve.",
    "source_record": {"file": "access_github.csv", "employee_id": "svc-fake-deploy"},
}


async def case_identity_resolution_merged_into_reconciliation() -> bool:
    from access_review_agent.orchestrator import run_full_reconciliation

    async def fake_detect(data_dir, system_name):
        if system_name == "github":
            return {"findings": [FAKE_FINDING], "cost_usd": 0.0}
        return {"findings": [], "cost_usd": 0.0}

    with patch(
        "access_review_agent.orchestrator.detect_identity_resolution",
        new=AsyncMock(side_effect=fake_detect),
    ):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=False
        )

    github_result = results["systems"]["github"]
    problems = []
    # detected counts BEFORE the grounding gate - the fixture's own real
    # Unapproved finding plus the mocked identity-resolution one, proving
    # detect_identity_resolution's output actually reached the merged
    # findings list, not just that detect_all()'s five Tier 1 checks ran.
    if github_result["detected"] != 2:
        problems.append(f"expected 2 findings detected for github (1 fixture + 1 mocked), got {github_result['detected']}")

    # The mock's employee_id ("svc-fake-deploy") isn't a real row in the
    # fixture's access_github.csv, so grounding correctly rejects it
    # rather than opening an Issue for it - a synthetic finding here
    # SHOULD be caught, the same guardrail Tier 1 findings go through.
    # Asserting rejection (not silent disappearance) still proves the
    # finding reached open_issue's grounding check.
    rejected_categories = {r["finding"]["category"] for r in github_result["rejected"]}
    if "identity-resolution" not in rejected_categories:
        problems.append(
            f"expected the mocked identity-resolution finding to reach grounding and be rejected "
            f"(it references no real access record), got rejected categories: {rejected_categories}"
        )

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] identity-resolution-wiring — run_full_reconciliation merges Identity "
        "resolution's findings into a system's results, and grounding applies to them too"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def case_identity_resolution_failure_isolated() -> bool:
    """A live Agent SDK call is a fundamentally different failure surface
    than Tier 1's local file parsing - a network/API error shouldn't
    crash the whole reconciliation run any more than a malformed file
    does. Simulates a real (not "bad data") failure for one system and
    confirms it isolates the same way Milestone 11's fail-loud-
    completeness guardrail already isolates a malformed file, while every
    other system still completes normally in the same run.
    """
    from access_review_agent.orchestrator import run_full_reconciliation

    async def flaky_detect(data_dir, system_name):
        if system_name == "github":
            raise RuntimeError("simulated Agent SDK network timeout")
        return {"findings": [], "cost_usd": 0.0}

    with patch(
        "access_review_agent.orchestrator.detect_identity_resolution",
        new=AsyncMock(side_effect=flaky_detect),
    ):
        results = await run_full_reconciliation(
            FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=False
        )

    problems = []
    github_result = results["systems"]["github"]
    if not github_result["failed"] or "network timeout" not in github_result["failed"]:
        problems.append(f"expected github to fail loudly with the simulated error, got: {github_result['failed']!r}")

    # aws fails too, but for its own unrelated reason (the fixture's
    # deliberately malformed file, same as case-39) - both failures must
    # coexist in the same run without either one masking or crashing out
    # the other systems.
    for system_name in ("salesforce", "finance_erp", "vpn"):
        summary = results["systems"][system_name]
        if summary["failed"]:
            problems.append(f"expected {system_name} to succeed despite github's failure, got: {summary['failed']!r}")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] identity-resolution-failure-isolated — a simulated Agent SDK error on one "
        "system doesn't abort the run; every other system still completes"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [
        await case_identity_resolution_merged_into_reconciliation(),
        await case_identity_resolution_failure_isolated(),
    ]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
