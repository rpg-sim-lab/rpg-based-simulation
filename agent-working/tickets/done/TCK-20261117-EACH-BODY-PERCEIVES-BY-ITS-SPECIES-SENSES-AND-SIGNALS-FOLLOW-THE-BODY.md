---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY

## Title
Each body perceives by its species' senses, and what it gives off follows the body (PERC-02a)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
PERC-02a, the first half of TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS: senses derived from the species at read, signals that follow the body, night vision, and a gate error that is not perception.

## Scope
1. The gate resolves catalog.species[species_of(entity)].sense_profile at one read site; no stored field. A species in content with no profile is a typed SenseProfileError; a body whose species is not in content is unprofiled (baseline, counted, DEBUG).
2. emitted_signals(entity, body): visibility by size, noise/vibration by activity, scent and life for the living; body models may declare `signals`.
3. night_vision on the profile (goblin_alert, predator_smell, spider_vibration, undead_dread, new troll_senses); vision counts two levels lower at night otherwise.
4. A gate exception is not perception and logs at ERROR.
5. Divergence 2.210, ledger STRAT-352, Bible 04.

## Out of Scope
- Stealth and concealment; weather's perception multiplier (unread today; it stays unread).
- Balance tuning (Phase 3).

## Acceptance Criteria
- P2: bodies whose derived profile differs from their species' profile: 0; unprofiled bodies in the 3 gate worlds: 0.
- P3: no perception granted below the gate threshold (unit grid).
- Night -2 grid; gate exceptions in a run: 0, each with an ERROR record.
- Static test: perception modules read no `.kind`.

## Related Tickets
- TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS (parent; closes with 02b)
- TCK-20261117-DECISIONS-SEE-OTHER-BODIES-ONLY-THROUGH-PERCEPTION (02b)

## Related Docs
- docs/plans/systemic_world/m1_kernel_spec_items_2_6.md (Item 3)
- docs/world_rules/knowledge-agency/perception.md (PERC-02, on main with the planner's docs PR)

## Related Stored Artifacts
None.

## Related Code Areas
src/world/perception/, src/engine/appraisal.py, src/engine/hostility.py, src/engine/tactical*.py, data/content/living/

## Assumptions / Open Questions
None open; rulings by rpg-designer relayed by rpg-planner 2026-11-17 (split into 02a/02b; derive at read; unprofiled fixtures counted).

## Implementation Notes
Designer rulings 2026-11-17 via rpg-planner: derive at read (no stored field, no FIELD_RULES row); fixture policy (unprofiled counted, linked to TCK-20261117-TEST-FIXTURES-DECLARE-A-SPECIES-THROUGH-A-HELPER-AND-THE-BUILDER-DEFAULT-GOES). Known: legality.attack_allowed, is_feeding_kill, scorers_support.perceived_hostiles and the other get_neighbor_view sites stay day-by-default until 02b.

Body-model `signals` accepts an optional `magic` key (default none for every body; designer condition 2026-11-17). No production body in data/content declares it in this PR (grep-verified: none); only the test-only fixture in tests/unit/engine/test_pressure_perception_consumers.py does. To go in the PR body.

## Test Summary
All runs with -n 1 on the final head 44f88a7ce (merge of origin/main 3aafdb383 included), busy-gate first, one host job at a time.
- Targeted: tests/unit/world/test_perc02a_senses_signals_night.py (new), test_sense_perception_gate.py (two tests restored), test_pressure_perception_consumers.py, test_notice_unengaged_hostile.py, test_archetype_entity_factory.py, test_every_compiled_body_has_a_declared_diet.py: pass (28 in the last targeted run). Job (A) on 2b4b8b822: 1255 passed, 7 failed; the 7 are the corpus grade pins already stale on main (TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN; identical numbers and 1000/1000 identical hashes on main bb26e4e5f); tests/architecture passes. The frontier s123 corpus test stays red locally as on main (@slow, not in CI).
- All 26 slow/extra_slow scenario tests (tests/mechanic_scenarios + tests/integration/scenarios): 24 passed, 1 skipped, 1 xfailed, 0 failed (392s).
- lint-imports 17 kept, 0 broken; make code-health OK (4 report-only jscpd rows in src/observability, not touched); make typecheck-py rc=0. Code-health first failed on the merged head (WorldCompiler 597>596, compile 504>503); fixed by folding the diet and sense checks into require_declared_population_species (diet first, same messages), no ceiling edit.
- Bravery quartile scenario: from t=0 the run is at night, ratio 1.20 (< 1.5); with the day clock set in the scenario setup (world_time=600, threshold unchanged) top 0.2428, bottom 0.1105, ratio 2.20; identical on main bb26e4e5f by day.
- Channel spy (urban_political 200t, 5 seeds, 10 arm-cells, approved script sha 2d92097b): main perceives by vision only at night; 02a perceives movers by hearing and hardly any still bodies. Combat starts main to 02a: s42 5 to 10, s43 6 to 1, s44 6 to 5, s45 7 to 3, s46 10 to 6; the fixed decision rule (at least 4 of 5 seeds up and pooled rise at least 2 SD) is not met: cascade/chance, not systematic.
- Re-pins (rule (a)): grade_anchors.json frontier s42 NARRATIVE {A,1.715} to {S,2.2778}; frontier s123 COMBAT 0.18935 to 0.29143; frontier s123 NARRATIVE 1.62304 to 1.98985 (s123 PROGRESSION not re-pinned).
- Existing-test fixture edits (setup only, thresholds unchanged): pressure-consumer tests inject species via kind and a test-only magic-only catalog body, DAY=1200; wake tests world_time=1200; the archetype-id test uses species human because the archetype path refuses a non-content species (rpg-designer, PERC-02a).
- magic signal key: optional, default none; no production body declares it.

## Files Changed
See `git diff --stat origin/main...HEAD` (37 files): content (schema, sense_profiles, species, body_models), src/content/species_senses.py, src/core/species.py, src/world/perception/gate.py, src/engine/perception_signals.py and the night threading through appraisal, hostility, tactical, tactical_avoid, candidate_selector, scheduler, opening_steps, archetype_factory, compiler, diet_declaration, entity_spawner; tests as above; divergence 2.210, ledger STRAT-352, Bible 04.

## Completion Summary
Perception now uses each species' own senses (derived at read from the species' sense profile, never stored), what a body gives off follows its size, activity and life, vision drops two rungs at night unless the profile declares night_vision, and a gate error is not-perceived and logged at ERROR. Compile, spawn and archetype paths refuse a missing or unusable species profile with a typed SenseProfileError. Known: sites that read neighbours outside the gate (legality.attack_allowed, is_feeding_kill, scorers_support.perceived_hostiles, other get_neighbor_view sites) still see by day until 02b.
