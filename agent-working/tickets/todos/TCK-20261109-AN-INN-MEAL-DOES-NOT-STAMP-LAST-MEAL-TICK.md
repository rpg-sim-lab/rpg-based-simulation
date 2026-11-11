---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261109-AN-INN-MEAL-DOES-NOT-STAMP-LAST-MEAL-TICK
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-AN-INN-MEAL-DOES-NOT-STAMP-LAST-MEAL-TICK

## Title
An inn meal lowers hunger but does not stamp biological.last_meal_tick, which the other three meal writers do

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by rpg-implementer on 2026-11-09 while naming the meal writers for TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT. Of the four paths that lower hunger, three set `last_meal_tick_set` (carried_meal, the free meal in eat_update, corpse_meal: src/engine/domain/core_actions.py:54, :67, :89). The inn meal (`service_delta`, src/engine/building_services.py:80) sets only `hunger_delta=-INN_MEAL_HUNGER`, so the authoritative field is not stamped by it. No reader was found in the survey for the recorder ticket.

## Scope
1. Confirm there is no reader of `biological.last_meal_tick`: src, tools, API and presenters, tests, `checkpoint_fields`, and the canonical state digest (state.py:150 emits it, so it is in the digest).
2. Choose, with the simpler one preferred (owner's cost rule): stamp it at the inn writer, or retire the field. Either moves hashes, because the field is in the digest.
3. Measurement rides with the next behaviour batch. No code in this ticket until dispatched.

## Out of Scope
- The starvation recorder, which keys on the hunger drop and does not read this field.

## Acceptance Criteria
- The reader survey is written down.
- The choice is made and recorded; if stamped, a test that an inn meal stamps the tick; if retired, the checkpoint rule for old checkpoints.
- The hash movement is measured in a behaviour batch (it is not behaviour-neutral).

## Related Tickets
- TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-04: last_meal_tick and last_sleep_tick described as written and unread)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/engine/building_services.py (service_delta)
- src/engine/domain/core_actions.py
- src/core/state.py (BiologicalComponent)

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes
Not started.

## Test Summary

## Files Changed

## Completion Summary
