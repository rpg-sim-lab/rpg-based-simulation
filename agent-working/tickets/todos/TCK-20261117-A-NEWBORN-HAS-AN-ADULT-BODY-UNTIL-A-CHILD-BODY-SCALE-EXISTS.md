---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS

## Title
A newborn is built with its species' adult body stats because no CHILD body scale exists

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
This is a backlog item and not part of M1. rpg-designer-ubuntu's births rulings v2, Q11, build a newborn through the same species/archetype path as a t0 body. `src/` has no CHILD body scale (life_stage.py holds only goal multipliers), so a newborn gets the species' t0 stats at full HP. The births step discloses this. Adding a CHILD body scale is a new mechanic and is filed here as backlog.

## Scope
- Rule work first, owned by rpg-designer: how a CHILD body scales by life stage, and how it grows into an adult body.
- Then the content declaration and the body-building path.

## Out of Scope
- Any M1 item.

## Acceptance Criteria
- A newborn's body stats follow a declared CHILD scale and reach adult values by the normal LifeStage clock.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND

## Related Docs
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_v2_2026-11-17.md (Q11)

## Related Code Areas
src/ai/life_stage.py, src/core/state.py (LifeStage), the archetype/body builder

## Assumptions / Open Questions
None yet.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
