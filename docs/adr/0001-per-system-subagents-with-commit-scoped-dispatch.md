# 0001. Per-system subagents with commit-scoped dispatch and centralized write access

**Status:** accepted

## Context

The agent has to read six data sources sharing near-identical schemas (HRIS plus five Information Systems' access exports), reason over them through the Claude Agent SDK's tool-use loop, and write Findings to GitHub as Issues. The design already commits to one subagent per Information System producing that system's own report (the two-tier report split), and to the agent being triggered by commits to this repository's data files rather than only on a fixed schedule.

That left several concrete questions open, each with a real alternative:

- **Read-tool shape.** A single generic tool parameterized by system name is DRY, but leaves the isolation between subagents resting on the model's discipline rather than on what it can actually call.
- **Trigger granularity.** A commit could always trigger a full read of every source regardless of what changed, or the run could be scoped to only what the commit actually touched.
- **Write access.** Findings could be turned into Issues by the subagent that detected them, or centralized in one place.
- **Detection vs. notification cadence.** Non-Orphaned finding categories are Evidentiary/quarterly by report cadence, which could mean detection itself only happens at the quarterly trigger, or that detection is continuous and only *publication to a human* is cadence-gated.
- **Risk Assessment Entries** (per-category, per-system likelihood × impact synthesis, only ever appearing in the quarterly report) could be computed incrementally alongside Findings, or only at the quarterly trigger.
- **Cross-cycle state** (trend line, quarterly-recurrence check, SLA/re-check logic) needs both "what did the last report say" and "what's open right now," which are answerable from different sources.
- **Partial failure.** One system's malformed export or a failed subagent run could block the whole run's output or only that system's.
- **GitHub integration** could go through a general-purpose GitHub MCP server or through narrow custom tools.

## Decision

1. **Read-tool isolation is structural, not conventional.** One shared read implementation is instantiated as five separate tool bindings, each pre-bound to a single Information System at subagent-creation time, with no `system_name` parameter exposed to the model. Each subagent's tool registry contains only its own binding. HRIS and policy reads are shared, non-isolated tools available to every subagent, since they aren't system-specific — the isolation boundary is about *other systems'* access files, not about HRIS. Each subagent uses its shared HRIS access to detect its own system's findings independently: Orphaned, Drift, and Identity resolution are all per-record HRIS lookups (terminated status, current role, name/email match), and they happen inside that subagent's own isolated context, against its own system's records only. The main agent never re-derives these by combining raw subagent output against HRIS itself (see point 5) — it aggregates findings the subagents already detected.
2. **Read and validate atomically.** `read_access_data` and `read_hris` parse and validate schema (required columns present, `system_name` field matches the file it was read from) in the same step. Malformed data raises a structured error rather than returning unchecked rows for the agent to reason over.
3. **Dispatch is scoped by which file changed, not blanket "read everything, every time."** A commit touching a single Information System's access file triggers only that system's subagent. A commit touching `system_hr.csv`, `policy-config.yaml`, or `role-access-mapping.yaml` fans out to all five subagents, since a joiner/mover/leaver event or a change to the machine-consumed policy inputs has consequences across every system. A commit touching `access-control-policy.md` alone triggers nothing — it's human-readable policy prose the agent doesn't parse, not an input any tool consumes.
4. **Within whatever scope is triggered, reads are always full-file, never incremental.** Finding categories like Dormant and Drift require reasoning over complete current state, not a diff, so partial/incremental reads would be unreliable regardless of dispatch scope.
5. **The main agent is the sole entry point for every triggered run**, regardless of whether dispatch resolves to one subagent or five. It invokes the relevant subagent(s), receives their findings as data, runs the grounding/citation validation exactly once per run, and is the only holder of GitHub write tools (`open_issue`, `close_issue`, `apply_label`, `add_comment`, `create_release`). Subagents never write to GitHub directly.
6. **Detection is continuous; only notification is cadence-gated.** Every triggered run performs full reconciliation across all finding categories for whatever scope was dispatched, and opens Issues immediately on detection — not just for Orphaned. The quarterly audit report is a rollup of Issue-tracker state that already exists by the time it runs, not the first moment most Findings come into being. Orphaned's same-day SLA and escalation remain the one category with its own real-time human notification; every other category still only surfaces to a person at the next quarterly report.
7. **Risk Assessment Entries are computed only at the quarterly-audit trigger**, by the main agent, from accumulated Issue state plus a `read_prior_report` read — not maintained incrementally per-commit the way Findings now are. It's a periodic synthesis by nature, not a fact about current state.
8. **Cross-cycle state uses two distinct tools for two distinct questions.** `read_prior_report` is a local file read from the repo checkout (the committed report history), answering "what did we report last time" for the trend line and quarterly-recurrence check. `list_issues` is a live GitHub read, filtered by label/category/state, answering "what's open right now" for the re-check/auto-close logic and the Orphaned SLA check.
9. **Partial failure is loud and scoped to the affected system.** If one Information System's data is malformed or its subagent run fails, the main agent still publishes what it has for the other systems, with an explicit failed-system line, rather than aborting the entire run.
10. **GitHub integration is direct API calls as narrow custom tools** (Issues and Releases only), not a general-purpose GitHub MCP server.

## Consequences

- Isolation and least-privilege are properties a reviewer can verify by reading the tool registry itself — which tools exist and who holds them — rather than claims about how subagents are prompted to behave.
- One validation chokepoint for all Issue-writing holds regardless of how many systems a given run touches, at the cost of the main agent being invoked even on single-system runs where it only orchestrates one subagent.
- `CONTEXT.md`'s claim that the Reviewer has "standing read access to all Findings as they occur" is actually true of the implementation, not just asserted — Findings and their Issues exist from the moment a relevant commit is processed, not only from the next quarterly boundary.
- The agent now runs considerably more often than "once a quarter" — every commit to a relevant file is a real run performing full reconciliation. The still-unpinned tool-call/iteration cap (deferred, to be set from real run data) needs to account for many small, frequent runs, not just large quarterly ones.
- A future capability needing a *live* cross-quarter Issue trend (as opposed to a point-in-time comparison against the last committed report) would need both cross-cycle tools together, not either alone.
