# Access Review — AWS — 2026-Q1

**Report generated:** 2026-09-09T09:20:22.924311+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q1
**Asset Owner:** TBD
**Committed to:** `reports/2026-Q1/aws.md`

One of these is generated per Information System (AWS, GitHub, Salesforce, Finance ERP, VPN) each quarter. This is the line-item evidence; the aggregated Quarterly Audit Report links to these rather than repeating their contents.

## Summary

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 1 | 2 | 0 | 3 |
| Dormant admin-level access | 0 | 0 | 1 | 1 |
| Unapproved access | 0 | 1 | 0 | 1 |
| Identity resolution | 0 | 0 | 0 | 0 |
| Drift | 1 | 0 | 0 | 1 |
| Dormant ad-hoc access | 0 | 0 | 0 | 0 |
| **Total** | 2 | 3 | 1 | 6 |

## Findings

### Orphaned access

| Identity | Access detail | Expected per policy | Date detected | Time to revoke | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Alex Rivera | `write` access to aws | None (terminated 2026-08-01) | 2026-09-09 | same day as detection (Orphaned SLA — access-control-policy.md, Operational review) | Open | [#3](https://github.com/dotMR/access-review-agent-scratch/issues/3) |
| Alex Rivera | write access to aws | None (terminated 2026-08-01) | 2026-09-08 | same day as detection (Orphaned SLA — access-control-policy.md, Operational review) | Remediated | [#2](https://github.com/dotMR/access-review-agent-scratch/issues/2) |
| Alex Rivera | write access to aws | None (terminated 2026-08-01) | 2026-09-08 | same day as detection (Orphaned SLA — access-control-policy.md, Operational review) | Remediated | [#1](https://github.com/dotMR/access-review-agent-scratch/issues/1) |

### Dormant admin-level access (90-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Priya Anand | `admin` access to aws | Revoke if unused > 90 consecutive days | 2026-06-05 | 95 | Accepted risk | [#4](https://github.com/dotMR/access-review-agent-scratch/issues/4) |

### Unapproved access

| Identity | Access detail | Expected per policy | Date granted | Approved by | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Luis Ferreira | `write` access to aws | A recorded approval (auto or Asset Owner) on file | 2024-01-15 | none on file | Remediated | [#5](https://github.com/dotMR/access-review-agent-scratch/issues/5) |

### Identity resolution

| Access record (`employee_id` or local identifier) | Access detail | Resolution | Evidence cited | Date detected | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Drift

| Identity | Access detail | Expected per policy | Role changed | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Harriet Boone | `write` access to aws | 'admin' (baseline for current role 'Asset Owner') | `2026-07-01`: `Software Engineer` → `Asset Owner` | Open | [#6](https://github.com/dotMR/access-review-agent-scratch/issues/6) |

### Dormant ad-hoc access (180-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

## Sign-off

I attest that the findings above for AWS have been reviewed and, where applicable, remediated or formally accepted as risk.

**Asset Owner:** TBD
**Date:** _(pending sign-off)_
