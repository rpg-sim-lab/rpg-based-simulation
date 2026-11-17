---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261018-TWO-BARE-KERNEL-TESTS-DEPEND-ON-HOST-MEMORY
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-TWO-BARE-KERNEL-TESTS-DEPEND-ON-HOST-MEMORY

## Title
Two tests that build a bare Kernel fail when the pytest process is large

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while fixing TCK-20261018-REPLAY-NON-AUTHORITATIVE-TEST-INDEPENDENT-OF-HOST-MEMORY. A Kernel built with the default governor reads host RSS against the profile's memory cap. Above it (about 512 MB for the test profile in that case) the kernel drops to SURVIVAL, replay is switched off, and anything asserting on replay or on the mode goes red. A whole-red-list run reaches that size late in the process.

## Scope
Make these two tests independent of host memory:
- tests/unit/resource/test_resource_governor_contract.py::test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure
- tests/unit/core/test_operational_flags.py::test_no_replay_stops_the_replay_sink

Reproduction: run either file inside a process holding a 1500 MB ballast (allocate and touch a bytearray, then call pytest.main with --resource-budget off). Both pass with no ballast and fail with it; the other 52 tests in the 14 candidate files pass in both cases.

Judgement left to this ticket: the governor-contract test asserts the kernel "stays normal ABSENT real pressure", so the right fix may be zeroed signals (audit_mode, or a governor with zeroes_signals) rather than PinnedNormalGovernor, which would hide the very mode it checks. The test may also legitimately read the host, in which case it should say so and not be pinned. Decide per test; the established pin is tests/helpers/kernel_pinning.py.

## Out of Scope
Any src change. Bare-Kernel files outside the 14 candidates I ran were not checked and may share the exposure (candidates: bare Kernel, no PinnedNormalGovernor/audit_mode, asserting on replay or mode); a sweep is a separate decision.

## Acceptance Criteria
Both tests pass at 0, 100, 400, 700 and 1500 MB ballast with their assertions still meaning what they say; tests/unit/kernel and the two files pass with --resource-budget off.

## Related Tickets
TCK-20261018-REPLAY-NON-AUTHORITATIVE-TEST-INDEPENDENT-OF-HOST-MEMORY

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
tests/unit/resource/test_resource_governor_contract.py; tests/unit/core/test_operational_flags.py; tests/helpers/kernel_pinning.py

## Assumptions / Open Questions
Decided per test (not pinned): neither test is pinned with PinnedNormalGovernor or audit_mode, because both assert on the mode or on replay, which that would hide. The governor-contract test says 'stays NORMAL absent real pressure'; the process's own RSS is not real pressure, so its profile ceiling is now out of reach (max_ram_mb=1_000_000) and the mode is still derived live. The flag test (`_flag_profile`, shared by the file's flag tests) gets the same out-of-reach ceiling: above the ceiling the kernel drops to SURVIVAL and replay is switched off, which is what the test checks against. Neither test is meant to read the host.

## Implementation Notes
Ceiling raised from 512 and 1024 to 1_000_000 in `test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure` and in `_flag_profile()`, each with a comment. Same mechanism as TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT (live pytest-process RSS against a per-test ceiling). No src change.

## Test Summary
Ballast ladder, both files (17 tests, --resource-budget off), before: 0 MB 17 passed; 700 MB 1 failed (the governor test, ceiling 512); 1500 MB 2 failed (plus the flag test, ceiling 1024). After: 0, 100, 400, 700 and 1500 MB all 17 passed. tests/unit/kernel plus the two files: 99 passed in 37 s. Free memory before the 1500 MB runs: about 3.7 GB available.

## Files Changed
tests/unit/resource/test_resource_governor_contract.py; tests/unit/core/test_operational_flags.py; this ticket.

## Completion Summary
Both tests pass at 0, 100, 400, 700 and 1500 MB ballast with their assertions unchanged in meaning. Not cleared: the sweep for other bare-Kernel tests with live ceilings (out of scope here); tests with 256, 512 and 1024 ceilings elsewhere may bind in a larger process. Not pushed: pushing and merging need the owner's separate yes.
