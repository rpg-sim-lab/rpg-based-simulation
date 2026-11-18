---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE
phase: done
artifact_type: test_plan
date: 2026-11-18
tags: []
---

# Test plan

- Unit: `tests/unit/movement/test_failure_reason_lifecycle.py` (8), `tests/unit/movement/test_move_carries_clear_not_code.py` (9, incl. the phase-order guard).
- Four assertions that named YIELDING / POSITION_SWAP now assert None plus the clear (owner #715 6967398421).
- Own-job: diag spy v2 (writer attribution), 3 cells, s42, 5000 ticks, spy plus plain twin, bars L1 M1 M2 R2 = 0 and validity (see Test Summary and evidence/).
