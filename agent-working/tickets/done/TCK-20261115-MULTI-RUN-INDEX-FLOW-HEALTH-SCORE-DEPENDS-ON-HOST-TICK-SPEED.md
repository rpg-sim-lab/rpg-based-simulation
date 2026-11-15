---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-MULTI-RUN-INDEX-FLOW-HEALTH-SCORE-DEPENDS-ON-HOST-TICK-SPEED
phase: done
date: 2026-11-15
tags: []
---

# TCK-20261115-MULTI-RUN-INDEX-FLOW-HEALTH-SCORE-DEPENDS-ON-HOST-TICK-SPEED

## Title
test_multi_run_index_and_cli_flow fails on a loaded host: one HighCPULatencyRule WARNING scores a run 95, not 100

## Status
DONE

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
Owner dispatch #715 6889025067. test_multi_run_index_and_cli_flow takes the `tick_cost_ms` fixture and pins 5.0 ms; the four health assertions are unchanged. Checked the rest of tests/integration/observability/: test_baseline_generation_flow and test_baseline_comparison_flow already use the fixture; test_sweep_execution_flow asserts no health; test_balance_envelope_comparison overwrites metric_windows and its health envelope is min 80, so 95 still passes; test_scenario_level_report_flow writes its own run_report.json; test_report_v2, test_run_report_generator and test_analysis_pipeline_flow build synthetic inputs, not timed runs. No other test needed the fixture.

## Test Summary
tests/integration/observability, single process, run twice: 127 passed, 5 skipped both times (187 s, 179 s). The fixture brought the score to 100. tests/architecture/test_no_name_switches_in_decision_paths.py: 58 passed. Not run on a deliberately loaded host: the fixture removes the wall-clock input.

## Files Changed
- tests/integration/observability/test_multi_run_index_flow.py

## Completion Summary
The multi-run index flow test no longer depends on host tick speed; no src/ change.
