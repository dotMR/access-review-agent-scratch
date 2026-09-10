"""Production entrypoint: real push-triggered dispatch + reconciliation.

Called by .github/workflows/production.yml on every push touching a
relevant path (SPEC.md §2). Reads the changed-file list the workflow's
git diff step computed, feeds it to dispatch.determine_dispatch(), and
runs run_full_reconciliation() scoped to whatever that decided - a
single-system commit invokes one unit, not all five (Milestones 4-5).

GITHUB_WRITE_MODE stays unset (dry-run, the ADR-0007 default) until a
deliberate, separate decision to go live - see development-plan.md's
Milestone 5. REPO_FULL_NAME defaults to the repo this workflow runs in;
overridden only for throwaway verification runs against the scratch repo.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


async def main() -> None:
    from access_review_agent.dispatch import determine_dispatch
    from access_review_agent.orchestrator import run_full_reconciliation

    changed_files = [f for f in os.environ.get("CHANGED_FILES", "").splitlines() if f.strip()]
    if not changed_files:
        print("No changed files reported - nothing to dispatch.")
        return

    print("Changed files this push:")
    for f in changed_files:
        print(f"  {f}")

    dispatch = determine_dispatch(changed_files)
    if not dispatch:
        print("Dispatch: no systems triggered (only access-control-policy.md, or nothing recognized).")
        return

    print(f"Dispatch: {sorted(dispatch)}")

    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    repo_full_name = os.environ.get("REPO_FULL_NAME") or os.environ["GITHUB_REPOSITORY"]
    commit_sha = os.environ.get("GITHUB_SHA")

    results = await run_full_reconciliation(data_dir, repo_full_name, systems=dispatch, commit_sha=commit_sha)

    any_failed = False
    for system_name, summary in results["systems"].items():
        if summary["failed"]:
            # ::error:: surfaces this in the Action run's UI/annotations,
            # same visibility as the workflow's own period-validation
            # errors - a malformed file for one system must be loud and
            # visible (SPEC.md §7), not a line buried in scrollback.
            print(f"::error::{system_name} FAILED: {summary['failed']}")
            any_failed = True
            continue
        print(
            f"{system_name}: {summary['detected']} detected, "
            f"{len(summary['opened'])} opened, {len(summary['rejected'])} rejected, "
            f"{len(summary['skipped_existing'])} already open, "
            f"{len(summary['remediated_closed'])} remediated, "
            f"{len(summary['write_failed'])} write failed"
        )
        for rejected in summary["rejected"]:
            print(f"  REJECTED (ungrounded): {rejected['reason']}")
        for failure in summary["write_failed"]:
            # A real finding that never got recorded as an Issue - loud,
            # and marks the run failed, same as a system-level failure:
            # an operator needs to know and likely re-run.
            print(f"  WRITE FAILED: {failure['reason']}")
            any_failed = True

    lifecycle = results["lifecycle"]
    print(
        f"lifecycle: {len(lifecycle['escalated'])} escalated, "
        f"{len(lifecycle['accepted_risk_closed'])} accepted-risk closed"
    )

    if any_failed:
        # Non-zero exit marks the Action run itself as failed - a human
        # must notice and investigate - but only AFTER every other
        # system's real work above already completed, per-system
        # isolation intact regardless of this run's own final exit code.
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
