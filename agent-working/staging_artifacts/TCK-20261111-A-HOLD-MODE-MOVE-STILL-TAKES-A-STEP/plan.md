---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: plan
tags: []
---

# Plan (DRAFT v2, option (a) with rpg-designer's rulings Q1 = P1-b, Q2 = P3-alt; local only until the owner answers; NO src edit before then)

Recommended by rpg-designer 2026-11-14; the owner request goes through lead-planner-u24 (drafts/rpg-designer-hold-mode-owner-row.md). Cites: #715 6843780354 (run the ticket), investigation.md sections 1-10. One change in three pieces, built together.

## The three pieces, with the files
- **P1-b (the entry tick).** `MovementCandidateSelector.movement_target` (src/engine/candidate_selector.py:152-179) returns None when the pending update carries `navigation.target_clear` and no `target_set` (the update itself clears the target, so there is nothing stored to walk). The check goes before the stored/live branch (`elif holds_action_task` at :172 stays as it is). It uses the field `target_clear`, the one the patch applies (patches.py:284). **P1-b depends on P2:** without P2 the typed waits carry no `target_clear` and P1-b does nothing for them; a test pins both halves (a wait WITHOUT `target_clear` still walks, WITH it does not). P1-a (count any pending ENTITY_ACT regardless of payload) is REJECTED: it would also stop EAT / REST steps with no evidence that those steps are wrong. Why the as-worded P1 (a pending action task "with a payload") cannot be used: the actions phase runs before movement routing (pipeline.py:299 then :301) and empties a successful HOLD's payload (pipeline_phases/actions.py:317-328).
- **P2 (the gap).** The typed waits clear the stored target in the same update that sets HOLD: add `target_clear=True` to the `NavigationUpdate` of WATCH_HOSTILE (src/engine/tactical_hold.py:105-109), AVOID_NO_ROUTE (:114-118) and HOLD_CHOKEPOINT (src/engine/tactical.py:620-626). Measured: the next decision never re-chose the same target (0 of 17). Known limit (investigation 9, C2): the objective path re-derives its target at the next strategic pass (cadence 10).
- **P3-alt (the lifecycle).**
  - **Typed waits:** HOLD stays until the next decision that SETS A WALK; that decision resets the mode explicitly (WANDER, `NavigationComponent` default, state.py:494) in the same update that sets the target, at each mode-less target writer (list below). A wait that ends with no walk decision keeps HOLD and nothing steps; that is correct.
  - **Kill and collapse:** reset to WANDER when their task ends, in the task-end branch of the actions phase (pipeline_phases/actions.py:317-328): if the ending action is not `HOLD` and the effective mode is HOLD, add `movement_mode_set=MovementMode.WANDER` to the same update. Kill ends when the next swing at the dead target fails (TARGET_INCAPACITATED, actions.py:89-107); collapse ends at wake (`_survival_action_ends`, :51-58). A HOLD-action success (the typed waits) must NOT reset there. `_hold_in_place` (actions.py:77-80) and `collapse_update` (sleep_debt.py:67-73) need no change.
  - **REJECTED:** the one-site version where apply turns any mode-less `target_set` into a reset (an implicit coupling in the patch).

## The mode-less target writers (the reset list), and what I found beyond the designer's list
Every `NavigationUpdate(... target_set=...)` in src, by whether it names a mode (grep of src on origin/main 96db1f5e8):
| writer | mode today | P3-alt |
|---|---|---|
| intelligence.py:649 (material lead target) | none | explicit reset: WANDER if the current or pending mode is HOLD |
| intelligence.py:670 (objective target_position) | none | same |
| redirection.py:97 (lead redirection) | none | same |
| redirection.py:128 (objective redirection) | none | same |
| tactical_hold.py:99 (KEEP_WALKING) | inherits `entity.navigation.movement_mode` | must not inherit HOLD: write WANDER when the current mode is HOLD |
| **missed: intent/action_intent.py:139** (a `MOVE_TO` ActionIntent: `NavigationUpdate(target_set=intent.payload.get("position"))`) | none | a walk decision from the combat-engagement, information and adventure resolvers: same explicit reset |
| **missed, not a decision: executor.py:110 and worker_logic.py:34** (the per-tick reaffirm of a held ENTITY_MOVE's payload target, `target_set` only, no task update) | none | no reset: it re-emits a walk a decision already started; the guard test asserts no held ENTITY_MOVE exists under HOLD (every ENTITY_MOVE decision writes a mode, investigation 7.1, and KEEP_WALKING is fixed above) |
| intelligence.py:400, :406, :677, redirection.py:143 (town / objective REGROUP) | always REGROUP (checked: the `replace(... target_set=town_target, movement_mode_set=MovementMode.REGROUP)` at :677-680 and the fast path at :399-408 carry the mode in the same call; there is no mode-less branch) | none needed: REGROUP overrides HOLD (observed: typed-wait episodes end by `REGROUP intelligence.py:677`) |
| tactical_objective.py:42 (`_walk_to`), blacksmith.py:251 | WANDER | none needed |
| all tactical.py / tactical_hold.py / tactical_avoid.py ENTITY_MOVE decisions | a mode each | none needed |
Answer to "can :677 (regroup) ever carry no mode": no, it always carries REGROUP.
Two further things seen while listing (for the designer; not part of the build unless ruled): (1) `NavigationUpdate` has TWO clear flags: `target_clear` (applied: patches.py:284) and `clear_target` (never applied to state; only read by actor_validity.py:76 and set at actor_validity.py:116, movement.py:413 `clear_target=replan` and blacksmith.py:250), so those three writers do not clear the stored target; P1-b and P2 use `target_clear` on purpose. (2) a same-tick wait (target_clear) merged with a same-tick strategic target write: the order of the merge decides; a test pins it.

## Files and docs the build touches
src/engine/candidate_selector.py, src/engine/tactical_hold.py, src/engine/tactical.py, src/engine/pipeline_phases/actions.py, src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/redirection.py, src/engine/intent/action_intent.py; tests (test_plan.md); docs/engine/contracts/tactical_contract.md :89 (the hold is carried by the cleared target; HOLD ends at the next walk decision) and :90 (a target cleared by this tick's pending update takes no step); docs/mechanics/02_combat_laws.md :221 ("An Action Task Does Not Walk": add that a target cleared by this tick's update also takes no step) and the section 7 CONFLICT-04 paragraphs; docs/guidelines/intentional_divergences.md: a new entry, id 2.206 (u24's next free id; confirm at build time), class Bug Fix, with Observed / New Behavior / Measured / Disclosed / Verification; ledger only through tools/parity_ledger_writer.py (`write_entry`): a new combat_movement row for the HOLD law and support_boundary / v2_evidence updates on COMB-015 (combat_movement.yaml:212), COMB-338 (:4758), COMB-342 / COMB-343 (:4816, :4826) as the designer rules.
Re-baseline note: P1-b removes same-tick walking after ATTACK / SKILL decisions that carry a stored target (their updates carry `target_clear`), so combat trajectories on worlds with contact can move.

## Measurement (read-only spy per the approved method; sha approval and HOST FREE first; fix arm vs base arm)
- Stage 1: frontier_marches s42 and crowded_frontier s42, 5000 ticks (base plain-twin hashes 908eb3bb1441 / e0e20c2044d7). Stage 2, only if stage 1 passes: 3 worlds x 5 seeds, including def2.
- Report per arm: undecided HOLD steps (HOLD steps not made on a decision branch) and the opportunity attacks from them; re-wait loops within 10 ticks (a typed wait by the same subject within 10 ticks of the previous one ending); for waits, **HOLD after the next walk decision** (expected 0), for kill and collapse, **HOLD lifetime after task end** (expected 0); deaths and deaths within 10 ticks of a HOLD step; alive per role at the end.
- STOP RULES (designer-confirmed 2026-11-14), reported as they are, and a stop returns to the owner: (i) a hold of 50+ ticks beside a hostile that never hits the subject: STOP whether or not a walk decision was issued, but REPORT it SPLIT by whether one was issued, so a re-wait loop can be told apart from a blocked walk; (ii) a HOLD still in force at the last tick AFTER IT SHOULD HAVE ENDED: for a wait, after a walk decision since the hold began; for kill or collapse, after the task ended; (iii) the usual free-hit and death limits (divergences 2.89 / 2.204).
- Nothing lands from a stopped run. Owner yes at an exact sha before any push; one PR for the ticket.
