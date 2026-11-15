---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261115-THE-GO-TO-TOWN-STEP-RESETS-THE-WALK-TARGET-ON-A-TOWN-TILE
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-THE-GO-TO-TOWN-STEP-RESETS-THE-WALK-TARGET-ON-A-TOWN-TILE

## Title
The go-to-town step for item carriers resets the walk target to the subject's own tile when it stands on a town tile, so it overrides a walk to food chosen in the same tick

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
D2 from the V3 trace. Owner choice: #715 6893303548, "(a) Two defect tickets (Recommended)".
- **Cell B (crowded s46 e4), t3046-3051:** _walk_to (tactical_objective.py:42) sets the target to [27,20], the inn. In the same tick, fused_strategic_pass (intelligence.py :677/:699) sets it to the subject's own tile, with movement_mode REGROUP. The subject took 171 ticks to cover 18 tiles. At normal pace it eats around t3065, before the starving line at t3101.
- **The writer** is the one named in the closed TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK: intelligence.py :675-681 (slow path; fast path :394-406) writes `target_set = nearest_town_tile(state.town_tiles, position) or town_center` for any carrier with pending inventory. nearest_town_tile (town_targeting.py:5-20) returns the subject's own tile on a town tile. A compile of crowded s45 and s46 has 961 town tiles, and every traced position is one.
- That ticket closed as NO CHANGE ("cosmetic churn, pays no swing"), on crowded s42 subject 3. This cell disproves that it is harmless: a starving walker lost about 100 ticks on the way to the inn.

## Scope
The fix shape is rpg-designer's ruling (2026-11-15):
1. The town-return step is SATISFIED when the subject already stands on a town tile: no target write, and no REGROUP mode set.
2. It never overrides a navigation target chosen in the same tick by a need or objective walk. It is a fallback and only fills an empty target.
3. Bible 04, the ledger, and a divergence entry (Bug Fix) in the same change.
4. Measurement: the death bar, 3 worlds × 5 seeds, paired, with a REGROUP-target-write count added to the base and fix rows so the drop shows.

## Out of Scope
- Finding (a) of the closed ticket: nothing discharges pending inventory on arrival, so a carrier with no objective goes to town forever. It's a follow-on that needs its own design, because what a carrier does with its goods is an economy question.
- D1.

## Acceptance Criteria
- On a town tile, the step writes no target and no REGROUP mode. A same-tick need or objective target is never overridden. Unit tests cover both, plus a control where an off-town carrier still gets its town target.
- The paired run is inside its stop rules, and the REGROUP-write count drops.
- Docs, ledger and divergence entry in the same change.

## Related Tickets
- TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK (closed; same writer)
- TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER (D1)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK/

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (:394-406, :675-681, :699)
- src/systems/strategic_systems/town_targeting.py:5-20
- src/engine/tactical_objective.py:42

## Assumptions / Open Questions
- intelligence.py is on the hands-off list for COMBAT-RETREAT P2 and is the next-gen stage 3 slice. Check sequencing at dispatch.
- Landing hold: it moves crowded bases, so it doesn't land while HOLD stage 2 is measuring.
- Dispatch needs the owner's yes, through lead.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
