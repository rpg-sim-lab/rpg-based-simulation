---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: test_plan
tags: []
---

# Test plan (DRAFT for option (a); written before any src edit; the tests are NOT written yet)

New unit tests, in tests/unit/engine/ (the neighbours: test_action_task_does_not_move.py, test_engaged_adjacent_hostile_takes_no_stored_step.py, test_notice_unengaged_hostile.py, test_sleep_debt_stages.py) and tests/unit/combat/test_chokepoint_hold.py:
1. **Entry tick, no walk (P1/P2):** an entity with an idle tick-start task and a stored target, beside an unengaged perceived hostile, decides WATCH_HOSTILE / AVOID_NO_ROUTE (no route) / HOLD_CHOKEPOINT; `MovementCandidateSelector.movement_target` (and `route_movement_intent`, through the phase) takes NO step that tick: no `new_position`, no opportunity attack. Parametrised over the three typed waits. Built on a refined update in which the actions phase has already emptied the HOLD payload (the real order), so it pins the flaw named in plan.md, not the as-worded P1.
2. **Gap, no walk (P2):** after the wait, the entity's stored target is cleared; the next movement phase offers it no move (`select` and the phase agree); a fresh decision that sets a target moves normally.
3. **A decided move still moves:** an ENTITY_MOVE decision with a target set the same tick still steps (the first branch of `movement_target`), including from HOLD.
4. **HOLD ends with its task, per writer (P3):** WATCH_HOSTILE, AVOID_NO_ROUTE, HOLD_CHOKEPOINT (the mode is WANDER after the wait's task ends, per the designer's ruling on the open point), after-kill (HOLD set by `_hold_in_place`, back to WANDER when the swing at the dead target fails TARGET_INCAPACITATED), collapse (HOLD during the held SLEEP, WANDER at wake). One test per writer.
5. **KEEP_WALKING does not inherit HOLD:** `notice_unengaged_hostile` with posture `ignore` from mode HOLD writes WANDER.
6. **ATTACK / SKILL same-tick side effect (P1):** an entity with a stored target that decides ATTACK or SKILL this tick takes no stored-target step that tick (pins the new behaviour); an INTERACT / EAT / REST decision is unchanged unless the designer picks P1-a.
7. **Unchanged laws:** the 0.1 clamp stays (`verify_movement_legality` prices HOLD at 10x; a test pins it); an occupant in HOLD still refuses to yield and a HOLD party still refuses a swap; the chokepoint hold still returns a typed success that ends its task.
8. **Dispatcher parity:** `select` and `route_movement_intent` agree on every case above (they share `movement_target`).
Existing tests to keep green: tests/unit/engine/test_action_task_does_not_move.py, test_engaged_adjacent_hostile_takes_no_stored_step.py, test_notice_unengaged_hostile.py, test_sleep_debt_stages.py, tests/unit/combat/test_chokepoint_hold.py, tests/unit/movement/*, the kernel-level hold tests, tests/docs, the parity-ledger schema check, generate_registry --check.

## Proof Plan

- Level: unit tests for the three pieces; the kernel-level effect by the two-stage paired measurement (stage 1 fm and crowded s42, stage 2 3 worlds x 5 seeds incl. def2 only if stage 1 passes).
- Proof kind: behavioural unit tests on the movement phase and the actions phase; a read-only spy measured on base and fix with plain-twin hash matches.
- Oracle source: tactical_contract.md:89 and the code comments (a HOLD keeps the tile until the next decision); the 5000-tick evidence of this ticket.
- Expected effect: no entry-tick or gap step from a typed wait; a HOLD never outlives its task; no freeze (no 50+ tick hold beside a hostile that never hits; no HOLD at the last tick); deaths and alive-per-role inside the limits.
- Selected commands: `pytest <the files above> -n 1`; `make parity-ledger-schema-check`; `python3 tools/generate_registry.py --check`; the approved spy via the driver on HOST FREE; ledger edits only through tools/parity_ledger_writer.py.
