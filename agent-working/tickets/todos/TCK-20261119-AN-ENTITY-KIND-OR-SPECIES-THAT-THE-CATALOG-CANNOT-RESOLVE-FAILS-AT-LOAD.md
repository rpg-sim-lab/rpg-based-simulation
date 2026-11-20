---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261119-AN-ENTITY-KIND-OR-SPECIES-THAT-THE-CATALOG-CANNOT-RESOLVE-FAILS-AT-LOAD
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-AN-ENTITY-KIND-OR-SPECIES-THAT-THE-CATALOG-CANNOT-RESOLVE-FAILS-AT-LOAD

## Title
A body whose kind is not a catalog species, or a species with no need_profile, fails at world load or compile with a typed error, instead of running silently on fallback needs

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
rpg-designer's rulings on #965 (M1 kind step 5), 2026-11-19, relayed and filed by rpg-planner.
- In #965, a body whose kind is not a catalog species gets needs from a FLAGGED INTERIM role fallback in biological_needs.profile_id_for, ruling (a2). Those hits are counted under their own key.
- A catalog species without a need_profile gets base rates, and is counted in unprofiled_need_counts.
- Production gate worlds are clean at t0 (K6). These checks are guards.
- The designer, on the second item: a species with no needs is already declarable (undead → undead_purpose, hunger/sleep "none"). So a missing need_profile is a content gap, not a design choice, by the same doctrine as CAT-NEED-001.

## Scope
1. A typed world-load or compile validation error when an entity's kind does not resolve to a catalog species. Runtime behaviour is unchanged: no crash mid-tick.
2. A CONTENT INVARIANT: every species in the catalog declares a need_profile. It is checked at catalog load as a validator error with its own CAT-NEED code, plus a content test over data/content/living/species.yaml.
3. Retire the #965 interim role-fallback branch once (1) is on and the context-less test paths are triaged. This is done with TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE item AC.
4. The base-rate branch for a catalog species without a profile stays as defensive behaviour, along with its named test double. It becomes unreachable once (2) is on.

## Out of Scope
- Changing any species' need profile or rates (balance).
- The test-fixture policy (kind = species + occupation, or an explicit need_profile_id). That is the step-4 fixture-policy P3 ticket.

## Acceptance Criteria
- Load or compile of a world with a non-catalog kind raises the typed error. A unit test covers it.
- A species without a need_profile fails catalog load with the CAT-NEED code. The content test is green on today's species.yaml (all 14 species declare one, inspected 2026-11-19).
- The gate worlds still load, hash-equal.
- No Bible change until this lands; the Bible line is written with it.

## Related Tickets
- TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD (#965, the interim)
- TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE (stage 4b, item AC)
- TCK-20261119-A-GENERATED-FRONTIER-WORLD-FALLS-BELOW-ITS-POPULATION-FLOOR-BY-TICK-800

## Related Docs
- docs/mechanics/01_entity_anatomy.md (biological pressures); the CAT-NEED-001 doctrine

## Related Stored Artifacts
- None.

## Related Code Areas
- src/engine/biological_needs.py (profile_id_for, unprofiled_need_counts, the interim counter); the species catalog loader; data/content/living/species.yaml, need_profiles.yaml

## Assumptions / Open Questions
- Where the kind check sits (world load or the compiler) is decided at dispatch. It must not break context-less test compiles before item AC triages them.

## Durable state, lifecycle and clocks
None. This is validation only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
