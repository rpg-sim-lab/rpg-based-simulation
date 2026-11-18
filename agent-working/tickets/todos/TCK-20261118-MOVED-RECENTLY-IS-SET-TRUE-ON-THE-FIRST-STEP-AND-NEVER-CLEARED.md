---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261118-MOVED-RECENTLY-IS-SET-TRUE-ON-THE-FIRST-STEP-AND-NEVER-CLEARED
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-MOVED-RECENTLY-IS-SET-TRUE-ON-THE-FIRST-STEP-AND-NEVER-CLEARED

## Title
NavigationComponent.moved_recently becomes True on a body's first step and nothing ever sets it back, so it means "has ever moved"; retire it or give it a lifecycle

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during the PERC-02a (#955) test triage (rpg-implementer-4, 2026-11-18). rpg-planner verified it by grep on main dca5a8dbb and on the 02a branch, and rpg-designer confirmed it.
- Writers: movement.py (a yield, NavigationUpdate(moved_recently_set=True) at ~:127; a step at ~:406) and pipeline_phases/movement.py:~460. All of them write True.
- patches.py:~287 keeps the old value when the update carries None. Nothing writes False.
- Readers on main: the API state presenter (state_presenter.py:~184) only. PERC-02a briefly read it for its moving/still signal. rpg-designer ruled that 02a stops reading it and uses a new typed `last_moved_tick` with a moving window instead (02a, divergence 2.210).
So durable state that claims "moved recently" has no lifecycle (CLAUDE.md, Durable State Rule), and the presenter shows a value that is True for almost every body.

## Scope
1. List every reader after PERC-02a lands (expected: the presenter only).
2. Retire the field (drop it from NavigationComponent, its update field, the builder, the canonical dict and hash, and FIELD_RULES; the presenter shows last_moved_tick-derived data or nothing), OR give it a ruled lifecycle. rpg-planner decides with rpg-designer, and retiring is the default.
3. A checkpoint or hash change needs its own migration note and determinism re-check.

## Out of Scope
- The PERC-02a signal (uses last_moved_tick).

## Acceptance Criteria
- No durable field claims "recently" without a defined clear rule. A test pins whichever choice is made.

## Related Tickets
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (PERC-02a, where it was found)

## Related Docs
- docs/core/state.md (NavigationComponent)
- docs/mechanics/04_strategic_cognition.md (PERC-02 signals)

## Related Stored Artifacts
- none

## Related Code Areas
- src/core/state.py (NavigationComponent.moved_recently), src/core/updates.py (moved_recently_set), src/engine/patches.py, src/engine/movement.py, src/engine/pipeline_phases/movement.py, src/api/presenters/state_presenter.py

## Assumptions / Open Questions
- Whether the frontend reads moved_recently from the presenter output is unchecked.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
