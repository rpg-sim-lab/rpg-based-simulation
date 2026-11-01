---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE
phase: done
date: 2026-10-31
tags: []
---

# TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE

## Title
A sleeper holds a door or service tile (F3: a served rest occupies the building, not the door tile)

## Status
DONE (hand-orchestrated, lane B, local branch rpg-sleeper-lodges; push and merge are the owner's). Dispatched under owner go #715 6543182195 (dispatch only).

## Tier
standard

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

- BASE NOTE (2026-10-31): #795 (STATE-SET-ORDER, 2.144) merged as 6fdfdf555 and moves simulation hashes. Every F3 and N14 re-measure uses a base at or after 6fdfdf555, never ba7aa11bd; the N14 table above is evidence for direction only. rpg-nav-stall now also conflicts on intentional_divergences.md (scheduler.py already did); intelligence.py merges cleanly but needs a behaviour re-check.

## Scope
Base for all measurement: at or after 6fdfdf555 (#795), never ba7aa11bd.

Law text (Bible 04 sec 1 and local_world_interaction_contract 2.1):
"A subject served a bed at a building lodges inside it: while it lodges it stands on no tile, so it holds no tile beside the building,
and, as the building is a solid obstacle (2.1), no one outside can reach or see it. A building lodges at most its declared beds. A
lodger leaves when its rest ends and the next decision is not to keep resting, and steps out onto a free tile beside the building."

1. LODGING, typed, entity-side (one source of truth): a field on the entity, e.g. `navigation.lodged_in: Optional[int]` (building id),
   set and cleared only by the apply path. While set, the entity's position is the building tile. The building's lodger count is
   DERIVED (the entities whose `lodged_in` is that building). There is no occupant list on the building, so no dual state.
2. WHO LODGES: a REST that `service_delta` actually serves at a building with a free bed (the bed is delivered).
   - These do NOT lodge: a rough rest (CoreActions REST with no bed), a collapse (decision 41: it sleeps where it stands), a WORK
     shift, or an EAT.
3. CAPACITY: a content-declared `beds` per building kind (`buildings.yaml`, copied at compile like `maintenance_shifts_needed`; no
   number in code, D56).
   - 0 or absent means the building lodges no one. Its REST is then served as today, on the reach tile (homes or inns without
     declared beds keep main's behaviour).
   - The values are a content question (decision 33: they follow the fiction). My lean: inn 10, home 4. The owner or content confirms.
   - FULL means the bed is not delivered: `admits(entity, "REST")` (ONE-ADMISSION, "a way is open iff the service would deliver it
     now") includes "a free bed", so ways_in_reach and FatigueScorer see a full building as closed. Same-tick contest for the last
     bed: the lowest entity id wins (TOWN-006 order).
4. ARRIVAL WITH NO BED (full on arrival, or the admission changed en route): the arrival does NOT dispatch REST on the reach tile. The
   fatigue project ends with a typed "way closed" end, and the subject re-decides. This mirrors EARN's "EAT only at a serving
   building". Today a refused bed still runs the REST action, so the subject sleeps rough ON the reach tile: the jam itself.
5. LEAVING: a lodger leaves when its held REST ends and its next decision is anything other than to keep resting, or when the
   building stops being functional (eject). On leaving, it is placed by the apply path through OccupancyPhase like a move:
   - first a free orthogonal reach tile, in the fixed `_REACH_OFFSETS` order without (0,0);
   - else the nearest free walkable tile by a deterministic ring search up to radius 3;
   - else it stays lodged, awake, and tries again on the next tick (count these ticks).
   - It moves on from the next tick. Two leavers claiming one tile: the lowest id wins, the other tries the next tile.
6. WHAT A LODGER IS, for every consumer of position:
   - not in the occupancy map;
   - not a tile occupant for movement, combat targeting, adjacency (decision 32) or perception from outside;
   - exempt from the "two entities on one tile" hard law only with other lodgers of the same building.
   - The read model shows `lodged_in`. A frontend badge is out of scope.
   - The investigation lists every reader of `navigation.position` (spatial index, perception, combat target selection, LoS, the
     HardLawMonitor co-location law, read models) and states each one's lodger handling.
7. A lodger is IN REACH of its own building's services (the (0,0) reach offset): an inn lodger can be served EAT without leaving.
   Verify that the hunger arrival fires from the building tile; if it does not, that is an investigation finding, not a fold-in.

Investigation (read-only, before the plan):
1. Split of the door-tile sleeper ticks on base 6fdfdf555 (15 runs, 5000t) by sleep type: served bed / rough REST / collapse /
   refused-bed REST. Also the same split for awake holders: WORK shift, post-EAT idle, walker waiting. F3 targets served and
   refused-bed sleepers; the rest decide F3b and the rough-rest question.
2. On the existing s44 traces (base, new2, both ablations): every COMBAT/DEFEAT/HAZARD victim. Was it asleep at death, which sleep
   type, and on a reach tile or not? The test: whether 2.153's longer rest kills through exposure ON a reach tile (F3 covers it) or
   elsewhere (F3 does not, and then 2.153's rest length or the floor-end wake needs its own ruling).
3. EAT: confirm it is a single-tick action with no hold.
4. The list of `navigation.position` readers (Scope 6).

Planner notes (rpg-planner):
- Divergence number: 2.155 (u24 block; next free after 2.154).
- Investigation item 2 reads the EXISTING s44 traces, which sit on base ba7aa11bd (pre-#795). That is fine for classifying victims; no hash or count from them is compared with a 6fdfdf555 run.
- Investigation item 1 is 15 runs at 5000t on 6fdfdf555: a heavy-host slot, allotted by rpg-planner. Its base arm is reused as the base of the Acceptance pairs.
- `beds` values are content (decision 33); the dispatch ask carries the designer's lean (inn 10, home 4) for owner or content confirmation.

## Out of Scope
- N14 (2.153 rest-to-20, 2.154 threat wake): still lane B's WIP 173e5fd42, re-measured on top of F3.
- WORK shifts and other non-sleep holds. Measure them (AC 4); if they are a material share of reach-tile holds, F3b reuses the same
  lodging record with a purpose.
- A rough rest or a collapse on a reach tile: counts first (AC 4); no rule now.
- F2 door yield; A'; the nav family; #781.
- Dead lodgers / death closing records (TCK-20261031-DEATH-CLOSES-NO-PROJECT).

## Acceptance Criteria
Paired runs: base at or after 6fdfdf555 vs F3, 15 runs (3 worlds x s42-46), 5000t, on the same scripts as N14 (agg2/decomp).
1. Door-tile occupancy by sleepers falls below base in EVERY world.
2. No rise in deaths by cause per world, and asleep-at-death is not up. A rise in either is a STOP, reported to me with victim ids.
3. Stall runs of 20 ticks or more are reported (expected to fall; not gated).
4. Reported, not gated:
   - bed-full refusals per building;
   - peak lodgers per building;
   - stuck-awake-indoors ticks (expected about 0; any entity stuck more than 50 ticks is a finding);
   - the reach-tile hold split after F3 (served / rough / collapse / WORK / other).
5. Determinism: repeat runs byte-equal. Every run differs from base only from its first lodging event (first-diff report as in the
   #769 bisect).
6. Unit tests:
   - a served bed lodges; a rough rest, a collapse, WORK and EAT do not;
   - beds 0 means today's behaviour;
   - full means not admitted (an admission-grid row), and an arrival with no bed dispatches no REST and ends the project with the
     typed end;
   - the last bed goes to the lowest id;
   - leaving order: reach tiles in offset order, then the ring, then still lodged;
   - two leavers contesting one tile;
   - a non-functional building ejects its lodgers;
   - a lodger is absent from the occupancy map and from outside perception and targeting (under the owner row's answer);
   - an inn lodger can be served EAT.
7. Architecture tests: `lodged_in` round-trips in the canonical dict; it is set and cleared only through the apply path; decision
   code reads it and never writes it.
8. Docs in the same change:
   - the law text above in Bible 04 sec 1 and contract 2.1;
   - parity ledger rows (strategic_cognition, combat_movement);
   - a divergence (class Enforced: 2.1 obstruction applied to occupants; the planner numbers it);
   - mechanisms.yaml via rpg-planner.
9. THEN: N14 re-applied on top of F3 and re-measured with the same s44 ablation pair. N14 lands only if its STOPs clear (deaths,
   asleep share). The asleep-share owner question is framed after that.
   - If s44 still trips while its door-sleeper ticks stay below base, the remaining cause is HOW LONG. My next ruling is then on
     2.153's rest length and the floor-end wake, informed by investigation item 2.

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
OWNER ROW: ANSWERED YES by the owner 2026-10-31 (#715 6543182195; memo row 94): a lodger indoors cannot be attacked from outside. Beds: inn 10, home 4 (content). Dispatch GO to lane B (rpg-implementer-2), investigation first, same comment.
Original row text:
"A sleeper in a bed indoors cannot be attacked from outside." This follows from 2.1 (a building is a solid obstacle) and from
lodging leaving no tile, but it is a gameplay change: inns and homes become safe sleeping places, it moves combat deaths of
sleepers, and the 2.154 threat wake cannot fire indoors. My lean is YES (fiction: you bar the door). The alternative, "a lodger
stays attackable through a reach tile", keeps a position-less entity targetable and re-creates a per-building adjacency special
case, so I advise against it.

Answered by the design: occupancy is entity-side `lodged_in` with a derived count (no record on the building); full = not admitted, arrival with no bed ends the project with a typed way-closed end; leaving = reach offsets, ring search to radius 3, else stay lodged; served REST only (EAT, WORK, rough rest, collapse do not lodge).

## Implementation Notes
- Beds: only the inn declares beds (10). Home beds (owner: 4) apply when a home building kind is declared; none exists on main (no `home` in data/content/world/buildings.yaml), and adding a building kind is out of F3's scope (rpg-planner ruling 2026-10-31).
- Charge parity: the lodging path charges what a beds=0 hold charges on main (the bed is merged twice per hold today; TCK-20261031-AN-INN-BED-IS-CHARGED-TWICE-PER-HOLD owns that defect).
- Typed end: WAY_CLOSED goes through lane C's `end_record` (cherry-pick c1b14815c); parity ids STRAT-296 and COMB-350; divergence 2.155.
- phase_graph.py (+11) adds two run-gates in `should_run_phase` (occupancy_resolution runs while anyone lodges; resource_transactions runs when a lodge claim is on the update); pipeline.py wraps `grant_beds` inside the existing resource_transactions phase. No run_phase is added or removed: the PHASES table and the golden live-signal fixture are unchanged.

## Test Summary

Pre-existing failures, red on clean main 6fdfdf555 and not caused by this ticket: `tests/unit/worldassembly/test_corpus_diversity.py::test_hero_guild_routing_seed42_1000t_cognition_grade_stability` and `::test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` (WORLD pillar 0.25 against anchor 0.32). Everything else in the scoped unit runs passed.

Mechanism changed-code advisory (report-only), 12 findings, rpg-planner's review 2026-11-01: `buildings` and `combat_resolution` got a note in `registries/mechanisms.yaml`; the other ten are reviewed, plumbing only, no entry change (`action_pacing_readiness` legality.py, `attributes_biology` apply.py, `race_archetype` content/schema.py, `personality`/`city`/`camp` core/state.py, `entity_role` core/enums.py, `status_effects` core/updates.py and engine/patches.py, `world_composition_assembly` worldassembly/resolver.py, `world_compilation` worldbuilding/compiler.py).


Final-head checks (2026-11-01, merged with origin/main 61e984212):
- tests/architecture + tests/unit/{core,engine,systems,observability,ai,tools} + tests/engine: 3947 passed, 4 skipped; one `test_kernel_run_output_stays_out_of_data_runs` failure under xdist (parallel workers write data/runs) passes alone (4 passed). `-k mechanism`: 321 passed. Integration (`-m 'not slow'`) on 56abe4d8a: 1125 passed, 6 skipped, 0 failed.
- Determinism: urban s44 5000t final hash cb3913a288b2729e7db10b2b02774e16f121125ee215629d4edb1b4b0398f46a and 25-tick chain 18fa525567e3de175de0becd9248b4c3b49327888a53cb09547cfde8ca917f0f, byte-equal on 9fa23bc0c, 039af5373, 56abe4d8a, c16d16bcd and the merged head; crowded s46 (4d6657f5...) and frontier s45 (d626e239...) byte-equal on 9fa23bc0c vs 56abe4d8a.
- Defect found by tests/architecture and fixed: intelligence.py (systems) imported src.engine.lodging (systems to engine); the stay-or-leave predicates now live in src/core/lodging_rules.py.
- Checkpoint: pre-F3 checkpoints are refused with CheckpointFieldMissing (a ValueError) for BuildingState.beds; lodged_in fills None; both fields are the LAST field of their class (a slotted dataclass unpickles positionally). tests/unit/engine/test_checkpoint_fields.py builds records as an old pickle loads them.

## Files Changed
- agent-working/tickets/inprogress/TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE.md
- data/content/world/buildings.yaml
- docs/brainstorm/mechanism_verification_view.md
- docs/engine/contracts/local_world_interaction_contract.md
- docs/guidelines/intentional_divergences.md
- docs/mechanics/04_strategic_cognition.md
- docs/observability/hard_law_monitor.md
- docs/parity_ledger/combat_movement.yaml
- docs/parity_ledger/strategic_cognition.yaml
- docs/parity_ledger/world_dynamics.yaml
- registries/mechanisms.yaml
- src/ai/goals/scorers.py
- src/api/presenters/state_presenter.py
- src/content/schema.py
- src/core/enums.py
- src/core/lodging_rules.py
- src/core/state.py
- src/core/strategic.py
- src/core/updates.py
- src/domains/combat_engagement/phase.py
- src/domains/information/resolver.py
- src/domains/information/router.py
- src/engine/apply.py
- src/engine/appraisal.py
- src/engine/building_arrival.py
- src/engine/building_services.py
- src/engine/candidate_selector.py
- src/engine/checkpoint_fields.py
- src/engine/combat.py
- src/engine/domain/aoe_actions.py
- src/engine/domain/cognition.py
- src/engine/domain/view.py
- src/engine/legality.py
- src/engine/lodging.py
- src/engine/occupancy_snapshot.py
- src/engine/patches.py
- src/engine/phase_graph.py
- src/engine/pipeline.py
- src/engine/pipeline_phases/actions.py
- src/engine/pipeline_phases/movement.py
- src/engine/pipeline_phases/occupancy.py
- src/engine/scenario_checkpoint.py
- src/engine/service_admission.py
- src/engine/sleep_debt.py
- src/engine/spatial.py
- src/engine/spatial_query.py
- src/engine/world_index.py
- src/observability/hard_law_monitor.py
- src/replay/fingerprint.py
- src/systems/strategic_systems/intelligence.py
- src/worldassembly/context.py
- src/worldassembly/models.py
- src/worldassembly/resolver.py
- src/worldbuilding/compiler.py
- tests/unit/engine/lodging_kernel.py
- tests/unit/engine/test_beds_survive_a_checkpoint_restore.py
- tests/unit/engine/test_checkpoint_fields.py
- tests/unit/engine/test_lodged_in_is_carried_by_the_apply_path.py
- tests/unit/engine/test_lodged_in_stays_in_the_apply_path.py
- tests/unit/engine/test_lodger_is_invisible.py
- tests/unit/engine/test_lodging.py
- tests/unit/engine/test_lodging_leave_and_indexes.py
- tests/unit/engine/test_lodging_no_bed_and_arrival.py
- tests/unit/strategic/test_project_end_record.py
- tests/unit/tools/test_mechanism_registry_completeness_check.py
- data/worlds/*/resolved/{assembly_report,compile_context,provenance_manifest,validation_report}.json (regenerated compile outputs: the inn now carries beds; 91 files)
- agent-working/staging_artifacts (moved to stored_artifacts), agent-working/agent-monitoring shards, docs/REGISTRY.yaml

## Completion Summary
A subject served a bed at a building that declares beds now lodges inside it (navigation.lodged_in, position the building's tile, no tile held): it holds no door or service tile, is invisible and untargetable from outside, and leaves the tick its rest ends onto a free tile beside the building. Divergence 2.155 (class Enforced); Bible 04 sec 1; contract 2.1; parity STRAT-295/STRAT-296/COMB-350; hard law LAW-LODGER-INDOORS; mechanisms.yaml (town_services, strategic_intelligence_core, buildings, combat_resolution). Measured over 15 paired runs (base 6fdfdf555, 3 worlds x seeds 42-46 x 5000 ticks): door-tile sleeper ticks crowded 11128 to 100, frontier 18137 to 715, urban 34662 to 85; asleep on a door tile after a leave 0; LAW-LODGER-INDOORS 0; stuck awake indoors at most 4 ticks. Deaths crowded 176 to 174, frontier 122 to 119, urban 48 to 49. Details in divergence 2.155 Measured.
Disclosure:
- the FULL re-adoption race;
- the gold-0 clamp (to D73);
- the hoverer cycle with figures: urban relodge_within_20 63 to 1775 per run, lodged span p50/p90 6/46 (urban), 3/4 (crowded), 3/6 (frontier), WAY_CLOSED ends 2 to 103 per urban run;
- leaver re-target churn (to N14): 501 to 653 target changes in the first 20 ticks after a leave per urban run, 10 to 29 crowded, 4 to 67 frontier;
- the counter correction 039af5373: the stayer drops were the claim's own tile re-emitted by lodge_claim each tick of a held rest, not a movement writer;
- asleep share crowded 0.1035 to 0.1207 (0.59 of its asleep ticks are lodged rest), frontier 0.1876 to 0.1809, urban 0.2402 to 0.2458: the owner question follows N14;
- crowded HAZARD 23 to 27 (tier 1), traced by id: 6 extra victims, 0 fed by lodging/leave; H1 exposure (no hazard avoidance) on intercept, regroup and panic-retreat legs. Frontier COMBAT 58 to 59 (extras 26 and 30 never lodged or left) is divergence;
- subject 17 (urban s44, COMBAT t3306, divergence): the walk to (25,25) was a congestion blocker-resolution project replacing the finished fatigue project (intelligence.py:670), not town-return; to TCK-20261101-A-CONGESTION-BLOCKER-RESOLUTION-SENDS-A-SUBJECT-TO-THE-TOWN-CENTRE (counts-first);
- subject 30 (the pre-Q-B door-tile hold at t4001): not reproducible at 9c685e498, abe8d0074, 876388edc, 4b3ecce12 or the final head (the world trajectory differs by commit); the class count is 0 in all 15 repeat runs;
- the combat note wording, frontier item (b), and the clear_target versus target_clear field note in 2.155;
- checkpoint format: pre-F3 checkpoints are refused with a typed error (CheckpointFieldMissing), and the restore step is a single table (src/engine/checkpoint_fields.py, FIELD_RULES) that the churn lane extends with its own rows; the general fix, a checkpoint format version in the header, is a separate ticket;
- the import-boundary fix (src/core/lodging_rules.py) found by tests/architecture after 91014a88f;
- N14 is not on this branch: it is re-measured on top of F3. The churn fix is not on main either, so F3 lands first and the churn lane re-measures on F3.
Run data this session wrote under data/runs was cleaned by id; scratch trees outside data/runs (n14/old9fa, o_*, base6fd) stay for the owner.

## Ruling record carried from the seat copy (rpg-planner / rpg-designer, 2026-10-31 to 11-01)

### Status
OPEN. Design by rpg-designer 2026-10-31 SEATED (source: main-checkout .claude/handover/drafts/rpg-designer-f3-design.md). Order per owner #715 6541804604 (memo row 93): F3 first, then N14 re-measure, A', nav, D80C, #781. DISPATCHED 2026-10-31 to lane B (rpg-implementer-2) under owner go #715 6543182195, investigation first; heavy runs after lane C releases the slot.

### Tier
standard (a durable entity field, content, occupancy and perception). Dispatch needs an owner go via lead-planner-u24 / #715.

### Scope
PERCEPTION RULING (rpg-designer 2026-10-31, after investigation items 2-4): a lodger perceives NOTHING outside while it lodges and re-perceives normally on the tick it steps out (one symmetric lodger filter for every spatial read). It keeps what it knows (memory, leads, concerns); only perception stops updating; nothing is cleared on entry. While lodged it is woken only by its own body (sleep debt ending the rest; hunger under A' later); no outside event wakes it (no 2.154 threat wake indoors). Law text gains: "...no one outside can reach or see it, and it sees no one outside." Guard list accepted: six index builders (spatial_query.get_occupancy_map, occupancy_snapshot.from_state, world_index._build_entity_index, spatial.SpatialGrid, pipeline_phases/occupancy.py, candidate_selector.position_index) plus direct readers (AoE splash, engagement phase, cognition scans, swap detection, legality fallbacks); lodged_in carried in the navigation copy, omitted from the canonical dict when None; a unit test per direct reader that a lodger is invisible to it.
Investigation item 2 result (lane B, s44 traces, classification only): 27 of 28 new2 victims awake with no sleep in the 20 ticks before; F3 will not clear s44 (AC 9 branch). Designer's follow-up trace for the 2.153 ruling is on the N14 ticket.

### Implementation Notes
- 2026-11-01 Q-A RESTATED by the designer (independent of the dispatch path): a REST whose FIRST execution is in reach of a building that declares beds either lodges (served) or does NOT run on that reach tile. With a fatigue project: the project ends WAY_CLOSED and the subject re-decides. A bare REST with no project: the action is refused there with a typed reason and the subject re-decides. A collapse is unchanged (decision 41). This replaces the 'REST targeting a beds building' guard. Added test: a bare REST on the reach tile of a full inn is refused and holds nothing. Trace the dispatch path after lane C's batch, for the record only (a finding if a path should have refused earlier). RULED (designer): Q-A applies only to subjects service_building would serve (keeps_coin, decision 43's trait); non-persons are unchanged. Test row: a non-keeps_coin subject's REST beside a full inn runs as on main.
- 2026-11-01 DESIGNER ONE-ROUND RULING. Items 1-3 ACCEPTED: (i) = 0 closed; the FULL re-adoption is a disclosed race; the charge clamp goes to the D73 package. Q-A and Q-B are BOTH F3 scope and BLOCK closure (gaps against Scope 4 and the leave rule, not new rules).
  Q-A: a REST dispatched to a building that declares beds and finding NO bed at its first execution ends WAY_CLOSED (as at arrival) and never rests rough on the reach tile. The rule lives at the service's first execution, where admits_at refuses; no reservation. Scope guard: only a REST targeting a beds building; a rough REST elsewhere is unchanged. Test: two subjects for the last bed in the same tick; the lowest id lodges, the other ends WAY_CLOSED, holds no reach tile, and re-decides.
  Q-B: lodging IS arrival. On lodging, the fatigue project's reach objective RESOLVES in the same apply (so the redirect at intelligence.py ~654-668 has nothing to re-issue). GUARD: place_leavers moves a lodger out only when its held REST has ended or on an eject, never because a walk target appears. Both changes go in. Subject 30 must be explained before close. Test: a lodged subject with an active fatigue project stays lodged and asleep for N ticks with the redirect running, and leaves only when its rest ends.
  CLOSE CONDITIONS: Q-A and Q-B fixed + subject 30 explained; then the 15-run arm REPEATED: AC1, AC2 (deaths by cause, STOP rule), AC4, AC5, WAY_CLOSED ends, rough-rest-on-reach-tile ticks at beds buildings (about 0), leave-while-REST (must be 0). (b) frontier is non-blocking. Disclose: the race, the clamp (D73), the hoverer cycle indoors (N14).
- 2026-11-01 FINAL TRACE s44 (f3e_obs.py): (ii) is NOT a missed serve. All 598 unserved door ticks: service_delta returned None at admits_at because has_free_bed was FALSE (the inn was full at first execution; lane B retracted its earlier 'free bed 9/10', which was off by one tick). The served sample differs only in the bed count. The dispatch path and timing are NOT traced. Base cannot show this shape (no beds); that is reasoning, not a measurement. Sent to the designer: Q-A (should a REST that first executes at a full lodging end WAY_CLOSED as at arrival?) and Q-B (the leave-while-REST redirect: a blocker or a follow-up?). The slot went to lane C.
- 2026-11-01 TRACE s44 (f3d_obs.py, hash-neutral; tests/integration 1125 passed). (A) LEAVE-WHILE-REST NAMED: 20 of 2790 leaves fire `walking` (lodging.py:174), 18 with the REST still running. Source: the redirection fallback at intelligence.py:~654-668 re-issues the fatigue project's ACTIVE reach objective target (the inn tile) to a subject already lodged there; place_leavers treats it as a leave, and the sleep resumes rough on the reach tile. The 122 door ticks = subjects 6 and 8 (this path) + subject 30 (a normal leave; not traced). Designer to rule whether it blocks. (ii) 598 of 608 unserved door ticks: reach tile, building 20003 functional, keeps_coin, admits_at True, free bed (9/10), dispatch reason None, fatigue project, and yet not charged; cause not found; one more s44 run wraps with_service/service_delta (outcome guard / not in updates / delta None / resolver rejection), with base s44 for comparison. 10 ticks are normal REST_IN_PLACE.
- 2026-11-01 RERUN s44 (f3c_obs.py, hash-neutral): (i) SERVED_NOT_LODGED = 0 (the 22 short holds are all (ii)); the FULL re-adoptions are a RACE (all 51 same-building re-adoptions had a free bed at decision time = end of T-1; lowest-id grant contention; disclose); charge split: 1909 holds at 0 gold moved nothing, 78 at gold > 0 moved, 0 at gold > 0 with no loss, so NO conservation finding (CLAMP: service_admission.py:33, 40-41, divergence 2.150; the free-bed side of D73). Open, a trace run is going: the (ii) path (payment is not the cause: 397/400 at 0 gold, like the served holds) and leave-while-REST (18 leaves / 10 subjects, the sleep continuing as a rough REST on the reach tile; place_leavers lodging.py:152-176, candidate `walking` from a per-tick navigation target).
- 2026-11-01 DESIGNER (for a one-round ruling): (1) 122 'lodged then left still asleep on the door' ticks contradict the leave rule; name the path (an exit that does not end the sleep, or a sleep resuming on the reach tile in the same tick); this is a POSSIBLE SECOND BLOCKER. (2) Charge without a gold drop: likely the resolver clamp on all-broke subjects (the free-bed side of D73, to the D73 owner package, not F3); split by gold at the charge (0 vs > 0); any > 0 hold with no loss is a conservation finding. (3) Lodging median 4 / gap 9 is the base hoverer cycle carried indoors; N14 targets it; disclose it in the summary, no F3 action. Stalls and awake_other belong to the nav/WANDER family and TCK-20261101-A-WALKER-WAITS-AT-A-DOOR-TILE-AN-AWAKE-HOLDER-KEEPS.
- 2026-11-01 (a) on urban s44 (lane B, n14/out/a_urban_44.json). AC5 as restated: MET (the tick-0 diff is only 20003.beds and 20006.beds, both inns; the first diff outside buildings is t440 = the first lodging; the repeat is byte-identical; the probe is hash-neutral). WAY_CLOSED: of 122 ends, 71 not re-adopted, 49 re-adopted with a free bed, 2 re-adopted while FULL (s27 t4174, s26 t4515, building 20003 at 10/10). STOP; the cause (scorer path vs phase-order sampling) is being traced read-only before the designer rules. Residual door sleepers (730 ticks): (i) undetermined for 22 three-tick holds (66 ticks), rerun to classify; (ii) rough REST with reason None, 542 ticks; served-lodged-then-left-asleep, 122 ticks; (iii) 0; (iv) 0. Charges per hold: 1 x 1296, 0 x 19, no doubles. OPEN: on 1238/1315 holds the direct signal says charged while gold did not drop; under check (conservation). awake_other: 63% WANDER with no target, 34% REGROUP. Stalls: 80% target within 2 tiles of an inn door; the WAY_CLOSED hypothesis is REFUTED (2/439 stalls follow a WAY_CLOSED).
- 2026-11-01 DESIGNER: (1) restore-crash fix ACCEPTED: check_initial_placement skips lodged_in, matching check_occupancy and Scope 6. Owed: a negative test (a NON-lodged entity on a building tile still raises), hard_law_monitor.md, the ledger. (2) HELD-NEVER-CLAIMS is not a defect in itself: a rest is served, paid and healed ONCE, at its first execution; an unserved REST stays a rough rest for its whole hold, with no mid-hold charge and no mid-hold lodging. Residual classification uses the ACTUAL first-execution history: (i) SERVED (a charge transfer landed) but NOT lodged = F3 DEFECT, blocks closure, give the path file:line; (ii) not served, rough REST on a reach tile = not F3, name the starting path (these are the counts for the out-of-scope rough-rest-on-reach-tile question); (iii) probe artifacts dropped, corrected AC1 reported; (iv) collapses as reported. F3 CLOSES WHEN (i) = 0 AND the WAY_CLOSED question is answered (plus AC5 as restated).
- 2026-11-01 DESIGNER: a third possible blocker. Under F3's rule a served bed always lodges ("full" means not served), so every residual sleep_served_bed door-tile tick (arm 2983) is suspect until it is explained. Candidates: the lowest-id contest loser still being served; a bed served on the tick before the lodging applies; a serve path that bypasses lodging. A serve-without-lodge path is an F3 DEFECT and blocks closure. It is classified in diagnostic (a) on urban s44 by building and by reason. Homes: no home kind exists, and the owner's 10/4 (#715 6543182195) was applied to the inn only. The dead SERVICE_KINDS "home" entry is filed as TCK-20261101-SERVICE-KINDS-NAMES-A-BUILDING-KIND-NO-CONTENT-DECLARES (not F3).
- 2026-11-01 DESIGNER CORRECTION to AC5 (the AC was wrong, not the code: beds are copied at compile like maintenance_shifts_needed / hires_for_pay, set at compile and never changed). AC5 RESTATED: "Repeat runs are byte-identical. At tick 0 the ONLY difference from base is `beds` on buildings whose kind declares it, shown by a canonical-dict diff with nothing else differing. Every other difference starts at or after the first lodging, shown by a first-diff report with `beds` masked." Anything else in the tick-0 diff (a lodger field, or beds on a kind that does not declare it) is a finding and blocks closure.
- 2026-11-01 DESIGNER RULING on the F3 arm: AC1, AC2 and AC4 are MET. F3 does NOT close until both BLOCKERS are done:
  (i) the AC5 checks: the first diff falls at the first lodging, and the building canonical hash holds.
  (ii) diagnostic (a), widened. On the urban seed with the most WAY_CLOSED ends (122 or 113), for every WAY_CLOSED end: was the same building re-adopted within 50 ticks, and did it have a free bed at that adoption? Re-adopted while still FULL is an F3 DEFECT (the scorer or ways path is not carrying the capacity) and is fixed before close. A free bed that filled en route is an acceptable race; disclose it (reservation is out of scope). In the same run, classify urban awake_other (2798 -> 11972) and give the stall histogram and stall positions against the inn door, to confirm or refute that these are the WAY_CLOSED subjects re-deciding at the door. Fewer total stall ticks with more, shorter stalls is not by itself a regression; it is judged together with the WAY_CLOSED answer.
  Non-blocking, before the N14 re-measure: (b) the non-person door sleepers on frontier (animals = follow-up row, not F3 scope), lodge and re-lodge gaps, and frontier sleep_collapse 118 -> 630 from the same 3 subjects (who, where, why). If F3 is the cause, it returns to the designer as a finding.
  Completion summary must disclose: the re-lodge churn is a base cycle (median 3-tick spans already in base); the N14 re-measure judges it.
  Awake door-holders -> TCK-20261101-A-WALKER-WAITS-AT-A-DOOR-TILE-AN-AWAKE-HOLDER-KEEPS. The precedence base is measured ON F3.

### Landing-order condition (rpg-designer 2026-10-31)
TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT is measured on 6fdfdf555 (pre-F3). Whichever of it and TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE lands SECOND repeats, on top of the other, retention's recovery check (ticks with hp < 0.5, no present threat and no RECOVER/REST/FATIGUE project current; any entity over 200 ticks is a finding) and deaths by cause per world.

### Arm f3q STOP and ruling (2026-11-01)
- **Arm f3q (15 runs, abe8d0074):** LAW-LODGER-INDOORS fired in 13/15 runs (crowd 0/6/30/1/161; front 5/0/0/102/0; urban 326/521/200+/175/161).
  - Class (a): a lodger ends the tick holding a nav target. The town-return/REGROUP writers (intelligence.py:676, :668) re-set it after drop_lodger_targets runs.
  - Class (b): a lodger stands off its building tile with no target.
  - Deaths: crowded 176→163, frontier 122→119, urban 48→50 (s44 +2: COMBAT and HAZARD), an AC2 STOP pending attribution.
  - Asleep share: crowded 0.1035→0.1439, the other worlds flat. Hits on sleepers: 0.
- **Ruling (rpg-designer), (Q): a lodged subject has no movement intent.** (R), a later erase pass, is rejected as a hidden override.
  - One read-only predicate, is_lodged, at the shared target-emit point covering every writer. If no shared point exists, a per-writer guard through the same predicate plus one parametrised test over the full writer list.
  - Town-return counts a lodger as in town at its building, so the goal is satisfied.
  - REGROUP skips a lodged member; the group never wakes it.
  - drop_lodger_targets stays as the claim-tick backstop. After the claim tick its expected count is 0; anything left over is a finding naming the writer.
- **Class (b):** position == building tile while lodged_in is set (never accepted otherwise).
  - If (b) is downstream of (a): the guard fixes it, and the apply path refuses a move for a lodged subject (a typed, counted rejection).
  - Otherwise: trace the position writer and bring it to the designer before any fix.
- **Repeat run:** the same 15 runs and close conditions, plus class (a) = 0 and class (b) = 0. Report:
  - the crowded asleep-share split (lodged REST / outside REST / collapse; lodged REST length p50/p90 against base's served REST length);
  - the s44 victim ids, and whether each was a lodger or a leaver.

### Root causes and narrowed ruling (2026-11-01)
- **Lane B traces (local 4b3ecce12):**
  - Class (a): 495/505 rows are LEAVERS. The occupancy vet refused the leave step (OCCUPANCY_CONFLICT) and stripped lodged_in_clear and new_position, but left the :676 target. The other 10 rows are claim-tick :676.
  - Class (b): on the claim tick, a movement new_position (the reach tile) merged over the building tile.
  - No shared target-emit point exists (~30 writers).
- **Ruling (rpg-designer):**
  - A refused leave refuses all of that tick's movement outputs together, typed and counted.
  - LODGER_TARGET_DROPPED reasons: CLAIM_TICK | LEAVE_REFUSED.
  - Report leave-refused retries (more than 50 consecutive is a finding under AC4) and conflict winners (leaver vs mover).
  - If (iii) = 0 (no stayer drops after the claim tick): (Q) narrows to the backstop, plus a named and locked held-REST entry point with a unit test, plus an arm assert of (iii) = 0. The town-return and REGROUP decision meaning is dropped (YAGNI).
  - If (iii) > 0: one decision-entry skip via is_lodged, not 30 writer guards.
  - Class (b) accepted: the claim wins the merge over a same-tick move, explicitly. The move's new_position is refused and counted, with a test that the result is order-independent.

### (iii) > 0 and the entry-suppression ruling (2026-11-01)
- **Stayer drops after the claim tick are large.** LODGER_TARGET_DROPPED as claim / leave / stayer:
  - crowded s46: 16 / 794 / 3022
  - urban s42: 103 / 1190 / 13660
  - urban s44: 54 / 1285 / 13566
  - Dominant writer: intelligence.py:676 town-return REGROUP.
- **Ruling (rpg-designer): two entries share the is_lodged predicate** (stayers only):
  - the fused_strategic_pass per-entity loop;
  - cognition.py evaluate_entity_intent.
- **SUPPRESS movement-intent emission, don't skip the entity.** The entry runs what an outdoor sleeper with a held REST runs, minus outside perception. That keeps:
  - time-driven state (cleared_since);
  - needs and body, including REST end and the hunger/fatigue wake;
  - memory upkeep and decay.
  - The loop contents are listed keep/suppress in the change.
  - Dispatch writers are expected to be unreached; any hit is a finding.
- **Tests:**
  - one per entry;
  - a lodger's REST ends on time;
  - past the hunger wake, the lodger decides and is served EAT in place;
  - REST end leads to place_leavers on that tick or the next;
  - cleared_since advances while lodged.
- **Subject 17 (urban s44, dead t3306, 120t after leaving): provisionally divergence.** No leave-death law. The repeat reports, per world:
  - deaths within 200t of leaving, against base's deaths within 200t of a served REST end;
  - victim, cause and attacker for each;
  - subject 17's death chain;
  - leaver re-targets in the first 20t.
  - A world rise that is half or more in recent leavers is a STOP.
- **2026-11-01, 91014a88f reviewed OK by rpg-planner:**
  - is_lodged_stayer gates only the strategic target writers.
  - The tactical entry uses suppress_stayer_movement (not a skip: scheduler.py:79-83 routes the hunger/threat wake through execute_brain).
  - Typed reasons and claim-wins-merge are in.
  - Binding mechanisms notes given for strategic_intelligence_core and town_services.
  - Added a tick-count test: REST end leads to place_leavers on T or T+1.
  - LANDING ORDER: whichever of F3 and TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT lands second adds the test "cleared_since advances while lodged".
  - 15-run repeat: GO.
