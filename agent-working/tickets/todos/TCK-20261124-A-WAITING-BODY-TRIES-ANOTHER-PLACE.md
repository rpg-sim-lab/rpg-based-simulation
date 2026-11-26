---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261124-A-WAITING-BODY-TRIES-ANOTHER-PLACE
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-A-WAITING-BODY-TRIES-ANOTHER-PLACE

## Title
A body waiting on an occupied place can try another place that serves the same purpose

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Deferred from #996 by the owner's scope freeze (#715 7132422805). Under #996 a body whose place is OCCUPIED waits and rechecks; it never looks for another place serving the same purpose while it waits. The residual in ruling 476631fe: it can wait as long as its plan lasts if someone never leaves.

## Scope
1. While an OCCUPIED experience refuses a place, the strategic layer may choose another known place for the same purpose.
2. Places come from the subject's own knowledge (no remote look).
3. Designer proposes the rule to the owner before code.

## Out of Scope
- The real queue (TCK-20261124-A-CROWDED-PLACE-HAS-A-REAL-QUEUE).

## Acceptance Criteria
1. Owner approval recorded on #715.
2. A test where a second known place is taken while the first is occupied, with a failing control where none is known.

## Related Tickets
- TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON (#996)
- TCK-20261124-A-CROWDED-PLACE-HAS-A-REAL-QUEUE
- TCK-20261121-TWO-ANCHOR-TILES-ARE-GIVEN-UP-ON-BY-MANY-SUBJECTS-FOR-THOUSANDS-OF-TICKS (D6)

## Related Docs
- docs/plans/systemic_world/experience_memory_design.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- src/strategy/, src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Filed under the owner's scope freeze (#715 7132422805): a follow-up, not part of the PR it came from.

## Durable state, lifecycle and clocks
To be set at planning.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
