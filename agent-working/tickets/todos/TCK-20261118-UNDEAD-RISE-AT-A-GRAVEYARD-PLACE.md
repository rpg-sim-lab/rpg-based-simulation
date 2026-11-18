---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261118-UNDEAD-RISE-AT-A-GRAVEYARD-PLACE
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-UNDEAD-RISE-AT-A-GRAVEYARD-PLACE

## Title
Undead can rise only from a fresh corpse; no graveyard-type place exists for them to rise at

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
This is owner backlog, not M1. The owner widened M1 births with one non-birth undead origin, and chose "Corpse only now" for it (Q-R5, logged on #715 and relayed by lead-planner, 2026-11-18). So M1 ships only "a corpse rises" (rpg-designer-ubuntu's risen-origin design). The owner's original words named "undead birth from corpse or dark magic or a cementary place"; this ticket keeps the deferred part.

No graveyard, cemetery, crypt or barrow place kind exists: PlaceKind is CITY/CAMP/NEST/LAIR/RUIN/DUNGEON/LANDMARK (src/core/state.py:349-357). The undead ground today is the RUIN place haunted_battlefield_ruin (data/content/world_modules/undead_battlefield.yaml).

## Scope
- Rule work first. rpg-designer and rpg-designer-ubuntu decide whether a graveyard is a new place kind or a declared trait of an existing one, and what rises there and from what. A grave is not a CorpseState, which lasts 100 ticks. The rule must name its source, so nothing rises from nothing (ECOL-06 and its risen sibling, ECOL-07).
- Then the content, the origin and its HARD rows, reusing the M1 RISEN spawn source where it fits.

## Out of Scope
- Any M1 item, including the M1 corpse-rises origin.
- A dark-magic caster (TCK-20261118-UNDEAD-RAISED-BY-A-DARK-MAGIC-CASTER).
- Rates and balance (TCK-20261118-BIRTHS-BALANCING-PASS).

## Acceptance Criteria
- A declared graveyard place exists in content, and an undead arrival there is a typed declared arrival with a named source and no spawn from nothing, pinned by tests.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261118-BIRTHS-BALANCING-PASS

## Related Docs
- docs/world_rules/magic-supernatural/supernatural-transformation.md (STR-01, STR-02)
- docs/world_rules/scenarios/magic-supernatural-batch-12.md (MAG-S23)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_risen_origin_design_2026-11-18.md

## Related Code Areas
src/core/state.py (PlaceKind), data/content/world_modules/, src/world/

## Assumptions / Open Questions
None yet.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
