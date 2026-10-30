---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261030-RETIRE-PUSH-EVENT-SHAPER-ROLLBACK-PATHS
phase: open
date: 2026-10-30
tags: [observability]
---

# TCK-20261030-RETIRE-PUSH-EVENT-SHAPER-ROLLBACK-PATHS

## Title
Retire the flag-OFF rollback paths of the four push-event-shaper flags, and the flags themselves, once the push path is proven stable and the owner decides. PARKED.

## Status
BLOCKED

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
codebase-planner reported after #791 (M7 batch 2) that jscpd flags 2 duplicates: `src/observability/event_shapers.py` ~:1254 against `src/observability/extraction/world.py`, and ~:1652 against `src/observability/extraction/contracts.py`.
- They are the event_extractor rollback copies of what the push shapers emit by default.
- They were baselined before #791; the split only moved them.

Four flags gate these rollback paths: `ENABLE_PUSH_EVENT_SHAPERS`, `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, `ENABLE_PUSH_EVENT_SHAPERS_QUEST` and `ENABLE_PUSH_EVENT_SHAPERS_AGENCY`.
- All have defaulted ON since the August cutovers (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION, TCK-20260806-PUSH-CUTOVER-PHASE2, TCK-20260807-QUEST-EVENT-PUSH-MIGRATION).
- `docs/guides/feature_flags.md` documents each one as "a real, working rollback".

rpg-planner ruled on 2026-10-30 (relayed via lead-planner-u24 and lead-planner): file this now as a PARKED ticket so it isn't lost. No dispatch until all three blockers below clear. The M7 condition to keep the flag branches as they are stands until then.

## Blocked On
1. The u24 A'/D73 chain landing.
2. Push-path stability evidence: cite the flags-ON runs since the August cutovers (gate, SimQ and paired runs), showing the default push path has been stable over N runs. rpg-planner sets N when it unparks this ticket.
3. An owner decision, because this removes a working rollback.

## Scope
1. Inventory, before any deletion, of what the flag-OFF tests uniquely cover. Re-home anything that only they cover. Name each test. Known so far (origin/main 7bfeab187):
   - `tests/unit/observability/test_event_emit_order.py::test_rollback_path_emits_skills_traits_and_breakthroughs_sorted` (#790, PHASE2 OFF)
   - the M7 characterization flag-off config rows: `off_<flag>` for each of the 4 `FLAGS` in `tests/unit/observability/extractor_characterization/recorder_plugin.py:23`, recorded in `tests/fixtures/event_extractor_characterization/unit_corpus.jsonl` / `kernel_runs.jsonl` and asserted by `test_event_extractor_characterization.py::test_config_matrix_covers_every_rollback_flag_and_both_mode_sides`
   - other tests that set these flags, to classify: `tests/unit/observability/test_event_shapers_{agency,deferred_instrumentation,narrative,strategy}.py`, `tests/unit/config/test_phase10_feature_flags.py`, `tests/integration/test_scenario_feature_flag_defaults.py`, `tests/certification/test_phase10_enhanced_determinism_parity.py`, `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`, `tests/unit/cognition/test_information_seeking.py`, `tests/simulation_quality/test_calibrate_simq.py`, `tests/simulation_quality/test_region_transformation_pipeline_corpus.py`, `tests/perf/test_simq_isolation_overhead.py`
2. Delete the flag-gated rollback branches in `src/observability/event_extractor.py` and `src/observability/extraction/`, the flags, and their reads in `kernel.py` and `event_shapers.py::run_shadow_shapers()`.
3. Update `docs/guides/feature_flags.md`. It is rpg-planner's doc, and rpg-planner reviews the change.
4. Add a `Unified` divergence (ubuntu id block) only if any default-path behaviour shifts. None is expected: the final state hash and the event stream should be identical on the default path.

## Out of Scope
- Any change to the default push path's events.
- Other feature flags.

## Acceptance Criteria
1. The Scope 1 inventory is in investigation.md before any code. Each flag-OFF test is classified as re-homed, redundant with default-path coverage (cite the covering test), or deleted with a reason.
2. jscpd no longer reports the two duplicates.
3. On the default path, the event streams are byte-identical to before (the M7 characterization fixtures, flags-ON rows) and the final state hash is identical on the usual worlds and seeds. Any difference means STOP and report to rpg-planner.
4. feature_flags.md is updated and rpg-planner has reviewed it.
5. Scoped tests pass, and generate_registry --check and paths-guard pass.

## Related Tickets
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION, TCK-20260806-PUSH-CUTOVER-PHASE2, TCK-20260807-QUEST-EVENT-PUSH-MIGRATION (the cutovers)
- TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED (#790; its rollback-path test)
- codebase M7 batch 2 (#791; the duplicates and the keep-as-is condition)

## Related Docs
- docs/guides/feature_flags.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/event_extractor.py, src/observability/extraction/, src/observability/event_shapers.py, src/engine/kernel.py

## Assumptions / Open Questions
- PARKED. Standard tier, so dispatch needs the owner's go through lead-planner, and only after all three blockers clear.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
