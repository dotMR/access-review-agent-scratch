# Quarterly Access Review Audit Report — 2026-Q3

**Report generated:** 2026-09-10T08:18:12.388068+00:00
**Data snapshot:** N/A (manual/local run)
**Model:** Tier 1 (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift): plain Python, no model call (ADR-0006). Tier 2 (Identity resolution): claude-haiku-4-5-20251001 via the Agent SDK.
**Reporting period:** 2026-Q3
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/2026-Q3/aggregate.md`

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
| Drift | AWS | High | Medium | High | AWS IAM drift represents a recurring control vulnerability, with Issue &#35;16 (Karl Dandleton) remaining open across 2 consecutive audit cycles and Issue &#35;6 (Harriet Boone) having persisted across 3 consecutive audits before recent remediation. This pattern indicates a systemic detection and response gap rather than isolated incidents. Process-level improvements to drift monitoring and remediation workflows are warranted to prevent ongoing exposure. |
| Unapproved access | AWS | High | Medium | High | Unapproved AWS access issues present a recurring governance challenge. Issue &#35;15 is currently open and persists across two consecutive audits, indicating an active, unresolved compliance gap, while Issue &#35;5 was similarly open across three audit cycles before recent remediation. Process-level intervention is warranted to strengthen access-approval controls and prevent findings from recurring across multiple audit periods. |
| Orphaned access | AWS | High | Medium | High | Orphaned AWS access represents a recurring risk pattern with no signs of durable resolution. Issues &#35;3, &#35;2, and &#35;1 have persisted across three consecutive audit cycles, while issue &#35;14 has remained open across two audits; despite remediation status on &#35;14, &#35;3, and &#35;2, reemergence across subsequent audits indicates point fixes are not sustaining. Issue &#35;1's acceptance as residual risk across all three cycles further underscores systemic exposure. A formal access governance process—such as automated orphaned-account detection, enforced lifecycle policies, or periodic entitlement re-attestation—is required to break this recurrent pattern. |
| Dormant admin-level access | AWS | High | High | Critical | &#35; Risk Assessment Narrative: dormant-admin / aws

Issue &#35;4 documents dormant admin access on AWS classified as an accepted risk, with this finding open across three consecutive audit cycles. The recurring presence of a critical-rated risk across multiple audit periods indicates a pattern requiring governance strengthening, rather than an isolated exception that was resolved within a single audit window. Establishing a formal re-validation protocol for accepted risks—including documented re-approval at defined intervals—is recommended to ensure continued business justification and enable escalation if risk conditions change.

---

**Rationale:** The pattern here is *recurring* (Issue &#35;4 persists across 3 consecutive audits), not isolated, so a process-level recommendation is appropriate. The issue is not about remediating the access itself (which has been accepted), but about formalizing the governance around *why* it remains accepted and ensuring that acceptance is periodically re-confirmed rather than assumed to remain valid indefinitely. |
| Identity resolution | GitHub | Medium | Medium | Medium | The identity-resolution issue for svc-cicd-deploy within GitHub is recurring: Issue &#35;18 has remained open across two consecutive audit cycles, indicating unresolved access provisioning or validation failures. This persistence suggests that standard remediation workflows have been ineffective in closing the gap. Implement a service account identity re-certification process with defined ownership and closure timelines to address this access control gap and prevent recurrence across future audits. |
| Dormant admin-level access | GitHub | Medium | Medium | Medium | Dormant GitHub administrative privileges represent a recurring access-control gap, with issue &#35;17 remaining open across consecutive audit periods. This persistence indicates that earlier remediation efforts have not successfully closed the underlying vulnerability, warranting a process-level intervention. Recommend implementing mandatory automated access reviews for administrative accounts on a defined schedule (e.g., quarterly), with explicit attestation or removal workflows to prevent dormant credentials from accumulating across future audit cycles. |
| Dormant ad-hoc access | Salesforce | Medium | Low | Low | Dormant ad-hoc access to Salesforce demonstrates a recurring pattern, with Issue &#35;13 (remediated) and Issue &#35;9 (open) both appearing across consecutive audit periods. The continued openness of Issue &#35;9 indicates that ad-hoc access governance challenges persist despite prior remediation efforts. Implement a standardized approval workflow with documented periodic recertification requirements to address the root cause and prevent continued recurrence across audit periods. |
| Dormant admin-level access | Finance ERP | Medium | High | High | Dormant administrative access in finance_erp constitutes a recurring compliance concern across consecutive audits. Issue &#35;10 remains actively open, while Issue &#35;11, though recently remediated, demonstrates the persistence of access governance gaps that required multiple audit cycles to close. Given this pattern, implement a quarterly automated review process for dormant-admin accounts in financial systems to identify and remediate access violations before they accumulate across multiple audit periods. |
| Identity resolution | VPN | High | Low | Medium | Identity-resolution issues in VPN and billing-sync systems show a **recurring pattern**, not isolated findings. Issues &#35;20, &#35;19, and &#35;12 (vpn-legacy-4402) have persisted across 2 consecutive audits, and issues &#35;8 and &#35;7 (svc-billing-sync) across 3 consecutive audits, indicating that tactical remediation (&#35;20, &#35;19, &#35;8, &#35;7 marked as Remediated) has not prevented recurrence. **Recommend establishing a systematic identity-verification process review** for both systems to identify and address the root causes driving repeated identity-resolution failures, rather than treating each occurrence as an isolated remediation event. |

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