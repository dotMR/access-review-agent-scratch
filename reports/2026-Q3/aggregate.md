# Quarterly Access Review Audit Report — 2026-Q3

**Report generated:** 2026-09-10T08:30:42.092451+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q3
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/2026-Q3/aggregate.md`

This is the formal audit-evidence record for the period, the rollup of the five per-system reports below. It does not repeat their line-item findings, only aggregates and links to them, so the two can never drift out of sync with each other.

## Executive summary

20 findings identified this quarter across 6 finding categories and 5 Information Systems. 11 remediated, 6 open, 3 accepted as risk. 20 finding(s) this quarter vs. 20 last quarter (+0)

## Methodology

The Access Review Agent performed an automated cross-reference of each Information System's access records (Access/IT System) against the HRIS and the Access Policy Repository, per the Operational review and Compliance review Principles in access-control-policy.md. Findings are categorized per policy: orphaned, dormant (admin-level), unapproved, identity resolution, and drift access.

## Resolution status by system

| System | Open | Remediated | Accepted risk | Total | Detail |
| :-- | --: | --: | --: | --: | :-- |
| AWS | 2 | 5 | 2 | 9 | [aws.md](./aws.md) |
| GitHub | 2 | 0 | 0 | 2 | [github.md](./github.md) |
| Salesforce | 1 | 1 | 0 | 2 | [salesforce.md](./salesforce.md) |
| Finance ERP | 1 | 1 | 0 | 2 | [finance-erp.md](./finance-erp.md) |
| VPN | 0 | 4 | 1 | 5 | [vpn.md](./vpn.md) |
| **Total** | 6 | 11 | 3 | 20 | |

## Findings by category (aggregate)

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 0 | 3 | 1 | 4 |
| Dormant admin-level access | 2 | 1 | 1 | 4 |
| Unapproved access | 1 | 1 | 0 | 2 |
| Identity resolution | 1 | 4 | 1 | 6 |
| Drift | 1 | 1 | 0 | 2 |
| Dormant ad-hoc access | 1 | 1 | 0 | 2 |

Line-item detail for every finding lives in the per-system reports linked above and in the Appendix, not here.

## Risk Assessment

| Category | System | Likelihood | Impact | Risk Rating | Narrative & treatment recommendation |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Drift | AWS | High | Medium | High | AWS access drift is a recurring issue affecting multiple users across consecutive audit periods. Issue &#35;16 for Karl Dandleton remains unresolved in its second consecutive audit, while Issue &#35;6 for Harriet Boone was only remediated in this cycle after appearing for three consecutive audits. Given this persistent drift pattern, process-level automated compliance controls should be implemented to prevent recurrence and reduce manual remediation burden across future audits. |
| Unapproved access | AWS | High | Medium | High | Issue &#35;15 presents a recurring risk, having remained open across two consecutive audit cycles for the aws system. While Issue &#35;5 was eventually remediated after spanning three audits, the persistence of &#35;15 demonstrates that previous corrective actions have not fully addressed the root cause of unapproved access gaps. A process-level remediation plan with defined timelines and accountability is warranted to close this recurring finding and prevent continued recurrence in approval controls. |
| Orphaned access | AWS | High | Medium | High | Orphaned AWS access is a recurring condition within this system category, with Issues &#35;2 and &#35;3 appearing across three consecutive audits before remediation, and Issue &#35;14 across two before closure. Issue &#35;1 persists across three consecutive audits as an accepted risk, warranting periodic re-validation to ensure the risk rationale remains justified and organizational risk tolerance is actively maintained. |
| Dormant admin-level access | AWS | High | High | Critical | Issue &#35;4 remains open across three consecutive audits, indicating a persistent risk pattern in dormant AWS administrative access. Although categorized as an accepted risk, the recurring nature across multiple audit cycles suggests the need for formalized periodic reassessment of whether the original acceptance rationale and compensating controls remain adequate. Consider implementing a structured review cadence for accepted risks of this severity to ensure the acceptance decision stays current and justified. |
| Identity resolution | GitHub | Medium | Medium | Medium | This identity-resolution finding on GitHub is recurring: Issue &#35;18 has remained open across both the prior and current audit cycles, indicating an unresolved access-control gap. Given the persistent nature of this issue spanning 2 consecutive audits, a targeted remediation plan with defined ownership and resolution timeline should be established to prevent continued exposure in future audit periods. The medium risk rating warrants prioritized action to close this finding before the next assessment. |
| Dormant admin-level access | GitHub | Medium | Medium | Medium | Dormant administrative access to GitHub is a recurring finding, with Issue &#35;17 remaining open across two consecutive audit cycles. This persistence indicates systemic gaps in access removal procedures for deactivated accounts. A formal remediation process should be established to address this recurring pattern, including defined timelines for dormant admin access removal and verification procedures following account deactivation. |
| Dormant ad-hoc access | Salesforce | Medium | Low | Low | Issue &#35;9 constitutes a recurring finding, remaining open across two consecutive audits and indicating a persistent gap in Salesforce dormant account access controls. While the similarly-recurring Issue &#35;13 was remediated, demonstrating partial progress, the unresolved status of Issue &#35;9 suggests incomplete remediation of the underlying process failure. Formalized dormant-account detection and re-validation workflows are recommended to address this recurring pattern and prevent future violations. |
| Dormant admin-level access | Finance ERP | Medium | High | High | Dormant administrative access to finance_erp exhibits a recurring pattern, with findings persisting across two consecutive audits. While Issue &#35;11 has been remediated, Issue &#35;10 remains open, indicating incomplete resolution of the underlying dormant-account governance gap. We recommend implementing a quarterly administrative access re-certification process for finance_erp to prevent recurrence of this pattern. |
| Identity resolution | VPN | High | Low | Medium | Identity-resolution issues in VPN represent a recurring pattern rather than isolated incidents, with vpn-legacy-4402 problems in &#35;20, &#35;19, and &#35;12 spanning two consecutive audits and svc-billing-sync problems in &#35;8 and &#35;7 spanning three consecutive audits. Although these have been individually remediated or accepted as risk, their recurrence across audit periods indicates that the current handling approach does not prevent repeat occurrences. Implement a process-level control to systematically address the root cause of identity-resolution failures in VPN systems. |

## Escalations this period

| Finding | System | Category | Open since | Escalated | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Alex Rivera | AWS | Orphaned access | 2026-09-08T19:51:01+00:00 | 2026-09-09T10:18:00+00:00 | [#1](https://github.com/dotMR/access-review-agent-scratch/issues/1) |

## Reviewer attestation

I have reviewed this report and the underlying per-system reports, and accept this as the formal audit-evidence record for the period stated above.

**Security/Compliance Reviewer:** TBD
**Date:** _(pending sign-off)_

## Appendix

- Per-system reports: [AWS](./aws.md) · [GitHub](./github.md) · [Salesforce](./salesforce.md) · [Finance ERP](./finance-erp.md) · [VPN](./vpn.md)
- Data snapshot: N/A (manual/local run)
- PDF export: bundled as a Release asset (`aggregate.pdf`) alongside the tagged commit - see the Releases page for this period, not this Markdown file's own directory.

---
<!-- Out of scope (not shown in this report): Dormant admin-level's, Dormant ad-hoc's, and Drift's own monthly Operational/SLA variants, and the Unapproved-access grant-time gate — see SPEC.md §8. -->