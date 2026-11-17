---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-SDLC-CODEX-TRACK-MARKED-LEGACY
phase: open
date: 2026-11-16
tags: [ai, governance]
---

# TCK-20261116-SDLC-CODEX-TRACK-MARKED-LEGACY

## Title
The Codex / provider-neutral track is marked "legacy support (provider-agnostic)" where a reader meets it first, and its CI lane is split only if it also carries the agent-orchestration tests.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
OD-6, filed by agent-working-planner on 2026-11-16 at agent-working-designer's suggestion. Filing only: dispatch needs a separate owner go.

The owner's words (#715 6910853925): "OD-06 - if it cause no issue, keep it and mark as legacy support (provider-agnostic)." Plan §32a recommends a split, so that freezing the track does not also silence `tests/agent_orchestration`.

## Scope
1. **Read first.** Read the CI lane that runs the Codex, provider-neutral and replay tests in `.github/workflows/test.yml` (it is probably the `agent-orchestration` job; confirm its name). Record in the ticket:
   - its name and path filters;
   - whether it runs on every PR;
   - which test directories it runs.
2. **Mark legacy.** Add "legacy support (provider-agnostic)" where a reader meets the track first:
   - the provider-neutral contract doc's opening;
   - the Codex track's entry point docstring or README;
   - the lane's display name.

   Nothing is deleted, and no behaviour changes.
3. **Split only if needed.** If the lane also runs `tests/agent_orchestration` (the non-Codex orchestration tests), split it into two jobs, so a later freeze of the Codex lane leaves the orchestration tests running. If it doesn't, say so and change nothing. The workflow edit is a governing change: the exact diff goes to the owner through lead-planner before commit.

## Out of Scope
- Removing or freezing the track, and any R2 decision.
- Changing what any test asserts.

## Acceptance Criteria
1. The ticket records the lane read: name, filters, directories, and whether it runs on every PR.
2. The legacy label is present in the three places, or the ticket names why a place doesn't exist.
3. If the lane was split, both jobs run on a PR that touches `tools/agent_orchestration/`, and the CI-coverage test (`tests/tools/test_ci_workflow_test_coverage.py`) passes. If it wasn't split, the reason is stated.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (the `sdlc-codex-track-20261031` and `sdlc-provider-neutral-contract-20261031` tags)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (§32a)
- docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md (2026-11-16, OD-6)

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/test.yml (`agent-orchestration` job)
- tools/agent_orchestration/, tools/agent_replay/

## Assumptions / Open Questions
- "If it cause no issue": if the read in scope 1 finds a real cost of keeping the track (for example a failing or flaky lane), report it to agent-working-planner. Don't fix it here.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
