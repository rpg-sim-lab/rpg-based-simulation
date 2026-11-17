---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261101-SLOW-KNOWN-REDS-PERF-PAUSE-REWORD
phase: done
date: 2026-11-01
tags: [testing]
---

# TCK-20261101-SLOW-KNOWN-REDS-PERF-PAUSE-REWORD

## Title
Five perf known-reds entries move to perf-planner's parking ticket and name the pause, and catalog_arena_smoke is reclassified flaky

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Five slow_known_reds entries cited a closed ticket and a stale owner. The owner chose "Reword, skip arena smoke" (#715 6556925036): perf-planner writes reasons naming the pause, testing-planner edits the file. Separately, rpg-planner's quiet-host retest of catalog_arena_smoke passed 4 of 4 and it asked for the entry to become flaky.

## Scope
- tests.perf movement, passive_scaling, strategic and combat, and arena_stress_50v50: ticket TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE, owner perf-planner, note from that ticket's Reason Text. expires_on, added_on and kind unchanged.
- catalog_arena_smoke: kind flaky, owner rpg-planner, expires_on 2026-12-31, rpg-planner's note. Ticket unchanged.

## Out of Scope
- Any test, threshold or src change.
- Naming arena_stress_50v50's failing check: the parking ticket's AC.
- The other entries, and a lint for entries citing closed tickets.

## Acceptance Criteria
- [x] AC1: the six entries read as above; no other entry changes.
- [x] AC2: the registry lint tests pass.

## Related Tickets
TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE, TCK-20261019-CATALOG-ARENA-SMOKE-TICK-3-BUDGET-OVERRUN-AFTER-645, TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP

## Related Docs
None

## Related Stored Artifacts
None

## Related Code Areas
tools/test_architecture/slow_known_reds.yaml

## Assumptions / Open Questions
catalog_arena_smoke's flaky reading rests on one quiet-host retest and one CI failure; a recurrence reopens it. arena_stress_50v50 stays cause not attributed, and could be a real bug.

## Implementation Notes
Note text taken as written from the parking ticket and from rpg-planner.

## Test Summary
tests/unit/tools/test_slow_regression_report.py and test_known_reds.py.

## Files Changed
tools/test_architecture/slow_known_reds.yaml

## Completion Summary
Entries repointed and reworded. These tests stay red when they fail; only the ownership and reasons change.
