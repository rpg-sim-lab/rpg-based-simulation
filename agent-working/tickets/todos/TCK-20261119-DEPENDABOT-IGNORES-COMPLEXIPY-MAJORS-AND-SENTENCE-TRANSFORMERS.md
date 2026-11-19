---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-DEPENDABOT-IGNORES-COMPLEXIPY-MAJORS-AND-SENTENCE-TRANSFORMERS
phase: open
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-DEPENDABOT-IGNORES-COMPLEXIPY-MAJORS-AND-SENTENCE-TRANSFORMERS

## Title
Dependabot ignores complexipy semver-major updates and all sentence-transformers updates in the uv block

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Owner yes (#715, logged by lead-planner-u24 as 7006619870): add two ignores to the uv block of `.github/dependabot.yml`, in the shape of the mcp entry that PR #969 added. (1) `complexipy`, semver-major only, until a code-health re-baseline under its own ruling: Dependabot #974's complexipy 8 to 9 bump produced "60 new/worse violations" on the code-health ratchet (lead-planner-u24's figure; the planner did not re-run it). (2) `sentence-transformers`: knowledge stack, bumped by hand like torch, graphifyy and headroom-ai under #882 (owner decision, option A, #715 6812820923). Full-name ignore chosen, not majors-only: `pyproject.toml` declares `sentence-transformers>=2.7.0` with no upper bound and `requirements-knowledge.txt` pins `==6.1.0` by hand, so a minor or patch bump in `uv.lock` would drift from the hand-pinned knowledge env, and a version change can change the embeddings and therefore the search index (the 2026-10-14 ticket rebuilt the index before taking 6.x). The same reason covers all three names already ignored in full. `duckdb`, `pyarrow` and `websockets` stay un-ignored and come back one at a time. #974 itself is being closed by the owner.

## Scope
- Two entries in the uv block's `ignore:` list, each with a comment naming its reason or ticket. The exact diff goes to lead-planner before it is committed.
- No other file changes.

## Out of Scope
- `pyproject.toml` and `uv.lock` (lead-owned).
- The code-health re-baseline itself.
- Any other dependency.

## Acceptance Criteria
1. The yaml parses and the uv ignore list ends with the complexipy entry (`update-types: ["version-update:semver-major"]`) and the sentence-transformers entry (no `versions`).
2. Each entry has a comment naming its reason or ticket.
3. No test or workflow reads dependabot.yml (checked by grep before the commit).

## Related Tickets
- TCK-20261119-MCP-2X-MIGRATION-VISUAL-ASSETS-SEARCH-MCP-HEADROOM-AI (the mcp entry this follows)
- TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the two tickets named above are cited; the rest share only generic words)

## Related Docs
- `.github/dependabot.yml`

## Related Stored Artifacts
- none

## Related Code Areas
- `.github/dependabot.yml`

## Assumptions / Open Questions
- Whether a Dependabot security update for sentence-transformers is still raised under a full-name ignore: unverified. Check Dependabot's documentation before relying on either answer.
- complexipy is pinned exactly (`complexipy==8.0.1`) in `pyproject.toml`; minor and patch updates still flow and could also move the ratchet's counts: unmeasured.

## Durable state, lifecycle and clocks
N/A: no src change; a Dependabot configuration entry only.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay of an owner yes.

## Test Summary

## Files Changed

## Completion Summary
