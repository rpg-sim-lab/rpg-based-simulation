---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-MULTI-RUN-INDEX-FLOW-HEALTH-SCORE-DEPENDS-ON-HOST-TICK-SPEED
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-MULTI-RUN-INDEX-FLOW-HEALTH-SCORE-DEPENDS-ON-HOST-TICK-SPEED

## Title
test_multi_run_index_and_cli_flow fails on a loaded host: one HighCPULatencyRule WARNING scores a run 95, not 100

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Reported by agent-working-planner-u24 on 2026-11-15. tests/integration/observability/test_multi_run_index_flow.py::test_multi_run_index_and_cli_flow failed CI Integration on PR #917, which changes no src/, with `assert 95.0 == 100.0`. It reproduced locally 3 of 3 times at a9c1bd9ca. Seed 10's run_report.json has one HighCPULatencyRule WARNING ("average 57.65 ms exceeds 50ms limit"), so its health_score is 95. Main passed it at 5ba65854c, so the failure depends on host load. The cause is the same wall-clock dependency that TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100 fixed in the two baseline flow tests. This sibling test was missed.

## Scope
- Pin the tick compute cost in test_multi_run_index_and_cli_flow with the existing `tick_cost_ms` fixture (tests/integration/observability/conftest.py, which patches LiveSignalSource.tick_end_signals). Use the same 5 ms the baseline flow tests use.
- Leave the health_score assertions (:38, :40, :47, :88) unchanged.
- Check the rest of tests/integration/observability/ for any other flow test that asserts a health score without the fixture, and fix it the same way.

## Out of Scope
- Any src/ change, including the HighCPULatencyRule threshold or the health-score formula.

## Acceptance Criteria
- The test passes on a loaded host (2 of 2 runs, with the host busy), where it fails today.
- No other flow test in that directory still asserts a health score without the fixture.
- No src/ change.

## Related Tickets
- TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100 (same cause; its fixture is reused here)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tests/integration/observability/test_multi_run_index_flow.py:38-47, :88
- tests/integration/observability/conftest.py (tick_cost_ms)

## Assumptions / Open Questions
- Assumes the seed-10 WARNING is the only thing that makes the health score fall below 100, as it was in the baseline tests. If the fixture does not bring the score to 100, stop and report.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
