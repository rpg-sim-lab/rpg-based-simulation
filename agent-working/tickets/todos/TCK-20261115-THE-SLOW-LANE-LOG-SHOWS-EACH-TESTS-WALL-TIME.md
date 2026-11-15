---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261115-THE-SLOW-LANE-LOG-SHOWS-EACH-TESTS-WALL-TIME
phase: open
date: 2026-11-15
tags: [testing]
---

# TCK-20261115-THE-SLOW-LANE-LOG-SHOWS-EACH-TESTS-WALL-TIME

## Title
The slow-regression log shows each slow test's wall time, so a "under 540 s" rule can be checked from CI

## Status
OPEN (rides digest-light; owner go #715 6890063899 item 1b)

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
#837 requires each long test to finish under 540 s, and the distributed-workers design §8 requires a slow-lane sibling test with a measured wall time under 540 s. The slow job prints no per-test durations, so neither rule can be checked from a CI run. This is the cheapest fix testing-planner proposed when #837 was reviewed.

## Scope
- In `.github/workflows/slow-regression.yml`, add `--durations=30` to the `pytest tests/ -m "slow or extra_slow" ...` line. Change nothing else.
- Update the workflow shape test if it pins that line (`tests/static/test_ci_*slow*`).

## Out of Scope
- Any wall-time gate or threshold. This only reports durations.

## Acceptance Criteria
1. The pytest line carries `--durations=30`, and the static workflow tests pass.
2. After merge, the next scheduled slow-regression run's log shows the "slowest 30 durations" block. testing-planner checks this post-merge.

## Related Tickets
- TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS (#837, the 540 s rule)

## Related Docs
- docs/plans/architecture/distributed_workers_experiment_design.md §8

## Related Stored Artifacts

## Related Code Areas
- .github/workflows/slow-regression.yml

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
