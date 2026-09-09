"""Grounding/citation guardrail: independently re-verify a claimed finding.

Per SPEC.md §7 — a validation step confirms a claimed finding's source
record actually exists with the claimed properties, before that finding
is trusted. Trusts nothing about what happened during detection; re-reads
the source data itself, the same way a real reviewer re-checks a source
rather than trusting "I already looked."

One validator per category, each independently re-deriving that
category's own flag/no-flag decision from the source record - not just
checking the finding's fields are internally consistent. For the two
dormancy categories this means recomputing the day-count from
`last_used_date` and the finding's own `date_detected` (never
`date.today()`, so this check stays correct regardless of when it runs
relative to when the finding was detected) and re-comparing it against
policy-config.yaml's threshold, exactly as ADR-0006 intends: defense-in-
depth against bugs in the deterministic detection code, not hallucination
defense (deterministic Python can't hallucinate) - but it runs the same
way regardless of a finding's origin, so the write-gate in front of
open_issue never needs to special-case which.

Built once here, used twice: the eval runners reject hallucinated/buggy
findings with it; open_issue reuses it unchanged as the write gate.
"""

from datetime import date
from pathlib import Path
from typing import Any, Callable

from access_review_agent.tools.access_data import read_and_validate as read_access_data
from access_review_agent.tools.hris import read_and_validate as read_hris
from access_review_agent.tools.policy import (
    DEFAULT_POLICY_CONFIG_PATH,
    DEFAULT_ROLE_ACCESS_MAPPING_PATH,
    baseline_access_level,
    read_policy,
)


class GroundingError(Exception):
    """Raised when a claimed finding does not hold up against source data."""


def _require_date_detected(finding: dict[str, Any]) -> date:
    date_detected = finding.get("date_detected")
    if not date_detected:
        raise GroundingError("Finding missing date_detected — can't re-derive its threshold check")
    return date.fromisoformat(date_detected)


def _validate_orphaned(
    finding: dict[str, Any], access_row: dict, hris_row: dict | None, hris_rows: list[dict]
) -> None:
    if access_row["status"] != "active":
        raise GroundingError(
            f"Access record has status={access_row['status']!r}, not 'active' — "
            "Orphaned requires currently-active access"
        )
    if hris_row is None:
        raise GroundingError(f"No HRIS record for employee_id={finding['employee_id']!r}")
    if hris_row["status"] != "terminated":
        raise GroundingError(
            f"HRIS record has status={hris_row['status']!r}, not 'terminated' — "
            "Orphaned requires HRIS status=terminated"
        )


def _validate_dormant_admin(
    finding: dict[str, Any], access_row: dict, hris_row: dict | None, hris_rows: list[dict]
) -> None:
    if access_row["access_level"] != "admin":
        raise GroundingError(f"Access record has access_level={access_row['access_level']!r}, not 'admin'")
    if access_row["status"] != "active":
        raise GroundingError(f"Access record has status={access_row['status']!r}, not 'active'")
    if access_row["last_used_date"] != finding.get("last_used_date"):
        raise GroundingError(
            f"Claimed last_used_date={finding.get('last_used_date')!r} doesn't match "
            f"source record's {access_row['last_used_date']!r}"
        )
    threshold = read_policy(DEFAULT_POLICY_CONFIG_PATH)["dormant_thresholds"]["admin_level_days"]
    days_dormant = (_require_date_detected(finding) - date.fromisoformat(access_row["last_used_date"])).days
    if days_dormant <= threshold:
        raise GroundingError(
            f"Recomputed days_dormant={days_dormant} does not exceed threshold={threshold}"
        )


def _validate_dormant_ad_hoc(
    finding: dict[str, Any], access_row: dict, hris_row: dict | None, hris_rows: list[dict]
) -> None:
    if access_row["status"] != "active":
        raise GroundingError(f"Access record has status={access_row['status']!r}, not 'active'")
    if hris_row is None:
        raise GroundingError(f"No HRIS record for employee_id={finding['employee_id']!r}")
    role_mapping = read_policy(DEFAULT_ROLE_ACCESS_MAPPING_PATH)
    baseline = baseline_access_level(role_mapping, hris_row["role"], finding["system_name"])
    if access_row["access_level"] == baseline:
        raise GroundingError(
            f"Access level {access_row['access_level']!r} matches the current role's "
            f"baseline ({baseline!r}) — not ad-hoc"
        )
    if access_row["last_used_date"] != finding.get("last_used_date"):
        raise GroundingError(
            f"Claimed last_used_date={finding.get('last_used_date')!r} doesn't match "
            f"source record's {access_row['last_used_date']!r}"
        )
    threshold = read_policy(DEFAULT_POLICY_CONFIG_PATH)["dormant_thresholds"]["ad_hoc_days"]
    days_dormant = (_require_date_detected(finding) - date.fromisoformat(access_row["last_used_date"])).days
    if days_dormant <= threshold:
        raise GroundingError(
            f"Recomputed days_dormant={days_dormant} does not exceed threshold={threshold}"
        )


def _validate_unapproved(
    finding: dict[str, Any], access_row: dict, hris_row: dict | None, hris_rows: list[dict]
) -> None:
    if access_row["status"] != "active":
        raise GroundingError(f"Access record has status={access_row['status']!r}, not 'active'")
    if access_row["approved_by"]:
        raise GroundingError(
            f"Source record has approved_by={access_row['approved_by']!r} set — not unapproved"
        )


def _validate_drift(
    finding: dict[str, Any], access_row: dict, hris_row: dict | None, hris_rows: list[dict]
) -> None:
    import json

    if access_row["status"] != "active":
        raise GroundingError(f"Access record has status={access_row['status']!r}, not 'active'")
    if hris_row is None:
        raise GroundingError(f"No HRIS record for employee_id={finding['employee_id']!r}")
    role_changes = json.loads(hris_row["role_change_history"] or "[]")
    if not role_changes:
        raise GroundingError("No role change on record — out of Drift's scope")
    role_mapping = read_policy(DEFAULT_ROLE_ACCESS_MAPPING_PATH)
    baseline = baseline_access_level(role_mapping, hris_row["role"], finding["system_name"])
    if access_row["access_level"] == baseline:
        raise GroundingError(
            f"Access level {access_row['access_level']!r} already matches the current "
            f"role's baseline ({baseline!r}) — no drift"
        )


def _validate_identity_resolution(
    finding: dict[str, Any], access_row: dict, hris_row: dict | None, hris_rows: list[dict]
) -> None:
    if access_row["status"] != "active":
        raise GroundingError(f"Access record has status={access_row['status']!r}, not 'active'")
    if hris_row is not None:
        raise GroundingError(
            f"employee_id={finding['employee_id']!r} matches an HRIS record directly — "
            "not Identity resolution's territory (that's Orphaned's, per the anti-join "
            "distinction in SPEC.md §4)"
        )

    outcome = finding.get("resolution_outcome")
    if outcome == "stale-ownership":
        owner_id = finding.get("claimed_owner_employee_id")
        if not owner_id:
            raise GroundingError("stale-ownership finding missing claimed_owner_employee_id")
        owner_row = next((r for r in hris_rows if r["employee_id"] == owner_id), None)
        if owner_row is None:
            raise GroundingError(f"No HRIS record for claimed owner employee_id={owner_id!r}")
        if owner_row["status"] != "terminated":
            raise GroundingError(
                f"Claimed owner has HRIS status={owner_row['status']!r}, not 'terminated' — "
                "stale-ownership requires the documented owner to actually be terminated"
            )
    elif outcome != "unresolved":
        raise GroundingError(
            f"Unrecognized resolution_outcome={outcome!r} — expected 'unresolved' or "
            "'stale-ownership' (the only two outcomes that produce a Finding)"
        )
    # "unresolved" itself isn't independently re-derivable here - whether the
    # evidence was genuinely insufficient/ambiguous is the model's own
    # judgment call, which is what eval-cases.md cases 21-22 test directly,
    # not something grounding can re-check against source data.


_VALIDATORS: dict[str, Callable[[dict[str, Any], dict, dict | None, list[dict]], None]] = {
    "orphaned": _validate_orphaned,
    "dormant-admin": _validate_dormant_admin,
    "dormant-ad-hoc": _validate_dormant_ad_hoc,
    "unapproved": _validate_unapproved,
    "drift": _validate_drift,
    "identity-resolution": _validate_identity_resolution,
}


def validate_finding(finding: dict[str, Any], data_dir: Path) -> None:
    """Raise GroundingError if `finding` isn't actually supported by the
    source data in data_dir. Returns None (no exception) if grounded.
    """
    category = finding.get("category")
    system_name = finding.get("system_name")
    employee_id = finding.get("employee_id")

    if not system_name or not employee_id:
        raise GroundingError(f"Finding missing system_name or employee_id: {finding}")

    validator = _VALIDATORS.get(category)
    if validator is None:
        raise GroundingError(f"No grounding check implemented for category={category!r} yet")

    access_rows = read_access_data(data_dir / f"access_{system_name}.csv", system_name)
    access_row = next((r for r in access_rows if r["employee_id"] == employee_id), None)
    if access_row is None:
        raise GroundingError(
            f"No access record for employee_id={employee_id!r} in "
            f"access_{system_name}.csv — finding not grounded"
        )

    hris_rows = read_hris(data_dir / "system_hr.csv")
    hris_row = next((r for r in hris_rows if r["employee_id"] == employee_id), None)

    validator(finding, access_row, hris_row, hris_rows)
