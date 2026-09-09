# 0004. `role-access-mapping.yaml` as single source, no Markdown duplicate

**Status:** accepted

## Context

The original plan had `policy-config.yaml` holding a *duplicate* of the Role → Access Mapping and System Criticality data, alongside a separate `role-access-mapping.md` in Markdown — mirroring the deliberate split between `access-control-policy.md` (human-readable Principles) and `policy-config.yaml` (machine-consumed parameters), and accepting drift risk between the two copies as a known, precedented trade-off.

Reconsidering it raised a sharper question: is this data an information source the agent reads at runtime (like HRIS), or config — and either way, does it actually need a separate human-readable duplicate at all?

The `access-control-policy.md`/`policy-config.yaml` split is genuinely justified because the content is *narrative*: a Principle like "Access to Information Systems must be assigned to an individual employee rather than a group or shared account" (Individual Usage) doesn't reduce to a table row — it's governing language a human auditor needs to read as prose, not data.

The Role → Access Mapping's content was never narrative — it's already a table (Role × System → Access Level). Converting Markdown-table-syntax to YAML doesn't lose anything a human reviewer would need: a well-structured YAML mapping is exactly as git-diffable and reviewable in a PR as the Markdown version was. The duplication being considered would have meant accepting real drift risk (two copies, no generation or validation step between them) for a human/machine split that doesn't actually correspond to a difference in content *shape* — unlike the policy/config split, where it does.

## Decision

`role-access-mapping.yaml` is the single, machine-consumed source for the Role → Access Mapping and System Criticality table. No separate `role-access-mapping.md`. Procedurally, it's classified the same as `policy-config.yaml` in the trigger dispatch table (ADR-0001) — both fan out to all five subagents on change — distinguishing it from `access-control-policy.md`, which is never read by a tool and never triggers anything.

## Consequences

- No drift risk between two copies of the same data — unlike `access-control-policy.md`/`policy-config.yaml`, which does still carry drift risk, because that split *is* genuinely justified by a real content-shape difference.
- A human still reviews changes to this file the normal way (git diff, PR review of the YAML) — nothing about reviewability is lost by dropping the Markdown copy.
- Sets the general test for future config decisions in this project: content that's always been structured data, even if currently typeset in Markdown, should become the machine format directly, not duplicated. Content that's genuinely narrative still needs the human/machine split `access-control-policy.md` has.
