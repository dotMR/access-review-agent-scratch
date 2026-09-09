# Access Review Agent

A joiner-mover-leaver (JML) access review agent: reconciles HR data alongside IT System access permissions in comparison with the company access control policy, flagging discrepancies as Findings. See `access-control-policy.md` for the formal policy these terms are drawn from.

## Language

**Information System**:
Any of the five tools in policy scope (AWS, GitHub, Salesforce, Finance ERP, VPN) to which individual employee access is granted, tracked, and reviewed.
_Avoid_: System (too generic on its own — qualify as Information System or name it directly), IT System.

**Role**:
An employee's job function (e.g. Software Engineer, HR Admin), the basis for the Baseline Access granted to an employee automatically.

**Baseline Access**:
Access an employee's Role entitles them to automatically, granted without a separate request or approval step. `approved_by` = `"auto (granted per role policy)"`.
_Avoid_: Default access, standard access.

**Ad-hoc Access**:
Access outside an employee's Role-based Baseline Access, requested individually by the Employee and approved by the Asset Owner.
_Avoid_: Elevated access (used interchangeably in places, but Ad-hoc is the precise term — elevated is a description of some ad-hoc grants, not a synonym for all of them).

**Service Account**:
A non-individual account (CI/CD, integrations, bots) exempt from the Individual Usage principle, provided it carries a documented accountable human owner in its `provisioning_note`. The owner's employment status must stay current for the exception to hold.
_Avoid_: Bot account, system account.

**Finding**:
A discrepancy between actual access and policy that the Agent identifies during a review (orphaned, dormant admin-level, dormant ad-hoc, unapproved, drifted, or identity resolution). Always cites the specific source record(s) it's based on, and stays open until closed: remediated, accepted as risk, or otherwise resolved. Gets its own GitHub Issue.
_Avoid_: Issue (an Issue is the GitHub artifact a Finding produces, not the Finding itself), violation, flag, unresolved-identity access (superseded name — Identity resolution is the category, and it covers both an unresolved identity and a stale service-account owner, not just the unresolved case).

**Risk Assessment Entry**:
A per-category, per-system synthesis across a quarter's Findings, produced only in the Quarterly Audit Report's Risk Assessment section: a deterministic likelihood × impact score paired with a narrative justification and treatment recommendation. Not a Finding: cites Findings as evidence but never gets its own GitHub Issue.
_Avoid_: Finding (a Risk Assessment Entry is built from Findings, not one itself), Risk (too generic — this is a specific report artifact).

**Escalation**:
A Finding the Agent raises to the Security/Compliance Reviewer immediately, outside the regular report cadence. Triggered solely by a finding still open past its own category's next Operational-cadence deadline (the Unremediated findings principle) — a category with no Operational cadence of its own (everything except Orphaned, in v1) has nothing to escalate against, and stays fully documented in the Quarterly Audit Report regardless. Fires at most once per Finding: once escalated, the Agent never escalates that same Finding a second time, even if it stays open across further cycles — sustained non-remediation past that point is what Risk Assessment's recurrence scoring is for, not a repeated Escalation.

**Accepted Risk**:
A human decision (Reviewer or Asset Owner) to stop treating an open Finding as needing remediation, applied as an `accepted-risk` label on the Finding's Issue with a required comment recording the justification. Applying the label **closes the Issue**, the same action as remediation — distinguished only by the label persisting on the closed Issue as the permanent record of why (see ADR-0005). This keeps "open" meaning the same thing everywhere (the monthly report, resolution-status counts, SLA re-checks): a closed, accepted-risk Issue stays fully visible and filterable by its label, just not counted as needing attention. No expiry planned in v1 — the underlying condition is never re-reviewed or re-surfaced automatically once accepted.

## Actors

**Employee**:
Subject of the HR and access records. Receives Baseline Access automatically; can request Ad-hoc Access beyond it.

**HR Admin**:
Initiates joiner/mover/leaver events in HRIS.

**Asset Owner**:
The accountable owner for one Information System, executing grants and revokes directly and approving Ad-hoc Access requests within their own system. Named for the accountability relationship (owner of the asset), not a job title — Finance ERP's and Salesforce's owners, for instance, aren't IT roles.
_Avoid_: IT Admin (superseded name), Manager (cut as a separate actor — its two jobs are absorbed into Employee self-service and Asset Owner approval).

**Security/Compliance Reviewer**:
Receives the Agent's Quarterly Audit Report and Escalations; has standing read access to all Findings as they occur via the Issue tracker. Makes the call on Escalations and Accepted Risk. Doesn't act on Findings operationally — that's the Asset Owner's job.
_Avoid_: Auditor (cut as a modeled actor — the Quarterly Audit Report is what an auditor would read, but the auditor isn't simulated in the event system).

**The Agent**:
The system itself. Runs reviews, calls tools, applies policy via retrieval, flags Findings, escalates, and produces Risk Assessment Entries. Never has grant or revoke capability.