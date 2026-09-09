# 0007. Local-vs-remote parity via a dry-run-capable adapter

**Status:** accepted

## Context

`iam-review-agent-design.md`'s Local vs. remote section deferred this as an ADR candidate until implementation surfaced whether it was a real problem, rather than speculating about it upfront. Milestone 2 (`open_issue`, the agent's first real write) is that implementation.

The core question: how does the same `open_issue` code run safely against fixture data during development, in eval/CI, and against a real GitHub repo, without three separate code paths to keep in sync — and without every local run risking an accidental write.

## Decision

**A single `open_issue()` function, gated by `validate_finding()`, delegates the actual write to an adapter selected by one environment variable, `GITHUB_WRITE_MODE`.** Unset (or any value other than `"real"`) selects `DryRunAdapter`, which logs the would-be title/body/labels and returns a result with `dry_run=True`, `number=None` — no network call. `"real"` selects `RealAdapter`, which calls the GitHub API via PyGithub and returns the actual Issue number and URL.

**Dry-run is the default, not opt-in.** An accidental real write is harder to undo than a missed one, so the safe path requires no flag at all; only a deliberate `GITHUB_WRITE_MODE=real` opts into real writes.

**Token resolution**: `GITHUB_TOKEN` env var first — the same variable name whether it's a local `.env` value or a GitHub Actions secret, so the adapter code never knows or cares which. Falls back to `gh auth token` for local-dev convenience only (CI always sets `GITHUB_TOKEN` directly and never reaches this fallback). This fallback is what let Milestone 2's real-mode verification run without adding any new local secret — the existing `gh` CLI session was sufficient.

**The eval harness needs none of this** — confirmed in Milestone 1 and unchanged since: it exercises the core reconciliation logic against fixtures with no GitHub dependency at all.

## Consequences

- `src/access_review_agent/github/adapter.py` holds both adapters plus `get_adapter()`; `github/issues.py`'s `open_issue()` is the only caller, and the only thing it imports from the adapter module. Detection code and the grounding gate stay entirely unaware that dry-run mode exists.
- Verified for real, not just by inspection: dry-run mode was exercised against both a grounded finding (correct title/body/labels logged) and a fabricated ungrounded one (correctly rejected by `validate_finding()` before the adapter was ever reached); real mode was then exercised once against the scratch repo (`dotMR/access-review-agent-scratch`), producing an Issue with the exact title/body/labels `SPEC.md` §4 specifies, confirmed via `gh issue view`, then closed.
- The Source record citation in the Issue body cited a bare file path at the time this ADR was filed, not a GitHub blob permalink (`.../blob/<sha>/<path>`) — a triggering commit SHA had nowhere to come from until Milestone 5's push-triggered dispatch existed. That gap is closed as of Milestone 5 (`SPEC.md` §4, `development-plan.md`).
- `GITHUB_WRITE_MODE` and `GITHUB_TOKEN` join `ANTHROPIC_API_KEY` as the project's environment-variable surface — both follow the same `.env`-locally / repo-secret-in-CI pattern, no new mechanism introduced.
