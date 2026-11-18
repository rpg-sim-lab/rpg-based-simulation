---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-NEARBY-ENTITIES-QUERY-HAS-NO-SPATIAL-INDEX
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-NEARBY-ENTITIES-QUERY-HAS-NO-SPATIAL-INDEX

## Title
nearby_entities is a linear neighbourhood scan with no spatial index (combat_engagement is 60 % of the tick at 500 entities)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`src/engine/spatial_query.py:59-60` is 3.8 to 4.7 % self time at corpus size and drives `combat_engagement` to 60 % of the `movement_500` tick (section 10.4). Whether it dominates at 400 to 500 entities is not attributed yet: a py-spy run at `mixed` 400 is owed (births slot).

Found by `TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS` (profile of main `99a83adc9`, loaded host, PROVISIONAL shares). A backlog entry: no implementation without the normal review and approval; the src ticket goes to rpg-planner on u24 through lead-planner before the owner (#715 6968328816).

## Scope
Sequencing: after PERC-02b, with a perf budget there (rpg-planner via lead). Measure first; the index must return the same neighbours in the same order.

## Out of Scope
Any change to determinism, exact replay or the per-tick commit sort (`kernel.py:593`). Any perf target (waits for a quiet-host baseline).

## Acceptance Criteria
- Sized on a quiet host before and after, with the denominators of `docs/engine/performance_contract.md`.
- Committed state and replay hashes unchanged.

## Related Tickets
TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS, TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION

## Related Docs
docs/performance/tick_cost_growth.md section 10

## Related Stored Artifacts
None.

## Related Code Areas
See the request summary.

## Assumptions / Open Questions
Shares come from one py-spy run per world on a loaded host (about 1 point of noise).

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
