---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261125-THE-STALEMATE-WANDER-FAMILY-LEFT-AFTER-996-COUNTS-TEST-AND-PAIRED-RUN
phase: open
date: 2026-11-25
tags: [cognition]
---

# TCK-20261125-THE-STALEMATE-WANDER-FAMILY-LEFT-AFTER-996-COUNTS-TEST-AND-PAIRED-RUN

## Title
What F1 left unmeasured after #996: the stalemate/wander counts table, a test for the s44 p1 shape, and an F1 paired run.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
A follow-up split from TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (F1), which closed on 2026-11-25 as LANDED CODE (#996), not as a measured cure. Owner ruling #715 7157496515 Q2; rpg-designer's classification #715 7157686023 (recorded as 7157730160). Filed by rpg-planner into the cognition-rework backlog. NOT HARD, and outside systemic_foundation (M1).
- #996's lifecycle read left the lifecycle world NOT GONE on seed 42; the owner accepted the 10-seed spread.

## Scope
1. A counts table: main vs the D73 shape, 3 gate worlds × s42-46 × 5,000 t, by stall trigger and target type.
2. A test for the s44 p1 shape: a project move replaced by a wander every tick while the nav reports no failure.
3. An F1-specific paired run under its own S9.

## Out of Scope
- Any change to #996's landed code unless (1) shows a HARD class (a state that never exits), which comes to rpg-planner for an owner ruling.

## Acceptance Criteria
- The counts table is recorded, with the test named and passing (or failing as a strict xfail with this ticket), and a paired run read by rpg-designer.

## Related Tickets
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (parent, done)
- overlap scan: not run yet; run it at dispatch.

## Related Docs
- docs/guidelines/intentional_divergences.md 2.213

## Related Stored Artifacts
- None yet.

## Related Code Areas
- src/engine movement and nav (the oscillation replan ladder from #996)

## Assumptions / Open Questions
- It may be superseded by the owner's cognition rework.

## Durable state, lifecycle and clocks
- None new.

## Implementation Notes
- Not started.

## Test Summary
- None.

## Files Changed
- None.

## Completion Summary
- Open.
