---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261109-STATE-TOWN-CENTER-DEFAULT-IS-A-SENTINEL-A-RETREAT-CAN-AIM-AT
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-STATE-TOWN-CENTER-DEFAULT-IS-A-SENTINEL-A-RETREAT-CAN-AIM-AT

## Title
The state.town_center default (0.0, 0.0) lets CombatRetreatScorer aim a retreat at a sentinel coordinate in a world with no town (MOV-03)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
src/core/state.py:1345 defaults town_center to (0.0, 0.0). CombatRetreatScorer (src/ai/goals/scorers.py:248-252) takes state.town_center as the retreat objective's point with no check that a town exists, so in a state with no town (the lodging_kernel test fixture) a COMBAT_RETREAT project aims at (0,0). MOV-03 says never a sentinel coordinate. No gate world lacks a town (crowded_frontier, frontier_living_world and urban_political give (25,25)), so this is out of the low-hp ticket.

## Scope
1. Decide whether a state with no town is a valid world. 2. If so, the scorer (and the TownScorer and RecoverScorer sites that read town_center) return no goal or a typed absence instead of the default point; if not, assembly refuses it. A guard test either way.

## Out of Scope
- The low-hp retreat hold of TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE.

## Acceptance Criteria
- The scoping is written and the designer's call recorded before any code.

## Related Tickets
- TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE

## Related Docs
- docs/mechanics/04_strategic_cognition.md (section 1, the wound escalates like a need)
- docs/guidelines/intentional_divergences.md (2.200)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/core/state.py (town_center, :1345)
- src/ai/goals/scorers.py (:168, :250, :273, :313)

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes
Found by rpg-implementer on 2026-11-09 with a unit-run spy on NavigationUpdate; no code in this ticket yet.

## Test Summary

## Files Changed

## Completion Summary
