---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-NEAREST-TOWN-TILE-SCANS-EVERY-TOWN-TILE-PER-ENTITY
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-NEAREST-TOWN-TILE-SCANS-EVERY-TOWN-TILE-PER-ENTITY

## Title
nearest_town_tile scans every town tile per entity every tick (8-18 % of the tick)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`src/systems/strategic_systems/town_targeting.py:16-20` runs `min()` with a Python lambda key over all `state.town_tiles` once per entity (callers `intelligence.py:397, :674`, `redirection.py:138`). It is 8.2 to 17.6 % of the tick (key lambda 4.8 to 11.9 %) on the three gate worlds, 39 to 62 % of `fused_strategic_pass` (section 10.2). Expected saving 6 to 15 % of the tick.

Found by `TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS` (profile of main `99a83adc9`, loaded host, PROVISIONAL shares). A backlog entry: no implementation without the normal review and approval; the src ticket goes to rpg-planner on u24 through lead-planner before the owner (#715 6968328816).

## Scope
Sequencing (rpg-planner via lead): subsumed by M1 "Places are found from perception and memory", which carries a perf budget. Do not build a separate structure first. The ticket's job is to hand that M1 item its budget: nearest-tile answer must keep the `(distance, x, y)` tie-break and exact replay; add a parity test against the current function.

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
