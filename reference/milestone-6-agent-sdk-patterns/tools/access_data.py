"""read_access_data: pre-bound, per-system access-file reader.

Per ADR-0001, isolation is structural: each subagent gets its own tool
instance, closed over a single system's file at creation time. The model
never supplies a system name - there is nothing for it to vary.
"""

import csv
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool

REQUIRED_COLUMNS = {
    "employee_id",
    "system_name",
    "access_level",
    "granted_date",
    "approved_by",
    "last_used_date",
    "status",
    "provisioning_note",
}


def _read_and_validate(path: Path, expected_system_name: str) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Access data file not found: {path}")

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path}: missing required columns: {sorted(missing)}"
            )
        rows = list(reader)

    for row in rows:
        if row["system_name"] != expected_system_name:
            raise ValueError(
                f"{path}: row for {row['employee_id']} has system_name="
                f"{row['system_name']!r}, expected {expected_system_name!r} "
                "(same-file consistency check)"
            )
    return rows


def make_read_access_data_tool(system_name: str, data_dir: Path):
    """Return a read_access_data tool pre-bound to one system's file.

    system_name: e.g. "aws" - used both to locate the file and to validate
    each row's own system_name field matches.
    data_dir: directory containing access_<system_name>.csv.
    """

    file_path = data_dir / f"access_{system_name}.csv"

    @tool(
        "read_access_data",
        f"Read all current access records for {system_name}. Takes no "
        "arguments - this tool is scoped to a single system.",
        {},
    )
    async def read_access_data(_args: dict[str, Any]) -> dict[str, Any]:
        rows = _read_and_validate(file_path, system_name)
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{len(rows)} access record(s) for {system_name} "
                        f"(source: {file_path.name}):\n{rows}"
                    ),
                }
            ]
        }

    return read_access_data
