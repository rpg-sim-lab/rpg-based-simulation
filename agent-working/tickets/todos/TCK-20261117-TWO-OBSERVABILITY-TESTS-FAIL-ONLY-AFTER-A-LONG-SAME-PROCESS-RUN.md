---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261117-TWO-OBSERVABILITY-TESTS-FAIL-ONLY-AFTER-A-LONG-SAME-PROCESS-RUN
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-TWO-OBSERVABILITY-TESTS-FAIL-ONLY-AFTER-A-LONG-SAME-PROCESS-RUN

## Title
Two tests in tests/unit/observability fail only late in one long `-n 1` process and pass alone; find the cause before calling it a state leak

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by lane C (rpg-implementer-3) during the blocker-churn fix's first local run (2026-11-17). The log is /mnt/data2/rpg-measure/blockerchurn/unit_run1.log: `-n 1`, 2113 tests in the lane's own list order, 8 failed, 6 of them explained by the churn fix. The other two:
1. `tests/unit/observability/test_death_ledger.py::test_the_ledger_reads_the_states_and_writes_nothing_back`: `assert {'meat+plant+prepared|COMBAT': 1, 'meat+plant+prepared|HAZARD': 2} == {}`.
2. `tests/unit/observability/test_live_anomaly_worker.py::test_worker_lifecycle_in_process`: `assert 'DEGRADED' == 'RUNNING'`.

Both ran late in the observability directory, after tests/unit/strategic, the engine checkpoint files and the earlier observability files in the same process. Each passes alone, and both passed in the lane's fuller step (1) order (2155 passed, 0 failed). Neither touches code the churn branch changed.

Caution: TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT was filed as a state leak, and the leak framing turned out wrong (there was no leaking test). So this ticket claims only the observed order dependence, not its cause.

## Scope
1. Reproduce from the run 1 order (one `-n 1` process), on a host-free slot.
2. Bisect the preceding tests to the smallest prefix that makes each test fail, or show that the failure is timing or wall-clock dependent rather than ordering.
3. Fix the real cause: test isolation (a fixture reset) if a test leaks, or the code if module or global state survives where it should not. Never weaken or skip either assertion.

## Out of Scope
- The churn fix and its PR.
- Any change to the two assertions' expectations.

## Acceptance Criteria
- The run 1 order passes both tests, and so does each test alone.
- The cause is named in this ticket, with the bisect evidence.
- A regression guard exists if the cause is a shared-state leak.

## Related Tickets
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION (where it was found)
- TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT (earlier mis-framing)
- TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON (a prior singleton leak in live health)

## Related Docs
- docs/plans/test_architecture/roadmap.md §4.5 (failure triage)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/blockerchurn/unit_run1.log (on the owner's delete list once this ticket closes)

## Related Code Areas
- tests/unit/observability/test_death_ledger.py, tests/unit/observability/test_live_anomaly_worker.py
- src/observability/ (the death ledger and the live anomaly worker)

## Assumptions / Open Questions
- Unproven reading from lane C: #1 is death-ledger module or global state carried over from an earlier test, and #2 is a worker health state left DEGRADED (timing or shared state).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
