---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261117-A-MAGICAL-DEMONIC-ENTITY-BODY-DECLARES-A-SPECIES
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-MAGICAL-DEMONIC-ENTITY-BODY-DECLARES-A-SPECIES

## Title
A magical or demonic entity body declares a species, and `magical_demonic_entity` leaves the non-living allowlist

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
After M1 step 4, `EntityGenerator.spawn_magical_demonic_entity` still defaults `kind` to `magical_demonic_entity`, a value on the named non-living allowlist (rpg-designer Q1 ruling, 2026-11-17), because the path sits behind the OFF flag ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH (caller `src/world/calamity.py`). The same class as the world boss ticket.

Drafted by rpg-implementer-2 on the M1 step-4 branch (rpg-m1-kind-step4) for rpg-planner's review, as rpg-designer 3045e98a (and the Q1 ruling) require. Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

## Scope
1. Declare the entity's species in content, so `kind` is a species id.
2. Spawn it with that species (occupation stays None).
3. Remove `magical_demonic_entity` from NON_LIVING_KIND_ALLOWLIST.

## Out of Scope
- Changing what any decision does with the body. This is a declaration of the species, not a rebalance.

## Acceptance Criteria
- The spawn writes a species id as `kind`.
- `magical_demonic_entity` is no longer on the allowlist.
- Tests for the spawn with ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH ON.

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
