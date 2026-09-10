# Access Review — Finance ERP — 2026-Q3

**Report generated:** 2026-09-10T08:30:42.092451+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q3
**Asset Owner:** TBD
**Committed to:** `reports/2026-Q3/finance_erp.md`

One of these is generated per Information System (AWS, GitHub, Salesforce, Finance ERP, VPN) each quarter. This is the line-item evidence; the aggregated Quarterly Audit Report links to these rather than repeating their contents.

## Summary

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 0 | 0 | 0 | 0 |
| Dormant admin-level access | 1 | 1 | 0 | 2 |
| Unapproved access | 0 | 0 | 0 | 0 |
| Identity resolution | 0 | 0 | 0 | 0 |
| Drift | 0 | 0 | 0 | 0 |
| Dormant ad-hoc access | 0 | 0 | 0 | 0 |
| **Total** | 1 | 1 | 0 | 2 |

## Findings

### Orphaned access

| Identity | Access detail | Expected per policy | Date detected | Time to revoke | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Dormant admin-level access (90-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Dana Whitfield | `admin` access to finance_erp | Revoke if unused &gt; 90 consecutive days | 2026-04-22 | 140 | Remediated | [#11](https://github.com/dotMR/access-review-agent-scratch/issues/11) |
| Dana Whitfield | `admin` access to finance_erp | Revoke if unused &gt; 90 consecutive days | 2026-04-22 | 140 | Open | [#10](https://github.com/dotMR/access-review-agent-scratch/issues/10) |

### Unapproved access

| Identity | Access detail | Expected per policy | Date granted | Approved by | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Identity resolution

| Access record (`employee_id` or local identifier) | Access detail | Resolution | Evidence cited | Date detected | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Drift

| Identity | Access detail | Expected per policy | Role changed | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | |

### Dormant ad-hoc access (180-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

## Sign-off

I attest that the findings above for Finance ERP have been reviewed and, where applicable, remediated or formally accepted as risk.

**Asset Owner:** TBD
**Date:** _(pending sign-off)_
