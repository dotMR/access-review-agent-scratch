# Monthly Operational Flags — {{SYSTEM_NAME}} — {{PERIOD}}

**Report generated:** {{GENERATED_TIMESTAMP}}
**Asset Owner:** {{ASSET_OWNER_NAME}}
**Committed to:** `reports/monthly/{{PERIOD}}/{{SYSTEM_NAME}}.md`

An informational nudge, not a compliance deadline. Lists every currently open Finding for {{SYSTEM_NAME}}, any category — including Orphaned. Orphaned doesn't need this report to *surface* it (it already gets its own same-day notice, and may already have escalated), but if one is still open, it belongs in the complete picture here too, same as everything else — this report documents current state, it doesn't gate what gets into it by how a finding was originally noticed.

This report runs a full reconciliation check every month, the same detection logic as any other run — so even a system with no recent commits still gets a fresh look, rather than waiting until next quarter. That does **not** change anything about how a Finding it catches is classified: it's still Evidentiary/quarterly, with no SLA of its own, and this report does **not** gate Escalation or change its category's escalation eligibility (see `access-control-policy.md`'s Unremediated findings Principle) — it's committed directly, no PR, no review gate, no sign-off required.

## Open items

| Category | Identity | Access detail | Expected per policy | Open since | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| {{category}} | {{employee_name}} | {{access_level}} | {{expected}} | {{date_first_flagged}} | [#{{issue_number}}]({{issue_url}}) |

*Empty is a valid, good state — show "No open items" explicitly rather than omitting this section.*

---
<!-- This system's subagent runs full reconciliation first (same as a push-triggered run), then this report is compiled from the results, filtered to open state, no category exclusion, Orphaned included — see ADR-0003. Committed directly via commit_report, no PR/review gate — informational only, not evidentiary; no SLA or Escalation eligibility follows from being caught here. -->
