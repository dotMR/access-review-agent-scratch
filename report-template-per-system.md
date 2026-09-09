# Access Review — {{SYSTEM_NAME}} — {{PERIOD}}

**Report generated:** {{GENERATED_TIMESTAMP}}
**Data snapshot:** {{DATA_SNAPSHOT_REF}}
**Model:** {{MODEL_NAME_AND_VERSION}}
**Reporting period:** {{PERIOD_START}} – {{PERIOD_END}}
**Asset Owner:** {{ASSET_OWNER_NAME}}
**Committed to:** `reports/{{PERIOD}}/{{SYSTEM_NAME}}.md`

One of these is generated per Information System (AWS, GitHub, Salesforce, Finance ERP, VPN) each quarter. This is the line-item evidence; the aggregated Quarterly Audit Report links to these rather than repeating their contents.

## Summary

| Category | Open | Remediated | Accepted risk | Total |
| :-- | --: | --: | --: | --: |
| Orphaned access | {{n}} | {{n}} | {{n}} | {{n}} |
| Dormant admin-level access | {{n}} | {{n}} | {{n}} | {{n}} |
| Unapproved access | {{n}} | {{n}} | {{n}} | {{n}} |
| Identity resolution | {{n}} | {{n}} | {{n}} | {{n}} |
| Drift | {{n}} | {{n}} | {{n}} | {{n}} |
| Dormant ad-hoc access | {{n}} | {{n}} | {{n}} | {{n}} |
| **Total** | {{n}} | {{n}} | {{n}} | {{n}} |

## Findings

### Orphaned access

| Identity | Access detail | Expected per policy | Date detected | Time to revoke | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| {{employee_name}} | {{access_level}} | None (terminated {{termination_date}}) | {{date_detected}} | {{time_to_revoke}} | {{status}} | [#{{issue_number}}]({{issue_url}}) |

### Dormant admin-level access (90-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| {{employee_name}} | {{access_level}} | Active use, ≤90 days since last use | {{last_used_date}} | {{days_dormant}} | {{status}} | [#{{issue_number}}]({{issue_url}}) |

### Unapproved access

| Identity | Access detail | Expected per policy | Date granted | Approved by | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| {{employee_name}} | {{access_level}} | `approved_by` populated (auto or Asset Owner) | {{granted_date}} | {{approved_by}} | {{status}} | [#{{issue_number}}]({{issue_url}}) |

### Identity resolution

| Access record (`employee_id` or local identifier) | Access detail | Resolution | Evidence cited | Date detected | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| {{identifier}} | {{access_level}} | {{resolved individual / documented exception / unresolved}} | {{provisioning_note excerpt or name-match basis}} | {{date_detected}} | {{status}} | [#{{issue_number}}]({{issue_url}}) |

Only unresolved and stale-ownership outcomes are findings (see iam-review-agent-design.md, Identity resolution); a clean resolution to an individual or a documented exception isn't a finding and doesn't get a row here.

### Drift

| Identity | Access detail | Expected per policy | Role changed | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- |
| {{employee_name}} | {{access_level}} | Access matching current role per role-access-mapping.yaml | {{role_change_date}} ({{old_role}} → {{new_role}}) | {{status}} | [#{{issue_number}}]({{issue_url}}) |

### Dormant ad-hoc access (180-day threshold)

| Identity | Access detail | Expected per policy | Last used | Days dormant | Status | Issue |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| {{employee_name}} | {{access_level}} | Active use, ≤180 days since last use | {{last_used_date}} | {{days_dormant}} | {{status}} | [#{{issue_number}}]({{issue_url}}) |

*Any category with zero findings this period should still appear with an explicit "No findings" line, not be omitted — an auditor should never have to wonder whether a category was skipped or simply had nothing to report.*

## Sign-off

I attest that the findings above for {{SYSTEM_NAME}} have been reviewed and, where applicable, remediated or formally accepted as risk.

**Asset Owner:** {{ASSET_OWNER_NAME}}
**Date:** {{SIGNOFF_DATE}}
