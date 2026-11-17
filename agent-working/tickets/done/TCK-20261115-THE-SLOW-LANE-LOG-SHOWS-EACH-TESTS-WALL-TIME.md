---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261115-THE-SLOW-LANE-LOG-SHOWS-EACH-TESTS-WALL-TIME
phase: done
date: 2026-11-15
tags: [testing]
---

# TCK-20261115-THE-SLOW-LANE-LOG-SHOWS-EACH-TESTS-WALL-TIME

## Title
The slow-regression log shows each slow test's wall time, so a "under 540 s" rule can be checked from CI

## Status
DONE

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
`--durations=30` added to the one pytest line of `.github/workflows/slow-regression.yml` (line 111); nothing else changed. No static test pins that line, so none needed an update.

## Test Summary
tests/static/test_ci_slow_workflow_shape.py, test_corpus_diversity_ci_isolation.py, test_workflow_run_blocks_take_github_context_via_env.py, tests/tools/test_ci_workflow_test_coverage.py, test_ci_split_tools_jobs.py, test_delivery_ci_lanes.py, tests/unit/tools/test_slow_regression_report.py, test_impact_report.py, test_rpg_gate_workflow_support.py: 221 passed.

## Files Changed
.github/workflows/slow-regression.yml

## Completion Summary
The slow lane's pytest line carries `--durations=30`. AC1 met. AC2 (the next scheduled run's log shows the slowest-30 block) is testing-planner's post-merge check.
