# Quarterly Access Review Audit Report — 2026-Q2

**Report generated:** 2026-09-10T07:14:14.307194+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q2
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/2026-Q2/aggregate.md`

This is the formal audit-evidence record for the period, the rollup of the five per-system reports below. It does not repeat their line-item findings, only aggregates and links to them, so the two can never drift out of sync with each other.

## Executive summary

21 findings identified this quarter across 6 finding categories and 5 Information Systems. 12 remediated, 6 open, 3 accepted as risk. N/A, no prior period

## Methodology

The Access Review Agent performed an automated cross-reference of each Information System's access records (Access/IT System) against the HRIS and the Access Policy Repository, per the Operational review and Compliance review Principles in access-control-policy.md. Findings are categorized per policy: orphaned, dormant (admin-level), unapproved, identity resolution, and drift access.

## Resolution status by system

| System | Open | Remediated | Accepted risk | Total | Detail |
| :-- | --: | --: | --: | --: | :-- |
| AWS | 2 | 5 | 2 | 9 | [aws.md](./aws.md) |
| GitHub | 2 | 0 | 0 | 2 | [github.md](./github.md) |
| Salesforce | 1 | 1 | 0 | 2 | [salesforce.md](./salesforce.md) |
| Finance ERP | 1 | 2 | 0 | 3 | [finance-erp.md](./finance-erp.md) |
| VPN | 0 | 4 | 1 | 5 | [vpn.md](./vpn.md) |
| **Total** | 6 | 12 | 3 | 21 | |

## Findings by category (aggregate)

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | 0 | 4 | 1 | 5 |
| Dormant admin-level access | 2 | 1 | 1 | 4 |
| Unapproved access | 1 | 1 | 0 | 2 |
| Identity resolution | 1 | 4 | 1 | 6 |
| Drift | 1 | 1 | 0 | 2 |
| Dormant ad-hoc access | 1 | 1 | 0 | 2 |

Line-item detail for every finding lives in the per-system reports linked above and in the Appendix, not here.

## Risk Assessment

| Category | System | Likelihood | Impact | Risk Rating | Narrative & treatment recommendation |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Drift | AWS | Medium | Medium | Medium | Issue &#35;6 (Harriet Boone) appeared across consecutive audits but has been remediated, indicating effective prior corrective action. Issue &#35;16 (Karl Dandleton) is an isolated finding appearing only in this audit cycle. No process-level treatment action is warranted, as the previously recurring exposure has been resolved and the current finding has not yet demonstrated persistence across multiple audit periods. |
| Unapproved access | AWS | Medium | Medium | Medium | Issue &#35;5 (Luis Ferreira) represents a recurring pattern, appearing across two consecutive audits before being remediated. Issue &#35;15 (Mike Truk) is an isolated, newly identified finding that remains open. Since the recurring concern has been resolved through remediation and the current issue is a one-time occurrence, no process-level treatment intervention is warranted. |
| Orphaned access | AWS | Medium | Medium | Medium | Orphaned AWS access demonstrates a recurring pattern, with issues &#35;3, &#35;2, and &#35;1 each open across two consecutive audits. While &#35;3 and &#35;2 have been remediated, &#35;1 remains as an accepted risk, and issue &#35;14 appears isolated to this audit. Process-level improvements to AWS access de-provisioning procedures are warranted to address this recurring pattern. |
| Dormant admin-level access | AWS | Medium | High | High | The dormant-admin pattern in AWS represents a recurring risk exposure, with Issue &#35;4 persisting as an accepted-risk finding across the prior audit and this quarter's review. Given the high impact of unmonitored administrative credentials against a medium likelihood of exploitation, this sustained gap warrants formalization of compensating controls: establish a quarterly attestation process requiring AWS account owners to certify the business justification for dormant admin roles, or commit to their removal within a defined remediation window. Until the underlying access rationalization is completed, documented acceptance and active monitoring should replace passive acceptance across consecutive quarters. |
| Identity resolution | GitHub | Low | Medium | Low | Issue &#35;18 on the GitHub system represents an isolated identity-resolution finding, present only in this current audit with no evidence of recurrence. As this is a one-time incident rather than a recurring pattern, no process-level treatment action is recommended. The finding should be closed through standard operational procedures. |
| Dormant admin-level access | GitHub | Low | Medium | Low | Issue &#35;17 appears as a new finding in the current audit period, representing an isolated occurrence rather than a persistent pattern across multiple audits. The dormant-admin access on github carries a low overall risk rating, combining low likelihood with medium potential impact. Standard monitoring through the regular audit cycle is sufficient; no escalated remediation process is warranted for this one-off finding. |
| Dormant ad-hoc access | Salesforce | Low | Low | Low | The Salesforce dormant ad-hoc access risk remains isolated to this audit cycle, with no recurring pattern established. Issue &#35;13 has been remediated, while Issue &#35;9 remains open but does not yet demonstrate persistence across multiple audits necessary for systemic process treatment. Monitor Issue &#35;9 for closure in the next audit; if it persists into a second consecutive audit, escalate to process-level review. No recurring treatment action is warranted at this time. |
| Orphaned access | Finance ERP | Low | High | Medium | **Orphaned access in finance_erp** is a high-impact risk mitigated by low frequency. Issue &#35;21 (Glenallen Mixon) represents an isolated occurrence, appearing and resolving within a single audit cycle. The remediation is complete and no recurring pattern is evident. No process-level action is warranted at this time; standard monitoring should confirm the issue does not resurface. |
| Dormant admin-level access | Finance ERP | Low | High | Medium | This category shows two findings from the current audit cycle with no recurring pattern: Issue &#35;11 has been remediated, while Issue &#35;10 remains open. Since neither finding spans multiple consecutive audits, this represents an isolated set of issues rather than a systemic control concern and does not warrant process-level remediation recommendation at this time. |
| Identity resolution | VPN | Medium | Low | Low | Identity-resolution findings in the VPN environment are predominantly isolated; issues &#35;20, &#35;19, and &#35;12 were remediated or risk-accepted within this audit cycle. Issues &#35;8 and &#35;7 (svc-billing-sync), however, recur across 2 consecutive audits despite remediation status, indicating a persistent gap in the identity-sync mechanism. Process-level review of the billing-sync integration control logic and identity enrichment validation is warranted to prevent further recurrence. |

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
- PDF export: bundled as a Release asset (`aggregate.pdf`) alongside the tagged commit - see the Releases page for this period, not this Markdown file's own directory.

---
<!-- Out of scope (not shown in this report): Dormant admin-level's, Dormant ad-hoc's, and Drift's own monthly Operational/SLA variants, and the Unapproved-access grant-time gate — see SPEC.md §8. -->