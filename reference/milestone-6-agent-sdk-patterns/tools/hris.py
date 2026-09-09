"""read_hris: shared, non-isolated HRIS reader.

Per ADR-0001, HRIS is available to every subagent unrestricted - the
isolation boundary is about *other systems'* access files, not about HRIS.
"""

import csv
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool

REQUIRED_COLUMNS = {
    "employee_id",
    "name",
    "role",
    "start_date",
    "end_date",
    "status",
    "role_change_history",
}


def _read_and_validate(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"HRIS file not found: {path}")

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing required columns: {sorted(missing)}")
        return list(reader)


def make_read_hris_tool(data_dir: Path):
    """Return a read_hris tool bound to one data directory's system_hr.csv."""

    file_path = data_dir / "system_hr.csv"

    @tool(
        "read_hris",
        "Read all current HRIS employee records. Takes no arguments.",
        {},
    )
    async def read_hris(_args: dict[str, Any]) -> dict[str, Any]:
        rows = _read_and_validate(file_path)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"{len(rows)} HRIS record(s) (source: {file_path.name}):\n{rows}",
                }
            ]
        }

    return read_hris
