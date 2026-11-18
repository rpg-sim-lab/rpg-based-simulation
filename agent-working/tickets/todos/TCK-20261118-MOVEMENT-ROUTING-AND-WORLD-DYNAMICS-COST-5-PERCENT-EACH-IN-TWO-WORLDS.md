---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-MOVEMENT-ROUTING-AND-WORLD-DYNAMICS-COST-5-PERCENT-EACH-IN-TWO-WORLDS
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-MOVEMENT-ROUTING-AND-WORLD-DYNAMICS-COST-5-PERCENT-EACH-IN-TWO-WORLDS

## Title
movement_routing (2.7-5.6 %) and world_dynamics (5.0-5.7 %) are untimed Resolution children not yet looked into

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`pipeline.py:301` and `:344` are untimed `run_phase` children of Resolution, so they sit in `resolution_overhead`; shares 2.7 to 5.6 % and 5.0 to 5.7 % on `urban_political`, `frontier_living_world`, `crowded_frontier` (section 10.2). Not attributed below the phase.

Found by `TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS` (profile of main `99a83adc9`, loaded host, PROVISIONAL shares). A backlog entry: no implementation without the normal review and approval; the src ticket goes to rpg-planner on u24 through lead-planner before the owner (#715 6968328816).

## Scope
Backlog and measurement only. One py-spy callee split per phase, on a quiet host, before any fix ticket.

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
