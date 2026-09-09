# 0005. Issue lifecycle semantics: Escalation mechanism and Accepted Risk closure

**Status:** accepted

## Context

Two related questions about what happens to a Finding's Issue after it's opened, both left underspecified until worked through directly.

**Escalation.** `CONTEXT.md` describes it as a Finding "the Agent raises to the Security/Compliance Reviewer immediately" — which reads naturally as assigning the Issue to the Reviewer, reusing GitHub's native assignment notification as the delivery mechanism. But this project's repo is explicitly about a *fictional* company (`access-control-policy.md`: "fake data for a fictional company, not a copy of any real employer's"). There is no real GitHub account behind "the Security/Compliance Reviewer" or any Asset Owner. Assigning every escalation to one real account (or failing against a nonexistent one) either misrepresents the mechanism or floods one real inbox regardless of which fictional role is actually responsible. A GitHub Projects (v2) board with a custom Owner/Status field was also considered, as a dashboard-style role display that doesn't require a real account — but the information it would show already exists: Asset Owner is a strict 1:1 relationship with a system, so the existing system label already identifies the owner, and Escalation is by definition raised to the Reviewer, so an `escalated` label already says that. A Projects board would add a real, separate API surface and new tools for a marginal display improvement over label filtering that already works.

**Accepted Risk.** `CONTEXT.md`'s own text was in tension with itself: the Finding entry listed "accepted as risk" as one of the ways a Finding gets *closed*, parallel to remediation — but the Accepted Risk entry's own description ("the Agent checks for the label on each run and stops re-flagging the Finding as open") read more like detection logic than a statement about the Issue's actual GitHub state, leaving genuinely ambiguous whether an accepted-risk Issue stays open (just labeled) or gets closed like a remediated one.

## Decision

- **Escalation** = `apply_label` (`escalated`, additive to the Finding's existing category/system labels) + `add_comment` (stating what SLA was missed and when) on the Finding's own, already-existing Issue. **No assignee, for any actor, anywhere in this project.** No GitHub Projects board.
- **Accepted Risk** = applying the `accepted-risk` label also closes the Issue (`close_issue`) — the same action as remediation, distinguished only by which label persists on the closed Issue as the record of why.
- Together: "open," wherever it's checked (`list_issues`, the Monthly Operational Flags report, both report templates' resolution-status counts, the SLA re-check logic), means exactly one thing — genuinely still needing attention. There is no second "open but accepted" state to special-case anywhere.

## Consequences

- Escalation's actual demonstrated value in this project is recorded, filterable visibility (`is:open label:escalated`, the Issue's own comment timeline, and the aggregate report's Escalations table) — not live notification. A deliberate, honest scope for what a fictional-company demo can actually show, versus what a live deployment with real staff would need.
- Modeling this project as a genuine live deployment later (real Asset Owners, real notifications) would need to revisit both decisions here — real accounts would make assignment meaningful again, and could reopen the GitHub Projects question.
- The three-bucket resolution-status count (Open / Remediated / Accepted risk) both report templates already display works cleanly off raw Issue open/closed state, split only by which label is on the closed Issue — no separate tracking mechanism needed.
- Same "no real account behind a fictional actor" reasoning that shaped ADR-0003's rejection of PR-with-reviewer-request delivery for Monthly Operational Flags — recorded here as the general project-wide constraint it actually is, not a one-off observation.
