---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-STRATEGIC-INTENT-AND-BANDWIDTH-PASSES-COST-1-TO-3-PERCENT-EACH
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-STRATEGIC-INTENT-AND-BANDWIDTH-PASSES-COST-1-TO-3-PERCENT-EACH

## Title
evaluate_strategic_intent_with_expiry and enforce_bandwidth cost 1-3 % of the tick each

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`intelligence.py:1282` is 3.3 to 3.9 % and `detour.py:212, 247` 1.2 to 2.6 % of the tick (section 10.2). Legitimate work per entity; waste not shown.

Found by `TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS` (profile of main `99a83adc9`, loaded host, PROVISIONAL shares). A backlog entry: no implementation without the normal review and approval; the src ticket goes to rpg-planner on u24 through lead-planner before the owner (#715 6968328816).

## Scope
Backlog and measurement only (rpg-planner via lead). Reopen if either grows past 5 % of a tick after items 1-3.

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
