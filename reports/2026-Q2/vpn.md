# Access Review — VPN — 2026-Q2

**Report generated:** 2026-09-10T07:55:06.176776+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q2
**Asset Owner:** TBD
**Committed to:** `reports/2026-Q2/vpn.md`

One of these is generated per Information System (AWS, GitHub, Salesforce, Finance ERP, VPN) each quarter. This is the line-item evidence; the aggregated Quarterly Audit Report links to these rather than repeating their contents.

## Summary

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 0 | 0 | 0 | 0 |
| Dormant admin-level access | 0 | 0 | 0 | 0 |
| Unapproved access | 0 | 0 | 0 | 0 |
| Identity resolution | 0 | 4 | 1 | 5 |
| Drift | 0 | 0 | 0 | 0 |
| Dormant ad-hoc access | 0 | 0 | 0 | 0 |
| **Total** | 0 | 4 | 1 | 5 |

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
| vpn-legacy-4402 | `granted` access to vpn | `unresolved` | `Empty provisioning_note and legacy identifier 'vpn-legacy-4402' that does not correspond to any HRIS employee_id. Approval metadata only indicates it is a pre-dated legacy grant with no specific owner named.` | 2026-09-09 | Remediated | [#20](https://github.com/dotMR/access-review-agent-scratch/issues/20) |
| vpn-legacy-4402 | `granted` access to vpn | `unresolved` | `Provisioning note is empty, and the legacy identifier 'vpn-legacy-4402' provides no name or description that could be matched to a specific active HRIS employee. Insufficient evidence to confidently resolve to an individual.` | 2026-09-09 | Remediated | [#19](https://github.com/dotMR/access-review-agent-scratch/issues/19) |
| vpn-legacy-4402 | `granted` access to vpn | `unresolved` | `The record has an empty provisioning_note and a legacy identifier from 2019 that does not match any HRIS employee_id. No provisioning documentation exists to identify the account owner or justify its continued active status.` | 2026-09-09 | Accepted risk | [#12](https://github.com/dotMR/access-review-agent-scratch/issues/12) |
| svc-billing-sync | `granted` access to vpn | `stale-ownership` | `The provisioning_note identifies this as a service account for 'nightly billing sync' with owner Marcus Webb, but Marcus Webb (E6003) has terminated status in HRIS with end_date 2026-07-01.` | 2026-09-09 | Remediated | [#8](https://github.com/dotMR/access-review-agent-scratch/issues/8) |
| svc-billing-sync | `granted` access to vpn | `stale-ownership` | `Provisioning note identifies this as a service account owned by Marcus Webb (E6003), but Marcus Webb's HRIS record shows status 'terminated' with end_date 2026-07-01, prior to today (2026-09-09).` | N/A | Remediated | [#7](https://github.com/dotMR/access-review-agent-scratch/issues/7) |

### Drift

| Identity | Access detail | Expected per policy | Role changed | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | |

### Dormant ad-hoc access (180-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| No findings | | | | | | |

## Sign-off

I attest that the findings above for VPN have been reviewed and, where applicable, remediated or formally accepted as risk.

**Asset Owner:** TBD
**Date:** _(pending sign-off)_
