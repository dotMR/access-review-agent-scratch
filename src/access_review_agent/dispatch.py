"""Commit -> trigger -> dispatch: SPEC.md §2's push-triggered dispatch
table, as a pure function over a list of changed file paths.

Deliberately pure and GitHub-Actions-agnostic: it takes whatever file
list a caller already has (from `git diff --name-only`, a GitHub Actions
event payload, or a hand-written eval case) and returns which systems to
invoke — nothing here reads the filesystem or talks to git. That's what
makes eval-cases.md's dispatch cases (25-28) testable locally, credential-
free, in scripts/run_milestone5.py, with the same function the real
`.github/workflows/production.yml` calls.
"""

from pathlib import PurePosixPath

from access_review_agent.units import SYSTEMS

FAN_OUT_ALL = {
    "data/system_hr.csv",
    "policy-config.yaml",
    "role-access-mapping.yaml",
}

_ACCESS_FILE_TO_SYSTEM = {f"data/access_{system}.csv": system for system in SYSTEMS}


def determine_dispatch(changed_files: list[str]) -> set[str]:
    """Which systems' detection units a commit touching `changed_files`
    should invoke. `access-control-policy.md` (and anything else not
    listed in the dispatch table) contributes nothing — human-readable
    prose, not machine-consumed (SPEC.md §2).
    """
    systems: set[str] = set()
    for raw_path in changed_files:
        path = str(PurePosixPath(raw_path))
        if path in FAN_OUT_ALL:
            return set(SYSTEMS)
        if path in _ACCESS_FILE_TO_SYSTEM:
            systems.add(_ACCESS_FILE_TO_SYSTEM[path])
    return systems
