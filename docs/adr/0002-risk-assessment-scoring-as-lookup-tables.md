# 0002. Risk Assessment scoring as chained lookup tables, not a formula

**Status:** accepted

## Context

Risk Assessment Entries (`CONTEXT.md`) need a deterministic score — likelihood × impact — that an auditor can verify by hand, not a black box. Likelihood was already settled (Low/Medium/High from quarterly-recurrence count). Impact and the final Risk Rating were not: the design doc only gave two worked endpoints (Finance ERP/Critical/admin → Impact High, Risk Rating Critical; VPN/Low/read → Impact Low, Risk Rating Low), not a full specification.

Three formula-based approaches were tried against those two known points and a motivating example (AWS admin access should read as more significant than an orphaned VPN finding):

- **Impact = min(System Criticality, Access Level).** Matches both known points, but caps Impact at "Low" for *any* read-level access regardless of system — a read-only Orphaned finding on Finance ERP (Critical) would score Low impact, understating a genuine risk on the project's own flagship "most critical" system.
- **Impact = max(System Criticality, Access Level).** Also matches both known points, but pushes *any* admin-level access to "High" impact regardless of system — admin access on VPN (Low criticality) would score the same as admin access on Finance ERP, losing the criticality signal entirely.
- **Score = Criticality × Likelihood × Impact, three factors each scaled 1–3, bucketed across the 1–27 range.** Breaks down two ways: (1) System Criticality has four real tiers (Critical/High/Medium/Low) in `role-access-mapping.yaml`, not three, so fitting it to a 1–3 scale forces two tiers to collapse — naturally Critical and High, which erases exactly the distinction Finance ERP (Critical) is meant to carry over AWS/Salesforce (High) throughout the rest of the design. (2) The product of three values in {1,2,3} only takes 10 distinct values (1, 2, 3, 4, 6, 8, 9, 12, 18, 27), unevenly spaced — an even three-way bucket split puts 7 of the 10 possible combinations in "Low" and only the all-maxed case in "High," which is *less* discriminating than a hand-authored table, not more, and still requires hand-picking irregular bucket cutoffs to fix.

No formula tried satisfied both the known data points and the qualitative judgment calls (a Critical system's read-level exposure still matters; a Low-criticality system's admin access still shouldn't equal a Critical system's) without a real trade-off. Meanwhile, `System Criticality` itself (`role-access-mapping.yaml`) and the dormant-access thresholds (`access-control-policy.md`) are both already hand-authored, fixed lookups, not derived values — there's an existing convention this decision can just follow instead of inventing a formula that needs its own justification.

## Decision

Impact and Risk Rating are both direct, hand-authored lookup tables, not formulas — the same discipline already used for System Criticality and the dormant-access thresholds.

**Impact** = lookup(System Criticality, Access Level):

| System Criticality ↓ / Access Level → | read | write | admin |
| :-- | :-: | :-: | :-: |
| Critical | Medium | High | High |
| High | Low | Medium | High |
| Medium | Low | Medium | Medium |
| Low | Low | Low | Medium |

**Risk Rating** = lookup(Likelihood, Impact):

| Likelihood ↓ / Impact → | Low | Medium | High |
| :-- | :-: | :-: | :-: |
| Low | Low | Low | Medium |
| Medium | Low | Medium | High |
| High | Medium | High | Critical |

Both tables reproduce the two known worked examples exactly. "Critical" is reachable only as a Risk Rating output (High likelihood × High impact) — Impact itself never takes the value "Critical."

## Consequences

- Twelve cells (Impact) plus nine cells (Risk Rating) are judgment calls made once, here, rather than derived — auditable at a glance, and adjustable cell-by-cell if a specific combination reads wrong later, without re-deriving a formula.
- `report-template-quarterly-audit.md`'s Risk Assessment table placeholder for Impact was `{{Low/Medium/High/Critical}}`; corrected to `{{Low/Medium/High}}` to match — Critical belongs only in the Risk Rating column.
- Both tables belong in `policy-config.yaml` once that file exists (planned next session) — they're exactly the kind of parametric, machine-consumed input that file is for, distinct from `access-control-policy.md`'s human-readable prose.
- Extending System Criticality or Access Level to a new value (a sixth Information System, or a new access tier) means extending these tables by hand, not recomputing a formula — an explicit, visible edit rather than a silent behavior change.
