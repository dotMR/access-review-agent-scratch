"""Read and validate one system's access data file.

Per ADR-0001, isolation is structural: callers pass their own system_name
and only ever read that system's file - there is no cross-system access
here. For Tier 1 (deterministic) categories, read_and_validate() is called
directly from plain Python (see detection/). For Tier 2 (reasoning-
requiring) categories starting at Milestone 6, make_read_access_data_tool()
wraps the same function as an Agent SDK tool, pre-bound to one system at
creation time - no system_name parameter exposed to the model, matching
the reference pattern in reference/milestone-6-agent-sdk-patterns/, but
reusing this module's own read_and_validate rather than duplicating it.
"""

import csv
from pathlib import Path
from typing import Any

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


def read_and_validate(path: Path, expected_system_name: str) -> list[dict[str, str]]:
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
    """Return a read_access_data Agent SDK tool, pre-bound to one system's
    file. Takes no arguments - there is nothing for the model to vary.
    """
    from claude_agent_sdk import tool

    file_path = data_dir / f"access_{system_name}.csv"

    @tool(
        "read_access_data",
        f"Read all current access records for {system_name}. Takes no "
        "arguments - this tool is scoped to a single system.",
        {},
    )
    async def read_access_data(_args: dict[str, Any]) -> dict[str, Any]:
        rows = read_and_validate(file_path, system_name)
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
