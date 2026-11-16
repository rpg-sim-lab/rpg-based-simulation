---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER
phase: open
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER

## Title
The semantic-drift certification test does not fail on a slow runner: its healthy-run half is not judged against a 10 ms wall-clock tick budget

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
rpg-planner reported this on 2026-11-16, at lead-planner-u24's suggestion. On #931's CI (run 43805317187, job 133094635683), `tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py` failed. Inside it, the third guarded test failed: `tests/certification/test_harness_contract.py::test_certification_detects_semantic_drift`, at `assert result.conformance_passed` (line 40).
That run's log shows "Replay finalize: Skipping final rotation due to insufficient budget (Remaining: -0.000s)". #931 touches nothing on this path, and the test passes locally (9.25 s).

Likely cause: the test's profile sets `max_tick_budget_ms=10.0`. `src/certification/conformance.py:62` fails a scenario when any tick's wall-clock `tick_compute_ms` exceeds `max_tick_budget_ms * 1.5`, which is 15 ms here. The RSS guard runs this test in a subprocess that first holds a 1200 MB ballast, on a shared GitHub runner. A single slow tick there fails conformance. The test checks something else: the baseline hash equals the final hash, and a healthy DET_EQUIV run passes. Its tick budget is incidental, just as its RAM ceiling was in TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT.
The CI log could not be read for the exact `fail_reason`, so confirming it is Scope 1.

## Scope
1. Confirm the failing check without a heavy run. Make `CertificationHarness`'s tick timing report one tick above 15 ms (for example, patch the timer that feeds `tick_compute_ms`), then assert that `conformance_passed` is False with a "Tick budget violation" `fail_reason`. If the `fail_reason` turns out to be something else (a required NORMAL mode, or a telemetry gap), stop and report back before changing anything.
2. Fix it at the test, with a test-only change. Give the drift test's profile a tick budget that never binds, for example `max_tick_budget_ms=10000.0`, the same value `test_authoritative_outcome_truth` uses. Its hash assertions stay unchanged.
3. Check the other three guarded tests for the same exposure:
   - `test_envelope_violations` (two profiles at 10 ms): does its expected outcome depend on the budget?
   - `test_resilience_recovery` (100 ms).
   Change one only if its subject is not timing, and record the reasoning either way.
4. The regression test: under the patched slow tick from Scope 1, the drift test's healthy half still passes. It fails with the old 10 ms budget; record that revert.

## Out of Scope
- `src/certification/` and its wall-clock checks. Those are production certification semantics and rpg's domain.
- Changing the RSS guard's ballast or its timeout.

## Acceptance Criteria
- [ ] AC1: the failing check is confirmed (Scope 1), or the ticket stops and reports a different cause.
- [ ] AC2: the drift test passes with a simulated slow tick, and the revert to 10 ms fails.
- [ ] AC3: `tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py` and `tests/certification/` pass at `-n 1`, unit tests only.
- [ ] AC4: the finding on each of the other guarded tests is recorded.

## Related Tickets
- TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT (the RSS guard; the same "incidental envelope" class)
- TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY (#932, the same class: a test bound by host state)

## Related Docs
- `docs/engine/contracts/certification_contract.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/certification/test_harness_contract.py`
- `tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py`
- `src/certification/conformance.py:62` (read only)

## Assumptions / Open Questions
- The certification semantics are rpg's (`src/certification`). I'm asking rpg-planner to review, as on #928, #930 and #932. The change is test-only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
