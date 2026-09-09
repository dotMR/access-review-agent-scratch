"""Read policy YAML and look up an employee's role-baseline access.

Per SPEC.md §3's read_policy tool: one generic YAML reader, reused for
both role-access-mapping.yaml (the "ought" access baseline) and
policy-config.yaml (thresholds and scoring tables) - both are the same
shape of machine-consumed structured data with no per-record schema to
validate, unlike the CSV tools in this package, which enforce a strict
column contract because Access/HRIS data comes from an external system
this agent doesn't control.

Not fixture-scoped like access_data.py/hris.py: thresholds and the role
mapping are project-wide policy, not per-eval-case data, so callers read
the real repo-root files by default rather than something duplicated into
every fixture directory.
"""

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_CONFIG_PATH = REPO_ROOT / "policy-config.yaml"
DEFAULT_ROLE_ACCESS_MAPPING_PATH = REPO_ROOT / "role-access-mapping.yaml"


def read_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    with path.open() as f:
        return yaml.safe_load(f)


def baseline_access_level(role_mapping: dict[str, Any], role: str, system_name: str) -> str:
    """The access level (`none`/`read`/`write`/`admin`/`yes`) an employee's
    role entitles them to automatically for one system, per
    role-access-mapping.yaml. Raises if the role isn't in the mapping -
    every HRIS role is expected to have an entry.
    """
    for entry in role_mapping["role_access_mapping"]:
        if entry["role"] == role:
            return entry["access"][system_name]["level"]
    raise ValueError(f"No role-access-mapping entry for role={role!r}")
