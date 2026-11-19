---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE

## Title
Triage the 24 tests and tools that compile a world without the content context, which gives a world with no starting purses or inventories

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
On 2026-10-20 Lane B found that `tests/regression/test_behavioral_5k.py` compiles its world with `repo.load_world` and `WorldCompiler.compile(spec, seed)` and no `context=`. With no context, `compiler.py:155` gives entities no starting inventory, so gold_avg read 0.0. That one is fixed separately (TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT). A read-only probe found 24 files under tests/ and tools/ with the same pattern; the list is in /mnt/data/scratch-rpg-implementer-2/load_world_no_context.txt. These are likely measuring a world with no purses:
- tests/integration/scenarios/test_balance_regression.py
- tests/integration/scenarios/test_content_foundation.py
- tests/unit/worldassembly/test_hero_guild_routing_population_stability.py
- tests/unit/worldassembly/test_throttled_kernel_smoke.py
- tests/engine/test_hard_law_monitor.py
- tests/integration/world/test_camp_raid_targeting.py
- tests/integration/world/test_lair_region_trauma_reachability.py
- tests/unit/engine/test_terrain_cost_from_content.py
- tests/simulation_quality/test_traceability_path.py
- tools/review_pipeline_check.py
The rest are rendering, visual and place-corpus tests.

## Scope
- For each file, decide whether its assertions depend on starting inventory or gold. If they do, move it to the shared world-build helper that the gate uses, from the behavioral_5k fix. If they don't, record why.
- Consider a guard that makes a context-less compile of a world that declares starting gold explicit, such as a required `context=` or an opt-out flag, so the trap can't come back silently.
- Re-check any expected values that move, and treat each one as a behaviour finding. Don't re-pin values to make tests pass.

## Out of Scope
- behavioral_5k (its own ticket). Changing compiler semantics.

## Acceptance Criteria
- Every listed file is classified with a reason. Each dependent file uses the shared helper, and its tests pass with any moved expectation explained.
- A decision on the guard is recorded.

## Related Tickets
- TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/load_world_no_context.txt

## Related Code Areas
- src/worldbuilding compiler.py:155
- tools/test_architecture rpg_gate_run.build_kernel (load_world_with_context)

## Assumptions / Open Questions
- Some tests may deliberately want a bare world. Record them, don't convert them.

## Implementation Notes
After v1.

- 2026-11-17 (M1 step 4, rpg-designer 3045e98a, stage 4b): this ticket also owns the kind=species stage 4b. A `WorldCompiler.compile` with no content context (149 test calls in 43 files and 3 tools: tools/calibrate_rendering.py:81, tools/review_pipeline_check.py:70, tools/visual_assets_sample_map.py:139; no src caller) keeps the legacy behaviour in step 4: `kind` = the role label with `occupation` equal to it, named as the legacy path in `src/worldbuilding/compiler.py` and pinned by a test. Giving those calls a context, then removing the legacy path, is stage 4b; the parent TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD does not close until it is done.

- 2026-11-19 (#965 step 5, rpg-designer ruling, relayed by rpg-planner): THE ITEM-AC INTERIM.
  - #965 adds a FLAGGED INTERIM rule in the context-less compile path. A body whose EntityRole is a person role (main's `_role_int(identity.role) in _PERSON_ROLES`) and whose population declares no species gets kind="human", occupation=<its old role label>. Every other body keeps today's kind.
  - Why: with the species mirror gone, a role-label kind (worker, guard, raider) is not a catalog species, so those bodies got base need rates (2x hunger). test_corpus_diversity::test_generated_frontier_3_42_extended_population_stability then failed 3/3 (22-25/44 at t800, floor 26.4); main passed 2/2. Lane B's popdiag3, executed: deaths are HAZARD/COMBAT from earlier food-seeking, not starvation.
  - This ticket RETIRES the interim: the code comment reads "FLAGGED INTERIM (rpg-designer 2026-11-19): retires with the stage-4b ticket (compile-context triage, item AC)".
  - Also in scope here: the population test compiles WITH a content context (the right long-term shape, since it does not test the production path). It is a test edit, so an owner ask. With a context the world is already below the floor on main: see TCK-20261119-A-GENERATED-FRONTIER-WORLD-FALLS-BELOW-ITS-POPULATION-FLOOR-BY-TICK-800.

## Test Summary

## Files Changed

## Completion Summary
