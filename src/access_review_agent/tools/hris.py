"""Read and validate the HRIS file.

Per ADR-0001, HRIS is shared and non-isolated - available to every
system's detection logic unrestricted. For Tier 1 (deterministic)
categories, read_and_validate() is called directly from plain Python (see
detection/). For Tier 2 (reasoning-requiring) categories starting at
Milestone 6, make_read_hris_tool() wraps the same function as an Agent
SDK tool - unbound to any one system, same rationale as the plain-Python
version's shared access.
"""

import csv
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {
    "employee_id",
    "name",
    "role",
    "start_date",
    "end_date",
    "status",
    "role_change_history",
}


def read_and_validate(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"HRIS file not found: {path}")

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing required columns: {sorted(missing)}")
        return list(reader)


def make_read_hris_tool(data_dir: Path):
    """Return a read_hris Agent SDK tool bound to one data directory's
    system_hr.csv. Takes no arguments.
    """
    from claude_agent_sdk import tool

    file_path = data_dir / "system_hr.csv"

    @tool(
        "read_hris",
        "Read all current HRIS employee records. Takes no arguments.",
        {},
    )
    async def read_hris(_args: dict[str, Any]) -> dict[str, Any]:
        rows = read_and_validate(file_path)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"{len(rows)} HRIS record(s) (source: {file_path.name}):\n{rows}",
                }
            ]
        }

    return read_hris
