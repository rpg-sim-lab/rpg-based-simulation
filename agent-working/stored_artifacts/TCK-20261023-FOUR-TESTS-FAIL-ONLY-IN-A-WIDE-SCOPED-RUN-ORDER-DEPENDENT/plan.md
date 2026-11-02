---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT
phase: done
date: 2026-11-01
tags: [testing]
---

# TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT: plan

Raise max_ram_mb to 1_000_000 in the four tests (none is about RAM; the RAM-focused test_harness_catches_ram_violation is untouched). Add tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py: re-runs the four in a fresh process holding 1200 MB; it fails without the fix. No src change. Scope guard: other tests with 256/512/1024 ceilings are not changed.
