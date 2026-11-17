---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT
phase: done
date: 2026-11-01
tags: [testing]
---

# TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT: test_plan

## Proof Plan
- level: unit/integration plus an architecture guard
- proof kind: ballast regression (0/700/1500 MB) and a wide scoped run
- oracle source: the four pass in the wide run and fail under ballast without the fix
- expected effect: no failures from this class
- selected commands: the ticket's scoped command; pytest tests/architecture/test_rss_bound_tests_pass_in_a_large_process.py
