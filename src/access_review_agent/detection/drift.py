"""Drift detection: plain Python, no model call.

Deterministic per eval-cases.md's Tier 1 classification. Per
access-control-policy.md's Role-based Access Principle ("any changes to
the role must trigger a review of access"), Drift is scoped specifically
to *post-role-change* mismatches: a non-empty `role_change_history` is
required, not just "access exceeds baseline" in general - that broader
case (ad-hoc access, no role change involved) is Unapproved's job when
it lacks a recorded approval, not Drift's. See ADR-0006: a lookup-table
comparison needs no LLM.

`role_change_history` is stored in HRIS CSVs as a JSON array of
`{"date", "old_role", "new_role"}` objects (`[]` if the employee has
never changed roles) - parsed with the standard library, not hand-rolled.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any

from access_review_agent.tools.access_data import read_and_validate as read_access_data
from access_review_agent.tools.hris import read_and_validate as read_hris
from access_review_agent.tools.policy import (
    DEFAULT_ROLE_ACCESS_MAPPING_PATH,
    baseline_access_level,
    read_policy,
)


def detect_drift(
    data_dir: Path,
    system_name: str = "aws",
    role_mapping_path: Path = DEFAULT_ROLE_ACCESS_MAPPING_PATH,
) -> dict[str, Any]:
    """Detect Drift for one system: the employee has a recorded role
    change, and their current access no longer matches the baseline for
    their *current* role.
    """
    role_mapping = read_policy(role_mapping_path)

    access_rows = read_access_data(data_dir / f"access_{system_name}.csv", system_name)
    hris_rows = read_hris(data_dir / "system_hr.csv")
    hris_by_id = {r["employee_id"]: r for r in hris_rows}
    today = date.today().isoformat()

    findings = []
    for row in access_rows:
        if row["status"] != "active" or row["employee_id"] not in hris_by_id:
            continue
        employee = hris_by_id[row["employee_id"]]
        role_changes = json.loads(employee["role_change_history"] or "[]")
        if not role_changes:
            continue  # no role change on record - not Drift's scope

        current_baseline = baseline_access_level(role_mapping, employee["role"], system_name)
        if row["access_level"] == current_baseline:
            continue  # already matches the current role - no drift

        findings.append(
            {
                "category": "drift",
                "system_name": system_name,
                "employee_id": row["employee_id"],
                "employee_name": employee["name"],
                "access_level": row["access_level"],
                "expected_per_policy": (
                    f"{current_baseline!r} (baseline for current role {employee['role']!r})"
                ),
                "date_detected": today,
                "role_change_history": role_changes,
                "source_record": {
                    "file": f"access_{system_name}.csv",
                    "employee_id": row["employee_id"],
                },
            }
        )
    return {"findings": findings}
