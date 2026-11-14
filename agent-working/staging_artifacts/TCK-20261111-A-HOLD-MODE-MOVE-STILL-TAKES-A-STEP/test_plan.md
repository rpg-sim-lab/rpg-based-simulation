---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: test_plan
tags: []
---

# Test plan (DRAFT v2 for option (a), P1-b and P3-alt; written before any src edit; the tests are NOT written yet)

New unit tests, in tests/unit/engine/ (neighbours: test_action_task_does_not_move.py, test_engaged_adjacent_hostile_takes_no_stored_step.py, test_notice_unengaged_hostile.py, test_sleep_debt_stages.py) and tests/unit/combat/test_chokepoint_hold.py:
1. **P1-b depends on P2 (both halves):** an entity with an idle tick-start task and a stored target, beside an unengaged perceived hostile, whose pending update is a typed wait (mode HOLD, ENTITY_ACT HOLD with the payload already emptied, as the actions phase leaves it): WITHOUT `target_clear` in the update, `movement_target` still returns the stored target (the step happens: documents that P1-b does nothing alone); WITH `target_clear` (what P2 adds) it returns None and the phase takes no step and no opportunity attack. Parametrised over WATCH_HOSTILE, AVOID_NO_ROUTE, HOLD_CHOKEPOINT.
2. **Gap, no walk (P2):** after the wait is applied the stored target is gone; the next movement phase offers no move (`select` and the phase agree). A wait that ends with no walk decision keeps HOLD and nothing steps (correct).
3. **A decided move still moves:** an ENTITY_MOVE decision with a target set the same tick still steps (the first branch), including from HOLD.
4. **The reset at each mode-less target writer (P3-alt, typed waits):** for each writer in plan.md's table (intelligence.py:649, :670; redirection.py:97, :128; tactical_hold.py:99 KEEP_WALKING; intent/action_intent.py:139 MOVE_TO): an entity in mode HOLD that gets a walk from that writer leaves the update with `movement_mode_set` = WANDER together with the target. And with the current mode not HOLD, the writer adds no mode (no change to other modes).
5. **GUARD TEST (every mode-less target writer):** a static scan (ast) of `src` finds every `NavigationUpdate(...)` with `target_set` and no `movement_mode_set`, and asserts the set equals the documented allow-list (the six reset writers above plus the two reaffirm sites executor.py:110 and worker_logic.py:34); a new mode-less writer fails the test. A dynamic companion drives each reset writer with a HOLD entity and asserts none leaves HOLD in place; and asserts that no held ENTITY_MOVE task can exist under HOLD (KEEP_WALKING no longer inherits it). A test records that :677 and the other REGROUP writers always carry REGROUP.
6. **Kill and collapse reset when their task ends:** after-kill (HOLD set by `_hold_in_place`; WANDER when the next swing at the dead target fails TARGET_INCAPACITATED), collapse (HOLD during the held SLEEP; WANDER at wake). A HOLD-action success (the typed waits) does NOT reset: the mode is still HOLD after the wait's task ends.
7. **ATTACK / SKILL same-tick side effect (P1-b):** an entity with a stored target that decides ATTACK or SKILL this tick (their updates carry `target_clear`) takes no stored-target step that tick; EAT / REST / INTERACT decisions (no `target_clear`) are unchanged.
8. **Same-tick wait plus strategic write:** a wait (target_clear) merged with a strategic target write in the same tick: pin the outcome (which wins) so the order is documented.
9. **Unchanged laws:** the 0.1 clamp stays (HOLD priced 10x; a test pins it); an occupant in HOLD still refuses to yield and a HOLD party still refuses a swap; the chokepoint hold still returns a typed success that ends its task; `target_clear` (applied) vs `clear_target` (not applied) behave as today.
10. **Dispatcher parity:** `select` and `route_movement_intent` agree on every case above (they share `movement_target`).
Existing tests to keep green: tests/unit/engine/test_action_task_does_not_move.py, test_engaged_adjacent_hostile_takes_no_stored_step.py, test_notice_unengaged_hostile.py, test_sleep_debt_stages.py, tests/unit/combat/test_chokepoint_hold.py, tests/unit/movement/*, the kernel-level hold tests, tests/docs, the parity-ledger schema check, generate_registry --check.

## Measurement checks and STOP rules (the spy, fix arm vs base arm; designer-confirmed)
- Reported per arm: undecided HOLD steps and their OA; re-wait loops within 10 ticks; for waits "HOLD after the next walk decision" (expected 0); for kill and collapse "HOLD lifetime after task end" (expected 0); deaths and deaths within 10 ticks of a HOLD step; alive per role.
- STOP (a stop returns to the owner; nothing lands): (i) a hold of 50+ ticks beside a hostile that never hits the subject, whether or not a walk decision was issued, REPORTED SPLIT by whether one was issued (a re-wait loop vs a blocked walk); (ii) a HOLD still in force at the last tick after it should have ended: for a wait, after a walk decision since the hold began; for kill or collapse, after the task ended; (iii) the free-hit and death limits of divergences 2.89 / 2.204.

## Proof Plan

- Level: unit tests for the three pieces and the guard; the kernel-level effect by the two-stage paired measurement (stage 1 fm and crowded s42, stage 2 3 worlds x 5 seeds incl. def2 only if stage 1 passes).
- Proof kind: behavioural unit tests on the movement phase and the actions phase; a static guard over the mode-less target writers; a read-only spy measured on base and fix with plain-twin hash matches.
- Oracle source: tactical_contract.md:89 and the code comments (a HOLD keeps the tile until the next decision); the 5000-tick evidence of this ticket.
- Expected effect: no entry-tick or gap step from a typed wait; HOLD ends at the next walk decision (waits) or at task end (kill, collapse); no freeze (no 50+ tick hold beside a hostile that never hits; no HOLD in force after it should have ended); deaths and alive-per-role inside the limits.
- Selected commands: `pytest <the files above> -n 1`; `make parity-ledger-schema-check`; `python3 tools/generate_registry.py --check`; the approved spy via the driver on HOST FREE; ledger edits only through tools/parity_ledger_writer.py.
