# Architecture Decision Records

Lightweight ADRs for the Access Review Agent: Context / Decision / Consequences, one file per decision, four-digit zero-padded numbering, never renumbered or deleted even if superseded. See `template.md` for the format and `iam-review-agent-design.md`'s "Decision record" section for why this convention exists.

## Index

| ADR | Title | Status |
| :-- | :-- | :-- |
| [0001](./0001-per-system-subagents-with-commit-scoped-dispatch.md) | Per-system subagents with commit-scoped dispatch and centralized write access | Accepted |
| [0002](./0002-risk-assessment-scoring-as-lookup-tables.md) | Risk Assessment scoring as chained lookup tables, not a formula | Accepted |
| [0003](./0003-monthly-summary-as-informational-not-new-detection.md) | Monthly Operational Flags: informational summary, with monthly detection | Accepted |
| [0004](./0004-role-access-mapping-single-source-no-markdown-duplicate.md) | `role-access-mapping.yaml` as single source, no Markdown duplicate | Accepted |
| [0005](./0005-issue-lifecycle-escalation-and-accepted-risk-closure.md) | Issue lifecycle semantics: Escalation mechanism and Accepted Risk closure | Accepted |
| [0006](./0006-no-model-call-for-deterministic-categories.md) | No model call at all for deterministic (Tier 1) categories | Accepted |
| [0007](./0007-local-vs-remote-dry-run-adapter.md) | Local-vs-remote parity via a dry-run-capable adapter | Accepted |
