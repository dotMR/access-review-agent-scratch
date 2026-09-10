# Access Review — GitHub — 2026-Q3

**Report generated:** 2026-09-10T08:18:12.388068+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q3
**Asset Owner:** TBD
**Committed to:** `reports/2026-Q3/github.md`

One of these is generated per Information System (AWS, GitHub, Salesforce, Finance ERP, VPN) each quarter. This is the line-item evidence; the aggregated Quarterly Audit Report links to these rather than repeating their contents.

## Summary

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 0 | 0 | 0 | 0 |
| Dormant admin-level access | 1 | 0 | 0 | 1 |
| Unapproved access | 0 | 0 | 0 | 0 |
| Identity resolution | 1 | 0 | 0 | 1 |
| Drift | 0 | 0 | 0 | 0 |
| Dormant ad-hoc access | 0 | 0 | 0 | 0 |
| **Total** | 2 | 0 | 0 | 2 |

## Findings

### Orphaned access

| Identity | Access detail | Expected per policy | Date detected | Time to revoke | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Dormant admin-level access (90-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Bobson Dugnutt | `admin` access to github | Revoke if unused &gt; 90 consecutive days | 2026-06-06 | 95 | Open | [#17](https://github.com/dotMR/access-review-agent-scratch/issues/17) |

### Unapproved access

| Identity | Access detail | Expected per policy | Date granted | Approved by | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

### Identity resolution

| Access record (`employee_id` or local identifier) | Access detail | Resolution | Evidence cited | Date detected | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| svc-cicd-deploy | `write` access to github | `stale-ownership` | `Service account provisioning note names 'Cecilia Tisio (Platform Engineering)' as accountable owner; Cecilia Tisio (E9301) is found in HRIS but has status 'terminated' as of 2026-09-09.` | 2026-09-09 | Open | [#18](https://github.com/dotMR/access-review-agent-scratch/issues/18) |

### Drift

| Identity | Access detail | Expected per policy | Role changed | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | |

### Dormant ad-hoc access (180-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

## Sign-off

I attest that the findings above for GitHub have been reviewed and, where applicable, remediated or formally accepted as risk.

**Asset Owner:** TBD
**Date:** _(pending sign-off)_
