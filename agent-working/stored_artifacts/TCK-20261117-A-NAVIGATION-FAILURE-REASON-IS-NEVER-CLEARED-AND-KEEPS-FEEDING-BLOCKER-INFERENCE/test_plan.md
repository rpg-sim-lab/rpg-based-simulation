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

## Proof Plan

- Level: unit (patch, update merge, movement phase helper) plus a measured own-job on three full worlds.
- Proof kind: regression tests with a hand-computed oracle, and a read-only spy that wraps the writers of `last_failure_reason`.
- Oracle source: AC1 (defined lifecycle) the ruled move law (owner #715 6967356642, 6967398421) and divergence 2.215; AC2 (inference never acts on an old failure) the patch precedence (a code beats a clear, a bare None keeps the old value) and the stale-PATH_NOT_FOUND blocker test.
- Expected effect: a successful step or any move leaves `last_failure_reason` None unless a later code or an earlier-phase action code applies; a stale code files no ACCESS blocker; spy bars L1, M1, M2, R2 equal 0 with non-vacuous set/cleared counts and every move kind seen.
- Selected commands: `pytest tests/unit/movement/test_failure_reason_lifecycle.py tests/unit/movement/test_move_carries_clear_not_code.py` (named tests: `test_a_yield_displacement_moves_the_occupant_with_the_clear_and_no_code`, `test_both_swapped_bodies_end_the_tick_with_no_last_failure_reason`, `test_a_code_from_an_earlier_phase_survives_a_later_move_of_the_same_body`, `test_the_phase_order_is_action_then_swaps_then_movement_and_a_swapped_body_is_not_resolved_again`), the four edited assertions in test_swaps_and_yields_pay_step_time, test_movement_spatial_regression, test_migration_proof, test_position_swap; own-job summary sha256 a073160db807cc2f546e37632362e77651912b7dc647cedd0a596f530beed9d0 (`evidence/summary.txt`, manifest 488582e9, tree stream 3dace138).
