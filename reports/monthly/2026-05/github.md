# Monthly Operational Flags — GitHub — 2026-05

**Report generated:** 2026-09-10T07:06:51.004941+00:00
**Asset Owner:** TBD
**Committed to:** `reports/monthly/2026-05/github.md`

An informational nudge, not a compliance deadline. Lists every currently open Finding for GitHub, any category — including Orphaned. Orphaned doesn't need this report to surface it (it already gets its own same-day notice, and may already have escalated), but if one is still open, it belongs in the complete picture here too.

This report runs a full reconciliation check every month, the same detection logic as any other run — so even a system with no recent commits still gets a fresh look. That does not change how a Finding it catches is classified: it's still Evidentiary/quarterly, with no SLA of its own, and this report does not gate Escalation or change its category's escalation eligibility.

## Open items

| Category | Identity | Access detail | Expected per policy | Open since | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Identity resolution | svc-cicd-deploy | `write` access to github | Individual Usage — access must be assigned to a specific employee, or a Service Account with a documented, currently-active owner (access-control-policy.md, Individual Usage / Service Account Ownership) | 2026-09-09 | [#18](https://github.com/dotMR/access-review-agent-scratch/issues/18) |
| Dormant admin-level access | Bobson Dugnutt | `admin` access to github | Revoke if unused &gt; 90 consecutive days | 2026-09-09 | [#17](https://github.com/dotMR/access-review-agent-scratch/issues/17) |
