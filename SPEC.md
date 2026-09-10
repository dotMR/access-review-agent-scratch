# Access Review Agent — Spec

This is the settled *what*: data shapes, trigger/dispatch rules, tool registry, finding definitions, report structure, and guardrails. It's implementation-facing, not a rationale document.

For *why*, see `iam-review-agent-design.md` (design rationale) and `docs/adr/` (architecturally significant decisions). For vocabulary and actors, see `CONTEXT.md`. For the formal policy this agent enforces, see `access-control-policy.md`.

**Status:** in active development — 11 of 12 milestones built and merged; see `development-plan.md` for progress and the remaining build order.

---

## 1. Data sources

| Source | File | Notes |
| :-- | :-- | :-- |
| HRIS | `data/system_hr.csv` | Source of truth for employment status and role |
| AWS access | `data/access_aws.csv` | Same schema as the other four access files |
| GitHub access | `data/access_github.csv` | |
| Salesforce access | `data/access_salesforce.csv` | |
| Finance ERP access | `data/access_finance_erp.csv` | SSO-gap system — `employee_id` may hold a local identifier instead |
| VPN access | `data/access_vpn.csv` | SSO-gap system — `employee_id` may hold a local identifier instead |
| Role → Access Mapping | `role-access-mapping.yaml` | Per-role baseline access per system, plus the System Criticality table. Single machine-consumed source, no Markdown duplicate — see ADR-0001, ADR-0002 |
| Policy config | `policy-config.yaml` | Dormant thresholds, the Orphaned escalation trigger, and the Risk Assessment Impact/Risk Rating tables (ADR-0002) — thresholds and scoring only, not the Role → Access Mapping |
| Policy (human-readable) | `access-control-policy.md` | Not machine-consumed. Never triggers the agent — see §2 |

### HRIS schema

`employee_id`, `name`, `role`, `start_date`, `end_date` (null if active), `status` (`active` / `terminated` / `on-leave`), `role_change_history` (list of `{date, old_role, new_role}`)

### Access file schema (identical across all five systems)

`employee_id` (or a local identifier for VPN/Finance ERP), `system_name` (redundant with the file itself — same-file consistency check), `access_level` (`read` / `write` / `admin`; VPN uses `none` / `granted` instead — network access is binary, not leveled, per `role-access-mapping.yaml`), `granted_date`, `approved_by` (null, `"auto (granted per role policy)"`, or the Asset Owner's identifier), `last_used_date`, `status` (`active` / `revoked`), `provisioning_note` (free text; populated only for records Identity resolution needs to reason over — service accounts, shared identifiers, SSO-gap local identifiers)

---

## 2. Event → trigger → dispatch model

Three distinct trigger mechanisms. See ADR-0001 (push-triggered + quarterly) and ADR-0003 (monthly) for the full architecture.

### Push-triggered runs (every commit to a relevant file)

| Commit touches | Subagents invoked | Reasoning |
| :-- | :-- | :-- |
| One access file (e.g. `access_aws.csv`) | That system's subagent only | The business event (a grant/revoke) is confined to one system |
| `system_hr.csv` | All five subagents | A joiner/mover/leaver event's consequences span every system |
| `policy-config.yaml` or `role-access-mapping.yaml` | All five subagents | Changes the "ought" side of the comparison for every system |
| `access-control-policy.md` | None | Human-readable prose, not machine-consumed — nothing to react to |

Every push-triggered run performs **full reconciliation** across all finding categories for whatever scope was dispatched (not just Orphaned), and opens Issues **immediately** on detection. The quarterly report is a rollup of Issue-tracker state that already exists by the time it runs — publication is cadence-gated, detection is not.

### Quarterly-audit trigger (schedule/cron or `workflow_dispatch`)

Always processes all six sources in full, regardless of what changed since the last run. This is the only point Risk Assessment Entries are computed (§5), and the only point the two-tier report set + Release are produced (§6).

### Monthly-summary trigger (cron)

Invokes all five subagents for a full reconciliation run — same mechanism as a push-triggered run (ADR-0001) — closing a real gap where a system with no commits for a stretch would otherwise go unchecked between quarters. The main agent then generates one `report-template-monthly-flags.md` per Information System from the results, listing that system's currently open Findings, any category, including Orphaned — Orphaned doesn't need this report to surface it (it already has its own same-day notice, and may already have escalated), but a still-open one belongs in the complete picture same as anything else. Committed directly via `commit_report` to `reports/monthly/<period>/<system>.md` — no PR, no review gate. Informational only — does **not** gate Escalation and does not give any category an Operational cadence to escalate against, regardless of how often detection now runs. See ADR-0003.

### Not implemented in v1

Dormant admin-level's and Drift's own **Operational, SLA-bearing, escalation-eligible** cadence (as opposed to their quarterly-only Evidentiary classification) is still out of scope. This is a distinct question from "how often does detection run" — the monthly trigger above runs full detection monthly, but a Finding it catches is still Evidentiary/quarterly-classified, with no SLA and no Escalation eligibility. Deliberately kept separate: Escalation is reserved for genuinely acute risk (Orphaned), and persistence across quarters is already the Risk Assessment's recurrence-scoring's job — giving every persistent Dormant/Drift finding its own Escalation would reintroduce the clutter this whole design works to avoid.

---

## 3. Agent architecture

Full detail: ADR-0001. Summary:

- **Main agent** is the sole entry point for every triggered run, regardless of fan-out width. It's the only holder of GitHub write tools and runs the grounding/citation validation exactly once per run. It aggregates each subagent's *already-detected* findings — it does not re-derive them by combining raw subagent data against HRIS itself.
- **Subagents**, one per Information System, each detect their own system's findings independently, in isolated context: a pre-bound read tool for their own system's access file only (no `system_name` parameter, no access to other systems' files), plus shared read access to HRIS and policy. Orphaned, Drift, and Identity resolution are all per-record HRIS lookups (terminated status, current role, name/email match) — they happen *inside* each subagent's own isolated context, against its own system's records only, not in the main agent.
- **Shared, non-isolated reads**: HRIS and policy inputs are available to every subagent — the isolation boundary is about *other systems'* access files, not about HRIS.

### Tool registry

| Tool | Held by | Behavior |
| :-- | :-- | :-- |
| `read_access_data` | Each subagent (pre-bound to its own system) | Full-file read + inline schema validation; raises a structured error on malformed data |
| `read_hris` | All subagents, main agent | Same read-and-validate pattern |
| `read_policy` | All subagents, main agent | Reads `role-access-mapping.yaml` / `policy-config.yaml` |
| `read_prior_report` | Main agent only | Local file read of a past quarterly report from the repo checkout — trend line, quarterly-recurrence check |
| `list_issues` | Main agent only | Live GitHub read, optionally filtered by label (its only real parameter — every Issue's state is always fetched, `state="all"`); category/state filtering happens in caller code (`orchestrator.py`, `lifecycle.py`), not the tool itself — "is this still open right now" (re-check/auto-close, Orphaned SLA) |
| `open_issue` / `close_issue` / `apply_label` / `add_comment` | Main agent only | Direct GitHub API calls, not an MCP server. `open_issue`'s title/body/label format is specified in §4, Issue format |
| `commit_report` | Main agent only | Writes a report file to `reports/` and commits it directly — no PR, no review gate. Used for per-system reports, the aggregate report, and Monthly Operational Flags (§6) |
| `create_release` | Main agent only | Tags the commit `commit_report` just wrote the quarterly reports in (tag = `<period>`, e.g. `2026-Q1` — same canonical value as the `reports/` folder and every template's `{{PERIOD}}`), sets a human-readable title, writes a body summarizing the aggregate report's Executive Summary numbers with links, and uploads the six report Markdown files plus the aggregate's PDF as assets (§6) |

No tool anywhere in the registry grants or revokes access. Read-only on HRIS/Access data, write-only to the agent's own outputs (Issues, reports, Releases).

**Tool-call/iteration cap:** 10 `query()` turns (`ClaudeAgentOptions.max_turns`), pinned from real run data (ADR-0001 Consequences) — two live identity-resolution queries against real data (GitHub's `svc-cicd-deploy`, VPN's `kjack_vpn`) both completed in exactly 4 turns (2 tool calls + 2 results, matching the 2-tool registry above); 10 leaves headroom for a retry/self-correction cycle without being effectively unbounded. `identity_resolution.py`'s `build_options` is the only Agent SDK call anywhere in the codebase with real tool access — narrative synthesis and the LLM judge (`narrative.py`) pass `allowed_tools=[]` and are pinned to `max_turns=1` instead, since no tool-calling loop is possible for either.

---

## 4. Finding categories

Every category cites the specific source record(s) it's based on. A Finding stays open until remediated, accepted as risk, or otherwise resolved (`CONTEXT.md`).

| Category | Detection rule | Cadence (v1 Core) | Status |
| :-- | :-- | :-- | :-- |
| **Orphaned access** | Access record's identifier matches an HRIS record with `status=terminated` | Event-triggered (same-day, on the triggering commit) **and** Evidentiary/quarterly | Core |
| **Dormant admin-level access** | `access_level=admin`, `status=active`, `last_used_date` > 90 consecutive days ago | Evidentiary/quarterly only | Core (monthly Operational variant out of scope) |
| **Dormant ad-hoc access** | Ad-hoc (non-baseline) access, unused > 180 consecutive days | Evidentiary/quarterly only | Core (monthly Operational variant out of scope) |
| **Unapproved access** | `approved_by` is null | Evidentiary/quarterly only | Core (grant-time immediate gate out of scope) |
| **Identity resolution** | See below | Evidentiary/quarterly only | Core |
| **Drift** | Access doesn't match the mapping for the employee's *current* role after a role change | Evidentiary/quarterly only | Core (monthly Operational variant out of scope) |

### Orphaned vs. Identity resolution — the anti-join distinction

- Zero HRIS match at all → Identity resolution (not Orphaned).
- Matches an HRIS record with `status=terminated` → Orphaned.

### Identity resolution — four outcomes

1. **Resolved to a specific employee** (name/email similarity against HRIS, e.g. an SSO-gap VPN/Finance ERP record) — no Finding.
2. **Resolved to a documented non-individual exception** (a Service Account with an accountable owner extracted from `provisioning_note`, owner currently active in HRIS) — no Finding.
3. **Unresolved** (no HRIS match, insufficient evidence to resolve) — Finding.
4. **Stale ownership** (previously resolved to outcome 2, but re-validating the owner's current HRIS status on this run finds them terminated) — Finding. Re-validated on *every* run, not just at first resolution.

### Issue format

Reuses each category's own report-row columns (`report-template-per-system.md`) rather than a separate, invented convention — the Issue *is* the evidentiary record the grounding/citation guardrail checks, not a summary of one.

- **Title:** `{Category} — {identity} ({System})`, where `{identity}` is whatever that category's report table already uses as its identifying column — `employee_name` for Orphaned, Dormant admin-level, Unapproved, and Drift; the raw `identifier` (`employee_id` or local identifier) for Identity resolution, since its two Finding-producing outcomes don't have a cleanly resolved employee name. E.g. "Orphaned access — Ronnis Pawgood (AWS)," "Identity resolution — svc-cicd-deploy (AWS)."
- **Body:** Access detail + Expected per policy always, plus that category's specific fields (Orphaned: date detected, time to revoke; Dormant admin-level: last used, days dormant; Unapproved: date granted, approved-by; Identity resolution: resolution outcome, evidence cited; Drift: role-change dates). Plus one field no report table carries explicitly: **Source record** — the exact file and row the finding is based on (e.g., `data/access_aws.csv`, row matching `employee_id=E12345`), rendered as a clickable GitHub blob permalink (`.../blob/<sha>/<path>`) pinned to the triggering commit when `open_issue` is called from a real triggered run (`commit_sha`, Milestone 5) — a plain backticked file path otherwise (eval/dry-run callers, which have no real triggering commit to pin to). That citation is what the Grounding/citation guardrail's validation step checks before `open_issue` is allowed to run.
- **Labels:** one category label (`orphaned`, `dormant-admin`, `dormant-ad-hoc`, `unapproved`, `identity-resolution`, `drift`) plus one system label (`aws`, `github`, `salesforce`, `finance-erp`, `vpn`) — kebab-case, matching `accepted-risk`/`escalated`'s style. Both applied at creation; `accepted-risk` and `escalated` are added later, by their own mechanisms, never at creation.

### Escalation mechanism

See ADR-0005 for the full reasoning. Applied to the Finding's **existing** Issue — never a new or separate one, keeping "one Issue per Finding" intact (`CONTEXT.md`). Uses tools that already exist, `apply_label` and `add_comment`:

- Add the `escalated` label, alongside the Finding's existing category/system labels.
- Post a comment stating what SLA was missed and when (e.g., the Orphaned same-day SLA).

**No assignee.** This is a public repo about a fictional company (`access-control-policy.md`) — there is no real GitHub account behind "the Security/Compliance Reviewer" to assign or notify, and assigning every escalation to one real person (or failing against a nonexistent one) would misrepresent the mechanism. Escalation's actual job here is recorded visibility, not live notification: `is:open label:escalated` surfaces every escalation across the repo's history, the Issue's own comment timeline shows exactly when it escalated relative to when it was first flagged, and the aggregate quarterly report's "Escalations this period" table (`report-template-quarterly-audit.md`) already gives a scannable, aggregated view on top of that — a reviewer never has to dig through individual Issues to find them.

**Considered and not built:** a GitHub Projects (v2) board with a custom "Owner"/"Status" field, for a dashboard-style role display. The information it would show already exists via the system label (Asset Owner is a strict 1:1 relationship with a system — the system label already identifies the owner) and the `escalated` label (Escalation is by definition raised to the Reviewer). Would add a real, separate API surface and new tools for a marginal display improvement over label filtering that already works — a real future enhancement if a dashboard layer is ever wanted, not v1 scope.

Same "no real account" reasoning is *also* why Monthly Operational Flags' PR-with-reviewer-request delivery mechanism was rejected (ADR-0003) — not only because a scripted demo can't authentically exercise live engagement, but because there's no real Asset Owner account to request review from in the first place.

---

## 5. Risk Assessment Entry

Not a Finding — see `CONTEXT.md`. Computed only at the quarterly-audit trigger, by the main agent, from `list_issues` (accumulated state) and `read_prior_report` (prior periods). One entry per (category, system) pair with at least one Finding this quarter.

- **Likelihood**: Low = new this audit · Medium = open across 2 consecutive audits · High = open across 3+ consecutive audits

- **Impact**: a hand-authored lookup, not a formula — see ADR-0002 for why min/max/multiplicative formulas were tried and rejected in favor of a direct table.

  | System Criticality ↓ / Access Level → | read | write | admin |
  | :-- | :-: | :-: | :-: |
  | **Critical** | Medium | High | High |
  | **High** | Low | Medium | High |
  | **Medium** | Low | Medium | Medium |
  | **Low** | Low | Low | Medium |

  Impact never reaches "Critical" — that value only ever appears as a Risk Rating output (below), never as an Impact value on its own.

- **Risk Rating**: Likelihood × Impact, a second lookup:

  | Likelihood ↓ / Impact → | Low | Medium | High |
  | :-- | :-: | :-: | :-: |
  | **Low** | Low | Low | Medium |
  | **Medium** | Low | Medium | High |
  | **High** | Medium | High | **Critical** |

Both tables are hand-authored and fixed, the same discipline as the dormant-access thresholds — not derived from a formula. See `policy-config.yaml`.

---

## 6. Reports

Two evidentiary tiers plus one informational report, per `iam-review-agent-design.md` and the three templates. No two reports repeat another's line-item content — each links out instead.

| Report | Template | Path | Cadence | Signed by | Content |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Monthly Operational Flags | `report-template-monthly-flags.md` | `reports/monthly/<period>/<system>.md` | Monthly | — (informational, no sign-off) | Per-system, all currently-open Findings any category (Orphaned included, if still open); runs full detection monthly to catch quiet systems, but stays Evidentiary-free — no SLA, doesn't gate Escalation, plain commit not a PR — see ADR-0003 |
| Per-system | `report-template-per-system.md` | `reports/<period>/<system>.md` | Quarterly | Asset Owner | Line-item Findings for that one system only, including "No findings" lines for zero-count categories |
| Aggregate (Quarterly Audit Report) | `report-template-quarterly-audit.md` | `reports/<period>/aggregate.md` | Quarterly | Security/Compliance Reviewer | Executive summary + trend line, methodology, resolution-status rollup, Risk Assessment section, Escalations section, links out to the five per-system reports |

All three are written by `commit_report` (§3) — a plain commit, no PR, no review gate, for all three. `<period>` is `YYYY-Qn` for the quarterly tier (e.g. `2026-Q1`) and `YYYY-MM` for the monthly tier (e.g. `2026-02`) — different granularity, same convention, and the two never collide since they live under different `reports/` subpaths (`reports/<period>/` vs. `reports/monthly/<period>/`).

Every quarter also produces a tagged **GitHub Release**, pinning the commit (code + policy + data snapshot) and bundling the five per-system reports, the aggregate report, and its PDF export. The Markdown in `reports/` is the diffable evidence trail; the Release is the packaged, citable bundle on top of it. Publishing is gated behind a human-in-the-loop approval (GitHub Actions environment protection rule). Monthly reports are never bundled into a Release — they're informational, not evidentiary (ADR-0003), and the quarterly Release's whole point is pinning the audit-evidence trail specifically.

**Tag:** `<period>` exactly (e.g. `2026-Q1`) — the same canonical value used for the `reports/` folder and every template's `{{PERIOD}}`, not a separate tag-specific format. **Title:** a human-readable label, e.g. "Q1 2026 Quarterly Access Review Audit." **Body:** the aggregate report's own Executive Summary numbers (total findings, remediated/open/accepted-risk counts, trend note, escalation count) plus links to the six report files — not new content, a preview of the aggregate report readable without downloading anything. **Assets:** the five per-system `.md` files, the aggregate `.md`, and the aggregate's PDF export — seven files. **Sequencing:** `commit_report` writes and commits all six Markdown files first; `create_release` then tags that exact commit and uploads the assets, so the tag always points at the commit the reports were actually written in.

---

## 7. Guardrails

From `iam-review-agent-design.md`'s Guardrails section, restated as commitments:

- **Tool-permission scoping** — no grant/revoke capability anywhere in the registry (§3).
- **Grounding/citation checks** — every Finding must cite the exact source record; a validation step confirms it exists with the claimed properties before it becomes an Issue. Runs once per run, in the main agent (ADR-0001). Proven by eval case 37 (`eval-cases.md`).
- **Human-in-the-loop publish gate** — the quarterly Release (and possibly individual Issues) requires approval before publishing.
- **Fail-loud completeness** — every report shows every category explicitly, including "No findings." Malformed source data errors visibly rather than producing a quietly incomplete report. Per ADR-0001: a failure is scoped to the affected system — the run still publishes what it has for the other four, with an explicit failed-system line, rather than aborting entirely.
- **Input safety** — HRIS/access-data fields (name, role, notes) are read as inert data, never as instructions. Proven by eval case 38 (`eval-cases.md`), not just asserted.
- **Cost/budget control** — a tool-call/iteration cap is enforced (`ClaudeAgentOptions.max_turns`) on every Agent SDK call in the codebase, pinned from real run data (§3).
- **Least-privilege CI credentials** — `GITHUB_TOKEN` explicitly scoped in workflow YAML (`permissions: issues: write, contents: read`), not left at default breadth.

---

## 8. v1 Core scope

**In:**
Orphaned (both variants), Dormant admin-level (Evidentiary only), Dormant ad-hoc (Evidentiary only), Unapproved (Evidentiary only), Identity resolution, Drift (Evidentiary only), Risk Assessment synthesis, Unremediated-findings Escalation (fires at most once per Finding — ADR-0003), the Monthly Operational Flags summary (runs full detection monthly to catch quiet systems, but stays informational — not evidentiary, no SLA, no Escalation eligibility — ADR-0003), the trend line, remediation re-check/auto-close, Accepted Risk, PDF generation for the aggregate report (Markdown → HTML → PDF via `markdown` + `xhtml2pdf`, both pure Python — a mechanical rendering step with no reasoning in it, so eval cases still test Markdown content only and don't cover PDF output; built in Milestone 11 once the Release Gate needed a real PDF asset, having originally been deferred here for the same "no reasoning in it" reason).

**Out of scope:**
Dormant admin-level's monthly Operational variant, Dormant ad-hoc's own monthly Operational variant, Drift's monthly Operational variant, the grant-time Unapproved gate, contractor end-date expiry detection. Each of the three monthly Operational variants is a deliberate product boundary (Escalation reserved for genuinely acute risk, per Orphaned), not a cost cut — see `iam-review-agent-design.md` for the reasoning. See `future-capabilities.md` for larger, more substantial candidate capabilities (Predictive prioritization, Certification-triage by novelty, Policy-to-config drift detection) kept separate from this list given their depth.
