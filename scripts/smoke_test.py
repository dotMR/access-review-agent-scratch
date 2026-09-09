"""One-off smoke test: confirms the Claude Agent SDK can reach the API.

Not part of the eval suite or the agent itself - a throwaway check that
the environment (API key, package install) is actually working before
building real logic on top of it. Loads .env internally so credentials
never pass through a shell command.
"""

import asyncio
import os
from pathlib import Path


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


async def main() -> None:
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("FAIL: ANTHROPIC_API_KEY not set (checked .env and environment)")
        return

    from claude_agent_sdk import query, ClaudeAgentOptions

    options = ClaudeAgentOptions(
        system_prompt="Reply with exactly one word: pong",
        allowed_tools=[],
    )

    saw_response = False
    async for message in query(prompt="ping", options=options):
        text = str(message)
        if "pong" in text.lower():
            saw_response = True

    print("PASS: reached Claude and got a response" if saw_response else "FAIL: no expected response received")


if __name__ == "__main__":
    asyncio.run(main())
