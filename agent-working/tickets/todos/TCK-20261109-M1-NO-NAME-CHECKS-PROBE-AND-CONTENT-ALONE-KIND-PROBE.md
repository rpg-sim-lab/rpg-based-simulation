---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE

## Title
Milestone 1's two gate probes: no name switch in a decision path, and a test kind declared only in content perceives, eats and fights

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.5 done item 1: "no decision reads a role, kind or faction name, a new kind works from content alone, and the 'no name checks in decision code' probe finds no name switch left in a decision path. 'Works from content alone' is proven by a named probe: a test kind declared only in content, with no code change, perceives, eats and fights by its declarations." §12.3 lists the name-check probe as a standing check.

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. The name-check probe: a mechanical scan of the decision paths for role, kind and faction name comparisons, with an explicit, reasoned allowlist. Run it early, because its output is the inventory for the retire-name-branches item.
2. The content-alone probe: a test kind declared only in test content, with no code change, perceives, eats and fights by its declarations through the real kernel.
- Whether these live under tests/architecture is testing-planner's call (route: tests/architecture/** belongs to testing-planner).

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- The name-check probe runs in CI and reports every name switch it finds. It goes green only when milestone 1's retirements are done.
- The content-alone probe passes on the milestone 1 record commit.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
tests/, decision code (read only)

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
