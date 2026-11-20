---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261117-TEST-FIXTURES-DECLARE-A-SPECIES-THROUGH-A-HELPER-AND-THE-BUILDER-DEFAULT-GOES
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-TEST-FIXTURES-DECLARE-A-SPECIES-THROUGH-A-HELPER-AND-THE-BUILDER-DEFAULT-GOES

## Title
Test fixtures declare a species through a helper, and the `V2EntityBuilder` default kind goes

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
M1 step 4 leaves `V2EntityBuilder`'s default kind `"hero"` in place for tests: about 1003 `.kind(` literals in 610 test files (TEST, actor, npc, ...) write a label as `kind`, and 429 builder sites never call `.kind(`. They need one fixture policy, not allowlist rows. src builders are already guarded by a static test (K6c).

Drafted by rpg-implementer-2 on the M1 step-4 branch (rpg-m1-kind-step4) for rpg-planner's review, as rpg-designer 3045e98a (and the Q1 ruling) require. Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

## Scope
1. A test helper that builds an entity with a declared species and an occupation.
2. Move the fixtures to it in stages, with no assertion change.
3. Remove the builder default so a chain with no `.kind(` is refused.

## Out of Scope
- Changing what any decision does with the body. This is a declaration of the species, not a rebalance.

## Acceptance Criteria
- No test builder chain relies on the default kind.
- `V2EntityBuilder` has no default `kind`.
- No assertion changes in the migrated tests.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (step 4 created the allowlist this ticket retires from)
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES

## Related Docs
- src/core/species.py (NON_LIVING_KIND_ALLOWLIST)
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
None.

## Related Code Areas
src/core/species.py, src/world/

## Assumptions / Open Questions
- Which species (or a declared content mapping) the body takes is the designer's ruling; none is chosen here.

## Implementation Notes
- 2026-11-19 (rpg-designer's H1 ruling on TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK, relayed by lead-planner-u24):
  - Some fixtures use NON-CONTENT kinds as kind ("entity", "monster", "hero"); for example tests/.../test_campaign_runtime.py::test_entity_state_persists_across_episodes.
  - Because of them, H1's CAMPAIGN and SCENARIO-RUNNER senses checks stay LOOSER than compile, spawn and archetype: an unknown kind gets the baseline.
  - Once this ticket moves those fixtures to real species, the two sites TIGHTEN to refuse unknown kinds too. That's a follow-up step on H1's sites, named in this ticket's closure.
  - Restore is already strict in H1.
- 2026-11-17 (M1 step 4, rpg-designer ruling (c), option (i)): the test-side `spawn_monster` and `spawn_natural_creature_offspring` calls pass `species=X, occupation=X` with the SAME literal and no assertion change; K6's run counts cover the 3 gate worlds and the src writers (K6c), and tests are out of K6. These calls write a label as the species and are this ticket's to migrate (file, literal):
  - tests/unit/world/test_spawn_monster_catalog_faction.py: parametrized `kind` over goblin_warrior, orc_warrior, goblin_raider, wolf, slime, bear, harpy, golem (spawn_monster, 2 tests) and over wolf, bear, golem, goblin_warrior, orc_warrior, dragonkin, bandit; literals goblin_warrior (4 calls), orc_warrior (3), wolf (1)
  - tests/unit/world/test_natural_creature_reproduction.py: goblin_warrior (3 calls), monster (1)
  - tests/integration/optimization/test_component_patch_apply_parity.py: goblin_warrior (1)
  - tests/unit/world/test_spawned_entity_validity.py: parametrized monster, goblin, world_boss
  - tests/unit/world/test_boss_gate_reachability.py: world_boss (2)
  - tests/unit/engine/test_canonical_hash_covers_world_components.py: world_boss (1)
  - tests/unit/ai/test_guild_need_scorer.py: goblin_raider (1)
  - tests/integration/world/test_phase9_stability.py: wolf (1)
  - tests/unit/core/test_engine_integrity.py: goblin (1)
  - tests/unit/engine/test_mid_run_adds_never_reuse_an_entity_id.py: monster (1, was the default kind)
  - tests/unit/progression/test_species_base_stats_preserved.py: monster (1, was the default kind)
  (a grep of `species=` with `occupation=` in `git diff main..rpg-m1-kind-step4 -- tests` re-derives the exact lines.)

## Test Summary

## Files Changed

## Completion Summary
