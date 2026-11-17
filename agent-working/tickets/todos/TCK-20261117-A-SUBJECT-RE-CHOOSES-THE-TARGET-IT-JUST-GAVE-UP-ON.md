---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON

## Title
After a way-round give-up, the target choice picks the same target again within 200 ticks; add a typed give-up memory that target choice respects (F2)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by the STALEMATE fix's own-job run (S9 #715 6947037311, fixtree 08b9dcae8). After a way-round give-up, the given-up target is chosen again within 200 ticks:
- crowded_frontier: 17 of 17 subjects, 238 events;
- frontier_living_world: 37 of 38 subjects, 1093 events;
- urban_political: 20 of 20 subjects, 477 events.

The give-up clears the target, but nothing remembers that it was given up, so target choice picks it again. The rpg-designer ruling (draft .claude/handover/drafts/rpg-designer-stalemate-s3-ruling.md, sha prefix 82f62819) makes this F2: a separate Phase-1 liveness ticket in run 1. It does NOT gate the STALEMATE F1 PR, with one exception: if F1's rerun shows any subject giving up the same anchor 5 or more times in 5000 ticks, it comes back to the designer before merge.

## Scope
1. DESIGN BY rpg-designer, pending. A typed give-up memory, durable with a defined lifecycle and expiry, that target choice respects.
2. Implementation, tests and a measured rerun, after the design.

## Out of Scope
- F1, the way-round count anchoring (the STALEMATE fix PR).
- Blocker-churn work.

## Acceptance Criteria
- Set by the designer's design. At minimum: after the fix, the "give-up target re-chosen within 200 ticks" count falls by an agreed bar on the 3 standard cells, with no S1/S2/S3 regression.

## Related Tickets
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (the STALEMATE fix lane; F1)
- TCK-20261117-A-BLOCKED-WALKER-HAS-NO-MEMORY-OF-ITS-DETOUR-HEADING (neighbouring memory gap)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- the 2.213 amendment in the designer's draft

## Related Stored Artifacts
- /mnt/data2/rpg-measure/stalemate/cells_fix/ and cells_fix_v7/ (on the owner's delete list)

## Related Code Areas
- src/engine/patches.py (navigation apply), resolve_move, the target-choice path (to be located in the design)

## Assumptions / Open Questions
- Where the memory lives (NavigationComponent or cognition memory), its expiry and its scope (per tile, per anchor or per target kind): the designer decides.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
