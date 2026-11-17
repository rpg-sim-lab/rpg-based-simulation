---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261117-A-BLOCKED-WALKER-HAS-NO-MEMORY-OF-ITS-DETOUR-HEADING
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-BLOCKED-WALKER-HAS-NO-MEMORY-OF-ITS-DETOUR-HEADING

## Title
A subject blocked by an obstacle longer than one step has no memory of its detour heading

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
From the STALEMATE nav fix (TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK): its bounded give-up (N=2 way-rounds with no progress) hands a blocked subject back to the brain. A typed detour heading on NavigationComponent (cleared on arrival, progress or a replan) would let a blocked step slide one way along the obstacle (rpg-designer: a later quality item; it still needs the bound, since a heading can circle a closed obstacle).

Filed by rpg-planner during M1 Phase 1 (owner #715 6936893143: deeper issues found now are filed and fixed in Phase 3 unless they are hard errors). rpg-designer ruled the class.

## Scope
1. Count, after the STALEMATE fix lands, the give-ups by obstacle shape (entity vs terrain).
2. If they matter, add the typed heading with FIELD_RULES and fingerprint entries.

## Out of Scope
- Any change in Phase 1 unless it is found to be a hard error.

## Acceptance Criteria
- The give-up count by obstacle shape is reported.
- If built: the heading is typed state with a test, and the bounded give-up is kept.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- as named in the Request Summary

## Assumptions / Open Questions
- Line numbers are from the M1 Phase 1 branches on 2026-11-17; re-check before acting.

## Implementation Notes
- Binding M1 rule: species reads via species_of(), label reads via occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
