---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS
artifact_type: investigation
phase: done
date: 2026-11-11
tags: []
---

# Investigation

Written retroactively at close (2026-11-11). This records the work as done; it was not a pre-implementation artifact.

## The defect
`StrategicIntelligenceSystem.fused_strategic_pass` (`src/systems/strategic_systems/intelligence.py`) has an off-cadence fast path. Its "keep the objective's direction" guard (~:394-411 on main 2ea0e4d8f) tested only `getattr(active_obj, 'target_position', None) is not None`. An entity-typed objective (`target_entity_id` set, no `target_position`) failed the guard, so a loaded entity got `target_set=town_target`, `movement_mode_set=REGROUP` and an interaction reset: it was sent home off its pursuit.

## The slow-path rule
The slow path (~:663) treats `target_entity_id is not None` as owning the direction (`has_nav_update = True`, no point set), so it writes no regroup. That rule is recorded in `docs/guidelines/intentional_divergences.md` 2.68 (TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK): strategy writes no navigation point for an entity-typed objective. Until this fix the fast path broke it.

## Characterisation (C, #852)
`tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py` pinned the bug: `test_row1_current_behaviour_entity_objective_off_cadence_regroups_home` asserted REGROUP_HOME, and the differential row `entity_objective_loaded_entity` was a strict xfail on DEFECT_A.

## Findings during the work
- `active_obj` is assigned only at :381-387 (`curr_proj_id` and `project.status == ProjectStatus.ACTIVE`); nothing between there and the guard reassigns `active_obj`, `project` or `curr_proj_id`. So the old guard's extra operands were equivalent to `active_obj`.
- The parity text for the fast-path guard is COMB-329 in `docs/parity_ledger/combat_movement.yaml`, not a STRAT row as the ticket first assumed.
- The guard never checked the objective's own status; the slow path (:657) requires `ObjectiveStatus.ACTIVE`. Recorded on TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE.
- B: three bare `except: pass` inside `fused_strategic_pass` (cache store, access-blocker parse, material-lead parse); two more at ~:775 and ~:1251 lie outside the function.
