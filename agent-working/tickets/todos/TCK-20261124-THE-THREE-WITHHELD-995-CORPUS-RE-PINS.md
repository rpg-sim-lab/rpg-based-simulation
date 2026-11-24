---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261124-THE-THREE-WITHHELD-995-CORPUS-RE-PINS
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-THE-THREE-WITHHELD-995-CORPUS-RE-PINS

## Title
The three corpus re-pins withheld from #995 (urban SOCIAL, hero COGNITION, unit ECONOMY) are re-pinned once guard (ii) is clean

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Deferred outside #995 by the owner's scope freeze (#715 7132422805). The three slow corpus re-pins (urban SOCIAL, hero COGNITION, unit ECONOMY) stay withheld until guard (ii) is clean, as recorded in rpg-planner's handover. The W read (7090280198) failed P2 urban, so there is no guard (ii) yet.

## Scope
1. After #995 and #996 merge, re-measure guard (ii) on main.
2. If it is clean, re-pin the three rows with the owner's yes (a changed expectation), one owner ask covering all three.

## Out of Scope
- Any other corpus pin.

## Acceptance Criteria
1. Guard (ii) is clean, recorded with its run S9.
2. The owner's yes is recorded on #715, and the three pins match the measured values.

## Related Tickets
- #995 (rpg-free-meal-atomic)
- TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN

## Related Docs
- docs/simulation_quality/ (corpus grades)

## Related Stored Artifacts
- none yet

## Related Code Areas
- tests/ corpus diversity pins (exact ids recorded by lane A at planning)

## Assumptions / Open Questions
- The exact test ids and the guard (ii) definition are confirmed with lane A at planning.

## Durable state, lifecycle and clocks
No durable state.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
