---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE
artifact_type: test_plan
---

# Test plan — TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3, lodging)

Real Kernel for behaviour tests (as `test_a_chosen_rest_lasts_until...`: ids 1-10, inn-bed SLEEP); pure tests for helpers. No test pins a number from a run.

## Unit (AC 6)
1. A served bed lodges: REST at an inn with beds>0 and a free bed sets `lodged_in`, position = building tile; a rough rest (CoreActions REST without a bed), a collapse, a WORK shift and an EAT do not.
2. `beds` 0 or absent: REST is served on the reach tile exactly as on main (golden comparison with a no-beds building).
3. Admission grid row: a full building does not admit REST (`admits`), `ways_in_reach` and FatigueScorer see it closed; an arrival with no bed dispatches no REST and ends the fatigue project with the typed way-closed end.
4. Same-tick contest for the last bed: lowest entity id wins.
5. Leaving: free reach tile in `_REACH_OFFSETS` order without (0,0); else ring search radius 3; else stays lodged awake and retries next tick (counted); two leavers on one tile: lowest id wins, the other takes the next tile.
6. A building that stops being functional ejects its lodgers.
7. A lodger is absent from `get_occupancy_map`, `OccupancySnapshot`, `entities_by_tile`, `SpatialGrid`, `candidate_selector.position_index` and the occupancy phase map; unattackable (legality gate, stale-id case), not splashed (AoE), not a swap partner, not in outside perception (`perceived_hostile`, neighbor view), not an adjacent hostile (decision 32); two lodgers of one building on one tile raise no LAW-OCCUPANCY-COLLISION.
8. An inn lodger is served EAT from the building tile (single tick, stays lodged or leaves per the next decision); hunger arrival fires at distance 0.
9. Lodging does not leak a stale cache: lodge and leave mark the entity dirty (movement plan cache version, entities index).

## Architecture (AC 7)
- `lodged_in` round-trips in `NavigationComponent.to_canonical_dict` (omitted when None: canonical dict of a non-lodging entity unchanged) and survives `_fast_replace_navigation` after a move.
- Set and cleared only through the apply path; decision code reads, never writes (source scan like existing apply-path tests).
- Replay/fingerprint equal to base while nobody lodges (determinism baseline).

## Paired runs (AC 1-5; slot required)
- Base arm: item 1's 15 runs at 6fdfdf555 (3 worlds x s42-46, 5000t) with an observer extended for door-tile holders by sleep type; reused as the acceptance base. F3 arm: same 15. Same scripts as N14 (agg2/decomp). Report: door-tile sleeper ticks per world (must fall below base in every world), deaths by cause per world and asleep-at-death (STOP if up, victim ids), stall runs, bed-full refusals per building, peak lodgers, stuck-awake-indoors ticks (any > 50 is a finding), reach-tile hold split. Two repeats of one seed byte-equal; first-diff report vs base.

## Docs/parity (AC 8)
- Bible 04 sec 1 and local_world_interaction_contract 2.1 law text; divergence 2.155 (Enforced) with Verification test path; parity rows STRAT/MOV; mechanisms.yaml via rpg-planner.

## Existing suites to run (scoped)
tests/unit/engine, tests/unit/strategic, tests/unit/ai, tests/unit/cognition, tests for legality/occupancy/spatial/hard_law_monitor/replay fingerprint, the architecture tests touching apply path and canonical dict.
