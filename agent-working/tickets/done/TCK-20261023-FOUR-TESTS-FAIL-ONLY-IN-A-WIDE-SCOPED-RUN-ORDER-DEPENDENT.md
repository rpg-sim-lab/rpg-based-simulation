---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT
phase: done
date: 2026-10-23
tags: []
---

# TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT

## Title
Four tests fail only inside a wide scoped run and pass alone: a per-test RAM ceiling meets the growing pytest process (not a state leak)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by rpg-implementer (Lane A) during HUNGER step B's local scoped run (2026-10-23). CORRECTION (2026-11-01): the filed framing, an order-dependent state leak, was wrong. There is no leaking test. The four tests build a profile with `max_ram_mb=512`, the engine compares that ceiling with the live RSS of the pytest process, and a wide run grows past 512 MB. See Implementation Notes.

## Scope
1. Reproduce: the same scoped command on 341f700d0; bisect the collection order (pytest -p no:randomly, then --lf with a growing prefix) to find the test that leaks state.
2. Fix the leak (fixture teardown, a monkeypatch left in place, a module-level cache) at its source. Never by reordering or skipping.

## Out of Scope
The step B changes themselves.

## Acceptance Criteria
- REPLACED (premise wrong, no leaking test exists): the four tests pass in the wide scoped run on main, and a guard test runs them in a process already holding 1200 MB.
- The original criterion 'the leaking test is named and fixed' is NOT ticked: there is no leak.

## Related Tickets
TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (where it was seen).

## Related Docs
docs/testing/test_taxonomy.md

## Related Stored Artifacts

## Related Code Areas
tests/ (the four named tests and their fixtures)

## Assumptions / Open Questions
- Ownership: if the leak is in tests/architecture/**, route to testing-planner.

## Implementation Notes
Reproduced on main 6fdfdf555 (5 failed, 9686 passed): the four plus the governor test. Ballast evidence, four tests alone: 0 MB pass; 700 MB all four fail; with the fix 1500 MB pass. Fix: `max_ram_mb=1_000_000` in the four tests; guard `tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py` (fails without the fix). Why a ceiling and not PinnedNormalGovernor: the ceiling removes only the RAM signal and the certification harness builds its own kernel. The guard's subprocess timeout is 50 s because the medium budget's 60 s SIGALRM fires first.

## Test Summary
Wide scoped run on the fixed tree (2152e484e): 9691 passed, 11 skipped, 52 deselected, 1 xfailed, 0 failed (17m29s). After merging origin/main (0c319ca21): the four tests, the guard and tests/certification with -m "not slow" rerun green (74 passed, 1 skipped, 3 deselected). One unmarked tests/certification run (it also executes the slow and extra_slow tests) ended 3 failed, 74 passed, 1 skipped, 1 error in 30m18s. Named in the kept output: test_cert_long_run_stability.py::test_long_run_determinism_parity (slow-marked) failed, and test_world_compile_determinism.py::test_compile_report_contents (not marked slow) errored once after the extra_slow tests; it passes alone (1 passed, 0.9 s) and passes in the -m "not slow" set above. The error text was not kept and the other failures in that run were not named in the kept output, so the cause is not established and not reproduced; whether it is an order or process-state effect is unknown. The ticket's wide-run claim covers only the scoped command above.

## Files Changed
tests/integration/kernel/test_authoritative_outcome_truth.py, tests/certification/{test_envelope_violations,test_harness_contract,test_resilience_recovery}.py (one ceiling each); tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py (new).

## Completion Summary
The four tests no longer depend on the size of the pytest process. NOT cleared: the guard covers only these four; other tests still carry 256, 512 and 1024 ceilings, including tests/api and tests/arena, which the wide scope did not run, and a larger process could bind them. test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure failed in the first wide run for the same reason and passed in the second; it belongs to TCK-20261018-TWO-BARE-KERNEL-TESTS-DEPEND-ON-HOST-MEMORY. Not pushed: pushing and merging need the owner's separate yes.
