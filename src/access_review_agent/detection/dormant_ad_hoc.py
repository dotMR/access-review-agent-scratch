"""Dormant ad-hoc access detection: plain Python, no model call.

Deterministic per eval-cases.md's Tier 1 classification. "Ad-hoc" means
the access record's level doesn't match the employee's current-role
baseline (role-access-mapping.yaml) - baseline access, however long
unused, isn't a Finding under this category (access-control-policy.md's
Dormant Ad-hoc Principle only covers access "that falls outside of the
employee's role"). See ADR-0006: no LLM involved, a threshold plus a
lookup-table comparison needs none.
"""

from datetime import date
from pathlib import Path
from typing import Any

from access_review_agent.tools.access_data import read_and_validate as read_access_data
from access_review_agent.tools.hris import read_and_validate as read_hris
from access_review_agent.tools.policy import (
    DEFAULT_POLICY_CONFIG_PATH,
    DEFAULT_ROLE_ACCESS_MAPPING_PATH,
    baseline_access_level,
    read_policy,
)


def detect_dormant_ad_hoc(
    data_dir: Path,
    system_name: str = "aws",
    as_of: date | None = None,
    policy_config_path: Path = DEFAULT_POLICY_CONFIG_PATH,
    role_mapping_path: Path = DEFAULT_ROLE_ACCESS_MAPPING_PATH,
) -> dict[str, Any]:
    """Detect Dormant ad-hoc access for one system: access that doesn't
    match the employee's current-role baseline, status=active,
    last_used_date more than `ad_hoc_days` (default 180, policy-config.yaml)
    consecutive days before `as_of` (defaults to today, overridable so
    eval fixtures pin boundary cases to a fixed reference date).
    """
    as_of = as_of or date.today()
    threshold_days = read_policy(policy_config_path)["dormant_thresholds"]["ad_hoc_days"]
    role_mapping = read_policy(role_mapping_path)

    access_rows = read_access_data(data_dir / f"access_{system_name}.csv", system_name)
    hris_rows = read_hris(data_dir / "system_hr.csv")
    hris_by_id = {r["employee_id"]: r for r in hris_rows}

    findings = []
    for row in access_rows:
        if row["status"] != "active" or row["employee_id"] not in hris_by_id:
            continue
        employee = hris_by_id[row["employee_id"]]
        baseline = baseline_access_level(role_mapping, employee["role"], system_name)
        if row["access_level"] == baseline:
            continue  # matches baseline - not ad-hoc, out of scope for this category

        last_used = date.fromisoformat(row["last_used_date"])
        days_dormant = (as_of - last_used).days
        if days_dormant <= threshold_days:
            continue

        findings.append(
            {
                "category": "dormant-ad-hoc",
                "system_name": system_name,
                "employee_id": row["employee_id"],
                "employee_name": employee["name"],
                "access_level": row["access_level"],
                "expected_per_policy": (
                    f"Role baseline is {baseline!r}; ad-hoc grant unused > "
                    f"{threshold_days} consecutive days"
                ),
                "date_detected": as_of.isoformat(),
                "last_used_date": row["last_used_date"],
                "days_dormant": days_dormant,
                "source_record": {
                    "file": f"access_{system_name}.csv",
                    "employee_id": row["employee_id"],
                },
            }
        )
    return {"findings": findings}
