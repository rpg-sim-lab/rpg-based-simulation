---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE

## Title
A sleeper holds a door or service tile (F3: a served rest occupies the building, not the door tile)

## Status
OPEN (design: rpg-designer; seated by rpg-planner 2026-10-31; NEXT item, ahead of A', the nav family and #781)

## Tier
standard (provisional; the designer's design decides. Dispatch needs an owner go via lead-planner-u24 / #715)

## Type
repair

## Priority
P1

## Request Summary
A walk to a building ends on reach, standing orthogonally beside its unenterable tile (divergence 2.78). A subject served REST/SLEEP there sleeps ON that reach tile, so the building's only entry tile is held by a sleeper and others cannot reach the service. N14's 2.153 (a chosen rest lasts until debt < REST_MIN_SLEEP_DEBT) consolidates sleep and so lengthens these holds: the jam moves from fatigue-project holders to sleepers. rpg-designer ruled 2026-10-31 that N14 does not land alone; F3 goes first and N14 is re-measured on top of it.

## Evidence (N14 final-code table, base ba7aa11bd vs new2 = 2.153 + 2.154 narrowed; 15 paired runs, 3 worlds x s42-46, 5000t; lane B, /mnt/data/scratch-rpg-implementer-2/n14/)
- Door-tile occupancy 195,981 -> 170,318 ticks; by SLEEPERS 74,281 -> 111,824 (every world: crowded 11,128->23,456; frontier 28,491->38,391; urban 34,662->49,977); by fatigue-project holders 174,830 -> 110,094.
- Stall runs >=20 ticks 878 -> 813 (target not met); stall ticks 130,995 -> 65,796.
- Deaths 346 -> 376 (urban s44 6->28, frontier +14); asleep share 0.1951 -> 0.2057. Both N14 STOPs tripped.
- Hoverer split (cut: >=3 REST spans of <=4 ticks within 50 ticks, fatigue project current, no collapse; base-defined ids): hoverers' chosen-sleep ticks about unchanged (spans consolidate); the crowded_frontier rise is in non-hoverers (0.058 -> 0.104).
- s44 final-code ablation pair (urban_political s44, 5000t; lane B 2026-10-31; traces n14/out/trace_new2_ablate_{rest20,floor}_urban_political_44.jsonl):
  - base: deaths 6 (2/2/2 HAZ/COMBAT/DEFEAT); inn door ticks 25,654, by sleepers 8,802; subject 17 0 collapses, alive.
  - new2: 28 (9/10/9); door 10,290, sleepers 7,644; 17 collapses, subject 17 dies t4434.
  - rest-to-20 OFF: BYTE-IDENTICAL to base. The whole s44 divergence is 2.153's longer chosen rest.
  - floor-end wake OFF: 17 (2/8/7); door 20,091, sleepers 10,528; 0 collapses, subject 17 dies t3661. The floor-end wake feeds the collapse cascade and the extra HAZARD deaths; the longer rest alone brings +11 COMBAT/DEFEAT.
  - CAUTION for F3: in s44 the door-sleeper ticks FALL in new2 (7,644 < 8,802), so s44's deaths are HOW LONG (plus the floor-end wake), not WHERE. F3 alone may not clear s44; the all-world door rise is the WHERE evidence.

## Scope
(designer to define) A served rest at a building occupies the building (not the door/reach tile), so the reach tile stays free for others while the subject sleeps; the 2.78 reach semantics for services that serve a rest.

## Out of Scope
- N14's own changes (2.153, 2.154), parked as lane B's local WIP 173e5fd42 on rpg-nav-stall, re-measured on top of F3.
- F2 (a door yield to pressing hunger: an owner row, only if still needed after F3).
- STALEMATE/WANDER nav family; #781 D73.

## Acceptance Criteria
(designer to define) Minimum, carried from N14: door occupancy by sleepers falls below base; no rise in deaths by cause; asleep-at-death not up; then N14 on top of F3 clears its STOPs (asleep share, deaths), with the owner question on the asleep share framed after that re-measure.

## Related Tickets
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (N14; source of F3; parked behind this)
- TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED (2.78)
- TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED (A', after this and N14)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.78, 2.106, 2.153, 2.154
- docs/engine/contracts/local_world_interaction_contract.md section 2.1 (occupancy and obstruction)
- docs/mechanics/04_strategic_cognition.md section 1 (sleep)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/n14/ (agg2.py, decomp.py, out/new2_*.json, out/trace_new2_urban_political_44.jsonl)

## Related Code Areas
- src/engine/building_arrival.py (service on reach), occupancy and movement candidate checks, src/engine/sleep_debt.py

## Assumptions / Open Questions
- Is "occupies the building" a typed occupancy record on the building (capacity), and what happens when the building is full?
- Where does the sleeper reappear on wake if the reach tile is taken?
- Does this apply to every served rest, or also to EAT holds?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
