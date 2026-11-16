---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY
phase: done
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY

## Title
A test kernel does not degrade because an earlier test used memory: the lodging test kernel pins its governor

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
rpg-planner-ubuntu reported an order-dependent failure on main c9279925b, relayed by lead-planner-u24 on 2026-11-16.
`tests/unit/tactical/test_low_hp_retreat_gate.py::test_a_held_retreat_does_not_walk_a_stored_target_through_the_kernel` fails at line 177, `assert (1 >= 2)`, "the low-hp hold must have been decided". It fails when it runs after `tests/architecture/test_unwired_subject_check.py::test_the_real_tree_completes_and_the_found_case_is_unwired_with_its_tests` (from #924). It passes when run alone. Under xdist, CI hides it whenever the two tests land on different workers.

Root cause, traced by testing-planner on 2026-11-16 in a scratch worktree at c9279925b:
- `tests/unit/engine/lodging_kernel.kernel()` builds `Kernel(profile(), state, DeterministicRNG(1))` with the default `ResourceGovernor` and no audit_mode. That governor reads the process's live RSS through `src/engine/observability.py` (`psutil`) → `signal_source` → `governor.py:84/109`, and switches to DEGRADED or SURVIVAL against `profile.max_ram_mb`.
- The unwired check parses every `src/` and `tests/` file with `ast`. That raises the process RSS, and the RSS stays high after `gc.collect()` because Python keeps the memory arenas. The next kernel built in that process starts degraded, decides less often, and the test sees 1 decision instead of 2 or more.
- The check is the trigger, not the cause. The unwired scan is AST-only and imports no `src` module, so it leaks no module state.

Evidence (same process, `-p no:xdist -p no:randomly`):
- the real-tree test, then the target: 1 failed;
- a 15 s sleep, then the target: 2 passed, so it is not timing;
- an AST parse of all `src` and `tests` files, then the target: 1 failed, and still 1 failed with `del` plus `gc.collect()`, so it is RSS, not garbage;
- 2M small objects allocated and freed, then the target: 2 passed (too small to cross the threshold);
- `lodging_kernel.kernel()` given `governor=PinnedNormalGovernor()` (from `tests/helpers/kernel_pinning.py`): the parse-then-target pair and the real pair both pass.

## Scope
1. `tests/unit/engine/lodging_kernel.kernel()` takes `governor=None`, which defaults to `PinnedNormalGovernor()`; a caller can still pass its own. That is the shared pin for tests that run a real Kernel and must not depend on the host. Nine test files use this helper (`tests/unit/engine/test_*lodg*`, `test_beds_survive_a_checkpoint_restore`, `test_checkpoint_fields`, `test_checkpoint_group_fields`, and `tests/unit/tactical/test_low_hp_retreat_gate`). All of them must still pass.
2. A regression test that needs no heavy run. In one process, raise the signal the governor reads (patch `KernelObservability`'s cached RSS, or the platform signal, above `max_ram_mb`), build `lodging_kernel.kernel()`, and assert that it stays NORMAL and that the low-hp test's decision count is unchanged. The test must fail with the pin removed.
3. Report only, no fixes: list the other test helpers or tests under `tests/` that build a real `Kernel(` with no `governor=` pin and no `audit_mode`, and attach the list to the ticket for a follow-on sweep.

## Out of Scope
- Any `src/` change. The governor reading RSS is production behaviour.
- Changing the unwired check. Lowering its memory would only hide the defect.
- The sweep itself. Scope 3 only lists the candidates.

## Acceptance Criteria
- [x] AC1: the real-tree unwired test followed by the target passes in one process (`-p no:xdist -p no:randomly`). So does `tests/architecture` plus the target, which was 1 failed / 237 passed before.
- [x] AC2: the Scope 2 regression test passes with the pin and fails without it, and the Test Summary records that.
- [x] AC3: the nine files that use `lodging_kernel` pass.
- [x] AC4: the Scope 3 list is in the ticket.

## Related Tickets
- TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE (#924, added the unwired check)

## Related Docs
- `tests/helpers/kernel_pinning.py` (the pin's contract)

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/unit/engine/lodging_kernel.py`
- `src/engine/governor.py`, `src/engine/observability.py`, `src/engine/signal_source.py` (read only)

## Assumptions / Open Questions
- RESOLVED 2026-11-16 (rpg-planner): testing builds this and rpg-planner reviews the diff, the same arrangement as #928 and #930. rpg-planner's conditions:
  (1) Before pinning, check that none of the 9 files asserts anything that depends on the governor's tier (a DEGRADED or LOD path, a cadence count under pressure, or a decision count that only holds at NORMAL by accident). If one does, that test builds its own governor explicitly. Don't bend it.
  (2) Pin at the helper with a keyword default (`governor=None` becomes `PinnedNormalGovernor()`), so a caller can still pass its own. No assertion or expected value changes in those files. The suite must pass at `-n 1` in both orders: with the unwired test first, and alone.
  (3) Scope 3's list is report-only. Builders in RPG areas go to rpg-planner as a finding, and rpg-planner decides per file.

## Implementation Notes
- rpg-planner condition 1, checked before pinning: none of the nine files asserts anything tier-dependent. A search of the nine for DEGRADED, SURVIVAL, LOD, governor, tier, cadence and NORMAL found only unrelated words (rejection counters such as LODGER_*, `frontier_living_world`, a docstring about the brain's decision cadence in the target itself, whose assertion is a decision count that holds at NORMAL by design). So no test builds its own governor, and no assertion or expected value changed in those files.
- `tests/unit/engine/lodging_kernel.kernel()` takes `governor=None` and passes `PinnedNormalGovernor()` to `Kernel` by default (the shared pin in `tests/helpers/kernel_pinning.py`); a caller can pass its own. That is the whole change to the helper.
- New `tests/unit/engine/test_lodging_kernel_is_pinned.py` (3 tests, no heavy run): the sampled RSS (`SignalCollector.collect_platform_signals`) is patched to 20 times the profile's `max_ram_mb`; the helper kernel stays NORMAL; a caller's own governor is still honoured; and the failing target test itself, run under that raised RSS, still decides at least twice.
- Scope 3, report only (not touched): see the list in the Test Summary.

## Test Summary
- AC1 at `-p no:xdist -p no:randomly` (one process): (a) the unwired real-tree test then the target: 2 passed. (b) `tests/architecture` plus the target: 238 passed in 104 s (was 1 failed / 237 passed). (c) the target alone: 1 passed.
- AC2: the new test file passes with the pin (3 passed). With the pin removed (`governor=governor`), `test_the_helper_kernel_stays_normal...` FAILS (`'SURVIVAL' == 'NORMAL'`) and `test_the_low_hp_target_decides_at_least_twice...` FAILS with the production failure itself (`assert (1 >= 2)`, "the low-hp hold must have been decided"); the own-governor test passes either way. The pin was restored before commit.
- AC3: the nine files that use `lodging_kernel` (test_lodging, test_beds_survive_a_checkpoint_restore, test_lodger_is_invisible, test_lodged_in_stays_in_the_apply_path, test_checkpoint_group_fields, test_checkpoint_fields, test_lodging_leave_and_indexes, test_lodging_no_bed_and_arrival, test_low_hp_retreat_gate): 81 passed in 40 s.
- AC4, Scope 3 list (report only). Files under `tests/` with at least one `Kernel(` call whose line shows neither `governor=` nor `audit_mode=True`: 156 files, 230 call lines. The match is by line, so a multi-line call that passes the pin on a later line is listed too; treat it as the candidate set for the sweep, not a verdict. Per directory: tests/integration/kernel 18, tests/unit/engine 16, tests/unit/kernel 7, tests/integration/scenarios 7, tests/integration/observability 6, tests/unit/observability 5, tests/unit/core 5, tests/unit/resource 4, then 3 or fewer each in worldassembly, optimization, combat, world, campaigns, worldgeneration, social, rendering, perf, entities and cli. The RPG-area builders (tests/unit/{combat,social,resource,world,entities}, tests/mechanic_scenarios, tests/simulation_quality, tests/integration/scenarios) go to rpg-planner as a finding (condition 3).
```
tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py (1)
tests/arena/test_arena_tactics.py (1)
tests/certification/test_event_observability_parity.py (1)
tests/helpers/replay_diff.py (1)
tests/helpers/scenario.py (1)
tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py (1)
tests/integration/campaigns/test_mid_episode_grief_trigger.py (4)
tests/integration/combat/test_wound_healing_permanence.py (1)
tests/integration/domains/progression/test_recipe_reachability_under_real_kernel_tick.py (1)
tests/integration/economy/test_economic_vacancy_signal.py (1)
tests/integration/kernel/test_authoritative_outcome_truth.py (1)
tests/integration/kernel/test_canonical_signal_contract.py (4)
tests/integration/kernel/test_certification_scenarios.py (1)
tests/integration/kernel/test_determinism_suite.py (3)
tests/integration/kernel/test_executor_determinism.py (4)
tests/integration/kernel/test_kernel_boundaries.py (2)
tests/integration/kernel/test_long_run_determinism.py (2)
tests/integration/kernel/test_milestone_a_closure.py (1)
tests/integration/kernel/test_milestone_b_closure.py (2)
tests/integration/kernel/test_milestone_d_closure.py (4)
tests/integration/kernel/test_minimal_kernel.py (2)
tests/integration/kernel/test_read_models_do_not_move_the_run.py (1)
tests/integration/kernel/test_seed_stability.py (6)
tests/integration/kernel/test_simulation_kernel_contract.py (1)
tests/integration/kernel/test_substrate_freeze_m1.py (2)
tests/integration/kernel/test_tick_budget_report_only.py (1)
tests/integration/kernel/test_work_debt_is_gone.py (1)
tests/integration/kernel/test_worker_determinism.py (2)
tests/integration/observability/test_cognition_snapshot_artifact.py (1)
tests/integration/observability/test_decision_trace_determinism.py (1)
tests/integration/observability/test_initial_placement_check.py (4)
tests/integration/observability/test_kernel_event_recording.py (5)
tests/integration/observability/test_metric_windows_flow.py (4)
tests/integration/observability/test_run_artifact_flow.py (3)
tests/integration/optimization/test_cache_memory_bounds.py (1)
tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py (1)
tests/integration/optimization/test_profile_specific_behavior.py (3)
tests/integration/pipeline/test_phase_order.py (1)
tests/integration/progression/test_allocate_ap_dormancy.py (1)
tests/integration/scenarios/test_a_broke_hungry_worker_earns_and_then_eats.py (2)
tests/integration/scenarios/test_balance_regression.py (1)
tests/integration/scenarios/test_content_foundation.py (1)
tests/integration/scenarios/test_entity_differentiation.py (1)
tests/integration/scenarios/test_hunger_satiation.py (1)
tests/integration/scenarios/test_information_seeking_wiring.py (1)
tests/integration/scenarios/test_macro_economy.py (1)
tests/integration/strategic/test_occupation_change_reachability.py (1)
tests/integration/test_anomaly_worker_failure.py (1)
tests/integration/test_observatory_stream_outage.py (1)
tests/integration/test_observatory_warehouse_outage.py (1)
tests/integration/world/test_lair_region_trauma_reachability.py (1)
tests/integration/world/test_long_run_stability.py (1)
tests/integrity/test_logic_guards.py (3)
tests/mechanic_scenarios/test_action_pacing_readiness_gate.py (1)
tests/mechanic_scenarios/test_aging_death_value_differential.py (1)
tests/mechanic_scenarios/test_belief_cycle_lead_staleness.py (1)
tests/mechanic_scenarios/test_causal_spatial_memory_gated_visit_tracking.py (1)
tests/mechanic_scenarios/test_cognition_capacity_fatigue_lead_trim.py (1)
tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py (1)
tests/mechanic_scenarios/test_combat_death_trace_encounterability.py (2)
tests/mechanic_scenarios/test_combat_engage_objective_kind_through_kernel.py (1)
tests/mechanic_scenarios/test_combat_judgement_withdrawal.py (1)
tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py (1)
tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py (1)
tests/mechanic_scenarios/test_conflict04_movement_layer.py (1)
tests/mechanic_scenarios/test_emotion_near_death_hardening.py (1)
tests/mechanic_scenarios/test_entity_death_authority_boundary.py (1)
tests/mechanic_scenarios/test_entity_role_level_up_branch_value_differential.py (1)
tests/mechanic_scenarios/test_entity_target_navigation_tracks_live_position_through_kernel.py (1)
tests/mechanic_scenarios/test_evolution_xp_reward_value_differential.py (1)
tests/mechanic_scenarios/test_forage_loop_wild_food.py (1)
tests/mechanic_scenarios/test_grazing_on_plant_cover.py (1)
tests/mechanic_scenarios/test_hungry_wolf_meets_a_wounded_person.py (1)
tests/mechanic_scenarios/test_hunting_kill_to_meat.py (1)
tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py (2)
tests/mechanic_scenarios/test_near_wild_is_survivable_deep_wild_is_not.py (1)
tests/mechanic_scenarios/test_passive_death_cause_and_rebirth_defeat_lifecycle.py (1)
tests/mechanic_scenarios/test_perception_pipeline_wiring.py (1)
tests/mechanic_scenarios/test_plant_eater_graze_and_avoid.py (1)
tests/mechanic_scenarios/test_quest_generation_sourcing_orphan_calibration.py (1)
tests/mechanic_scenarios/test_self_model_and_knowledge_model_gated_dormancy.py (1)
tests/mechanic_scenarios/test_sleep_debt_collapse.py (1)
tests/mechanic_scenarios/test_sleep_pull_nearest_open_way.py (1)
tests/mechanic_scenarios/test_starvation_over_days.py (1)
tests/mechanic_scenarios/test_strategic_intelligence_detour_resolution.py (1)
tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py (1)
tests/mechanic_scenarios/test_temporal_pressure_gated_dormancy.py (1)
tests/mechanic_scenarios/test_treasury_upkeep_pays_a_town_wage.py (1)
tests/perf/test_concurrency_parity.py (2)
tests/perf/test_dirty_parity.py (2)
tests/perf/test_dirty_set_integrity.py (1)
tests/perf/test_observability_scale_validation.py (1)
tests/perf/test_persistence_phase_cost.py (1)
tests/perf/test_production_observatory_overhead.py (1)
tests/perf/test_profiler_integrity.py (1)
tests/perf/test_simq_isolation_overhead.py (1)
tests/regression/test_behavioral_5k.py (1)
tests/simulation_quality/test_age_tier_transitions_corpus.py (2)
tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py (1)
tests/simulation_quality/test_grade_regression.py (1)
tests/simulation_quality/test_heir_inventory_transfer_corpus.py (1)
tests/simulation_quality/test_kernel_simq_integration.py (2)
tests/simulation_quality/test_named_refugee_threads_corpus.py (1)
tests/simulation_quality/test_regional_reputation_corpus.py (1)
tests/simulation_quality/test_reproduction_cohort_seeding_corpus.py (2)
tests/simulation_quality/test_traceability_path.py (3)
tests/tools/test_perf_scenarios_placement.py (1)
tests/unit/cli/test_diagnostics_resources.py (2)
tests/unit/combat/test_chokepoint_hold.py (1)
tests/unit/combat/test_terrain_mechanics_forced_scenarios.py (2)
tests/unit/core/test_catalog_smoke_simulation.py (1)
tests/unit/core/test_engine_integrity.py (8)
tests/unit/core/test_graceful_shutdown.py (3)
tests/unit/core/test_operational_flags.py (4)
tests/unit/core/test_signal_truth.py (4)
tests/unit/engine/test_action_task_does_not_move.py (1)
tests/unit/engine/test_beds_survive_a_checkpoint_restore.py (1)
tests/unit/engine/test_checkpoint_fields.py (1)
tests/unit/engine/test_default_run_id_cannot_collide.py (1)
tests/unit/engine/test_diagonal_melee_pair_strikes.py (1)
tests/unit/engine/test_hash_scheduler.py (2)
tests/unit/engine/test_health_never_exceeds_max_hp.py (1)
tests/unit/engine/test_kernel_digest_via_scheduler.py (2)
tests/unit/engine/test_kernel_feature_flags_propagation.py (4)
tests/unit/engine/test_kernel_provenance_manifest_load.py (1)
tests/unit/engine/test_kernel_run_output_stays_out_of_data_runs.py (2)
tests/unit/engine/test_lifecycle_supervisor.py (1)
tests/unit/engine/test_pinned_governor_is_host_independent.py (1)
tests/unit/engine/test_proof_digest_contract.py (1)
tests/unit/engine/test_run_manifest_signal_contract.py (1)
tests/unit/engine/test_runtime_status.py (3)
tests/unit/entities/test_archetype_entity_factory.py (1)
tests/unit/kernel/test_grief_trigger_drain.py (1)
tests/unit/kernel/test_live_signal_golden.py (1)
tests/unit/kernel/test_phase_cost_accounting.py (1)
tests/unit/kernel/test_replay_determinism.py (2)
tests/unit/kernel/test_verification_level.py (3)
tests/unit/kernel/test_worker_equivalence.py (4)
tests/unit/kernel/test_worker_harden.py (3)
tests/unit/observability/extractor_characterization/kernel_scenario.py (1)
tests/unit/observability/test_event_extractor_identity.py (2)
tests/unit/observability/test_event_extractor_vitals.py (1)
tests/unit/observability/test_run_ledger.py (1)
tests/unit/observability/test_starvation_death_record.py (1)
tests/unit/perf/test_proof_digest_populated_parity.py (1)
tests/unit/rendering/test_render_incremental.py (1)
tests/unit/resource/test_buy_price_independent_of_host_timing.py (1)
tests/unit/resource/test_resource_governor_contract.py (1)
tests/unit/resource/test_resource_intelligence_contract.py (1)
tests/unit/resource/test_total_coin_is_conserved.py (1)
tests/unit/social/test_multi_hero.py (1)
tests/unit/worldassembly/test_corpus_diversity.py (2)
tests/unit/worldassembly/test_hero_guild_routing_population_stability.py (2)
tests/unit/worldassembly/test_throttled_kernel_smoke.py (1)
tests/unit/worldgeneration/test_generator.py (1)
tests/unit/world/test_resource_regrowth_wiring.py (1)

```

## Files Changed
- tests/unit/engine/lodging_kernel.py
- tests/unit/engine/test_lodging_kernel_is_pinned.py

## Completion Summary
The lodging test kernel no longer reads the process's live RSS: it pins `PinnedNormalGovernor` by default, so it cannot go DEGRADED because an earlier test used memory. The failing order (the whole-tree unwired scan, then the low-hp test) passes, and `tests/architecture` plus the target is 238 passed. The candidate list for the sweep is attached.
