---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE
artifact_type: plan
---

# Plan — TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3, lodging) — FOR REVIEW, NO CODE YET

Base 6fdfdf555. Owner answers (#715 6543182195): indoors is safe (a lodger cannot be attacked/reached/perceived from outside), beds inn 10 / home 4 declared in content, beds 0/absent keeps main's behaviour. Divergence 2.155 (Enforced).

## 0. Lodger perception — RULED by the designer (via rpg-planner, 2026-10-31)
A lodger perceives NOTHING outside while it lodges and re-perceives normally on the tick it steps out. It keeps memory, leads and concerns (nothing is cleared on entry). While lodged only its own body wakes it: sleep debt ending its rest (hunger under A' later); no outside event wakes it. Law text gains: "...no one outside can reach or see it, and it sees no one outside."
Code paths (the observer is lodged, so the reader returns nothing): `engine/domain/view.py:27 get_neighbor_view` and the `SpatialQueryService` queries (`nearby_entities`, `get_entities_near`, `get_entities_in_bounds`) return () when the QUERYING entity is lodged; `engine/cognition.py:35-43,139-144` perception/threat scans skip a lodged observer; `hostility.perceived_hostile` and `tactical_threat.perceived_threats` are False when observer or target is lodged; `tactical.py:193` hostile list empty for a lodger; `domains/information/router.py:39/69` and `resolver.py:37/43` deliver nothing to a lodger; `scheduler._threat_wakes_sleeper` never fires indoors (no outside hostile is perceived). The hunger wake (2.115) and the floor-end/sleep-debt end stay. Everything sits behind the one predicate `is_lodged` (engine/lodging.py). Every direct reader gets a unit test that a lodger is invisible to it (section 5).

## 1. Data
- `NavigationComponent.lodged_in: Optional[int] = None` (core/state.py:487). `to_canonical_dict` emits `"lodged_in"` only when not None (pattern of `step_ready_tick` :541) so every non-lodging canonical dict/fingerprint is unchanged. `EntityState._canonical_cache` is rebuilt by the usual replace path.
- `NavigationUpdate.lodged_in_set: Optional[int]` and `lodged_in_clear: bool` (core/updates.py:168; `is_noop`, `merge` extended). Applied in `NavigationPatch.apply` (engine/patches.py:277-300) and CARRIED by `ApplyPath._fast_replace_navigation` (engine/apply.py:721): this field is added to the hand-copied list, with a test (move keeps lodged_in) because forgetting it silently resets it on every move.
- Building: `BuildingState.beds: int = 0` (core/state.py ~:1258, beside `maintenance_shifts_needed`); content `beds:` per kind in data/content/world/buildings.yaml (inn 10, home 4); copied by `worldbuilding/compiler.py` like `maintenance_shifts_needed`; no number in code (D56). Content schema/validator updated.
- Lodger count of a building is DERIVED: `lodgers_of(state, building_id)` = entities with `navigation.lodged_in == building_id` (one helper in a new `src/engine/lodging.py`; no list on the building).
- `is_lodged(entity)` helper in `engine/lodging.py` is the single predicate every filter uses.

## 2. Who lodges, capacity, admission (scope 2-4)
- A REST executed by `building_services.with_service` where `service_delta` delivers the bed at a building with `beds > 0` and a free bed (`beds - lodgers_of(...) > 0`). A rough rest (CoreActions REST without a service building), a collapse, WORK and EAT do not.
- SHAPE CHOSEN (review change 1, grant BEFORE delivery): for a building with `beds > 0` the worker's `service_delta` does NOT deliver the bed. It emits only a lodge CLAIM (`NavigationUpdate(lodged_in_set=building.id)` plus `new_position=building.position`). The bed service (readiness +10, hp +5 and the REST charge `resource_transfers`) is added only to GRANTED claims by `lodging.grant_beds`, run at the head of the `resource_transactions` phase (pipeline.py:371), before the transactions resolve, in the same phase (no new run_phase). A loser therefore never has a charge, readiness or heal applied, and nothing has to be stripped afterwards. Why not strip in OccupancyPhase (406): it runs after resource_transactions (371), so a charge would already have been resolved. `beds == 0` keeps today's immediate delivery on the reach tile.
- `admits(entity, "REST")` (service_admission.py) gains "a free bed": a building with `beds > 0` and `lodgers_of >= beds` does not admit. `admits` is called with the entity only today; it needs the building, so a sibling `admits_at(entity, building, action)` carries the bed test; ONE source of truth (review change 2): `admits(entity, action)` delegates to `admits_at(entity, None, action)` (no building = no bed test) so the two cannot drift; `ways_in_reach`/`FatigueScorer`/`service_delta` call `admits_at` with the building. Golden test: on the admission grid `beds == 0` gives main's answer (R4). (Admission-grid row added.)
- Arrival with no bed (full, or admission changed en route): `building_arrival_update` (building_arrival.py:68-75) for kind "fatigue" returns `_end_project` with `ProjectEnd.WAY_CLOSED` (a new `ProjectEnd` value set with status ABANDONED, one mechanism with lane C's THREAT_CLEARED; the EARN "EAT only at a serving building" end is the model) and dispatches NO REST; the subject re-decides next tick. Today a refused bed still runs REST rough on the reach tile: that is the jam.

## 3. Authoritative apply: grant, lodge, leave (scope 1, 5)
All in `engine/pipeline_phases/occupancy.py` (OccupancyPhase.resolve) plus `engine/lodging.py`; no new pipeline phase (the golden live-signal fixture counts run_phase clock reads, and phase inventory docs are generated).
1. Bed contest (`lodging.grant_beds`, head of `resource_transactions`, see section 2): lodge claims per building are granted in ascending entity id up to `beds - lodgers_of`; a granted claim gets the bed service delta merged; a loser's claim (`lodged_in_set`, `new_position`) is removed, its REST task cleared and its fatigue project ended with `ProjectEnd.WAY_CLOSED` (status ABANDONED; the same ProjectEnd mechanism as lane C's THREAT_CLEARED, src/core/strategic.py:30; whichever lands second rebases). No delivered-then-stripped state exists (R3 closed by construction). Conservation test: a loser's gold, readiness and hp are unchanged and the building purse is not credited.
2. Granted lodge claims (surviving `grant_beds`) are exempt from tile contention in the claims loop (building tile is not an occupant tile; several lodgers share it); other claims onto a building tile stay rejected as today.
3. Leave: a lodged entity leaves when (a) its resulting task is not a REST/SLEEP hold at its own building and not an EAT at it (only EAT was ruled, scope 7; a lodger that SELLs leaves as normal), i.e. its next decision is not to keep resting; or (b) the building is not `functional` (eject). Placement: first a free orthogonal tile in `_REACH_OFFSETS` order without (0,0) (service_reach.py:22); else the nearest free walkable tile by deterministic ring search, radius 3; else it stays lodged awake and tries again next tick (counter `lodge_exit_blocked_ticks`). Two leavers on one tile: lowest id wins, the other takes its next tile (same claims loop). It moves from the next tick. Leave is a `new_position` plus `lodged_in_clear` so it goes through the same vetting as any move.
4. Dirty marking: lodge and leave set `new_position`, which marks the entity movement-dirty, which bumps `MovementPlanCache` occupancy_version and invalidates the "entities" index; a test pins that `entities_by_tile` / `_occupancy_map_cache` / `SpatialGrid` are rebuilt after a lodge/leave (state.py:1353 cache reset path).
5. A lodger does not hold the tile: at lodge, position = building tile; every index below excludes it.

## 4. One lodger filter in the six builders
Each builds from `lifecycle.active and combat.alive`; add `and not is_lodged(e)`:
1. engine/spatial_query.py:117-120 `get_occupancy_map`
2. engine/occupancy_snapshot.py:27-29 `OccupancySnapshot.from_state`
3. engine/world_index.py:161-166 `_build_entity_index` (also fixes LAW-OCCUPANCY-COLLISION, hard_law_monitor.py:238-285, no code change there)
4. engine/spatial.py:12-22 `SpatialGrid.__init__`
5. engine/pipeline_phases/occupancy.py:61-70 private `occ_map`
6. engine/candidate_selector.py:101-109 `position_index` (decision-32 `_adjacent_hostile`, :123-130)
Fallback loops at legality.py:128, :577, :604 get the same predicate.

## 5. Bypassers and their guards, with a test per class
| class | file:line | guard | test |
|---|---|---|---|
| legality | engine/legality.py:256-337 attack/skill legality | reject a target for which `is_lodged` (reason `TARGET_LODGED`), the stale-id guard | an attacker with a task/target id captured BEFORE the target lodged gets a rejection, no damage |
| legality fallbacks | legality.py:128, :577, :604 | `not is_lodged` in the AttributeError fallback scans | fallback path (maps raise) ignores a lodger |
| AoE | engine/combat.py:491-527 splash; engine/domain/aoe_actions.py:38 (`ent.navigation.position == target_pos` would match lodgers sharing the building tile) | skip lodged | AoE centred on/near an inn takes no lodger |
| engagement | combat_engagement/phase.py:308 direct scan, :205-206 witness radius | skip lodged as target and as witness | a fight beside the inn: lodgers are neither engaged nor witnesses |
| cognition scans | engine/cognition.py:35-43,139-144; hostility.py:64 `perceived_hostile` (last-line, False if either side lodged); tactical_threat.py:54-85; domains/information/router.py:39/69, resolver.py:37/43 (proximity-based delivery only: a lodger hears no news from an outside speaker that needs proximity; non-proximity channels unchanged) | skip lodged targets (and lodged observers) | a hostile next to the inn is not perceived by a lodger and a lodger is not perceived/threatened by it |
| swap | pipeline_phases/movement.py:105-119, :305, :333 swap detection via `occ_map`/`state.entities` | exclude lodged from partner search | a mover onto the building tile never swaps with a lodger |
| follow/target by id | candidate_selector.py:98, tactical.py:662-665,763,825 | lodged target treated as gone for following | a follower of an entity that lodged stops following |
| service | building_services.py:45,50; tactical_rest.py:69,114 | use `lodged_in` building for a lodger (same tile, so identical answer); lodging initiated here/in `service_delta` | EAT served from the building tile |
| observability/read models | extraction/lifecycle.py (lodge is a position change: no spawn/despawn event noise), api/presenters/state_presenter.py (expose `lodged_in`), replay/fingerprint.py:61 (include `lodged_in` only when not None, like the canonical dict, so runs with no lodgers stay byte-identical; AC 5 first-diff depends on it), rendering (skip drawing or draw as indoors) | explicit | `lodged_in` visible in the read model |
| other | reproduction_humanoid.py:49, cooperation/providers.py:100, world/environment.py:91; groups.py:298,310 (ubuntu's group-id fix is rewriting groups.py ~:308 and apply_plan.py:124: prefer the spatial-index filter if groups reads it; else a minimal guard, listed in Files Changed) | decided by the "lodger on every reader" test: add `is_lodged` where a lodger would be paired/recruited | one parametrised test per reader that returns entities by proximity |

## 6. Scope 7 (EAT from the building tile)
Verified in investigation: fires at distance 0, `_REACH_OFFSETS` start at (0,0). The arrival block (tactical.py ~:262-291) sees no hostiles for a lodger so it proceeds. Test: lodger, hunger, inn meal: EAT served, hunger down, lodger leaves afterwards.

## 7. Documents (AC 8)
Bible 04 sec 1 and engine/contracts/local_world_interaction_contract.md 2.1 (law text from the ticket); divergence 2.155 (Enforced; Verification test path; "Measured: pending" until the F3 runs); parity rows (strategic_cognition, combat_movement); mechanisms.yaml via rpg-planner; `make knowledge-index-update`.

## 8. N14 note (for the later re-apply, AC 9)
2.154's threat wake cannot fire indoors: a lodger is neither adjacent to nor perceivable by an outside hostile (owner row and the perception ruling). `scheduler._threat_wakes_sleeper` needs no change, but the N14 floor-end wake and rest-to-20 (2.153) act on lodgers as they do on rough sleepers; the lodger-leaves rule (3.3) interacts with the floor-end wake: the brain wake at the floor end is the "next decision" that triggers leaving. N14 on top of F3 is re-measured with the same s44 ablation pair; item 2 evidence (s44 deaths are awake subjects, not reach-tile sleepers) goes to the designer for the 2.153/floor-end ruling; F3 acceptance is unchanged (door sleepers below base in every world, deaths not up).

## 9. Order of work (after plan review)
1. content `beds` + compiler + BuildingState + schema test. 2. `lodged_in` field, NavigationUpdate/patch/apply (`_fast_replace_navigation`), canonical dict, round-trip tests. 3. `engine/lodging.py` (`is_lodged`, `lodgers_of`, leave placement) + admission `admits_at`. 4. service_delta/building_arrival changes. 5. OccupancyPhase grant/leave. 6. six builder filters + bypassers + per-class tests. 7. read models/fingerprint. 8. docs/parity/divergence. 9. scoped test run, graphify. 10. paired runs (slot): base arm = item 1.

## 10. Risks
- R1 `_fast_replace_navigation` omission resets lodged_in (test pins).
- R2 stale caches after lodge/leave (dirty marking; test).
- R3 CLOSED by construction (grant before delivery, section 2); the conservation test pins it.
- R4 `admits` signature: callers (FatigueScorer, ways_in_reach, service_delta, starvation record) are updated together; `beds == 0` must reproduce main exactly (golden test).
- R5 a held lodger whose brain never decides stays lodged awake: counted (`stuck_awake_indoors`), > 50 ticks is a finding, no timeout rule added.
- R6 lodger leaves and re-lodges (churn) if its next decision is REST again at the reach tile; leave only fires when the resulting task is not a REST/SLEEP hold, so a continuing REST at the same building keeps it lodged.
- R7 the observer-side guard is one predicate (`is_lodged`) read in about 6 places; a missed direct reader leaks perception, hence a per-reader invisibility test.

## 11. Changes during coding (lane B, 2026-10-31)
- CHARGE PARITY (rpg-planner ruling): the lodging path reproduces main's per-hold charge exactly. Main merges the bed delta twice for one REST hold (worker result plus actions phase; a separate defect, filed as its own ticket, not fixed here). Each lodge claim carries one `LODGE_CLAIM` marker transfer; the merged update therefore holds one marker per execution, and `grant_beds` delivers the bed once per marker. F3 changes where a subject sleeps, not what a bed costs, and follows main if the double merge is later fixed. Test: a lodger's gold, hp and readiness per hold equal main's beds=0 hold (`test_a_lodger_s_gold_readiness_and_heal_per_hold_equal_main_s_beds_zero_hold`).
- LEAVING: a lodger leaves the tick its held rest ends (an ended rest leaves no task; EAT does not keep it indoors after the meal). Accepted by rpg-planner: it avoids an awake lodger stranded indoors waiting on the brain cadence (R5). Re-lodges (the same entity lodging again at the same building within 20 ticks of leaving) are counted and reported with AC 4 (R6 churn).
- PHASE GATES: `occupancy_resolution` runs while anyone lodges (a leaver's rest ending marks no movement) and `resource_transactions` runs when a lodge claim is on the update (phase_graph.py 3d).
- WAY_CLOSED goes through lane C's `end_record` (cherry-pick c1b14815c); `ProjectEnd.WAY_CLOSED` is the only value F3 adds; lane C's enum test is widened by that one value.
- `beds` canonical-dict: present on `BuildingState` only when non-zero. Static content, so the state hash differs from base from tick 0 for worlds with an inn; AC 5's first-diff therefore compares entity trajectories and events, not the building content hash.
- No `home` building kind exists in data/content/world/buildings.yaml, so `home: 4` cannot be declared; only `inn: 10` is. A `home` definition would be a content change (no world uses it); flagged to rpg-planner.
