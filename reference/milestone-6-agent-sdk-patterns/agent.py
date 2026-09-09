"""Reference: Agent SDK wiring pattern for a category that needs real reasoning.

Originally written for Milestone 1's Orphaned check, before ADR-0006
established that deterministic categories need no model call at all -
kept here as a working pattern for Milestone 6 (Identity resolution),
the first category that actually needs this. See README.md in this
directory for the non-obvious bug this avoids re-discovering, and for
why this file is copy-from, not import-from.

The system prompt and TIER_1_MODEL choice below are Orphaned-specific
leftovers from that original version - replace both for whatever
category and model this is adapted for; don't carry them over unexamined.
"""

import json
import re
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, create_sdk_mcp_server, query

from tools.access_data import make_read_access_data_tool
from tools.hris import make_read_hris_tool

# Example only - Tier 1 turned out not to need a model call at all
# (ADR-0006). Pick a real model for whatever category this is adapted
# for, informed by what its reasoning actually requires.
EXAMPLE_MODEL = "haiku"

SYSTEM_PROMPT = """\
You are the AWS subagent of a joiner-mover-leaver access review agent. \
You only ever reason about AWS access - you have no visibility into any \
other system.

Task: detect Orphaned access. An access record is Orphaned if both are true:
- its employee_id matches an HRIS record whose status is "terminated"
- the access record's own status is "active" (not "revoked")

A contractor whose end_date has passed but whose HRIS status is still \
"active" is NOT Orphaned - that is a different, out-of-scope check. Only \
HRIS status="terminated" counts.

Call read_access_data and read_hris to get the current data. Do not guess \
or assume data you have not actually read.

Respond with your reasoning, then end your reply with a fenced json code \
block matching exactly this shape (empty findings list if none):

```json
{
  "findings": [
    {
      "category": "orphaned",
      "system_name": "aws",
      "employee_id": "<employee_id>",
      "source_record": {"file": "access_aws.csv", "employee_id": "<employee_id>"}
    }
  ]
}
```
"""


def build_options(data_dir: Path) -> ClaudeAgentOptions:
    access_tool = make_read_access_data_tool("aws", data_dir)
    hris_tool = make_read_hris_tool(data_dir)

    server = create_sdk_mcp_server(
        name="access_review",
        version="0.1.0",
        tools=[access_tool, hris_tool],
    )

    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"access_review": server},
        allowed_tools=[
            "mcp__access_review__read_access_data",
            "mcp__access_review__read_hris",
        ],
        model=EXAMPLE_MODEL,
    )


def extract_json_block(text: str) -> dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No fenced json block found in model output:\n{text}")
    return json.loads(match.group(1))


async def run_check(data_dir: Path) -> tuple[dict[str, Any], float]:
    """Run the check against fixture data in data_dir.

    Returns (findings dict, cost in USD). The key pattern: extract text
    via ResultMessage.result, never by stringifying raw SDK message
    objects - see this directory's README for why that silently breaks.
    """
    options = build_options(data_dir)
    result_text: str | None = None
    cost_usd = 0.0
    async for message in query(prompt="Check AWS for orphaned access.", options=options):
        if isinstance(message, ResultMessage):
            result_text = message.result
            cost_usd = message.total_cost_usd or 0.0

    if result_text is None:
        raise RuntimeError("Agent run finished without a ResultMessage")

    return extract_json_block(result_text), cost_usd
