---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261124-A-CROWDED-PLACE-HAS-A-REAL-QUEUE
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-A-CROWDED-PLACE-HAS-A-REAL-QUEUE

## Title
A crowded place keeps a real queue: order and places in line, not only a recheck

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner direction #715 7130838054 (2): crowding around a free tile is 'like a queue'. #996 implements only the OCCUPIED wait (recheck every occupied_review_delay); the real queue is deferred by the owner's scope freeze 7132422805 and ruling 476631fe.

## Scope
1. A place with more takers than room keeps a queue: who waits, in what order.
2. A waiter's turn comes in order, so nobody waits for as long as its plan lasts while others cycle in.
3. Designer proposes the model to the owner before code.

## Out of Scope
- The OCCUPIED wait itself (done in #996).

## Acceptance Criteria
1. Owner approval of the model recorded on #715.
2. A crowded-spot scene where every waiter gets a turn within a bounded time (with a failing control).
3. Measured band ticks per subject compare with main's turn-taking.

## Related Tickets
- TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON (#996)
- TCK-20261124-A-WAITING-BODY-TRIES-ANOTHER-PLACE

## Related Docs
- docs/plans/systemic_world/experience_memory_design.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- src/engine/movement.py, src/core/navigation_experience.py

## Assumptions / Open Questions
- Filed under the owner's scope freeze (#715 7132422805): a follow-up, not part of the PR it came from.

## Durable state, lifecycle and clocks
To be set at planning.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
