"""Milestone 11 eval runner: Tier 3 case 39 (partial failure isolation),
graded automatically. Pure Python, no model call, no network -
credential-free, matching Milestones 1-5/9/10.

The Release half of this milestone's Gate (a real tagged Release with
all seven assets) was verified manually against the real scratch repo
before this suite was written - see development-plan.md's Milestone 11.
A Release is a one-shot, human-approved publish action, not something
that belongs in a routine automated eval loop the way detection
correctness does.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "evals" / "cases" / "partial-failure-isolation"
SCRATCH_REPO = "dotMR/access-review-agent-scratch"


async def case_39_partial_failure_isolation() -> bool:
    from access_review_agent.orchestrator import run_full_reconciliation

    results = await run_full_reconciliation(FIXTURE_DIR, SCRATCH_REPO, systems=None, check_lifecycle=False)
    systems = results["systems"]

    problems = []
    if not systems["aws"]["failed"]:
        problems.append("expected aws (malformed access file, missing provisioning_note) to fail loudly, it didn't")
    elif "provisioning_note" not in systems["aws"]["failed"]:
        problems.append(f"aws failed, but not for the expected reason: {systems['aws']['failed']!r}")

    for system_name in ("github", "salesforce", "finance_erp", "vpn"):
        summary = systems[system_name]
        if summary["failed"]:
            problems.append(f"expected {system_name} to succeed, it failed: {summary['failed']!r}")
        elif summary["detected"] != 1:
            problems.append(f"expected 1 finding for {system_name}, got {summary['detected']}")

    status = "PASS" if not problems else "FAIL"
    print(
        f"[{status}] case-39-partial-failure-isolation — a malformed AWS access file fails "
        "loudly and visibly, while the other four systems still complete and report their "
        "findings normally"
    )
    for p in problems:
        print(f"         {p}")
    return not problems


async def main() -> None:
    results = [await case_39_partial_failure_isolation()]
    total, passed = len(results), sum(results)
    print(f"\n{passed}/{total} cases passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
