# Quarterly Access Review Audit Report — 2026-Q2

**Report generated:** 2026-09-10T07:55:06.176776+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q2
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/2026-Q2/aggregate.md`

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
| Drift | AWS | Medium | Medium | Medium | AWS drift issues show a pattern of resolution followed by emergence. Issue &#35;6 recurred across prior audit cycles but has been successfully remediated, demonstrating closure of a persistent control gap. Issue &#35;16 is a newly surfaced isolated finding. No process-level treatment action is warranted, as the recurring issue has been addressed and the current finding does not yet establish a recurring pattern. |
| Unapproved access | AWS | Medium | Medium | Medium | This unapproved access risk for AWS is represented by two distinct issues: &#35;5, which was open across two consecutive prior audits but has since been remediated, and &#35;15, newly surfaced in this audit. The successful remediation of &#35;5 addresses the previously recurring approval gap. &#35;15 remains isolated to this single audit, so no process-level treatment recommendation is warranted at this time. |
| Orphaned access | AWS | Medium | Medium | Medium | Orphaned AWS resources demonstrate a recurring pattern, with Issues &#35;3, &#35;2, and &#35;1 each appearing across 2 consecutive audits; Issue &#35;14 is an isolated one-time remediation within this audit cycle. The multi-audit presence of &#35;3 and &#35;2 (both now remediated) and the ongoing status of &#35;1 (accepted as an open risk) indicate systematic gaps in resource lifecycle management or orphan detection. Process-level improvements to AWS resource governance—such as enhanced inventory controls, automated orphan detection, or enforced lifecycle tagging—are warranted to interrupt this recurring pattern. |
| Dormant admin-level access | AWS | Medium | High | High | Issue &#35;4 reflects a recurring pattern of dormant administrative access on AWS that has persisted across two consecutive audits. While formally accepted as risk, the continuation across audit cycles indicates this exposure warrants a process-level response beyond one-time acceptance. A defined remediation roadmap with specific deprovisioning targets—or, if risk acceptance remains justified, an annually-refreshed control review with documented compensating measures—should be established to manage the High risk rating through active monitoring rather than passive acceptance. |
| Identity resolution | GitHub | Low | Medium | Low | Issue &#35;18 (svc-cicd-deploy) represents an isolated identity-resolution gap on github, appearing only in the current audit cycle. Without evidence of persistence across multiple audits, no process-level treatment is indicated. Standard operational remediation of this access anomaly will suffice to resolve the risk. |
| Dormant admin-level access | GitHub | Low | Medium | Low | The dormant-admin/github pairing presents a Low overall risk rating, reflecting low likelihood of unauthorized access despite medium potential impact. Issue &#35;17 remains open but constitutes an isolated finding within the current audit cycle, with no established recurrence pattern across consecutive reviews. Process-level treatment is not warranted at this stage given the absence of recurring findings. |
| Dormant ad-hoc access | Salesforce | Low | Low | Low | Both findings in this row are isolated to the current audit: Issue &#35;13 has already been remediated, and Issue &#35;9 is open but appears for the first time this cycle. With neither issue spanning multiple consecutive audits, there is no recurring pattern to trigger process-level treatment actions. The isolated status of these findings, combined with the Low risk rating, indicates that standard operational closure of Issue &#35;9 is the appropriate response without systemic control intervention. |
| Dormant admin-level access | Finance ERP | Low | High | Medium | The dormant-admin access risk in finance_erp presents a mixed picture. Issue &#35;11 was identified and remediated within this audit cycle, while Issue &#35;10 remains open and represents a newly surfaced concern. Both findings are isolated to a single audit period, indicating neither has established a recurring pattern. Given the lack of persistence across consecutive audits, address Issue &#35;10's remediation directly rather than implementing process-level controls at this time; monitor whether similar issues emerge in the next review cycle. |
| Identity resolution | VPN | Medium | Low | Low | Most identity-resolution issues affecting VPN are isolated: &#35;20 and &#35;19 were both remediated within this audit cycle, while &#35;12 represents an accepted risk decision contained to the current period. However, the billing-sync integration exhibits a recurring pattern, with &#35;8 and &#35;7 appearing across two consecutive audits despite remediation efforts. This persistence suggests the underlying synchronization workflow is not stable; a process-level review of svc-billing-sync identity-resolution logic should be prioritized to prevent further recurrence in future audits. |

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