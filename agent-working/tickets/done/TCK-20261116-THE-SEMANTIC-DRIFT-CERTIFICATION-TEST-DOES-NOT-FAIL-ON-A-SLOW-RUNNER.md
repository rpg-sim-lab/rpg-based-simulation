---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER
phase: done
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER

## Title
The semantic-drift certification test does not fail on a slow runner: its healthy-run half is not judged against a 10 ms wall-clock tick budget

## Status
DONE

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
3. Check the other guarded tests for the same exposure (rpg-planner's caution: read what each one asserts first). Widen a budget only if the test's own claim doesn't depend on it. If the claim needs a binding budget (for example, `test_harness_detects_missing_degradation_mode` may need pressure), make the slow tick deterministic, such as a simulated tick cost, instead of widening it. Write down which case each test is in:
   - `test_envelope_violations` (two profiles at 10 ms): does its expected outcome depend on the budget?
   - `test_resilience_recovery` (100 ms).
   Change one only if its subject is not timing, and record the reasoning either way.
4. The regression test: under the patched slow tick from Scope 1, the drift test's healthy half still passes. It fails with the old 10 ms budget; record that revert.
5. Keep Scope 1's confirmation as a permanent test: a deterministic slow tick fails conformance with "Tick budget violation", so the budget check stays tested with no wall-clock dependence (lead-planner-u24's ask). Before writing it, search `tests/` for an existing budget-exceeded conformance test, and state in the PR whether one exists.
6. The drift claim: today's test asserts only the healthy half, even though its name and comment promise drift detection. Check whether `tests/` already proves that the harness fails on a baseline/final hash mismatch ("Authoritative divergence"). If nothing does, add that half: simulate a final hash that differs and assert `conformance_passed` is False with that `fail_reason`. State the answer in the PR.

## Out of Scope
- `src/certification/` and its wall-clock checks. Those are production certification semantics and rpg's domain.
- Changing the RSS guard's ballast or its timeout.

## Acceptance Criteria
- [x] AC1: the failing check is confirmed (Scope 1), or the ticket stops and reports a different cause.
- [x] AC2: the drift test passes with a simulated slow tick, and the revert to 10 ms fails.
- [x] AC3: `tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py` and `tests/certification/` pass at `-n 1`, unit tests only.
- [x] AC4: the finding on each of the other guarded tests is recorded.

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
- RESOLVED 2026-11-16: testing builds this, and rpg-planner reviews the diff before the push, as on #928, #930 and #932. The change is test-only. lead-planner-u24's condition for the push ask: show that the drift half still fails on real drift, and that budget-exceeded conformance is still tested (Scopes 5 and 6).

## Implementation Notes
- Scope 1 (confirmed): a deterministic slow tick (every measurement point reports 40 ms, injected by patching `src.certification.models.MeasurementPoint`, the name `run_scenario` imports at call time) on the drift test's old 10 ms budget fails conformance with `failure_kind == FAILED_ENVELOPE` and the reason `Tick budget violation: 40.0ms > 15.0ms at tick 1`. It is the tick-budget check at `conformance.py:62`, not a mode or a telemetry gap, so the ticket went on.
- Scope 2: the drift test's budget is the module constant `DRIFT_TICK_BUDGET_MS = 1000.0`, so a tick must cost over 1.5 s to bind. Not 10000 ms as first suggested: a larger budget makes each of these certification runs take about 30 s instead of 4-9 s (measured: 30.8 s at 10000 ms, 3.8 s at 1000 ms), which overruns the RSS guard's 50 s subprocess budget for the four tests. The hash assertions are unchanged.
- Scope 3 (read each test's claim first):
  - `test_harness_detects_missing_degradation_mode` (10 ms): claim = the run stays in NORMAL and so never enters the required DEGRADED mode (`FAILED_DEGRADATION_SEQUENCE`). It does not need a binding budget, and it WAS exposed: the envelope check runs before the degradation check, so one slow tick would turn the expected `FAILED_DEGRADATION_SEQUENCE` into `FAILED_ENVELOPE`, and a tick cost at or above the budget can also move the governor out of NORMAL. Widened to 1000 ms.
  - `test_harness_catches_ram_violation` (10 ms, not one of the guarded four): claim = RAM. The RAM check precedes the tick check at every point, so it was not exposed; widened to 1000 ms together with its neighbour in the same file for one consistent budget.
  - `test_harness_catches_failed_recovery` (100 ms): its subject is the recovery check with a mocked governor. The exposure is real but small (a tick over 150 ms). It is NOT widened: raising it to 10000 ms made the test exceed the 60 s limit (4 s at 100 ms), and 1000 ms was not tried. Left at 100 ms; the residual risk is recorded here, to be fixed with a simulated tick cost if it ever flakes.
- Cause and where the time goes (corrected after rpg-planner's review; verified at `src/engine/kernel.py:451-469`):
  - The cause of the CI failure is real phase work over 1.5 x the budget (15 ms at a 10 ms budget) on a loaded runner under the 1200 MB ballast. The recorded `tick_compute_ms` is `_final_compute_ms = sum(self._phase_costs.values())` (line 469): the sum of the phase costs only. The pacing sleep (`kernel.py:451-461`) is excluded from it.
  - Pacing makes the wall time per tick about the budget (unless `no_frame_pacing` is set). That is why a 10000 ms budget made each of these tests take about 30 s (2 ticks x 10 s, plus startup and shutdown), and why 1000 ms is both non-binding (a phase cost over 1.5 s does not happen) and cheap (about 4 s per test; measured 3.8 s). `test_resilience_recovery` stays at 100 ms because it runs 10 ticks, so its wall time scales with ticks x budget; its residual exposure is phase work over 150 ms (1.5 x 100 ms).
  - The CI log line "Replay finalize: Skipping final rotation due to insufficient budget (Remaining: -0.000s)" is benign and unrelated to the failure: it comes from the harness's baseline run ending with `kernel.shutdown(timeout_s=0.0)` (`src/certification/harness.py:312`), so it is logged every time.
- Scope 5 search: no test under `tests/` names "Tick budget violation" or FAILED_ENVELOPE for a tick. `ConformanceEvaluator` was tested directly only in `test_allowed_failure_truth.py` (allowed failures). New `tests/certification/test_conformance_budget_and_divergence.py` pins the budget verdict (16 ms fails with the reason, 15 ms passes, a never-binding budget passes the same tick) with injected measurements and no wall clock.
- Scope 6 search: no test under `tests/` names "Authoritative divergence" or FAILED_SEMANTIC_DRIFT; `test_certification_detects_semantic_drift` asserted only its healthy half. The new file proves the other half: a final hash that differs from the baseline fails with `FAILED_SEMANTIC_DRIFT` and `Authoritative divergence from baseline: baseline=aaa, final=bbb`, and a missing hash fails the same way.

## Test Summary
- Final runs (`-n 1`, `-p no:xdist -p no:randomly`): test_harness_contract + test_conformance_budget_and_divergence + test_allowed_failure_truth: 11 passed in 9 s. The envelope tests and the drift test: 3 passed in 12 s. test_resilience_recovery (unchanged): 1 passed in 4 s. The RSS guard `test_the_four_pass_in_a_process_already_holding_1200_mb`: 1 passed in 15 s (with 10000 ms it TIMED OUT at 50 s).
- Revert evidence (AC2): with the constant set back to 10 ms, `test_the_healthy_half_passes_on_a_slow_runner` FAILS with `Tick budget violation: 40.0ms > 15.0ms at tick 1`. Restored, it passes.
- A first version of the slow-tick injection patched the wrong module (`harness.MeasurementPoint`, which `run_scenario` shadows with a local import), so the injected tick did nothing and the confirmation test failed; fixed to patch `src.certification.models` and re-run.
- A full `tests/certification` directory run at `-n 1` on a contended host (an unrelated pytest from another project was running) took 33 min and showed 5 failed / 1 error: `test_cert_long_run_stability` x3 and `test_resilience_recovery` hit the per-test 60 s limit (resilience only with the 10000 ms budget I then reverted), the new slow-tick test (the injection bug above, fixed), and a `QueueDrainWorker` thread-leak teardown error in `test_world_compile_determinism` (left behind by the timed-out tests). The three long-run files are not touched by this change; I did not re-run them in isolation.

## Files Changed
- tests/certification/test_harness_contract.py
- tests/certification/test_envelope_violations.py
- tests/certification/test_conformance_budget_and_divergence.py

## Completion Summary
The drift test and the missing-degradation test no longer fail on a slow runner: their tick budget never binds (1000 ms). The tick-budget verdict and the baseline/final divergence verdict are now tested with injected values and no wall clock. The recovery test keeps its 100 ms budget, and that residual exposure is recorded.
