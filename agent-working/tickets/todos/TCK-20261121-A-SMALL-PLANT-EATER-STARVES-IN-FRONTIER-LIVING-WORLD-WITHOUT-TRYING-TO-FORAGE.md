---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE

## Title
A small_plant_eater (entity 55) in frontier_living_world seed 42 starves at t4745 without ever trying FORAGE (gate V3, SURV-06/07, H6)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The rpg gate re-record run 44887314422 (main 85770a225) shows one V3 validity violation on frontier_living_world s42: entity 55, kind small_plant_eater, starves at t4745 with FORAGE untried (SURV-06/07, gate H6). Reported by testing-planner via lead-planner-u24 (#715 7062288026, correction 7062295489). It predates #988: identical in run 44750897157 (c540a0b17), and unowned since 44544845745. No ticket owned it: TCK-20261023 (#781) cites it only as base context. rpg_gate_candidate correctly refuses to build the REBASELINE from that run while the row is unowned. This ticket owns it, behind a scoped known entry (the #839 precedent) that the owner accepts.

Lineage (relayed by the ubuntu lead, who verified it; not re-checked by rpg-planner): the row is identical in every gate run from 3fc6d263a to 85770a225, and run 414fb74f7 has no e55 row. Done ticket TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN calls it "#955's V3 flw/42 e55" (#955 = 346c2dc78, PERC-02a species senses). So it most likely arrived with #955. Nobody has bisected it. The births head d3401ba43 shows 0 V3 on flw/42, but births changes the trajectory, so that is not a fix.

Why a known entry is allowed again: #948 (bb26e4e5f) removed all seven V3 known entries because they no longer failed at M1-base 9c398a068 (gate run 43840618903, rpg-designer ruling). That was a tightening, not a rule against owning a V3 row.

#781 is not expected to fix it (inspected, not executed): #781 removes the free meal at the inn, and divergence 2.119 limits building services to kinds that trade, so a plant eater never reaches that path. #781 moves every hash, so the row may shift by chance; that would not be a fix.

## Scope
1. Bisect the row's arrival between 414fb74f7 and 3fc6d263a (#955 first), from the kept gate reports where they suffice. Then trace e55 on frontier_living_world s42, 5000 ticks, at main (its own S9): its hunger, the forage and graze nodes it could see or knew, every goal and project it held in the last 1000 ticks before death, and why FORAGE never ran.
2. Name the cause with file:line evidence, then either fix it with a test, or file the fix ticket and record a verdict here.
3. At the known entry's expires_on: retire the entry (the row is gone with evidence), or renew it once with evidence and a new date.

## Out of Scope
- #781 (D73 / SEEK_WORK) and the free meal.
- Editing a gate, a threshold or the V3 check.

## Acceptance Criteria
1. The cause of e55's death is recorded, labelled inspected or executed.
2. A fix with a test lands, or a fix ticket is filed and cited here.
3. The scoped known entry for V3 frontier_living_world s42 e55 is retired, or renewed with evidence, by its expires_on.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781; cites the row as base context only)
- TCK-20261107-THREE-CROWDED-V3-STARVATIONS-GET-SCOPED-KNOWN-ENTRIES (#839 precedent)
- TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN (names the row as #955's)
- TCK-20261116-RE-BASELINE-THE-RPG-GATE-REFERENCE-TO-A-MAIN-RUN-AFTER-M1-BASE (#948, removed the earlier V3 entries)
- TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50
- TCK-20261010-WILD-LAND-CARRIES-PLANT-COVER-AND-FORAGE-DECLARED-PER-BIOME-GRAZING-D59

## Related Docs
- docs/mechanics/01_entity_anatomy.md (biological pressures), docs/mechanics/04_strategic_cognition.md (goal hierarchy)
- docs/guidelines/intentional_divergences.md 2.91, 2.119

## Related Stored Artifacts
None yet. Gate runs 44887314422, 44750897157 and 44544845745 (report docs kept by testing-planner).

## Related Code Areas
- #955 346c2dc78 (PERC-02a species senses): the likely arrival
- src/ai/goals/scorers.py (graze/forage scoring), src/systems/strategic_systems/intelligence.py
- tools/test_architecture/rpg_gate_known.yaml (the scoped known entry)

## Assumptions / Open Questions
- Whether other plant eaters share the cause; the gate shows only e55.

## Durable state, lifecycle and clocks
None expected until the cause is known.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
