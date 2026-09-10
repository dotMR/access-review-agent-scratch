# Access Review — Salesforce — 2026-Q1

**Report generated:** 2026-09-10T07:37:04.764570+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q1
**Asset Owner:** TBD
**Committed to:** `reports/2026-Q1/salesforce.md`

One of these is generated per Information System (AWS, GitHub, Salesforce, Finance ERP, VPN) each quarter. This is the line-item evidence; the aggregated Quarterly Audit Report links to these rather than repeating their contents.

## Summary

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 0 | 0 | 0 | 0 |
| Dormant admin-level access | 0 | 0 | 0 | 0 |
| Unapproved access | 0 | 0 | 0 | 0 |
| Identity resolution | 0 | 0 | 0 | 0 |
| Drift | 0 | 0 | 0 | 0 |
| Dormant ad-hoc access | 1 | 1 | 0 | 2 |
| **Total** | 1 | 1 | 0 | 2 |

## Findings

### Orphaned access

| Identity | Access detail | Expected per policy | Date detected | Time to revoke | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Dormant admin-level access (90-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

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
| Sleve McDichael | `read` access to salesforce | Role baseline is 'none'; ad-hoc grant unused &gt; 180 consecutive days | 2026-02-11 | 210 | Remediated | [#13](https://github.com/dotMR/access-review-agent-scratch/issues/13) |
| Sleve McDichael | `read` access to salesforce | Role baseline is 'none'; ad-hoc grant unused &gt; 180 consecutive days | 2026-02-11 | 210 | Open | [#9](https://github.com/dotMR/access-review-agent-scratch/issues/9) |

## Sign-off

I attest that the findings above for Salesforce have been reviewed and, where applicable, remediated or formally accepted as risk.

**Asset Owner:** TBD
**Date:** _(pending sign-off)_
