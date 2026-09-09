# Reference: Agent SDK patterns for Milestone 6

Working, verified code from the original Milestone 1 build — before it turned
out Orphaned detection didn't need a model call at all (it's deterministic:
`eval-cases.md`'s own Tier 1 classification, and `src/access_review_agent/detection/orphaned.py`
is the real implementation now). Preserved here rather than deleted, because
Milestone 6 (Identity resolution) is the first category that genuinely needs
the Agent SDK, and re-deriving this wiring from scratch — including one
non-obvious bug this took real debugging to find — would waste real effort.

**Not imported by anything in `src/`.** This is reference material, not live
code. Copy from it, don't import it — by the time Milestone 6 starts, `tools/`
and the eval-runner shape will likely have moved on from what's captured here.

## What's here

- `agent.py` — builds `ClaudeAgentOptions`, wires custom tools through
  `create_sdk_mcp_server`, runs a `query()`, and extracts a fenced JSON block
  from the model's final response.
- `tools/access_data.py`, `tools/hris.py` — the same read-and-validate logic
  as the live `src/access_review_agent/tools/` versions, plus the
  `@tool()`-decorated SDK wrapper factories (`make_read_access_data_tool`,
  `make_read_hris_tool`) that the live versions no longer need for Tier 1.

## The non-obvious bug, so it isn't rediscovered the hard way

**Extract text via `ResultMessage.result`, never by calling `str()` on raw
SDK message objects and concatenating.** The first version of `agent.py` did
exactly that (`full_text += str(message)` for every streamed message) and
silently failed to find a JSON block that was genuinely present in the
model's output. The cause: `str()` on a dataclass containing string fields
calls `repr()` on those fields, and `repr()` of a string escapes real
newlines as the literal two-character sequence `\n` — not an actual newline.
A regex expecting real whitespace (`\s*`) between "```json" and `{` then
can't match a literal backslash character, and fails with no indication why.
`message.result` (on the `ResultMessage` you get at the end of the stream)
is the clean, already-assembled final text — use that, not a hand-rolled
concatenation of message reprs.

## Other things worth carrying forward

- **Tool isolation**: `make_read_access_data_tool(system_name, data_dir)` is
  a factory returning a tool instance pre-bound to one system, no
  `system_name` parameter exposed to the model — matches ADR-0001's
  isolation design. `read_hris` is shared/unbound, same rationale.
- **`allowed_tools` scoped to only the custom MCP tools** — never the
  `claude_code` built-in preset, which would hand the agent Bash/Write/Edit.
  Confirmed this holds by inspecting `ClaudeAgentOptions.allowed_tools`
  directly in a test, not just by not setting the preset.
- **Model selection matters for cost**, but only where reasoning is actually
  needed — Identity resolution and Risk Assessment (Tier 2) may warrant a
  more capable model than Haiku; that's a real decision to make when
  building this out for real, informed by what the reasoning actually
  requires, not carried over from this reference code unexamined.
