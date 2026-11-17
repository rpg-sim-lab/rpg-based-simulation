---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261117-A-WORLD-BOSS-BODY-DECLARES-A-SPECIES
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-WORLD-BOSS-BODY-DECLARES-A-SPECIES

## Title
A world boss body declares a species, and `world_boss` leaves the non-living allowlist

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
After M1 step 4, the calamity and lair boss spawns write `kind` = `world_boss`, a value on the named non-living allowlist (`src/core/species.py::NON_LIVING_KIND_ALLOWLIST`), with `occupation` = `world_boss` (or `ancient_sentinel`). The feature is OFF by default (ENABLE_WORLD_BOSS_SPAWN), so no gate run reaches it. Filed under the calamity backlog (agent-working/tickets/backlogs/epic-20-calamity-system.md).

Drafted by rpg-implementer-2 on the M1 step-4 branch (rpg-m1-kind-step4) for rpg-planner's review, as rpg-designer 3045e98a (and the Q1 ruling) require. Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

## Scope
1. Declare the boss body's species in content (data/content/living/species.yaml or a declared mapping), so `kind` is a species id.
2. Spawn it with that species and keep `occupation` = `world_boss` / `ancient_sentinel`.
3. Remove `world_boss` from NON_LIVING_KIND_ALLOWLIST.

## Out of Scope
- Changing what any decision does with the body. This is a declaration of the species, not a rebalance.

## Acceptance Criteria
- A world boss spawn writes a species id as `kind`.
- `world_boss` is no longer on the allowlist; the K6 static test passes with no entry for it.
- Tests for the spawn with ENABLE_WORLD_BOSS_SPAWN ON.

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
None yet.

## Test Summary

## Files Changed

## Completion Summary
