"""Dormant admin-level access detection: plain Python, no model call.

Deterministic per eval-cases.md's Tier 1 classification - a threshold
comparison, same reasoning as ADR-0006 for Orphaned: no LLM adds
reliability here, only cost, latency, and run-to-run variance.
"""

from datetime import date
from pathlib import Path
from typing import Any

from access_review_agent.tools.access_data import read_and_validate as read_access_data
from access_review_agent.tools.hris import read_and_validate as read_hris
from access_review_agent.tools.policy import DEFAULT_POLICY_CONFIG_PATH, read_policy


def detect_dormant_admin(
    data_dir: Path,
    system_name: str = "aws",
    as_of: date | None = None,
    policy_config_path: Path = DEFAULT_POLICY_CONFIG_PATH,
) -> dict[str, Any]:
    """Detect Dormant admin-level access for one system: access_level=admin,
    status=active, last_used_date more than `admin_level_days` (default 90,
    policy-config.yaml) consecutive days before `as_of` (defaults to today).

    `as_of` exists so eval fixtures can pin boundary cases (89/90/91 days)
    to a fixed reference date instead of drifting relative to wall-clock
    time as real days pass - the threshold is deliberately `>`, not `>=`
    (access-control-policy.md's Dormant Admin-level Principle says "more
    than 90 consecutive days," so exactly 90 is still compliant).
    """
    as_of = as_of or date.today()
    threshold_days = read_policy(policy_config_path)["dormant_thresholds"]["admin_level_days"]

    access_rows = read_access_data(data_dir / f"access_{system_name}.csv", system_name)
    hris_rows = read_hris(data_dir / "system_hr.csv")
    hris_by_id = {r["employee_id"]: r for r in hris_rows}

    findings = []
    for row in access_rows:
        if row["access_level"] != "admin" or row["status"] != "active":
            continue
        last_used = date.fromisoformat(row["last_used_date"])
        days_dormant = (as_of - last_used).days
        if days_dormant <= threshold_days:
            continue
        employee = hris_by_id.get(row["employee_id"])
        findings.append(
            {
                "category": "dormant-admin",
                "system_name": system_name,
                "employee_id": row["employee_id"],
                "employee_name": employee["name"] if employee else row["employee_id"],
                "access_level": row["access_level"],
                "expected_per_policy": f"Revoke if unused > {threshold_days} consecutive days",
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
