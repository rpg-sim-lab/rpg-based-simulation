---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD
phase: done
date: 2026-11-19
tags: []
---

# TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD

## Title
The `identity.properties["species_id"]` mirror is gone: `kind` is the only species field and `species_of()` the only reader (M1 step 5 of 5)

## Status
DONE

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
Measured head 79713fae (src and tests identical to 23d6bf642); the closure commit touches docs, monitoring and the registry only.

Post-resync history (rpg-implementer-2, 2026-11-19). The first sweep at aca8891ff found 4 failing groups: the wild-wolf test (decision 47, T1/T2, owner-approved), the engine lodging test, 2 observability characterization tests (160 pinned digests) and `population_stability`. Control on main 77e4aeb72: lodging and observability pass there, population passes 2 of 2 (#965 fails 3 of 3). Cause: a role-word kind from a compile with no content context (`kind("citizen")`, the stage-4b legacy path) now reads as a species not in the catalog and so lost the person-profile fallback (hunger 0.05 became 0.10). (a) was a compiler rule (kind = "human" for person roles); the designer withdrew it after two flags (it failed `test_occupation_field.py:171-180` and made wolves and spiders human) in favour of (a2): the fix is in `biological_needs.profile_id_for` only, a non-catalog kind reads its role for needs (FLAGGED INTERIM, rpg-designer 2026-11-19, retires with stage-4b item AC / the P3 typed load error), counted apart in `interim_role_need_counts` (disjoint from `unprofiled_need_counts`, `kind|ROLE` keys, `<none>|ROLE` for no kind).

## Test Summary
Statics on 23d6bf642: code-health OK rc=0 (2 new/2 worse report-only jscpd rows that pre-exist on main), lint-imports 17 kept 0 broken, mypy no new. Regression 93 of 93 test files pass (one gated pytest per file). Throwaway fixture proof: 45 of 45 failing files green with patch f55b8167. S9 run (executed, 9 processes rc=0): K11 0 differing fields in all 3 gate worlds; unprofiled needs 0 at t0 and final; boss/demonic counts 0; 3 of 3 same_run=yes. Both arms predate #964 (duplicate boss fix), a fair A/B.

Post-resync evidence (all executed; shas are sha256 prefixes, files under /mnt/data2/rpg-measure/m1step5/):
- Sweep at aca8891ff (`resync_unit_aca8891ff.out` fcd32096): 9 failures in 3 directories (6 worldassembly, 2 observability, 1 engine). Control on main 77e4aeb72 (`resync_ctrl2_summary.txt` e6871aff): lodging 17 passed, characterization 12 passed, population 17 passed.
- Role-changed diagnostic (`rolechg_summary.txt` 3b36c3ea): the event is identical on both trees (tick 20); body 1 hunger rises 0.10 per tick on #965 against 0.05 on main (cause above). Mapping run (`obsmoved_summary.txt` 98f6995a): all 160 moved pins come from the one body at `test_event_extractor_identity.py:229`. Population diagnostic popdiag3 (`popdiag3_summary.txt` e0a42c1e): no-context arm 36 hunger projects and 20 deaths on #965 against 0 and 8 on main, no starvation deaths; with a context the arms do not differ in rates; population alternation `resync_pop_summary.txt` 9b6eeb5e: #965 fails 3 of 3, main passes 2 of 2.
- Rulings: designer (a2) 2026-11-19; owner approved T1/T2 ("good", #715 via the lead) and the lodging wolf line (#715 7010276730, `test_lodging_no_bed_and_arrival.py:53` -> `kind="wolf"`). S9 for the projection run: #715 7009764625.
- Pre-registered checks at eeb41ccdf: (i) population_stability 3 of 3 passed (`resync_vi_summary.txt` f94bca47); (ii) the three with-context gate cells hash-equal to aca8891ff, start and final (`cells_a2/strict.txt`, STRICT 0 differing fields); (iii) no test that is on main edited by (a2); (iv) `interim_role_need_counts` and `unprofiled_need_counts` are `{}` on the three gate worlds (`a2_interim_summary.txt` eb0b8db9); (v) characterization 12 passed with no fixture edit. Sweep at eeb41ccdf (`resync_unit_eeb41ccdf.out` d60c8a44): only the 5 known grade-stability rows (same numbers as main) and the lodging test.
- Final at 354392862 (merge of origin/main 5bedb5ff0 and the wolf commit a6b97e820): statics rc 0, head-named logs (`statics6_*.log`: code-health 8af13d7a, lint-imports e6e3ef50, mypy f9e35c85, `venv-statics` mypy 2.4.1 / ruff 0.17.5 / import-linter 2.16); `tests/unit/engine` 1146 passed 3 skipped (lodging test included), `core` 424 passed, `observability` 1251 passed 1 skipped (`resync_final_tests_summary.txt` 51c223b3).
- Docs search (`docs_search.py`) and the mechanism-registry advisory (`attributes_biology` cites `biological_needs.py::need_rates`, entry unchanged): reviewed, no change (rpg-planner). Edited by ruling: SURV-05 repository-evidence clause in `survival-needs.md`, PROG-128 `v2_evidence` in `progression.yaml`.
- Lair copy (executed, one tree, `lair6_rows.txt` 545861f8): a lair-spawned wolf copy gets faction `monster_horde` and is not a wild creature (2.216 disclosure).

## Files Changed
21 src files, 46 test files (fixture patch f55b8167), K12 test, docs (04_strategic_cognition.md, intentional_divergences.md 2.208, parity ledger SUB-403), this ticket and its stored artifacts.

Post-resync additions: `src/engine/biological_needs.py` (`profile_id_for` interim branch, `interim_role_need_counts`, disjoint `unprofiled_need_counts`), `tests/unit/core/test_species_mirror_is_gone.py` (revised to (a2)), `tests/unit/engine/test_need_profile_of_a_non_catalog_kind.py` (new), `tests/unit/engine/test_lodging_no_bed_and_arrival.py` (the owner-approved wolf line), `docs/guidelines/intentional_divergences.md` (one 2.216 sentence).

## Completion Summary
The species mirror is gone: no writer, no reader (K12), `species_of()` is the only species read; the owner-approved fixture patch f55b8167 moved 46 test files (8 assertion changes); Bible 04, divergence 2.208 and SUB-403 updated. Measured neutral by projection (K11 = 0) with unprofiled needs 0. Closure touched no src or tests.
