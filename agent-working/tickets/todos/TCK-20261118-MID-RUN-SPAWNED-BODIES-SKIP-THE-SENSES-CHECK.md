---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK

## Title
Bodies spawned mid-run by EntityGenerator (heroes, monsters, offspring, demonic entities) skip PERC-02a's senses check; lairs, bosses and calamities run in M1 cells

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
PERC-02a's law (Bible ch. 04, divergence 2.210, STRAT-352): at build, on every path, a body's sense profile is its species' sense_profile, and a species with no usable profile is refused with a typed SenseProfileError.

The five EntityGenerator spawn paths in src/systems/world_systems/generator.py on main 346c2dc78 build bodies with V2EntityBuilder and run NO check (rpg-designer's site list; lead-planner-u24 found it, inspected):
- spawn_hero :140
- spawn_monster :166
- spawn_natural_creature_offspring :205
- spawn_magical_demonic_entity :239
- spawn_humanoid_offspring :285

The mid-run callers include creature_territory.py:65 (lairs), boss.py:148 and :260, calamity.py:63 and :82, and certification/scenarios.py:74. These run in M1 cells.

A species spawned mid-run need not be in the compiled population, so nothing checks it. An unprofiled one goes blind, and the gate logs ERROR on every read. Empty logging_errors is an M1 HARD bar.

Split from TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK because this part is stricter: rpg-designer set it to P1, HARD before the Phase-3 measurement.

## Scope
1. A build-time check in each of the five spawn_* paths: require_species_sense_profile(species, where="EntityGenerator.<name>"), or the shared checked-build helper if the sibling ticket lands one first. This is the law, and it stays as the backstop.
2. A CONTENT-LOAD check over every species that spawner content can name: generator spawn tables, lair, boss and calamity content, and the offspring species. It refuses an unprofiled species before any tick. A spawn-time check alone would move the raise mid-run, which is a crash (rpg-designer).
3. Covered by the sibling ticket's source-scan test: these five sites must call the check, never be allowlisted.
4. Docs: the Bible ch. 04 and 2.210 path list gains "mid-run spawners"; STRAT-352's v2_evidence cites the new tests; the known_limitations §1.3 line drops this path when the ticket closes.

## Out of Scope
- The campaign, scenario-runner and restore paths (the sibling ticket).
- Births' newborn_archetype content-load check: rpg-designer ruled (A'), on the births branch.
- Changing which species spawn, or spawn rates.

## Acceptance Criteria
- Each spawn_* path refuses an unprofiled species at build with SenseProfileError, naming the site. A profiled species spawns exactly as before.
- The content-load check refuses spawner content naming an unprofiled species, before any tick, and accepts all committed content.
- On every committed M1 gate world, a short run logs no sense-gate ERROR. This is the existing HARD bar; it is measured under an S9 record if it needs a kernel run.
- No existing test expectation changes. If one must change, that is an owner ask.
- Statics and targeted tests run after every src commit.
- The perf NFR rule: no measurable spawn-path regression. It's a single dict lookup; state that in the PR.

## Related Tickets
- TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK (the sibling; P2)
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (PERC-02a, done in #955)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (births: (A') covers newborn_archetype)
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/mechanics/04_strategic_cognition.md, docs/guidelines/intentional_divergences.md 2.210, docs/parity_ledger/strategic_cognition.yaml STRAT-352, docs/engine/known_limitations.md §1.3

## Related Stored Artifacts
- None.

## Related Code Areas
- src/systems/world_systems/generator.py (EntityGenerator)
- its callers: creature_territory.py, boss.py, calamity.py, certification/scenarios.py
- src/content/species_senses.py

## Durable state, lifecycle and clocks
No new durable state. The check reads the catalog's species sense_profile at content load and at spawn. No record, field or clock is added.

## Assumptions / Open Questions
- Whether every species committed spawner content can name is already profiled. If one isn't, the content-load check refuses committed content. Then a content fix comes first, and this ticket can't land green until it does. AGREED (rpg-designer): bring the designer the species and the file naming it; the designer rules the content fix (give it a profile, or remove or rename the reference) before the check lands. The check is NEVER loosened to let content through.
- KNOWN CONTENT ROWS (lane B, inspected, 2026-11-19, from the step-5 #965 trace): spawn_monster occupations bear, harpy and golem have NO entry in data/content/living/species.yaml. Only wolf (:30), spider (:81) and slime (:267) exist. Yet generator.py SPAWN_KIND_CATALOG_FACTION (:37-39) gives them wild_beast_pack. get_kind_properties returns (None, None) for them, so they are neither profiled nor wild. The content-load check will refuse them, so the designer rules the content fix first. slime has a species but amorphous_body `diet: []` (body_models.yaml:75); whether that is intended is with the designer.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
