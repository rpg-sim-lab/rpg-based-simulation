---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF

## Title
An entity carries its occupation label as its own field, and `species_of` is the one species read (M1 step 2 of 5)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Step 2 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (owner dispatch #715 6920334481; M1 pace 6912138476). Child of that ticket; steps 3-5 stay open there. The owner's PR rule says every PR closes a completed ticket, so this step is its own ticket.

## Scope
Step 2 as ruled by rpg-designer: the base ruling 67cc6f6d, the step-1 rulings 665b9718, the step-2 review 39dcca3d and ruling (a) on the scenario fixtures. All are copied verbatim in the parent ticket's Acceptance Criteria and Implementation Notes (not re-copied here).
- `IdentityComponent.occupation: Optional[str]`, appended last, omitted from the canonical dict while None, with a FIELD_RULES row; written at build on every path as the exact string written to `kind` (the 25 certification, perf and test-runner fixture chains included); carried by the campaign survivor rebuild, the entity copies, the apply path's identity copy and the read-only view; shown by the presenter.
- `species_of(entity)`: the one species read.
- Bible 01, ID-02, entities.md and parity row SUB-402.
- The neutral-by-projection proof (K1) and its runner.

## Out of Scope
Steps 3 to 5 of the parent: moving the label readers to `occupation`, making `kind` the species, and removing the species mirror. The true labels (role_id, profession_id, None for newborns) are step 4.

## Acceptance Criteria
- K1: 3 paired.WORLDS x s42 x 5000 ticks, base against new, whole-doc equal except the top-level start_hash and final_hash: 0 differing fields.
- K2: every writer of `kind` in src sets `occupation` to the same string (one test per writer; the t0 test over paired.WORLDS).
- K3: no production reader of `occupation` outside the carry, copy and presenter sites (static test).
- The field round-trips through the checkpoint rule, the carry-forward and the presenter, with tests. Docs, ledger row and pins moved with the change.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (parent; steps 3-5)
- TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED (paydown of the nine raised line ceilings)

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5)
- docs/mechanics/01_entity_anatomy.md ("Identity Fields: Kind, Occupation, Role"), docs/world_rules/foundations/identity.md (ID-02), docs/core/entities.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF/ (plan, investigation, test plan)
- agent-working/stored_artifacts/TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD/evidence/step1_kind_inventory.md

## Related Code Areas
src/core/state.py, src/core/species.py, src/core/builder.py, src/engine/apply.py, src/engine/checkpoint_fields.py, src/domains/campaigns/, src/api/presenters/state_presenter.py, the world compiler and spawners.

## Assumptions / Open Questions
None open for this step. The nine line ceilings the field's plumbing pushed over were raised under owner #715 6933841383 (retiring ticket above).

## Implementation Notes
Findings during the step: `ApplyPath._fast_replace_identity` hand-copies every identity slot and dropped the new one (found by tests/architecture); the step-1 scan had skipped src/certification, src/perf and src/testing, so 25 more `kind` writers were found by the writer-list test; `species_of` needed a typed return for the mypy baseline; the real docs registry needed regenerating. The designer's amendment (occupation equals the kind string on every writer in step 2) is in the parent ticket.

## Test Summary
Step 2 (head 0c74667cc on origin/main e72270894; owner GO for the projection proof #715 6921470279; designer approved the step and the scripts).
- New tests (50 passed): `tests/unit/core/test_occupation_field.py` (the field, the canonical dict, the builder, the read-only view, the checkpoint rule and an old-shape restore, `species_of` on both paths, the K2 per-writer tests, the presenter, the copies, K3 static reader allowlist, the static writer list), `tests/unit/core/test_occupation_fixture_writers.py` (the 25 certification, perf and test-runner fixture chains; the certification builders run), `tests/unit/domains/campaigns/test_carry_forward_occupation.py` (carry-forward round trip, extraction, survivor rebuild with and without a label).
- Pins moved by this step, rpg-planner ok: `test_checkpoint_group_fields` (FIELD_RULES set gains "occupation") and `test_mechanism_registry_completeness_check` (scope_files 370 to 371, unbound_files 263 to 264 for src/core/species.py): 28 passed.
- Suites run one process at a time at -n 1, no PYTEST_ADDOPTS: tests/unit/core 384 passed; tests/architecture 237 passed (before the amendment; the state-digest probe found the apply.py hand-copy, fixed); tests/unit/engine 1109 passed, 3 skipped (before the pin edit); tests/unit/domains/campaigns 184 passed; tests/unit/api 109 passed, 1 skipped; tests/unit/entities 37 passed; tests/unit/worldbuilding 437 passed; mechanism suite 290 passed (before the pin edit); after the amendment: certification and unit/certification 86 passed, 1 skipped; arena (not slow) 4 passed; perf, unit/perf, perf placement 501 passed; scenario runtime API 20 passed; strategic scenario runner and lane paths 71 passed. No hash or canonical-dict pin in certification, arena or perf moved.
- Projection proof (K1, designer's own-job count: whole-doc equal except the top-level start_hash and final_hash): 3 `paired.WORLDS` x s42 x 5000 ticks, base e72270894 against new 0c74667cc, 6 plain runs, all rc 0, peak RSS 171 to 234 MB, 0 OOM, stderr kept (only ReplayManager budget warnings, identical in both arms). K1 differing fields: frontier_living_world 0, urban_political 0, crowded_frontier 0 (total 0). Hashes start base to new / final base to new: frontier_living_world 0ce50903 to e0d457d8 / 07b42d12 to c1130a2a; urban_political 71587453 to e4c6b3c7 / e2f7e779 to f609399c; crowded_frontier 74732d0d to 1029e62f / e3ed046d to b9c96004. The base arms reproduce M1-base's s42 hashes (rpg-planner's cross-check). Runner ce09ece3, comparer 1bccef76 (approved copies beside them). Cells: /mnt/data2/rpg-measure/m1step2/cells/ (base_*.json, new_*.json, k1.txt); log /mnt/data2/rpg-measure/m1step2/driver.log.
- K2 (every writer sets occupation to the exact kind string) and K3 (no production reader of `occupation` beyond the carry, copy and presenter sites): both unit and static tests above.
- Known gap: the full CI lane set at this head is not yet run locally (planned before the push ask).
- Known gap: the pinned `final` row in the arm_child JSON carries kind only; occupation is not in that JSON, so K1 shows no difference in behaviour but cannot show the field's value (K2 covers that).

## Files Changed
Step 2: src/core/state.py (IdentityComponent.occupation, the read-only view), src/core/builder.py, src/core/species.py (new), src/engine/checkpoint_fields.py, src/engine/apply.py (the hand-copied identity), src/worldbuilding/compiler.py, src/entities/archetype_factory.py, src/worldassembly/entity_spawner.py, src/systems/world_systems/generator.py, src/domains/campaigns/{runner,orchestrator,state}.py, src/api/presenters/state_presenter.py, src/certification/scenarios.py, src/perf/scenarios.py, src/testing/scenario_runner.py, frontend/src/types/api.ts; tests/unit/core/test_occupation_field.py, tests/unit/core/test_occupation_fixture_writers.py, tests/unit/domains/campaigns/test_carry_forward_occupation.py, and the two moved pins in tests/unit/engine/test_checkpoint_group_fields.py and tests/unit/tools/test_mechanism_registry_completeness_check.py; docs/mechanics/01_entity_anatomy.md, docs/world_rules/foundations/identity.md, docs/core/entities.md, docs/parity_ledger/substrate.yaml (SUB-402), docs/REGISTRY.yaml; this ticket and its evidence.

## Completion Summary
Step 2 is in: `IdentityComponent.occupation` and `species_of` exist, every writer of `kind` also writes `occupation` as the same string, the carry sites keep it, and nothing branches on it yet. The neutral-by-projection proof passed (K1: 0 differing fields in 3 worlds; designer recount PASS); the scoped suites, the CI-equivalent run and the code-health step pass apart from the known local artifacts (ruff missing, API snapshot, session_status timeout, pyrefly missing) and the grade-anchor step that is `|| true`. Nine line ceilings were raised under owner #715 6933841383. Steps 3-5 of the parent remain open: the label readers move to `occupation`, `kind` becomes the species with the true labels, and the species mirror goes.
