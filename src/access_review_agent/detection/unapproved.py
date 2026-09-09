"""Unapproved access detection: plain Python, no model call.

Deterministic per eval-cases.md's Tier 1 classification - a single null
check on `approved_by`. Per access-control-policy.md's Access Approval
Principle: "access lacking a recorded approval is treated as a risk and
flagged for review, regardless of how it arose" - baseline or ad-hoc,
role change or not, none of that matters here, only whether an approval
is on file. See ADR-0006: no reasoning involved, no model call.
"""

from datetime import date
from pathlib import Path
from typing import Any

from access_review_agent.tools.access_data import read_and_validate as read_access_data
from access_review_agent.tools.hris import read_and_validate as read_hris


def detect_unapproved(data_dir: Path, system_name: str = "aws") -> dict[str, Any]:
    """Detect Unapproved access for one system: `approved_by` is null/empty
    on an active access record. `"auto (granted per role policy)"` and a
    real Asset Owner identifier both count as approved - only a missing
    value flags.
    """
    access_rows = read_access_data(data_dir / f"access_{system_name}.csv", system_name)
    hris_rows = read_hris(data_dir / "system_hr.csv")
    hris_by_id = {r["employee_id"]: r for r in hris_rows}
    today = date.today().isoformat()

    findings = [
        {
            "category": "unapproved",
            "system_name": system_name,
            "employee_id": row["employee_id"],
            "employee_name": hris_by_id[row["employee_id"]]["name"]
            if row["employee_id"] in hris_by_id
            else row["employee_id"],
            "access_level": row["access_level"],
            "expected_per_policy": "A recorded approval (auto or Asset Owner) on file",
            "date_detected": today,
            "granted_date": row["granted_date"],
            "approved_by": row["approved_by"] or None,
            "source_record": {
                "file": f"access_{system_name}.csv",
                "employee_id": row["employee_id"],
            },
        }
        for row in access_rows
        if row["status"] == "active" and not row["approved_by"]
    ]
    return {"findings": findings}
