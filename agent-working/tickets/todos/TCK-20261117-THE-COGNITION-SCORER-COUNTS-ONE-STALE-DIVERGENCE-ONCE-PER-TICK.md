---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261117-THE-COGNITION-SCORER-COUNTS-ONE-STALE-DIVERGENCE-ONCE-PER-TICK
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-THE-COGNITION-SCORER-COUNTS-ONE-STALE-DIVERGENCE-ONCE-PER-TICK

## Title
The SimQ COGNITION scorer counts decision_divergence_detected once per tick, so one stale cause reads as an S or A grade

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by lane D's Read A: event_shapers.py:913-935 emits decision_divergence_detected on every tick where the top concern is a DANGER above 0.7 while the current project is non-survival, and the COGNITION scorer adds +5 per event. One stale concern held for about 100 ticks produced an S/A grade on simq_routing_test s42 (500t and 1000t), from no data. That grade can anchor nothing until this is fixed (rpg-designer).

Filed by rpg-planner during M1 Phase 1 (owner #715 6936893143: deeper issues found now are filed and fixed in Phase 3 unless they are hard errors). rpg-designer ruled the class.

## Scope
1. Count the divergence per episode (one cause, one run of ticks) or rate-normalise it.
2. Re-read the affected corpus anchors.

## Out of Scope
- Any change in Phase 1 unless it is found to be a hard error.

## Acceptance Criteria
- A sustained single-cause divergence counts once per episode, or is normalised, with a test.
- The simq_routing COGNITION anchors are re-read under the fix.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261117-A-DANGER-CONCERN-IS-NEVER-REMOVED-ONCE-ITS-HOSTILE-NO-LONGER-MATTERS

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
