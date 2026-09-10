# Quarterly Access Review Audit Report — 2026-Q1

**Report generated:** 2026-09-10T07:37:04.764570+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q1
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/2026-Q1/aggregate.md`

This is the formal audit-evidence record for the period, the rollup of the five per-system reports below. It does not repeat their line-item findings, only aggregates and links to them, so the two can never drift out of sync with each other.

## Executive summary

20 findings identified this quarter across 6 finding categories and 5 Information Systems. 11 remediated, 6 open, 3 accepted as risk. N/A, no prior period

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
| Drift | AWS | Low | Medium | Low | AWS drift findings in this audit are isolated to a single audit cycle, with no recurring pattern evident. Issue &#35;6 (Harriet Boone) has already been remediated, while Issue &#35;16 (Karl Dandleton) remains open but represents a one-off detection rather than a systemic recurrence. Given the Low risk rating and the isolated nature of these findings, no process-level treatment action is warranted at this time; standard remediation procedures for the open item should suffice. |
| Unapproved access | AWS | Low | Medium | Low | The unapproved access pattern for AWS presents as isolated to this audit cycle, with one ongoing finding (&#35;15) and one issue that has already been remediated (&#35;5). Neither finding exhibits a recurring pattern across consecutive audits, as both appear for the first time in this assessment period. With the remediation of &#35;5 already complete, no systemic process-level treatment is warranted at this time; continued monitoring of &#35;15's resolution status in the next audit will establish whether this represents a recurring control gap requiring procedural intervention. |
| Orphaned access | AWS | Low | Medium | Low | All findings in this row are isolated to the current audit cycle with no recurrence pattern across prior audits. Three issues (&#35;14, &#35;3, &#35;2) have been remediated and one (&#35;1) has been accepted as a managed risk; each appears for the first time this audit and shows no persistence history. Since no issues demonstrate a pattern of opening across multiple consecutive audits, no process-level treatment action is warranted—existing closure and risk-acceptance decisions are sufficient. |
| Dormant admin-level access | AWS | Low | High | Medium | Dormant administrative access in AWS creates a Medium-level risk from the combination of low exploitation likelihood and high operational impact. Issue &#35;4 represents an isolated finding in this audit cycle, with no pattern of recurrence across consecutive audit periods. Given its isolated nature, process-level remediation is not warranted; the documented accepted risk serves as the organization's current tolerance decision for this exposure. |
| Identity resolution | GitHub | Low | Medium | Low | The identity-resolution process for GitHub shows a single finding in this audit: Issue &#35;18 affecting the svc-cicd-deploy account. This appears to be an isolated occurrence rather than a recurring pattern, as it has emerged only in the current audit cycle with no history across prior consecutive audits. No process-level treatment recommendation is warranted at this stage; resolution should be tracked through standard remediation channels until closure is confirmed in the next audit cycle. |
| Dormant admin-level access | GitHub | Low | Medium | Low | The dormant-admin access in GitHub represents an isolated finding in the current audit. Issue &#35;17 was identified as open in this period but does not reflect a recurring pattern, appearing only once across the audit cycle. No process-level treatment is recommended; monitoring of this single issue &#35;17 should suffice pending its resolution within the standard remediation timeline. |
| Dormant ad-hoc access | Salesforce | Low | Low | Low | Both issues (&#35;13, &#35;9) are isolated to this audit cycle rather than indicators of a persistent pattern. Issue &#35;13 was remediated during the same audit, while Issue &#35;9 remains open and requires resolution. Without evidence of recurring findings across multiple audit periods, no ongoing process-level treatment action is recommended. |
| Dormant admin-level access | Finance ERP | Low | High | Medium | For the **dormant-admin** access in **finance_erp**, both identified issues (&#35;11 and &#35;10) are isolated findings appearing in a single audit cycle with no indication of prior occurrences. Issue &#35;11 has already been remediated, demonstrating responsiveness within the audit period, while Issue &#35;10 remains open but represents a first-time finding. No process-level treatment is warranted at this time, as the pattern does not demonstrate recurrence across multiple consecutive audits that would indicate systemic control gaps. |
| Identity resolution | VPN | Low | Low | Low | Identity-resolution gaps in the VPN system appear as an isolated finding confined to this audit cycle, with no persistence from prior cycles. Four of the five flagged issues (&#35;20, &#35;19, &#35;8, &#35;7) were remediated within this audit period, while one (&#35;12, vpn-legacy-4402) was accepted as a known risk. Because all issues span only a single audit and have been resolved or formally accepted, no process-level treatment action is warranted at this time. |

## Escalations this period

| Finding | System | Category | Open since | Escalated | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| No escalations this period | | | | | |

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