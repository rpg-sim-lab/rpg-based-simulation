---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261117-KIND-IS-THE-SPECIES-AT-EVERY-WRITER
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-KIND-IS-THE-SPECIES-AT-EVERY-WRITER

## Title
`kind` is the species id at every writer, and the label lives in `occupation` (M1 step 4 of 5)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Step 4 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (owner dispatch #715 6920334481; M1 pace 6912138476). Child of that ticket; step 5 and stage 4b stay open there. Every PR closes a completed ticket; this is step 4's.

## Scope
Step 4 as ruled by rpg-designer: 67cc6f6d (plan, counts K6-K10), 665b9718 (step 1 rulings), 3045e98a (step 4 rulings, FINAL) and the Q1-Q3 / K9-scope / (c) answers of 2026-11-17, all copied verbatim in the parent ticket.
- Every writer writes a species id into `kind` and its label into `occupation`; a writer with no species is refused (`SpeciesNotDeclaredError`); `species_of` reads `kind`; humanoids pair and inherit by species; newborns have no occupation.
- Non-living allowlist {world_boss, magical_demonic_entity}, each with a drafted P3 owner ticket.
- Certification, arena, perf and readiness fixtures write human or goblin as `kind`; the quest victim, its `target_kind` and the regional victim move together to goblin.
- Docs: Bible 01, entities.md, ID-02, divergence 2.208 (Unified), SUB-403.

## Out of Scope
Step 5 (the species mirror), stage 4b (the context-less compile; the parent ticket does not close until it lands), the test-fixture policy (P3 ticket), the births item.

## Acceptance Criteria
- K6 (kind is a species id or on the allowlist), K6b (kind never changes), K7 (the mirror agrees), K8 (births follow species), K9 (no lost labels, with the two named deltas) = 0 on the 3 gate worlds at s42 x 5000; logging_errors 0; exceptions {}; the spied run's hash equals its plain twin's; PINNED.
- K6c (no src builder chain without `.kind(`; every src spawn call passes a species id) and K6d (each typed refusal fires) as tests; the arena quest credit survives.
- No existing assertion changes beyond those the designer approved.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (parent; step 5 and 4b)
- TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF (step 2)
- TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND (step 3)
- TCK-20261117-A-WORLD-BOSS-BODY-DECLARES-A-SPECIES, TCK-20261117-A-MAGICAL-DEMONIC-ENTITY-BODY-DECLARES-A-SPECIES, TCK-20261117-TEST-FIXTURES-DECLARE-A-SPECIES-THROUGH-A-HELPER-AND-THE-BUILDER-DEFAULT-GOES (drafted here)
- TCK-20261117-PAY-DOWN-THE-STEP-4-KIND-IS-SPECIES-CEILING-RAISES (drafted here), TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED (repeat note)

## Related Docs
- docs/mechanics/01_entity_anatomy.md ("Identity Fields: Kind, Occupation, Role")
- docs/guidelines/intentional_divergences.md (2.208)
- docs/world_rules/foundations/identity.md (ID-02)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261117-KIND-IS-THE-SPECIES-AT-EVERY-WRITER/
- agent-working/stored_artifacts/TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD/evidence/step4_inventory.md

## Related Code Areas
src/core/species.py and every `kind` writer (compiler, entity_spawner, archetype_factory, generator, camp, creature_territory, boss, calamity, reproduction_humanoid, orchestrator, runners, certification/perf fixtures), src/engine/evolution.py.

## Assumptions / Open Questions
None open for this step. The gate worlds produced no post-t0 spawn at s42 x 5000, so the births, camp, respawn and boss writers are proven by unit and integration tests only (accepted by the designer).

## Implementation Notes
Merged origin/main efba7d95c (step 3's #949) and 61a5a9206 (doc-only #950) into the branch. Merge conflicts were doc/ticket only and approved: the step-3 done ticket (main's version), Bible 01 (main's paragraph, then step 4's), the parent ticket (kept the step-4 blocks). The name-switch scan found one stale row (the evolution 'goblin' switch, retired by step 4); allowlist 121 to 120 with the designer's and lead's yes. 12 code-health ceilings raised under owner #715 6941609832 (6 repeats retiring the nine-line pay-down ticket, 6 new retiring the step-4 pay-down ticket).

## Test Summary
Head 6ca920965 (src identical to the tested c858a8314; origin/main 61a5a9206 merged after).
- Targeted run (one process at a time, -n 1, 0 OOM): tests/architecture 245 passed; arena quests 3 passed; certification 86 passed; perf 488 passed; core, unit dirs and integration: the failures were my own new tests (fixed), survivor fixtures with an empty kind (12 constructions gained `kind="human"`), the K5 ruled dict (-2: evolution row 8 and reproduction_humanoid row 24, compares retired by step 4 per the step-1 rulings 665b9718), one existing assertion and two label selectors (all designer-approved: test_natural_creature_reproduction:51 now `kind == "goblin"` and `identity.occupation == "goblin_warrior"`, kind=species step 4, camp spawn rule (Q2 amendment); the two worker selectors use `occupation_of(e) == "worker"`, label selector moved to occupation at step 4). Re-run of the edited tests: 341 passed.
- Reported, not touched: 7 `test_corpus_diversity` grade pins moved (stale on main: they equal main's numbers); `test_live_anomaly_worker` lifecycle passes alone (host timing).
- CI-equivalent run on b1e286ce5 (3750 s, peak 1395 MB, 0 OOM): the failing lanes were the known local-only list (ruff/pyrefly snapshot, the API snapshot, simq 29) plus the camp assertion, the typecheck error (`hero_species_id` returned Any: now typed with a refusal) and code-health (5 function-level imports moved to module level; 12 blocking ceilings raised with owner approval). `python3 -m codebase.gates.mypy_gate` rc=0 on c858a8314. Final code-health on 6ca920965: OK, rc=0; the 4 report-only jscpd rows are identical on clean origin/main.
- Own-job run (tree_fix = git archive c858a8314, spy dd2f9d70, 6 processes, gate before each, 0 OOM): all rc=0, PINNED, twin hash matches plain, logging_errors 0, exceptions {}; K6, K6b, K7, K8, K9 = 0 and unclassed spawn rows 0 in frontier_living_world (55 entities), urban_political (30), crowded_frontier (38). Static mode (K6c, K6d, t0 K6/K7/K9, fixture writers, arena quest credit): 56 passed. Disclosure: no post-t0 spawn occurred in the gate worlds at s42 x 5000, so K8 saw 0 births and the births, camp, respawn and boss writers are proven by unit and integration tests only.
- Name-switch scan before/after: allowlist 121 to 120 (/mnt/data2/rpg-measure/m1step4/scan/before_scan.txt, after_scan.txt).

## Files Changed
src: src/core/species.py, src/worldbuilding/compiler.py, src/worldassembly/{entity_spawner,resolver}.py, src/entities/archetype_factory.py, src/systems/world_systems/generator.py, src/world/{camp,creature_territory,boss,calamity,reproduction_humanoid}.py, src/domains/campaigns/{orchestrator,runner,state}.py, src/testing/scenario_runner.py, src/certification/scenarios.py, src/perf/scenarios.py, src/observability/readiness/harness.py, src/engine/evolution.py, src/api/presenters/state_presenter.py and src/observability/event_shapers.py (comments only).
tests: tests/unit/core/test_occupation_field.py, test_occupation_fixture_writers.py, test_occupation_label_readers.py; fixture edits in 15 test files; tests/architecture/name_switch_allowlist.yaml.
docs: Bible 01, entities.md, identity.md, intentional_divergences.md (2.208), parity_ledger/substrate.yaml (SUB-403), docs/scenarios/phase1/*.yaml (species).
tickets: the parent, the 4b triage ticket, the name-branch retirement ticket, the births ticket, the nine-line pay-down ticket (notes); new P3 drafts (world boss, magical demonic entity, test fixtures, step-4 ceiling pay-down).
baselines: codebase/baselines/code_health_exceptions.jsonl (12 rows).

## Completion Summary
Step 4 is in: `kind` is the species id on every build path, the label is in `occupation`, a writer with no species is refused, and humanoids pair and inherit by species. The gate-world own-job run met every HARD bar. Step 5 (the species mirror) and stage 4b (the context-less compile) remain open on the parent ticket.
