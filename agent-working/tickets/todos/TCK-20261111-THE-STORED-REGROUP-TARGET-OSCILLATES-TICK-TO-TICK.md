---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK
phase: open
date: 2026-11-11
tags: []
---

# TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK

## Title
The REGROUP target that fused_strategic_pass stores (~:678) flips between neighbouring tiles tick to tick, walking the subject into contact and out of it

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
rpg-designer found this while checking the Scope 1 trace of TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING (lane B, free_swing_trace.py at sha256 7c22df89…, 5 hash-matched runs). rpg-planner filed it on 2026-11-11.

In the traced windows, the stored REGROUP navigation target written at intelligence.py ~:678 alternates:
- crowded s42 #3: 39↔38 on one axis;
- crowded s43 #12: 35↔34;
- def2 crowded s45 #5: around (25,25).

The movement phase walks each new target, so the subject steps toward the fight and back away from it, and each step off engagement pays the opportunity attack.

Raw data: /mnt/data2/scratch-b/fst_out/{flight_c42,flight_c43,def2_c45}.json; the readout is in the non-flight ticket's staging_artifacts/trace_readout.txt.

## Scope
1. Investigation first, read-only: what recomputes the REGROUP point each tick? Candidates: the nearest town tile from a moving position (`nearest_town_tile`), the slow/fast path alternating, or a group centroid. Name the writer and its inputs per tick, on main.
2. Then a fix proposal to rpg-designer. Whether a stored REGROUP point should be stable once chosen is a design question.

## Out of Scope
- The lethal free-swing step itself (TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING).
- Whether a stored target may step at all while engaged (TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE, widened).

## Acceptance Criteria
- The writer and its per-tick inputs are named, with a trace on main that hash-matches its cell.
- rpg-designer rules on the fix shape before any code.

## Related Tickets
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
- TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/mechanics/02_combat_laws.md §7

## Related Stored Artifacts
- None yet.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (~:670-:680 slow-path navigation writes)

## Assumptions / Open Questions
- intelligence.py is on the hands-off list for the COMBAT-RETREAT P2 and is the next-gen stage 3 slice. Any fix here is sequenced with both.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
