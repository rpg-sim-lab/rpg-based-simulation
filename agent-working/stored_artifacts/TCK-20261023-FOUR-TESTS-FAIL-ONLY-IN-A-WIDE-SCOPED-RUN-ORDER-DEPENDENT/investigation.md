---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT
phase: done
date: 2026-11-01
tags: [testing]
---

# TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT: investigation

Premise was wrong: there is no leaking test. Reproduced on main 6fdfdf555 with the ticket's scoped command (5 failed, 9686 passed, 18m52s): the four named tests plus test_resource_governor_contract.py::test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure. Each passes alone. The engine compares live process RSS (src/engine/observability.py, psutil) with the test profile's max_ram_mb; these tests used 512, and a wide run grows the pytest process past that, so the kernel goes CONSTRAINED and the certification harness reports failed_envelope. Evidence, the four alone with ballast: 0 MB pass; 700 MB all four fail; after the fix 1500 MB pass. CI shards stay under 512 MB, which is why they never hit it. Why a ceiling and not PinnedNormalGovernor: the ceiling removes only the RAM signal and leaves every other pressure path under test, and the certification harness builds its own kernel, so a governor pin would not reach it.
