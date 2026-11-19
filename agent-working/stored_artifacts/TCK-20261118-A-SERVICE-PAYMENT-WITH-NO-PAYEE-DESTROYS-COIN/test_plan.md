---
status: historical
layer: economy
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN
phase: done
date: 2026-11-19
tags: []
---

# Test plan
- New: tests/unit/resource/test_resolver_every_accepted_result_balances.py (150 passed; the apply-path t3181 test fails on 51a6516cf 130 vs 140, passes on the fix).
- Edited with owner approval: test_interleaved_transaction_grouping (#715 6997033044); test_every_building_service_payment_is_credited_to_the_building_that_served_it, one line (#715 6986615512).
- Sweep: tests/unit/** by directory at c2d9cb1fa: 42 rc=0, motivation rc=5 (no tests), worldassembly 5 pre-existing (identical on main 5713e2025).
- Statics: mypy filter 0, lint-imports 17/0, code-health rc 0. Own-job: hash-equal in 4 cells, V6 0, preflight 0 FAIL of 62.
