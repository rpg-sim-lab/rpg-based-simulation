---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: investigation
tags: []
---

# Investigation: what HOLD means for a step (read-first)

Code and docs read only; nothing run except reading the old-tree trace. Base: origin/main 96db1f5e8. Owner approval: #715 6843780354. Evidence: /mnt/data2/scratch-b/fst_out/def2_c43.json (tree 3300928e8, crowded s43, subject 1, t2939-t2942).

## 1. What HOLD means, in code
- Definition: `MovementMode.HOLD` "Staying in place, refusing to yield" (src/core/movement_modes.py:11). Consumers of the mode:
  1. Speed factor: `MovementSystem._move_speed_mult` maps HOLD to 0.0 (src/engine/movement.py:167; the function is :156-169). `resolve_move` computes it at :255 and hands it to `LegalityServiceV2.verify_movement_legality(..., move_speed_mult=...)` (:260-262).
  2. Legality: `readiness_cost = entity.combat.move_cost / max(0.1, move_speed_mult)` (src/engine/legality.py:204), refused only `if entity.combat.readiness < readiness_cost` (:206, ACTION_EXHAUSTION). The `max(0.1, ...)` clamp turns the HOLD factor 0.0 into 0.1, so HOLD makes a step cost TEN times the readiness a plain step costs, not impossible. Default `move_cost` is 10.0 (src/core/state.py:424; derived 5.0 minimum, progression/leveling.py:158-159), so the HOLD cost is 100 (50 at the minimum move_cost) and readiness is capped at 100 (src/engine/apply.py:188, patches.py:346): a subject at full readiness (and move_cost <= 10) takes the step; one that just attacked (readiness reset by -100) is refused until it regenerates. `route_movement_intent` does no check on the mode: it passes it through (src/engine/pipeline_phases/movement.py:239, :261). `MovementCandidateSelector.movement_target` and `select` do not read HOLD at all (their mode reads, candidate_selector.py:292-306, :348, :396, are for tracked-move kinds and WANDER).
  3. Yielding and swapping: an occupant in HOLD is not asked to yield (movement.py:116); two-party swaps refuse a HOLD party (pipeline_phases/movement.py:327-329; social_systems/appraisal.py:272-275).
  4. Stamina: HOLD counts as resting for stamina regeneration (engine/apply.py:175).
- So in code, "HOLD" holds the tile for OTHER entities (they cannot push it) and rests stamina; for the subject's own stored-target step it only prices the step at 10x readiness.

## 2. What the docs say
- docs/engine/contracts/tactical_contract.md:89 (Chokepoint hold, COMB-015): "movement mode `HOLD` (speed multiplier 0) plus an `ENTITY_ACT` `HOLD` ... so the tile is held by the mode and the brain re-decides on its next cadence."
- The code comments say the same intent: tactical_hold.py:103-104 ("the movement mode HOLD keeps the tile (speed multiplier 0) until the next decision") and :113 (AVOID_NO_ROUTE "a typed wait"); actions.py:78 (`_hold_in_place`: "it stays where it is until its next decision"). movement_modes.py:11: "Staying in place".
- Bible 02 section 7 (docs/mechanics/02_combat_laws.md:123-): the readiness gate and CONFLICT-04 ("an entity with an engaged, perceived, hostile entity orthogonally adjacent takes no step from a stored navigation target"); it does not describe the HOLD mode or the speed factors. Line 221 names HOLD among the action tasks that must not keep walking. The engine movement contract docs say nothing more about the factor table (COMB-011 in docs/compliance/checklist.md:121 lists "hold" among the semantic modes; ledger COMB-011, combat_movement.yaml:163, same).
- Verdict on intent (for the designer): every written statement says HOLD keeps the tile. Nothing says a HOLD subject may take a stored-target step.

## 3. Who writes the mode HOLD, with file:line
| writer | what |
|---|---|
| src/engine/tactical_hold.py:107 | `watch` verdict: a typed HOLD wait (WATCH_HOSTILE) |
| src/engine/tactical_hold.py:116 | `avoid` verdict with no route away: typed HOLD (AVOID_NO_ROUTE) |
| src/engine/tactical.py:622 | VANGUARD at a chokepoint: HOLD (HOLD_CHOKEPOINT) |
| src/engine/pipeline_phases/actions.py:79 (`_hold_in_place`, called at :338) | after a killing blow: `target_clear=True`, mode HOLD |
| src/engine/sleep_debt.py:71 | collapse sleep: `target_clear=True`, mode HOLD |
The mode is sticky: it stays on `navigation.movement_mode` until a later update sets another mode. Writers of a stored target that do not set a mode leave it as it is: intelligence.py:670 (an objective's `target_position`, `target_set` only); the town-regroup writers at :396-400 and :678 set REGROUP, and `_walk_to` (tactical_objective.py:42) sets WANDER.

## 4. The evidence, and whether it can still happen on main
- def2 crowded s43, subject 1 (hash-matched tree 3300928e8): t2939 the subject had engaged-by-catalog hostile 30 adjacent and decided `notice_unengaged_hostile` -> `avoid` with no route -> action HOLD reason AVOID_NO_ROUTE, mode HOLD (the typed wait that is meant to keep the tile). The same tick the strategic pass wrote a stored target (25,25) (stack: intelligence.py:670 in that tree) without a mode, so the mode stayed HOLD. t2940: `resolve_move` ran with mode HOLD toward (25,25), the subject stepped (27,40)->(26,40) and took the opportunity attack from 30 (hp 31 -> 9, damage 23); t2941 stepped again with nothing adjacent; t2942 stepped and the second opportunity attack killed it (hp 9 -> 0, damage 23, attacker 30).
- Why `movement_target` did not stop the step at t2940: it takes no step only for an ENGAGED (either names the other as target, hostility.is_engaged) PERCEIVED hostile adjacent (candidate_selector.py:162-178; tactical_contract.md:90: "Adjacency to a hostile that is not engaged is unchanged"). Hostile 30 was catalog-engaged (`engaged_hostiles: [30]`) but nobody named the other, so the stored target walked.
- On main 96db1f5e8 the shape is still reachable by the code path: (i) a HOLD write that leaves a stored target or lets one be written (the AVOID_NO_ROUTE and WATCH_HOSTILE waits do not clear the target); (ii) a mode-less target write (intelligence.py:670); (iii) an adjacent hostile that is not engaged; (iv) readiness at 100 and move_cost <= 10. What changed is only the last step: `_held_by_felt_lethal_swing` (movement.py:172-181) now holds a step when the subject has felt a lethal swing from an engaged hostile in `engaged_hostiles`; it does not apply to a step whose free swing is not felt to be lethal, so the first step at t2940 (31 hp vs 23 damage) is still taken on main; the later steps at hp 9 would be held. Whether it still occurs in play is a measurement, not a read.

## 5. The designer's queued finding (a): why a pinned subject chooses WANDER and not HOLD_BETWEEN_BLOWS
Two branches in `TacticalPass`, in this order, after the target is chosen (tactical.py:436):
1. Stalemate break (tactical.py:442-464): `stale_ticks` is carried in the task payload; each decision adds 5 when the current tile is in `recent_positions` (:453-455), which a pinned subject always satisfies (it does not move), so `stale_ticks > 10` is reached on the third decision. It then emits `stalemate_break_update` (tactical_hold.py:54-61: `target_set=wander_to`, mode WANDER, task ENTITY_MOVE reason STALEMATE_BREAK) unless `fighting_adjacent`, i.e. unless the CHOSEN target is orthogonally adjacent (:460-462).
2. Held swing (tactical.py:752-759): `held_swing_update` returns the queued ATTACK (HOLD_BETWEEN_BLOWS) only if the chosen `target` is adjacent, readiness < 100 and legality (with the readiness bypass) holds (tactical_hold.py:33-38).
Both depend on the CHOSEN target: `hostiles` is the list `hostile` by `perceived_hostile` (the Scope 4a test of #903), sorted with adjacent first (tactical.py:418-425), `target = legal_attack_targets[0] if legal_attack_targets else hostiles[0]` (:436). An adjacent opponent that is not in `hostiles` (not perceived_hostile: the wild-creature clause or `intruding` unset, the parked 4a causes) is never the chosen target, so `fighting_adjacent` is False, the held swing is never offered, and a subject whose position repeats reaches the stalemate break: a WANDER step the movement layer then holds (the step is refused by CONFLICT-04 or the felt-lethal hold), repeated every cadence. That is a candidate cause tied to 4a, not shown on the e31/e49 rows: it needs those rows' `hostiles` list (is the adjacent opponent in it?) to confirm. Another WANDER writer for a target walk is `_walk_to` (tactical_objective.py:42), reached by the objective pass, which also would be held beside an engaged hostile.

## 6. What is open
- Whether the shape occurs in play on main (and how often): needs a measurement (the same trace, on main) if the designer wants it.
- The designer rules the meaning: HOLD = no step (a defect in `_move_speed_mult`/legality:204 or in the stored-target writers), or HOLD = a priced step (then the docs/comments are wrong).
