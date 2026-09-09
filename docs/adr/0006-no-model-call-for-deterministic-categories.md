# 0006. No model call at all for deterministic (Tier 1) categories

**Status:** accepted

## Context

Milestone 1's first implementation of Orphaned detection routed it through the Claude Agent SDK — a real subagent, with `read_access_data`/`read_hris` as tools, reasoning over the results via a system prompt. It worked and passed all three eval cases, but at real cost (roughly $0.08–0.12 per case on the default model) and real latency (10+ seconds per case), for a category `eval-cases.md`'s own Tier 1 classification already calls deterministic — an anti-join plus a status check, no reasoning involved.

The first response to that cost was to switch to a cheaper model (Haiku 4.5), which measured out to roughly a 10x cost reduction ($0.0341 total for three cases, down from ~$0.25–0.35). That was solving the wrong problem. This project's own central design test, applied consistently since the first grilling session, is "does this need AI, or just automation?" — and the answer for Orphaned (and the rest of Tier 1: Dormant both variants, Unapproved, Drift) was already "just automation," decided well before any code existed. Routing a deterministic check through an LLM at all — even a cheap one — doesn't make it more reliable; a plain Python function is 100% reproducible, costs nothing, has no latency, and is at least as auditable as a grounded LLM claim, arguably more so (literal, inspectable code versus reasoning about reasoning).

ADR-0001's isolation design ("subagents... detect their own system's findings independently, in isolated context") doesn't actually require an LLM to be doing the detecting — isolation is a property of what data a piece of code can access, not of whether that code is a model call. A plain Python function scoped to one system's file satisfies the same isolation boundary a pre-bound tool call would.

## Decision

**Tier 1 categories (Orphaned, Dormant admin-level, Dormant ad-hoc, Unapproved, Drift) use no model call at all.** Detection is plain Python, living in `src/access_review_agent/detection/`, reusing the same read-and-validate functions the eventual Agent-SDK-based categories will also use. The grounding/citation guardrail (`validate_finding()`, ADR built alongside Milestone 1) still runs uniformly over every claimed finding regardless of origin — not because Python detection can hallucinate the way a model can, but as defense-in-depth against bugs in the detection logic itself, and so the write-gate in front of `open_issue` (Milestone 2) doesn't need to special-case "was this finding Python-derived or model-derived."

**The Agent SDK is reserved for categories that genuinely need it — first at Milestone 6 (Identity resolution)**, the first category requiring extraction from unstructured prose and the restraint to decline a guess. The working Agent SDK integration code from this exploration (tool wiring, `ClaudeAgentOptions` construction, the JSON-extraction pattern) is preserved as reference material in `reference/milestone-6-agent-sdk-patterns/`, not deleted — including a non-obvious bug (extracting response text via `ResultMessage.result`, not by stringifying raw SDK message objects, whose `repr()` escapes real newlines and silently breaks naive text-pattern matching) that took real debugging effort and shouldn't need rediscovering.

## Consequences

- Milestones 1, 3, and 5 (all Tier 1 categories plus the dispatch rule) need no `ANTHROPIC_API_KEY` at all and run in milliseconds, not seconds — a materially faster and fully free development loop for most of the pre-Milestone-6 build.
- The model-tiering idea (cheap model for Tier 1) this ADR was originally going to record is moot — there's no model call to tier in the first place. Model selection becomes a real decision again starting at Milestone 6, informed by what Identity resolution's and Risk Assessment's reasoning actually requires, not carried over from this exploration unexamined.
- `stub.py`'s original framing (a free dev-only stand-in, with a real SDK call as the "true" path) had it backwards for Tier 1 — the deterministic Python logic *is* the real implementation; the SDK call was solving a problem the category doesn't have. `stub.py` itself is retired; its logic lives on, promoted, as `detection/orphaned.py`.
- `development-plan.md` needs updating throughout: Milestones 1, 3, 4, 5 no longer involve the Agent SDK, and Milestone 6 becomes the actual first point it's used for real.
