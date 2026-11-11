---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
phase: done
artifact_type: test_plan
date: 2026-11-11
tags: []
---

# Test plan

Unit rows (`tests/unit/movement/test_felt_lethal_free_swing_step.py`, `MovementSystem.resolve_move`, scene: frontier_living_world s42, merchant 37 beside raider 24, as in the 2.202 tests):
1. `test_step_is_held_when_an_engaged_hostile_has_felt_lethal`: held, FELT_LETHAL_FREE_SWING, wait_count_delta 0, no combat update, target kept.
2. `test_step_is_held_for_a_decided_reposition_step`: the same with mode REPOSITION (the e24 shape).
3. `test_step_is_taken_when_the_felt_swing_is_under_hp`: step taken, the free swing fires.
4. `test_step_is_taken_when_the_felt_attacker_is_not_engaged`: felt attacker elsewhere, an engaged never-hit hostile: step taken, its free swing fires.
5. `test_step_is_taken_with_no_felt_blow`: last_hit_damage None: step taken.
6. `test_evasive_flight_is_unaffected`: skip_oa: step taken, no free swing.
7. `test_held_step_matches_a_blocked_step`: the held update equals the blocked-step update shape field by field; only failure_reason differs (wait_count_delta is 0 by the design, where a blocked step adds 1); plus the plan cache is left untouched by a held step and written by a taken one.
8. The existing 2.202 tests (`tests/unit/tactical/test_flight_weighs_free_swing.py`, `tests/mechanic_scenarios/test_flight_weighs_free_swing_through_kernel.py`) pass unedited after the helper move.

Kernel (`tests/mechanic_scenarios/test_engaged_subject_does_not_walk_a_stored_target_through_kernel.py`): `test_engaged_subject_does_not_walk_a_stored_target_into_a_felt_lethal_swing`. Arena of the CONFLICT-04 scenario; subject hp 20, last hit 23 from H, H adjacent; a stored REGROUP target off engagement; no decision lands for the subject (its decision is stood in by a no-op update, the cadence control). Assert: position unchanged, no opportunity attack on it, no DEFEAT. A control (the same scene with the new check disabled) takes the free swing.

Run order: the rows first on unfixed src (which fail is reported), then after the fix. Then: movement, engine and combat unit dirs (`-n 1`), `mypy_gate`, `python -m codebase.health check`, the mechanism-registry completeness pin.
