---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261118-UNDEAD-RAISED-BY-A-DARK-MAGIC-CASTER
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-UNDEAD-RAISED-BY-A-DARK-MAGIC-CASTER

## Title
No caster can raise undead; necromancy over a corpse is permitted by STR-01 but has no mechanism

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

No necromancy or dark-magic mechanism exists in src or content; MAG-S23 records it as "Confirmed MISSING — no necromancy mechanism exists". STR-01 permits a declared "necromancy over a corpse creating a new undead subject", and STR-02 requires the result to be a new subject.

## Scope
- Rule work first. rpg-designer and rpg-designer-ubuntu decide who can cast, what it costs, what the source is (a corpse, or another declared source), and the new subject's identity and faction under STR-02.
- Then the action, its typed records and its HARD rows, reusing the M1 RISEN spawn source and its conservation rows where they fit.

## Out of Scope
- Any M1 item, including the M1 corpse-rises origin.
- A graveyard place (TCK-20261118-UNDEAD-RISE-AT-A-GRAVEYARD-PLACE).
- Rates and balance.

## Acceptance Criteria
- A declared caster action raises a new undead subject from a named source, through the authoritative apply path, with conservation and identity rows pinned by tests.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261118-BIRTHS-BALANCING-PASS

## Related Docs
- docs/world_rules/magic-supernatural/supernatural-transformation.md (STR-01, STR-02)
- docs/world_rules/scenarios/magic-supernatural-batch-12.md (MAG-S23)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_risen_origin_design_2026-11-18.md

## Related Code Areas
src/world/, src/engine/, data/content/

## Assumptions / Open Questions
None yet.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
