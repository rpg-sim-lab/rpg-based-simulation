---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE

## Title
A COMBAT_RETREAT project walks its owner to the town centre through the strategic pass, against Bible 04's rule that a chosen retreat takes no step (held flight, memo row 91 (2))

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
In a kernel scene (hp 8/100, an acting hostile adjacent, no tactical retreat destination, a stored target elsewhere) the subject walks toward the town centre on base e512a40d9 from t16 and again from t22. The writer is src/systems/strategic_systems/intelligence.py:670 (fused_strategic_pass copies the active objective's target_position into the nav target), for the project built by CombatRetreatScorer (src/ai/goals/scorers.py:248-252, target state.town_center). Bible 04 section 1 says a chosen retreat is a stored target that takes no step (Chapter 2 section 7, CONFLICT-04) and the owner held the retreat flight (memo row 91 (2), measured as G).

## Scope
1. Confirm in a world scene (a real town centre, not the lodging fixture's default) that a COMBAT_RETREAT project walks its owner through the strategic pass. 2. rpg-designer scopes: keep the walk and fix the Bible sentence, or stop the strategic write for a retreat project. Measured as a behaviour step if code changes.

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
- src/systems/strategic_systems/intelligence.py (fused_strategic_pass, :670)
- src/ai/goals/scorers.py (CombatRetreatScorer, :248-252)

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes
Found by rpg-implementer on 2026-11-09 with a unit-run spy on NavigationUpdate; no code in this ticket yet.

## Test Summary

## Files Changed

## Completion Summary
