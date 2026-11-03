---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261103-BUILDINGS-ARE-NOT-SOLID-ON-COMPILED-WORLDS
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-BUILDINGS-ARE-NOT-SOLID-ON-COMPILED-WORLDS

## Title
Buildings are not solid on compiled worlds: the static-obstruction check short-circuits on an empty building_tiles map: counts first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found during the executor-parity diagnosis (rpg-planner-ubuntu and rpg-designer, 2026-11-03); requested by rpg-designer. rpg-planner read it on main: in src/engine/legality.py:55-57, `_static_obstruction` uses `building_tiles` when it isn't None and returns walkable if the tile isn't in it. The scan of `state.buildings` (:58-60) only runs when `building_tiles` is None. On compiled worlds `building_tiles` is a non-None empty dict (service_reach.py:11: "Compiled worlds declare buildings in `state.buildings` (`state.building_tiles` is empty there)"). So on the sequential reference path, no building tile is solid by this check.

Existing workarounds that show the code knows it:
- src/engine/service_reach.py:11 (comment);
- src/domains/campaigns/survivor_placement.py:77 (`self.building_tiles = None`, to force the scan);
- src/engine/blacksmith.py:115;
- src/engine/legality.py:410 (`getattr(..., 'building_tiles', {})`).

The executor fix goes back to parity only (rpg-designer): the packet reproduces sequential exactly, empty building_tiles with the same short-circuit and the same occupancy answer (the snapshot), and sequential is unchanged. This defect is fixed separately.

## Scope
Counts first, on the pinned runner, standard worlds and seeds:
1. Entity-ticks off lodging standing on a building tile.
2. Moves, intercept positions (tactical.py find_intercept_position) and route targets onto building tiles.
3. F3 leave placements onto another building's tile (lodging.leave_tile uses `_static_obstruction`).
4. Which systems would change if buildings became solid (pathing, service reach, intercept, placement): the F3 reach stated explicitly.
Fix lean: one source for building solidity (rpg-designer's shape, after counts).

## Out of Scope
- The executor parity fix (TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS).
- Removing the four workarounds, which goes with the fix.

## Acceptance Criteria
- Counts 1-4 reported, [D]/[I] marked; rpg-designer rules on the shape.
- An owner row for order: the fix moves the reference world and every baseline.
- If fixed: tests for a compiled world where a building tile is solid; the four workarounds reduced to the one source; Bible 06 and the parity ledger updated; a divergence entry (u24 block 2.159, then 2.200-2.249).
- Hot-loop: yes if fixed (legality runs per move). Under the perf pause (#715 6556861718), timing is NOT MEASURED; say so at close.

## Related Tickets
- TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3, done)
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (N14)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md; docs/engine/ (legality)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- src/engine/legality.py:41-61, :410; src/engine/service_reach.py; src/domains/campaigns/survivor_placement.py:77; src/engine/blacksmith.py:115; src/engine/lodging.py (leave_tile); src/engine/tactical.py (find_intercept_position)

## Assumptions / Open Questions
- Whether anything relies on buildings being walkable on compiled worlds; the counts show it.
- Dispatch needs an owner yes.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
