# Quarterly Access Review Audit Report — {{PERIOD}}

**Report generated:** {{GENERATED_TIMESTAMP}}
**Data snapshot:** {{DATA_SNAPSHOT_REF}}
**Model:** {{MODEL_NAME_AND_VERSION}}
**Reporting period:** {{PERIOD_START}} – {{PERIOD_END}}
**Systems in scope:** AWS, GitHub, Salesforce, Finance ERP, VPN
**ISO 27001:2022 controls addressed:** A.5.15 (Access control), A.5.16 (Identity management), A.5.18 (Access rights), A.8.2 (Privileged access rights)
**SOC 2 Common Criteria addressed:** CC6.1 (Logical access controls), CC6.2 (Access provisioning and de-provisioning), CC6.3 (Role-based access, least privilege, and segregation of duties)
**Committed to:** `reports/{{PERIOD}}/aggregate.md`

This is the formal audit-evidence record for the period, the rollup of the five per-system reports below. It does not repeat their line-item findings, only aggregates and links to them, so the two can never drift out of sync with each other.

## Executive summary

{{total_findings}} findings identified this quarter across 5 finding categories and 5 Information Systems. {{n_remediated}} remediated, {{n_open}} open, {{n_accepted_risk}} accepted as risk. {{trend_note, e.g. "Down from 14 findings in Q2 2026." — reads "N/A, no prior period" when this is the first report, must not be silently omitted}}

## Methodology

The Access Review Agent performed an automated cross-reference of each Information System's access records (Access/IT System) against the HRIS and the Access Policy Repository, per the Operational review and Compliance review Principles in access-control-policy.md. Findings are categorized per policy: orphaned, dormant (admin-level), unapproved, identity resolution, and drift access.

## Resolution status by system

| System | Open | Remediated | Accepted risk | Total | Detail |
| :-- | --: | --: | --: | --: | :-- |
| AWS | {{n}} | {{n}} | {{n}} | {{n}} | [aws.md](./aws.md) |
| GitHub | {{n}} | {{n}} | {{n}} | {{n}} | [github.md](./github.md) |
| Salesforce | {{n}} | {{n}} | {{n}} | {{n}} | [salesforce.md](./salesforce.md) |
| Finance ERP | {{n}} | {{n}} | {{n}} | {{n}} | [finance-erp.md](./finance-erp.md) |
| VPN | {{n}} | {{n}} | {{n}} | {{n}} | [vpn.md](./vpn.md) |
| **Total** | {{n}} | {{n}} | {{n}} | {{n}} | |

## Findings by category (aggregate)

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | {{n}} | {{n}} | {{n}} | {{n}} |
| Dormant admin-level access | {{n}} | {{n}} | {{n}} | {{n}} |
| Unapproved access | {{n}} | {{n}} | {{n}} | {{n}} |
| Identity resolution | {{n}} | {{n}} | {{n}} | {{n}} |
| Drift | {{n}} | {{n}} | {{n}} | {{n}} |
| Dormant ad-hoc access | {{n}} | {{n}} | {{n}} | {{n}} |

Line-item detail for every finding lives in the per-system reports linked above and in the Appendix, not here.

## Risk Assessment

Per-category, per-system risk rating, synthesized from this section's own inputs plus the findings above: a deterministic score (likelihood × impact) paired with a narrative justification and treatment recommendation. The score is reproducible from fixed inputs, not a judgment call; the narrative is genuine synthesis, citing the specific findings/Issues behind it and stating whether the pattern is isolated or recurring across cycles. See iam-review-agent-design.md, Data requirements for demonstrating v1 Core reasoning, for the worked examples this section is built on.

**Scoring inputs.** Likelihood from its own quarterly-recurrence check, a signal separate from Escalation (which is Operational-cadence-based, same-day for Orphaned, and doesn't apply to quarterly-only categories at all, see access-control-policy.md's Unremediated findings Principle): Low = new this quarterly audit, Medium = open across 2 consecutive audits, High = open across 3+ consecutive audits. Impact from System Criticality × access level (see role-access-mapping.yaml's System Criticality table, and ADR-0002 for the full scoring tables).

Only categories with at least one finding this quarter get a row, there's nothing to assess against zero findings; a category's absence here is explained by its zero count in Findings by category above, not a silent omission.

| Category | System | Likelihood | Impact | Risk Rating | Narrative & treatment recommendation |
| :-- | :-- | :-- | :-- | :-- | :-- |
| {{category}} | {{system_name}} | {{Low/Medium/High}} | {{Low/Medium/High}} | {{Low/Medium/High/Critical}} | {{narrative citing specific Issue numbers, noting isolated vs. recurring, and a treatment recommendation if recurring}} |

## Escalations this period

Findings whose GitHub Issue was still open past their own category's Operational cadence (same-day for Orphaned, currently the only category with one in v1), escalated to the Reviewer immediately rather than waiting for this report, per access-control-policy.md's Unremediated findings Principle, the sole Escalation trigger. Empty is a valid, good state, show "None this period" explicitly rather than omitting the section.

| Finding | System | Category | Open since | Escalated | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| {{employee_name}} | {{system_name}} | {{category}} | {{date_first_flagged}} | {{escalation_date}} | [#{{issue_number}}]({{issue_url}}) |

## Reviewer attestation

I have reviewed this report and the underlying per-system reports, and accept this as the formal audit-evidence record for the period stated above.

**Security/Compliance Reviewer:** {{REVIEWER_NAME}}
**Date:** {{SIGNOFF_DATE}}

## Appendix

- Per-system reports: [AWS](./aws.md) · [GitHub](./github.md) · [Salesforce](./salesforce.md) · [Finance ERP](./finance-erp.md) · [VPN](./vpn.md)
- Data snapshot: {{DATA_SNAPSHOT_REF}}
- PDF export: {{PDF_FILENAME}} (generated {{GENERATED_TIMESTAMP}})

---
<!-- Out of scope (not shown in this report): Dormant admin-level's, Dormant ad-hoc's, and Drift's own monthly Operational/SLA variants, and the Unapproved-access grant-time gate — see SPEC.md §8. -->
