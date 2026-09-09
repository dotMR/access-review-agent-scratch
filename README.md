# Access Review Agent

## Why this exists

I posted a thought on LinkedIn while thinking about my next role: you can't credibly sell customers transformational AI while your own internal operations still run on the manual processes AI is meant to replace. This project is that thesis made concrete.

Joiner-mover-leaver access review is normally a periodic, manual checklist — exactly the kind of control a well-staffed team lets slip, not from indifference but because continuously reviewing every system is tedious. This agent runs that review continuously instead, reasoning through cases a lookup can't: a shared login that's either a documented exception or a real violation depending on a justification note nobody but a human — or this agent — would actually read. When the evidence isn't there, it says so instead of guessing — and every claim it makes cites the specific record behind it.

It cross-references HR and IT access data against policy to flag orphaned, dormant (admin-level and ad-hoc), unapproved, drifted, and identity-resolution findings, and runs on three triggers: push-triggered whenever a commit touches source access data, HR data, or policy config in this repository; a monthly cron for an informational summary; and a quarterly cron for the formal audit record (`SPEC.md` §2).

**Status:** in active development — 11 of 12 milestones built and merged (real detection logic, real GitHub Issue writing, real GitHub Actions dispatch, real Identity resolution via the Agent SDK, real report generation and committing, real Risk Assessment scoring and narrative synthesis, real Escalation/Accepted-Risk lifecycle mechanics, real monthly quiet-system detection, per-system failure isolation, real tagged Releases gated behind human-in-the-loop approval); see `development-plan.md` for progress and what's left. The walkthrough below describes how to review the repository once the agent has run against the seeded demo timeline — there's no live data yet, so none of this exists in the repository today.

## Reviewing the repository

Three artifacts, in order of how current they are:

1. **GitHub Issues** are the live, continuously-updated source of truth — every Finding gets one the moment it's detected (`SPEC.md` §4), not just at report time. Filter by label to see current state directly: `is:open` for everything still needing attention, `label:escalated` for what's been raised to the Reviewer, `label:accepted-risk` (these are *closed* Issues — see the status note below) for what's been formally accepted rather than fixed. Category labels (`orphaned`, `dormant-admin`, `dormant-ad-hoc`, `unapproved`, `identity-resolution`, `drift`) and system labels (`aws`, `github`, `salesforce`, `finance-erp`, `vpn`) narrow further.
2. **`reports/monthly/<period>/<system>.md`** is the informational nudge — every currently open finding for one system, refreshed monthly. Useful for a quick read on what's outstanding ahead of the next formal record, but it's explicitly not evidentiary: no sign-off, and closed items (remediated or accepted-risk) don't appear here at all, only what's still open.
3. **`reports/<period>/aggregate.md`** is the formal audit-evidence record — the one an external auditor would actually read and cite. Executive summary, resolution-status rollup, the Risk Assessment section, and Escalations, with links out to `reports/<period>/<system>.md` for line-item detail per system. Each quarter's Release (tagged `<period>`, e.g. `2026-Q1`) bundles all six report files plus the aggregate's PDF export — start there for the fastest "what happened this quarter" read, since the Release body already summarizes the same headline numbers.

**A closed Issue isn't always a fixed one.** Applying the `accepted-risk` label closes the Issue, the same action as remediation — the label is what distinguishes "fixed" from "formally accepted as an acceptable risk" on an otherwise identical closed state (ADR-0005). Check for that label before assuming a closed Issue means the access was actually revoked.

## Documentation

- **`CONTEXT.md`** — glossary and actors; the vocabulary everything else uses.
- **`SPEC.md`** — the settled, implementation-facing shape: data schemas, trigger/dispatch rules, the tool registry, finding definitions, report structure, guardrails.
- **`development-plan.md`** — the walking-skeleton build order, milestone by milestone.
- **`eval-cases.md`** — the 40-case eval suite each milestone is graded against.
- **`iam-review-agent-design.md`** — the design rationale.
- **`future-capabilities.md`** — reasoning-capability candidates considered but not built, kept separate so the design doc stays focused on what actually exists.
- **`docs/adr/`** — architecturally significant decisions (Context/Decision/Consequences), one file per decision.
- **`access-control-policy.md`**, **`role-access-mapping.yaml`**, **`policy-config.yaml`** — the policy this agent enforces: human-readable Principles, the Role → Access Mapping and System Criticality, and the machine-consumed thresholds and scoring tables, respectively.
- **`demo-timeline.md`** — the concrete, commit-by-commit scenario the demo repository's history is seeded from.