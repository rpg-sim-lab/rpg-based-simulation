---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE
artifact_type: investigation
---

# Investigation — TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3, lodging)

Base: origin/main 6fdfdf555 (#795). Worktree `sleeper-lodges`, branch `rpg-sleeper-lodges`. Read-only. Item 1 (15-run base split) is NOT done: it waits for the host slot.

## Item 2 — s44 victims (existing traces, base ba7aa11bd, classification only)
Traces: n14/out/trace_{base,new2,new2_ablate_rest20,new2_ablate_floor}_urban_political_44.jsonl. For every death: last alive row, sleep within the 20 ticks before, on an inn/home reach tile (the 5 offsets), distance to the inn, attacker.

| arm | deaths | asleep at the last alive tick | slept within 20 ticks before | on a reach tile at the last alive tick |
|---|---|---|---|---|
| base | 6 (2 HAZ/2 COMBAT/2 DEFEAT) | 0 | 0 | 0 |
| new2 | 28 (9/10/9) | 1 (a COLLAPSE, not on a reach tile) | 1 (COMBAT, within 3 tiles of the inn) | 2 (both COMBAT, awake, inn reach) |
| rest-to-20 OFF | 6 | 0 | 0 | 0 |
| floor-end wake OFF | 17 (2/8/7) | 0 | 0 | 0 |

- new2: 27 of 28 victims were awake and had not slept in the 20 ticks before death. 8 died within 3 tiles of the inn; 20 died farther.
- The six extra HAZARD deaths (ticks 1629-1635) are a group at (42-44, 43-45), awake, sleep debt about 81, hazard cell; base survivors. Subject 17 (hunger 100) is the attacker in 8 of the COMBAT/DEFEAT deaths.
- Reading: in s44 the longer rest does NOT kill sleepers on a reach tile. The extra deaths are awake subjects with high debt (a consequence of consolidated sleep and the floor-end wake) and one hungry hostile. F3 (lodging) removes exposure of a sleeper on a reach tile and the door jam, and neither is the s44 mechanism. As the ticket's CAUTION says, F3 alone will not clear s44. The remaining cause is HOW LONG / the floor-end wake, which needs the designer's next ruling.
- Limits: one seed, pre-#795 base; the "reach tile" test uses inn/home positions from the trace header; "served bed vs refused bed" cannot be read from the trace (needs the item-1 observer).

## Item 3 — EAT
EAT is single-tick, no hold. `actions.py::_survival_action_ends`: a successful survival action ends its task unless it is WORK (held to the last shift tick) or a SLEEP_ACTIONS member (held until rested). EAT is in neither, so it ends the tick it succeeds. A lodger served EAT therefore never holds a tile or a bed through the meal.

## Scope 7 — hunger arrival from the building tile
Yes, it fires. `tactical.py` (reach_location objective, ~l.274-291) dispatches `building_arrival_update` when the Manhattan distance from `navigation.position` to the building position is <= 1.0; a lodger on the building tile has distance 0. `service_building` finds the building through `service_tile`, whose `_REACH_OFFSETS` already begin with (0, 0), so the EAT action is served from the building tile. Two things to settle in the plan, not findings of a defect: (a) that block runs only when `hostiles` is empty and after `in_place_survival_update`; a lodger's own outward perception (it does not see out?) is not specified by the law text; (b) `building_services.service_building` reads `entity.navigation.position`: for a lodger it must use `lodged_in` (same tile, so it works either way).

## What exists today (relevant to the design)
- A served REST: `with_service` merges `service_delta` (heal, readiness, charge) once per hold; when `service_delta` returns None (no building in reach, or `admits` false) the REST action still RUNS and sleeps rough on the tile. That rough fallback IS the jam: there is no refusal path today (scope 4 adds the typed "way closed" end at arrival).
- `admits(entity, "REST")` today covers only the payment law; the "free bed" test is new and must join `admits` (FatigueScorer, `ways_in_reach` read it).
- `buildings.yaml` (data/content/world/buildings.yaml) declares `inn`, `home`; `maintenance_shifts_needed` is copied by `worldbuilding/compiler.py` into `BuildingState` (core/state.py). `beds` follows the same route (content field, compiler, BuildingState field; 0/absent = no lodging).
- Beds are owner-decided: inn 10, home 4.

## Item 4 / Scope 6 — readers of `navigation.position`
Method: grep gave 314 `navigation.position` hits plus about 40 through the `EntityState.position` property (core/state.py:1045); an Explore agent classified them by function and read the six index builders (I re-checked the builder lines myself). Consumer bodies were not all read; a "covered" verdict assumes the filter at the builder.

### The six builders that need `lodged_in` filtered once (each currently keys on `lifecycle.active and combat.alive`)
1. `engine/spatial_query.py:117-120` `get_occupancy_map` (tile -> id). Feeds legality get_occupant / check_occupancy_legality / get_engaged_hostiles_at_pos, movement phases, executor worker packets; copies at pipeline_phases/movement.py:202,293 derive from it.
2. `engine/occupancy_snapshot.py:27-29` `OccupancySnapshot.from_state` (preferred over the map by legality.py:58,112,594): built separately, needs its own filter.
3. `engine/world_index.py:161-166` `_build_entity_index` (`entities_by_tile`): feeds `nearby_entities` and the HardLawMonitor occupancy law (hard_law_monitor.py:238-285). Filtering here means LAW-OCCUPANCY-COLLISION needs no code change.
4. `engine/spatial.py:12-22` `SpatialGrid.__init__` (cached in domain/view.py:34-48, or `state.spatial_grid` in worker packets): feeds neighbor view, `get_entities_near/in_bounds`, and with it perception, hostiles, scorers (tactical.py:193, work_wake.py:15, domain/cognition.py:57, intelligence.py:445/593/915, scorers.py:178/223, scorers_support.py:20).
5. `engine/pipeline_phases/occupancy.py:61-70` private occupancy map for move vetting.
6. `engine/candidate_selector.py:101-109` `position_index`, which drives `_adjacent_hostile` (decision 32).

### Readers that bypass the builders (need their own filter or a shared `is_lodged(entity)` helper)
- Combat: `legality.py:256-337` attack/skill legality (reject a lodged target: the guard against a stale id); `combat.py:491-527` AoE splash; `domain/aoe_actions.py:38` (entities on the target tile; lodgers share that tile and would match); `combat_engagement/phase.py:308` target scan and `:205-206` witness radius.
- Perception: `engine/cognition.py:35-43,139-144` direct entity scans; `hostility.py:64 perceived_hostile` (last-line guard: false if either side is lodged); `domains/information/router.py`, `resolver.py` (a lodger would "hear" outside news: MAYBE).
- Movement: `pipeline_phases/movement.py:105-119,305,333` swap detection (a lodger must not be a swap partner); `candidate_selector.py:98` follow-a-tracked-entity (by id).
- legality.py fallback loops at :128, :577, :604 (taken only when the maps raise AttributeError): filter for consistency.
- Service: `building_services.py:45,50`, `tactical_rest.py:69,114` (probably where lodging is initiated), `town/*` and `guild_visit.py:72`: MAYBE, same-tile so they keep working.
- Observability: `hard_law_monitor.check_initial_placement` (:160-235, kernel init only), `extraction/lifecycle.py` (a lodge is a position change: spawn/move events), `api/presenters/state_presenter.py` (expose `lodged_in`), rendering (would draw lodgers on the building), `replay/fingerprint.py:61` (include `lodged_in`).
- Everything else (world/, social, strategic, cooperation providers/services, lifecycle, ai scorers) reads its own position/region or goes through the builders. `reproduction_humanoid.py:49`, `groups.py:298,310` and `cooperation/providers.py:100` pair/scan by position (MAYBE).

### Write path and serialization
- Position is written only through `EntityUpdate.new_position` -> `NavigationPatch.apply` (patches.py:294-298) -> `ApplyPath._fast_replace_navigation` (apply.py:721), which copies every `NavigationComponent` field by hand with `object.__new__`: a new `lodged_in` MUST be added there, or it silently resets on every move. `NavigationUpdate` has no position field. Occupancy vetting is `pipeline_phases/occupancy.py` (lowest id wins on a claim).
- `NavigationComponent` (core/state.py:487) is frozen/slotted with defaults; `to_canonical_dict` at :522-545 already omits `step_ready_tick` when None (:541): `lodged_in` follows that pattern so existing canonical dicts and replay fingerprints do not change when nobody lodges (this keeps AC 5: "differs from base only from the first lodging event"). `core/builder.py:103` builds default navigation.
- Caches: `MovementPlanCache` (occupancy_version bump on dirty); `_occupancy_map_cache` (state.py:1353), `_spatial_grid_cache`, `WorldIndexes.entities_by_tile` (invalidated by the "entities" dirty class), `OccupancySnapshot` per tick, worker packets (`occupancy_map`, `spatial_grid`). A lodge/leave event must mark the entity dirty for the movement and "entities" classes or the indexes go stale.

## Design risks for the plan (for rpg-planner)
1. A shared predicate `is_lodged(entity)` read at the six builders keeps the filter in one vocabulary; the legality guard is the second line. The set of MAYBE readers should be settled by a lodger-on-every-reader test, not by reading alone.
2. Lodged entity = position equals the building tile. Anything doing "is the building tile free" (building obstruction, `is_static_position_blocked`) must not treat the lodger as blocking, and movement of other entities onto the building tile stays rejected (solid building).
3. Determinism: set/ring order for leavers follows #795 (sorted, lowest id wins).
4. Lodger's own outward perception (can it see out? can it be woken by a threat that is not adjacent?): the law only says no one OUTSIDE perceives it. Under 2.154 the threat wake cannot fire indoors; N14 re-applied on top needs that noted.
5. s44: see item 2. F3 will not by itself fix s44.

## Not done
- Item 1 (15-run base split on 6fdfdf555 by sleep type, door-tile holders served/rough/collapse/refused-bed and awake holders). Needs the slot and an observer edit (per-person door ticks by sleep type).
