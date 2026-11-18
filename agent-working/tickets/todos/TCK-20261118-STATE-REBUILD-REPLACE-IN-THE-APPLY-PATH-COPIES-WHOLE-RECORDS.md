---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261118-STATE-REBUILD-REPLACE-IN-THE-APPLY-PATH-COPIES-WHOLE-RECORDS
phase: open
date: 2026-11-18
tags: [performance]
---

# TCK-20261118-STATE-REBUILD-REPLACE-IN-THE-APPLY-PATH-COPIES-WHOLE-RECORDS

## Title
The apply path rebuilds records through a field-by-field Python replace (apply_generation 10-13 % of the tick)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`apply_generation` > `build_plan` > `_compute_entity_changes` is 10 to 13 % of the tick. The local `replace` (`apply.py:8-27`) is 5.8 to 6.8 % inclusive and tests `str(field_def._field_type).upper()` per field per call; `dataclasses._replace` leaf frames bring the replace total to 16 to 17 %. Expected saving 4 to 8 % of the tick.

Found by `TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS` (profile of main `99a83adc9`, loaded host, PROVISIONAL shares). A backlog entry: no implementation without the normal review and approval; the src ticket goes to rpg-planner on u24 through lead-planner before the owner (#715 6968328816).

## Scope
Sequencing: after M1 Phase 1 (rpg-planner via lead). First step is a read-only call-site count (calls and fields per tick) to size the saving; the committed state must be identical (exact replay).

- Before any design (rpg-planner via lead): (1) the calls-per-tick and fields-per-call count; (2) proof that the per-field `str(field_def._field_type).upper()` test at `apply.py:8-27` is pure cost: what reads its result, and whether any field name or type relies on case.

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
