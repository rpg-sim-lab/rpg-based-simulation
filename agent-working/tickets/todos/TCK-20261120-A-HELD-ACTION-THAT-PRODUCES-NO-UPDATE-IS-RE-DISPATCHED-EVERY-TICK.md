---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261120-A-HELD-ACTION-THAT-PRODUCES-NO-UPDATE-IS-RE-DISPATCHED-EVERY-TICK
phase: open
date: 2026-11-20
tags: []
---

# TCK-20261120-A-HELD-ACTION-THAT-PRODUCES-NO-UPDATE-IS-RE-DISPATCHED-EVERY-TICK

## Title
A held ENTITY_ACT whose actor produces no update (NO_ACTION_UPDATE) is never ended, so the scheduler may re-dispatch the same do-nothing action every tick

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by rpg-implementer's trace for #781's forced-60 LOOP (inspected at 2556ecac5, 2026-11-20); filed by rpg-planner on rpg-designer's ruling.
- A held action with no update gets outcome FAILURE / NO_ACTION_UPDATE (src/engine/pipeline_phases/actions.py:299).
- That reason is in neither end table: not in _UNRECOVERABLE_ANY_ACTION_REASONS (actions.py:25-28), and not in _ENDS_HELD_REASONS_BY_ACTION (actions.py:47).
- The task keeps a non-empty payload. The scheduler (scheduler.py about :131-146) then treats it as a plain ENTITY_ACT, never a brain item. This is the same never-exit pattern as the EAT case #781 fixes.
- It has not been seen in a run, and it is not known whether any shipped action path returns no update for a held task.

## Scope
1. A probe, executed, over the shipped action paths: does any held ENTITY_ACT produce no update? This stays report-only until the probe shows a real path. Its own S9 if a kernel run is needed.
2. If a real path exists, the fix follows the same table pattern (an end entry for that action or reason), with a test, and rpg-designer rules the reason set.

## Out of Scope
- #781 (D73), which adds the EAT entry.
- The scheduler's wake list.

## Acceptance Criteria
- A probe result: either no shipped path produces NO_ACTION_UPDATE for a held task (the ticket then closes, with that evidence), or the named paths are ended with tests.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781, the EAT entry; where this was found)

## Related Docs
- docs/engine/kernel.md (the actions phase)

## Related Stored Artifacts
- /mnt/data2/rpg-wt/freemeal-logs/forced_broke_control_v2_60.json (the EAT case)

## Related Code Areas
- src/engine/pipeline_phases/actions.py; src/engine/scheduler.py; src/engine/action_router.py

## Assumptions / Open Questions
- Whether NO_ACTION_UPDATE is ever transient (an action that legitimately produces nothing this tick and succeeds later).

## Durable state, lifecycle and clocks
The task record is durable. A fix ends it through the existing typed path, with no new field.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
