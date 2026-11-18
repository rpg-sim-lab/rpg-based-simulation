---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD

## Title
The `identity.properties["species_id"]` mirror is gone: `kind` is the only species field and `species_of()` the only reader (M1 step 5 of 5)

## Status
INPROGRESS

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Step 5 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (child ticket; the parent stays open for stage 4b). Every production reader of the mirror moves to `species_of()`, no writer writes it, and the test fixtures that read or wrote it follow (owner-approved #715 6985677098 / 6985692443, patch f55b8167). Rulings: rpg-designer set-but-unknown species (a): a species set but absent from content, or declared without a need profile, gets None = base rates, no role fallback, counted by `unprofiled_need_counts` and logged at DEBUG; (b) role fallback rejected; (c) fixture species via the P3 ticket plus the owner ask above.

## Scope
- Remove the mirror writes (`entity_spawner`, `archetype_factory`, `compiler`) and move every reader (`biological_needs`, `need_paths`, `serves`, `state_presenter`, `role_model_imitation`, `common_knowledge`, `event_shapers` payload, `identity_resolver`, `faction.get_species_id_str` and its callers) onto `species_of()`.
- `profile_id_for` / `need_rates` / `unprofiled_need_counts` as ruled; K12 static test (`tests/unit/core/test_species_mirror_is_gone.py`).
- The 46 test files of the approved fixture patch (tests only); the extraction of `_population_properties_and_species` from `WorldCompiler.compile` (class 584/596, compile 490/503; no ceiling edited).

## Out of Scope
Stage 4b (context-less compile), the NINE and step-4 ceiling pay-downs, removing the remaining dead `.properties({"species_id": ...})` fixture writes (P3 follow-up with a static test), the DAY line in `test_starvation_death_record.py` (not approved).

## Acceptance Criteria
- K11: neutral by projection, `arm_child` whole-doc equal except start_hash and final_hash, 3 gate worlds x s42 x 5000 (kit approved: runner, probe e88e69ba, compare 1bccef76).
- K12: production readers/writers of the mirror = 0 (AST test, the one allowed site is the `event_shapers` payload field).
- Unprofiled needs = 0 at t0 and at the final state in the 3 gate worlds; counts of `world_boss` / `magical_demonic_entity` reported.
- Statics green (code-health, lint-imports, mypy); regression 93 of 93 files green.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (parent)
- TCK-20261117-KIND-IS-THE-SPECIES-AT-EVERY-WRITER (step 4)
- TCK-20261117-TEST-FIXTURES-DECLARE-A-SPECIES-THROUGH-A-HELPER-AND-THE-BUILDER-DEFAULT-GOES (P3)
- TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED, TCK-20261117-PAY-DOWN-THE-STEP-4-KIND-IS-SPECIES-CEILING-RAISES (next)

## Related Docs
- docs/mechanics/01_entity_anatomy.md; docs/world_rules/foundations/identity.md (ID-02); docs/guidelines/intentional_divergences.md (2.208)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD/

## Related Code Areas
src/core/species.py, src/engine/biological_needs.py, src/worldbuilding/compiler.py, src/worldassembly/entity_spawner.py, src/entities/archetype_factory.py, src/content_semantics/faction.py

## Assumptions / Open Questions
`world_boss` and `magical_demonic_entity` bodies stay on the non-living allowlist (own P3 tickets); no post-t0 spawns occur in the gate worlds at s42 x 5000, so births/camp/respawn writers are proven by unit and integration tests only.

## Durable state, lifecycle and clocks
Species and identity reads only. No new record is created or ended: `kind` is the species set once at spawn (step 4) and never changes in a run; `identity.occupation` is its own field; nothing survives an update that did not before. The removed mirror was a copy, not a source. No clock is read (the need-rate cache key is `(need_profile_id, species_of, role)`, tick-independent).

## Implementation Notes
Head to measure: the commit that files this ticket (src and tests identical to 23d6bf642); the closure commit after the S9 run touches no src or tests.

## Test Summary
Statics on 23d6bf642: code-health OK rc=0 (2 new/2 worse report-only jscpd rows that pre-exist on main), lint-imports 17 kept 0 broken, mypy no new. Regression 93 of 93 test files pass (one gated pytest per file). Throwaway fixture proof: 45 of 45 failing files green with patch f55b8167. K11 and the unprofiled-needs bar: pending the S9 run.

## Files Changed
21 src files, 46 test files (fixture patch f55b8167), K12 test, this ticket and its staging artifacts.

## Completion Summary
Pending the S9 run.
