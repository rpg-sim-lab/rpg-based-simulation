---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND

## Title
The label readers read `occupation`, not `kind` (M1 step 3 of 5)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Step 3 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (owner dispatch #715 6920334481; M1 pace 6912138476). Child of that ticket; steps 4 and 5 stay open there. Every PR closes a completed ticket, so this step is its own ticket.

## Scope
Step 3 as ruled by rpg-designer: the base ruling 67cc6f6d, the step-1 rulings 665b9718 (rows 10-13, 15-23 lookups, B1-B3, B5, B9-B12), the step-2 review 39dcca3d, and the designer's step-3 answers (B4 needs no change; the rescan of src/certification, src/perf and src/testing is accepted; fixtures gain `occupation` equal to their kind literal with no assertion change). All are copied verbatim in the parent ticket (Acceptance Criteria and Implementation Notes), not re-copied here.
- Move every LABEL compare from `kind` to `occupation`, same literal; rename `BOSS_ENTITY_KINDS` and `SPAWN_CADENCE_EXCLUDED_KINDS` to `..._OCCUPATIONS` (a name only).
- K5 static test; K4 IDENTICAL proof.

## Out of Scope
Step 4 (`kind` becomes the species; true labels; the writers' `occupation = kind` copies go; the species readers; B4 and the respawn) and step 5 (the species mirror).

## Acceptance Criteria
- K4: 3 paired.WORLDS x s42 x 5000 ticks, base (step 2 head) against new, whole-doc IDENTICAL, start_hash and final_hash included: 0 differing fields.
- K5: no label compare is left on an entity's `kind` outside the species rows, the display rows and B6/B7 (static test).
- Every moved reader reads `occupation` with the same literal; fixtures reaching a moved reader carry `occupation`, with no assertion change.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (parent; steps 4-5)
- TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF (step 2)
- TCK-20261117-SPLIT-EVENT-SHAPERS-BELOW-ITS-LINE-CEILINGS (paydown of the two raised event_shapers ceilings)

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5)
- docs/mechanics/01_entity_anatomy.md ("Identity Fields: Kind, Occupation, Role")

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND/
- agent-working/stored_artifacts/TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD/evidence/step1_kind_inventory.md

## Related Code Areas
The moved readers (src/world, src/observability, src/systems), src/core/species.py.

## Assumptions / Open Questions
None open for this step.

## Implementation Notes
`occupation_of(entity)` returns None for an object with no identity or no label, with no fallback to `kind` (designer approved). The characterization pins (the event extractor) moved with the unlabelled fixtures and returned to their pinned digests once the fixtures carried `occupation`. creature_territory got a typed `maturity_rate` accessor so its function stays inside the complexity ceiling (an inline `or ""` raised it by one).

Merge of origin/main f433a9530 (the #946 squash of step 2) into the step-3 branch: 4 add/add conflicts (src/core/species.py, tests/unit/core/test_occupation_field.py, docs/mechanics/01_entity_anatomy.md and the parent ticket), because the squash shares no history with the branch. Main's version of each of the four files is byte-identical to its version at 1a676e15d (same sha256), so main has no drift; the resolution is `git checkout --ours` on those four files, with no hand edit. Proof that the branch diff is only step 3's own: the md5 of `git diff origin/main HEAD -- src` equals the md5 of `git diff 1a676e15d b6f02b3da -- src` (40b86670876533412649dfe4d94d0561), and the md5 of the tests, frontend and codebase diffs match the same way (24a5c74bb6ff48641de2ffd182420a7a); `git diff --stat 1a676e15d HEAD -- src` is 14 files, +50 -30.

## Test Summary
Step 3 (head b6f02b3da on origin/main f433a9530 / step-2 head 1a676e15d; owner GO for the K4 proof #715 6934624460; the two event_shapers ceilings raised under owner #715 6934602208).
- New tests (tests/unit/core): `test_occupation_label_readers.py` (K5: no label compare is left on an entity's `kind` outside the 9 ruled files; the renamed label sets keep their members; the territory rates keep their keys and default), plus the extended K3 reader allowlist in `test_occupation_field.py`.
- Fixtures: hand-built test entities that reach a moved reader gained `occupation` equal to their kind literal, with no assertion changes: tests/unit/world (test_aura, test_calamity_raid, test_world_dynamics), tests/unit/social/test_party_composition.py, and the MagicMock entity helpers in tests/unit/observability (the event-extractor agency, agency2, cognition, contract_milestone, economy, faction_economy, information2, narrative, progression, simq, social_faction, social_memory, world and world_dynamics files, and test_event_shapers, test_event_shapers_progression, test_event_shapers_world_dynamics). The two constant renames moved the import sites in test_entity_kind_constants.py and test_event_extractor_world_dynamics.py. The pinned event-extractor characterization tests moved 104 rows, then 32, until the fixtures carried occupation; they pass again at their pinned digests (no output change).
- Suites (one process at a time, -n 1, no PYTEST_ADDOPTS, 0 OOM, peak at most 372 MB): new files 53 passed; tests/unit/observability 1248 passed, 1 skipped; tests/unit/world 632 passed; tests/unit/social 369 passed; tests/unit/systems 18 passed; tests/unit/engine 1110 passed, 3 skipped; tests/unit/core 387 passed; tests/unit/domains 1138 passed; gameplay set (strategic, tactical, combat, ai, movement, quest, progression, economy, scenarios, replay, kernel, motivation, cognition) 1570 passed; mechanism completeness pins 14 passed; tests/integration (not slow) 1134 passed, 6 skipped; certification and unit/certification 86 passed, 1 skipped; arena (not slow) 4 passed; perf, unit/perf and perf placement 501 passed. mypy_gate rc 0. Code-health: only the 4 report-only jscpd rows remain after the two event_shapers ceilings were raised.
- K4 (the designer's own-job count: whole-doc IDENTICAL, start_hash and final_hash included): 3 paired.WORLDS x s42 x 5000 ticks, base 1a676e15d against new b6f02b3da, 6 plain runs, all rc 0, peak RSS 167 to 237 MB, 0 OOM, child logs only ReplayManager budget warnings (identical in both arms). K4 differing fields: frontier_living_world 0, urban_political 0, crowded_frontier 0 (total 0). Hashes equal between the arms: frontier_living_world start e0d457d8 final c1130a2a; urban_political start e4c6b3c7 final f609399c; crowded_frontier start 1029e62f final b9c96004. Runner run_identical.sh 83aad33c, comparer compare_identical.py 3b32e5ba (approved copies beside them). Cells: /mnt/data2/rpg-measure/m1step3/cells/; log /mnt/data2/rpg-measure/m1step3/driver.log.
- Designer recount (relayed by rpg-planner): the step-3 K4 recount PASSES, step 3 is IDENTICAL to step 2. Recounted from m1step3/cells; scripts cmp equal to the *_approved copies. All 3 worlds base == new as whole docs, hashes included, equal to step 2's new arm; all PINNED, rc 0, peaks 167-237 MB; child logs only ReplayManager lines; 7ccd32652 has no src diff vs b6f02b3da, so the proof covers it.
- Known gap: the pinned `final` rows of the arm_child JSON carry kind, not occupation; K4 shows no behaviour change, K2 (step 2) and the fixtures cover the field's value.

## Files Changed
src: src/core/species.py (`occupation_of`), src/observability/{entity_kind_constants,event_extractor,event_shapers}.py, src/observability/extraction/{combat,resources,world}.py, src/systems/social_systems/party_composition.py, src/systems/world_systems/navigation.py, src/world/{boss,calamity,creature_territory,environment,threat}.py; tests/unit/core/test_occupation_label_readers.py (new), tests/unit/core/test_occupation_field.py, 22 fixture files under tests/unit/{world,social,observability}; docs/mechanics/01_entity_anatomy.md, docs/simulation_quality/event_type_coverage.md, docs/parity_ledger/world_dynamics.yaml (renamed constants), docs/REGISTRY.yaml; codebase/baselines/code_health_exceptions.jsonl (two event_shapers rows); the paydown ticket TCK-20261117-SPLIT-EVENT-SHAPERS-BELOW-ITS-LINE-CEILINGS; this ticket and its evidence.

## Completion Summary
Step 3 is in: every label compare moved from `kind` to `occupation` with the same literal (party roles; the hero, world_boss, dragonkin, stronghold and goblin_raider labels; the boss and spawn-cadence label sets, renamed `..._OCCUPATIONS`; the territory-rate table), through `occupation_of`; the species rows, the display rows and the spawn-kind catalog table stay on `kind`. K5 (static) holds the line, and K4 (IDENTICAL, hashes included) passed in all 3 worlds. Two event_shapers line ceilings were raised under owner #715 6934602208 (paydown ticket filed). Steps 4 and 5 of the parent remain open: `kind` becomes the species with the true labels, then the species mirror goes.
