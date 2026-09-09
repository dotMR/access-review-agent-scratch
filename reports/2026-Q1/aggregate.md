# Quarterly Access Review Audit Report — 2026-Q1

**Report generated:** 2026-09-09T09:20:22.924311+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q1
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/2026-Q1/aggregate.md`

This is the formal audit-evidence record for the period, the rollup of the five per-system reports below. It does not repeat their line-item findings, only aggregates and links to them, so the two can never drift out of sync with each other.

## Executive summary

8 findings identified this quarter across 6 finding categories and 5 Information Systems. 4 remediated, 3 open, 1 accepted as risk. N/A, no prior period

## Methodology

The Access Review Agent performed an automated cross-reference of each Information System's access records (Access/IT System) against the HRIS and the Access Policy Repository, per the Operational review and Compliance review Principles in access-control-policy.md. Findings are categorized per policy: orphaned, dormant (admin-level), unapproved, identity resolution, and drift access.

## Resolution status by system

| System | Open | Remediated | Accepted risk | Total | Detail |
| :-- | --: | --: | --: | --: | :-- |
| AWS | 2 | 3 | 1 | 6 | [aws.md](./aws.md) |
| GitHub | 0 | 0 | 0 | 0 | [github.md](./github.md) |
| Salesforce | 0 | 0 | 0 | 0 | [salesforce.md](./salesforce.md) |
| Finance ERP | 0 | 0 | 0 | 0 | [finance-erp.md](./finance-erp.md) |
| VPN | 1 | 1 | 0 | 2 | [vpn.md](./vpn.md) |
| **Total** | 3 | 4 | 1 | 8 | |

## Findings by category (aggregate)

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 1 | 2 | 0 | 3 |
| Dormant admin-level access | 0 | 0 | 1 | 1 |
| Unapproved access | 0 | 1 | 0 | 1 |
| Identity resolution | 1 | 1 | 0 | 2 |
| Drift | 1 | 0 | 0 | 1 |
| Dormant ad-hoc access | 0 | 0 | 0 | 0 |

Line-item detail for every finding lives in the per-system reports linked above and in the Appendix, not here.

## Risk Assessment

_Not yet implemented — lands in Milestone 8. No rows below are a real computation._

| Category | System | Likelihood | Impact | Risk Rating | Narrative & treatment recommendation |
| :-- | :-- | :-- | :-- | :-- | :-- |

## Escalations this period

_Not yet implemented — lands in Milestone 9. No rows below are a real computation._

| Finding | System | Category | Open since | Escalated | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |

## Reviewer attestation

I have reviewed this report and the underlying per-system reports, and accept this as the formal audit-evidence record for the period stated above.

**Security/Compliance Reviewer:** TBD
**Date:** _(pending sign-off)_

## Appendix

- Per-system reports: [AWS](./aws.md) · [GitHub](./github.md) · [Salesforce](./salesforce.md) · [Finance ERP](./finance-erp.md) · [VPN](./vpn.md)
- Data snapshot: N/A (manual/local run)
- PDF export: _not yet implemented (out of scope per SPEC.md §8's Deferred section)_

---
<!-- Out of scope (not shown in this report): Dormant admin-level's, Dormant ad-hoc's, and Drift's own monthly Operational/SLA variants, and the Unapproved-access grant-time gate — see SPEC.md §8. -->