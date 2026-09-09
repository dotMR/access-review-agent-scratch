# Access Control Policy

## Purpose

The purpose of this document is to outline the information security procedures and processes related to Access Control that informs the Access Review Agent.

Note: this is purely an illustrative document with fake data for a fictional company, not a copy of any real employer's policies or data.

## Terms

- **Information System** — Any of the tools or platforms in this policy's scope (AWS, GitHub, Salesforce, Finance ERP, VPN), to which individual employee access is granted, tracked, and reviewed.
- **Role** — An employee's job function (e.g. Software Engineer, HR Admin), the basis for the automatic baseline access granted to an employee
- **Baseline Access** — Access an employee's role entitles them to automatically to perform their job function, granted without a separate request or approval step.
- **Ad-hoc Access** — Access outside an employee's role-based baseline, requested individually and approved by the Asset Owner rather than granted automatically.
- **Service Account** — A non-individual account (used for automation, integrations, or system-to-system access, e.g. a CI/CD pipeline) exempt from Individual Usage provided it has a documented accountable human owner on file.
- **Finding** — A discrepancy between actual access and this policy that the Agent identifies during a review (e.g. orphaned, dormant, unapproved, unresolved identity, or drifted access). Stays open, tracked, until closed: remediated, accepted as risk, or otherwise resolved.
- **Escalation** — A finding the Agent raises to the Security/Compliance Reviewer immediately, outside the regular report cadence, rather than waiting for the next Quarterly Audit Report. Triggered solely by Unremediated findings (see Principles, below): a finding still open past its own category's next Operational review deadline, same-day for acute-risk findings, monthly for anything else reviewed via the monthly scan. A finding with no Operational-cadence review of its own has nothing to escalate against; it's still fully documented in the Quarterly Audit Report regardless.

## Roles & Responsibilities

- **Employee** — Receives baseline access automatically on hire or role change. Requests ad-hoc access for anything beyond that baseline.
- **Asset Owner** — Owns, grants, and revokes access to the different Information System. Receives and approves employees' ad-hoc access requests. Acts on any flags raised by the Agent.
- **Security/Compliance Reviewer** — Receives the Agent's quarterly compliance report, the formal audit-evidence record, and escalated findings from the Agent between cycles (see Principles below for the trigger). Has standing read access to all findings and their status as they occur, but doesn't act on them operationally, that stays with the Asset Owner.

## Principles

- **Ownership**. Access to Information Systems must be controlled and managed by the owner of the system, in our case the Asset Owner.
- **Individual Usage**. Access to Information Systems must be assigned to an individual employee rather than a group or shared account.
- **Service Account Ownership.** A Service Account is an exception to Individual Usage, provided it names an accountable human owner. That owner's employment status must remain current for the exception to hold: if the owner is terminated, the account's access must be revoked or reassigned to a new documented owner. [2026-09-04]
- **Role-based Access.** Access to Information Systems must be granted according to the role of the employee. Any changes to the role must trigger a review of access.
- **Least Privilege.** Access to Information Systems must be granted according to the principle of least privilege.
- **Contractors.** Access to Information Systems granted to contractors must be set to expire according to their contract end date.
- **Initial Access,** Baseline access to Information Systems is pre-approved according to the employee role and granted automatically the day the employee starts.
- **Ad-hoc Access.** Any requests outside of employee role, including requests for elevated / Admin-level access, is requested by the employee and manually approved by the Asset Owner.
- **Access Approval.** All access, baseline or ad-hoc, must have a recorded approval, automatic for baseline, the Asset Owner's approval on file for ad-hoc. Access lacking a recorded approval is treated as a risk and flagged for review, regardless of how it arose.
- **Dormant Admin-level access.** Access at the `admin` level in the Role → Access Mapping (see role-access-mapping.yaml) that is dormant and unused for more than **90** consecutive days is treated as a risk and flagged for review.
- **Dormant Ad-hoc access.** Ad-hoc access requests that fall outside of the employee's role that is dormant and unused for more than **180** consecutive days is treated as a risk and flagged for review.
- **Operational review.** Findings carrying acute risk must be flagged to the Asset Owner the moment they are detected. All other findings are reviewed via an automated monthly scan across all Information Systems, cross-referenced against this policy.
- **Compliance review.** The Access Review Agent produces a formal audit report across all Information Systems each quarter for the Security/Compliance Reviewer; this becomes the audit-evidence record.
- **Orphaned access.** Any access retained by a terminated employee or a contractor past their contract end date must be revoked by the Asset Owner the same day it is detected.
- **Unremediated findings.** Any finding still open at its category's next Operational review, meaning the Asset Owner did not act on it within that cadence, escalates to the Security/Compliance Reviewer immediately, rather than waiting for the next Quarterly Audit Report. "Next Operational review" means that finding's own cadence under the Operational review Principle above, same-day for acute-risk findings, monthly for anything else reviewed via the monthly scan, not the Quarterly Audit Report's cadence, which is a comprehensive record of the period, not itself a monitoring cycle. A finding category with no Operational-cadence review of its own is still fully documented in the Quarterly Audit Report like any other finding, it simply has nothing to escalate against until it does. [2026-09-04]
- **Escalation fires once.** A finding escalates at most one time. If it remains open after escalating, it is not escalated again — its continued persistence across cycles is addressed through the quarterly Risk Assessment's recurrence scoring, not repeated Escalations. This keeps Escalation a deliberate signal reserved for genuinely new acute risk, not a recurring alarm on the same finding. [2026-09-07]
- **Reviewer visibility.** The Security/Compliance Reviewer has standing read access to all findings and their status as they occur, via the same issue tracking the Asset Owner works from, not limited to the quarterly report or escalations. The quarterly audit is a formal confirmation of a known risk posture, not the Reviewer's first exposure to it.

## Reporting

- **Monthly Operational Flags** — Per-system list of *every currently open* finding, any category (orphaned included, if still open — it doesn't need this report to surface it, but a still-open one belongs in the complete picture same as anything else), each with the affected employee, the system, and what's expected vs. what's actually granted. Sourced from findings already detected on their normal cadence, not a separate monthly detection pass — an informational nudge to close things out before the quarter closes, not itself an Operational-cadence review: it doesn't gate Escalation, and a category's presence here doesn't give it an Operational cadence to escalate against under the Unremediated findings Principle above. Framed as action items, not evidence. [2026-09-08]
- **Quarterly Audit Report** — All finding categories the Agent checks (orphaned, dormant admin-level, dormant ad-hoc, unapproved, identity resolution, drift), aggregated across all Information Systems, plus resolution status on anything flagged since the last audit (open, remediated, accepted risk). This is the artifact an external auditor would actually read.
- **Escalation** — A single finding rather than a batch report, triggered when a finding is still open at the next monitoring cycle (see Unremediated findings in Principles).