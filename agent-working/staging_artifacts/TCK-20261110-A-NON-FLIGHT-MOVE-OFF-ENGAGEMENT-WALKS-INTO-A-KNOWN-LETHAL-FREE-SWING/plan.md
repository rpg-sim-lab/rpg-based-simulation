---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
phase: plan
date: 2026-11-11
tags: []
---

# Plan: no step off engagement into a free swing the subject has felt will finish it (rule S1)

Spec: rpg-designer's design `.claude/handover/drafts/rpg-designer-nonflight-free-swing-design.md` (main checkout), sections "Build" and "Test rows (named)"; authority #715 6734312437. Dispatch: rpg-planner, 2026-11-11. Evidence: `investigation.md` (Scope 1, five hash-matched traces).

## Change (src gate: movement.py, felt_swing.py, tactical_flight_guard.py (import only), core/enums.py ReasonCode)
1. New `src/engine/felt_swing.py` holds `felt_lethal_attacker(state, entity)`, moved unchanged (body and docstring) from `tactical_flight_guard._felt_lethal_attacker`; the guard imports it. 2.202 stays byte-identical in behaviour. Reason for the module: movement.py cannot import the guard, which imports movement.
2. `ReasonCode.FELT_LETHAL_FREE_SWING` (typed, in the Movement group).
3. `MovementSystem.resolve_move`: at the free-swing site (`engaged_hostiles and not skip_oa`), before `resolve_multi_attack`, if `felt_lethal_attacker(state, entity)` is not None and its id is in `engaged_hostiles`, return `{entity.id: EntityUpdate(entity_id, navigation=NavigationUpdate(failure_reason=FELT_LETHAL_FREE_SWING, wait_count_delta=0))}`: no position change, no stamina drain, no free swing, no fled learning, the stored target kept. Because the plan-cache `put` currently happens earlier (step 4, normal-success branch), it is deferred to after this check, so a held step leaves the cache as a blocked step does.
4. No change in intelligence.py, tactical.py, candidate_selector.py or positioning.py.

## Docs (same PR)
Bible 02 section 7 sentence; a parity row; divergence entry 2.204 in the u24 block (2.203 is reserved for lane C's P1), Hardened, verified by the tests in `test_plan.md`.

## Also on this branch (rpg-planner's dispatch, unchanged files)
Two tickets to `agent-working/tickets/todos/` (TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK, TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP); the COMBAT-RETREAT widen note appended to that ticket's Implementation Notes; `record_review` for the audit ticket (863#6784395395).

## Measurement
Not run here. After the code is settled: a read-only held-step spy per the design's Measurement section, sent to rpg-planner with its sha for the designer's approval; the host belongs to lane C.

## Risks
A held subject keeps taking ordinary blows (DEFEAT may become COMBAT: relabels); a subject can be pinned beside a felt-lethal hostile that stays adjacent without striking (the same pin 2.202 has). Both are measured, not assumed.
