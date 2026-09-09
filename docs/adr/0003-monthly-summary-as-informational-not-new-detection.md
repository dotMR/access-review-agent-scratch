# 0003. Monthly Operational Flags: informational summary, with monthly detection

_Title originally "...not new detection" — revised once a real gap (quiet systems going unchecked between quarters) showed that framing was wrong. What stays true throughout: informational only, no SLA, no Escalation eligibility. What changed: detection now does run monthly, not just on commits. See Decision, below._

**Status:** accepted

## Context

`demo-timeline.md`'s 2026-09-04 note cut the monthly Operational-notification tier entirely for v1 ("No monthly Operational scan in v1"), putting Dormant admin-level's and Drift's monthly Operational variants out of scope. That left nothing reaching an Asset Owner between commit-triggered runs and the quarterly audit — every non-Orphaned category is silent until quarter-end.

The product goal driving this decision: demonstrate functionality that helps teams work toward compliance without getting in the way — Escalations should be a deliberate nudge, not inbox clutter, and the quarterly report should be able to show a genuinely solid compliance posture because Asset Owners had a real chance to clean things up beforehand, not because nothing surfaced until the audit already ran.

Two separate questions had to be settled: **what** the monthly artifact contains, and **how** it reaches the Asset Owner.

### What it contains

Three options:

- **Revive the out-of-scope monthly Operational variants** (new detection triggers, notified monthly, each with their own SLA). Rejected: recreates the build cost and scope the earlier demotion deliberately avoided, and adds more categories that would need their own escalation/re-escalation logic — working against the "don't clutter inboxes" goal, not for it.
- **Do nothing** — rely on the fact that Findings and their Issues already exist continuously (ADR-0001) and let Asset Owners check the tracker themselves. Rejected: nothing proactively surfaces to the Asset Owner; visibility existing in principle isn't the same as a nudge in practice.
- **A monthly, informational-only summary of currently open Findings.** Chosen. (Whether this needed its own fresh detection pass or could rely entirely on state the agent already had turned out to need revisiting — see Decision, below.)

Scope within that went through two corrections:

1. Initially narrowed to just Dormant admin-level and Drift (categories that accrue from the passage of time or an unfollowed role change, with no single discrete commit behind them), on the theory that Unapproved and Identity resolution are already visible to the Asset Owner via the commit that caused them. That theory doesn't hold: nothing in the design notifies or assigns the Asset Owner when *any* Finding's Issue is first opened, regardless of category — Issue creation only applies labels (see Issue-format decision, `SPEC.md` §3). So the real dividing line is just "currently open, not yet formally reported," which applies equally to all four quarterly-only categories. Broadening costs nothing against the clutter concern either, since that concern is about interruptive, real-time notifications (Escalations), not about how many rows are in one already-scheduled monthly digest.
2. Broadened to the four quarterly-only categories, but still explicitly excluding Orphaned — reasoning that it "already has its own same-day notice and doesn't need a monthly reminder." That conflates two different things: not needing this report to *surface* a finding for the first time isn't the same as it not belonging in a complete current-state snapshot. A still-open Orphaned finding (a real scenario in `demo-timeline.md` — commit 9's Orphaned finding stays open across an SLA miss and escalation, only closing in commit 12, spanning at least one monthly cycle) is exactly the kind of thing the Asset Owner should see reflected here too.

**Final scope: every currently open Finding for the system, any category, including Orphaned.** No category filter at all — the report documents current state; it doesn't gate inclusion by how a finding was originally noticed.

### How it's delivered

Three options, considered in this order:

- **A comment on a persistent, labeled Issue per system**, updated monthly. Reuses existing tools (`open_issue` once, `add_comment` monthly), genuinely low-clutter (one Issue per system, ever). Superseded once the delivery question was reconsidered against what this project actually needs to demonstrate (below).
- **A PR adding the report file, with the Asset Owner requested as reviewer.** Real appeal: GitHub's native review-request notification is an actual nudge, and merging becomes a lightweight acknowledgment — a monthly echo of the quarterly report's formal Sign-off. But there's a more basic problem than engagement timing: this is a public repo about a *fictional* company (`access-control-policy.md`) — there is no real GitHub account behind any Asset Owner to request review from at all. Even setting that aside, the mechanism depends on live, over-time human engagement to deliver any value, which a demo that seeds three quarters of history in one authored pass can't authentically exercise — at best it requires *scripting* a simulated merge, which starts to fake the thing being demonstrated. Worse, if a PR is never merged, the report content never lands in git history at all, undermining the project's core value as a legible, browsable artifact trail — a visitor reading `reports/` should be able to see what happened without depending on whether a fictional Asset Owner got around to clicking merge. (Reusing one long-lived branch/PR per system, rather than opening a new one every month, would avoid the accumulation problem this raises, but doesn't fix the core issues: no real account to request review from, and no genuine engagement occurs in a scripted demo either way.) Rejected for this project on that basis — noted as the stronger design for an actual production deployment with real staff, not thrown away.
- **A plain committed file**, `reports/monthly/<period>/<system>.md`, written by a new `commit_report` tool. No PR, no review gate, no dependency on anyone acting on it. Chosen: guarantees the content genuinely exists in git history regardless of engagement, which is what this project is actually optimized for.

## Decision

A third trigger, alongside ADR-0001's two: a **monthly cron schedule**. For each Information System, it invokes that system's subagent for a full reconciliation run — the same mechanism as a push-triggered run (ADR-0001) — then the main agent compiles `reports/monthly/<period>/<system>.md` via `commit_report` from the results, a plain commit, no PR, no review gate.

- **Full detection runs monthly, not just on commits.** Originally this trigger only read `list_issues` with no detection of its own, on the theory that everything was already caught by commit-triggered runs. That theory has a real gap: if a system receives no access-file, HRIS, or policy commits for a stretch, nothing re-evaluates its Dormant/Drift status during that gap — the quarterly trigger is a backstop, but a quiet system could go most of a quarter without a fresh check otherwise. Revised: the monthly trigger now invokes full detection for every system, closing that gap. **This does not change what's still out of scope** — Dormant admin-level's and Drift's own Operational/escalation-eligible cadence (see access-control-policy.md's Operational review Principle) is a different question from "how often does detection run," and stays out of scope. A Finding caught by this monthly detection pass is still classified Evidentiary/quarterly-only, exactly as before; nothing here gives it an SLA or makes it Escalation-eligible under the Unremediated findings Principle. Persistence across cycles is still the quarterly Risk Assessment's recurrence-scoring's job, not a new Escalation path.
- **One new tool: `commit_report`.** This also retroactively fills a gap that existed for the quarterly reports too — nothing in the original tool registry actually wrote a report file to `reports/`; that had gone unnoticed until this decision forced the question. `commit_report` is now used by all three report types (per-system, aggregate, monthly).
- **Explicitly not an Operational-cadence gate.** This report does not make any category eligible for Escalation under the Unremediated findings Principle. Escalation stays keyed to Orphaned's same-day SLA only. Stated explicitly in the report template itself, so it can't be mistaken for a new compliance deadline.
- **Escalation fires once per Finding** (see `CONTEXT.md`, `access-control-policy.md` — formalized alongside this decision), so a finding that keeps appearing on successive monthly reports is a legitimate, visible nudge rather than a repeated alarm.

## Consequences

- Closes the "nothing reaches an Asset Owner between quarters" gap, *and* closes the narrower "a quiet system's Dormant/Drift status goes unchecked for a stretch" gap — without touching v1 Core's escalation/SLA scope or ADR-0001's architecture.
- The quarterly audit report's "solid compliance posture" claim becomes more defensible in practice — Asset Owners had a documented, non-punitive chance to remediate before the formal record, not just a post-hoc report of what went wrong.
- A future decision to actually revive full monthly Operational *notification* (Dormant/Drift's own SLA-bearing, escalation-eligible cadence — still out of scope) remains genuinely separate from this: this ADR makes detection run monthly, not the escalation/SLA tier that item would add. That distinction is deliberate, not incidental — see Decision, above.
- Adds a third trigger type; `SPEC.md` §2 now documents three trigger mechanisms, not two.
- `commit_report`'s existence means the quarterly report-writing mechanism (previously undefined) is now specified too, as a side effect of working through this decision.
- If this project ever needs to model a genuine live deployment (rather than a seeded demo), the PR-with-reviewer-request mechanism is the documented fallback design, not a discarded one.
- The monthly trigger now costs five subagent invocations per run, not zero — worth factoring into the still-unpinned tool-call/iteration cap (ADR-0001 Consequences) once there's real run data to set it from.
