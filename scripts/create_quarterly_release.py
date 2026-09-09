"""Quarterly Release entrypoint (SPEC.md §6, Milestone 11): the gated
half of the quarterly workflow. Runs only after the human-in-the-loop
GitHub Actions environment protection rule approves it, and only after
the report-generation job's commits have already landed - this job's own
checkout (run afterward) includes them, which is what
create_quarterly_release reads from rather than re-deriving everything.

GITHUB_WRITE_MODE still gates whether this is a real write or a dry-run
log (ADR-0007's default), same as every other write path - environment
approval and "go live" are two separate decisions, not one.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def main() -> None:
    from access_review_agent.orchestrator import create_quarterly_release

    period = os.environ.get("PERIOD")
    if not period:
        print("PERIOD env var not set (e.g. 2026-Q1)")
        sys.exit(1)

    repo_full_name = os.environ.get("REPO_FULL_NAME") or os.environ["GITHUB_REPOSITORY"]
    checkout_dir = Path(os.environ.get("CHECKOUT_DIR", "."))

    result = create_quarterly_release(repo_full_name, period, checkout_dir)
    status = "DRY RUN" if result.dry_run else "created"
    print(f"Release {result.tag}: {status}" + (f" — {result.html_url}" if result.html_url else ""))
    print(f"Assets: {result.asset_names}")


if __name__ == "__main__":
    main()
