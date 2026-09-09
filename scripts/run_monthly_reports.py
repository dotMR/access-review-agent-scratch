"""Monthly Operational Flags entrypoint: full reconciliation across all
five systems (real detection, not just a list_issues read - closing the
quiet-system gap, ADR-0003), then commits one report per system listing
every currently-open Finding.

Called by .github/workflows/monthly-report.yml. GITHUB_WRITE_MODE stays
unset (dry-run, ADR-0007's default) until a deliberate decision to go
live - same reasoning as production.yml/quarterly-audit.yml.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


async def main() -> None:
    from access_review_agent.orchestrator import generate_monthly_reports

    period = os.environ.get("PERIOD")
    if not period:
        print("PERIOD env var not set (e.g. 2026-02)")
        sys.exit(1)

    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    repo_full_name = os.environ.get("REPO_FULL_NAME") or os.environ["GITHUB_REPOSITORY"]
    commit_sha = os.environ.get("GITHUB_SHA")

    results = await generate_monthly_reports(data_dir, repo_full_name, period, commit_sha=commit_sha)
    for name, result in results.items():
        status = "DRY RUN" if result.dry_run else "committed"
        print(f"{name}: {status} — {result.path}" + (f" ({result.commit_sha})" if result.commit_sha else ""))


if __name__ == "__main__":
    asyncio.run(main())
