---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
phase: investigation
date: 2026-11-11
tags: []
---

# Investigation: Scope 1 trace (read-only)

Script: `free_swing_trace.py`, approved by rpg-designer at sha256 7c22df890e70e53b9eff3bc5547338c66e284a7b820c0c0265db8e6fbdefea20 (commit 5c4b5da11), run unchanged. Detached trees: /mnt/data2/scratch-b/wt-83004a122, wt-3300928e8, wt-aa209f2d6. `PYTHONHASHSEED=0`, 5000 ticks, one run per cell (subjects of one cell share a run).

| run | tree | cell | subjects:t | final hash vs cell | wall |
|---|---|---|---|---|---|
| flight_c42 | 83004a122 | crowded s42 | 14:323, 3:2050, 12:4971 | b6a10dd0318a = b6a10dd0318a | 532 s |
| flight_c43 | 83004a122 | crowded s43 | 37:1632, 12:3053 | f6ba069ed76c = f6ba069ed76c | 536 s |
| def2_c43 | 3300928e8 | crowded s43 | 1:2942, 8:2795 | a00b0749b8b0 = a00b0749b8b0 | 547 s |
| def2_c45 | 3300928e8 | crowded s45 | 5:1300 | 240d7b1e5107 = 240d7b1e5107 | 561 s |
| e24_u46 | aa209f2d6 | urban s46 | 24:2418 | e84737238317 = e84737238317 | 457 s |

Outputs: /mnt/data2/scratch-b/fst_out/{flight_c42,flight_c43,def2_c43,def2_c45,e24_u46}.json. Raw readout: `trace_readout.txt` here (made by `sum.py`, which only prints; it drops the dataclasses and merge frames from each stack).

## Writer lines (raw)

Every row: `MovementPhase.route_movement_intent` (src/engine/pipeline_phases/movement.py:261) calls `MovementSystem.resolve_move(state, entity, nav_target, mode)`; `resolve_move` calls `CombatResolutionSystem.resolve_multi_attack(attackers, entity, state, is_opportunity_attack=True, is_lethal=False)` (src/engine/movement.py:332 on 83004a122; :324 on 3300928e8 and aa209f2d6) and stages the new position (:396). The tick-start task is ENTITY_ACT. `nav_target` is the stored navigation.target. The last staged write to it is shown per row.

- crowded s42 #14 t323: ENTITY_ACT ATTACK payload (target 34); engaged [34]; no decision on 322 or 323; stored target (40,40), last staged tick 279, intelligence.py:fused_strategic_pass:678; resolve_move target (40,40) mode REGROUP -> (42,41); OA attacker 34, hp_before 6, damage 11, DEFEAT.
- crowded s42 #3 t2050: ENTITY_ACT {}; engaged [30,38]; no decision on 2049 or 2050; stored target (38,30), last staged tick 2049, fused_strategic_pass:678; resolve_move target (38,30) mode REGROUP -> (38,30); OA attackers [30,38], hp_before 26, damage 40, DEFEAT. Tick 2049 had resolve_move (39,30) REGROUP, engaged [] (a step back and forth between two tiles).
- crowded s42 #12 t4971: ENTITY_ACT {}; engaged [30]; no decision on 4970 or 4971; stored target (40,30), last staged tick 4970, fused_strategic_pass:678 (clear_target flag set); resolve_move target (40,30) mode REGROUP -> (41,29); OA attacker 30, hp_before 2, damage 21, DEFEAT. On 4969 a PANIC_RETREAT decision had staged target (41,30); the 4970 resolve_move had target (25,25) RETREAT.
- crowded s43 #37 t1632: ENTITY_ACT {}; engaged [30]; no decision on 1631 or 1632; stored target (31,40), last staged tick 1626, fused_strategic_pass:670; resolve_move target (31,40) mode RETREAT -> (34,41); OA attacker 30, hp_before 11, damage 12, DEFEAT.
- crowded s43 #12 t3053: ENTITY_ACT {}; engaged [30]; no decision on 3052 or 3053; stored target (34,40), last staged tick 3052, fused_strategic_pass:678; resolve_move target (34,40) mode REGROUP -> (34,40); OA attacker 30, hp_before 13, damage 21, DEFEAT.
- def2 s43 #1 t2942: ENTITY_ACT {}; engaged [30]; no decision on 2941 or 2942; stored target (25,25), last staged tick 2939, fused_strategic_pass:670; resolve_move target (25,25) mode HOLD -> (26,38); OA attacker 30, hp_before 9, damage 23, DEFEAT. Engaged was [] at the start of 2941.
- def2 s43 #8 t2795: ENTITY_ACT {}; engaged [30]; no decision on 2794 or 2795; stored target (31,40), last staged tick 2792, route_movement_intent:274 (a merge of resolve_move's own navigation update); resolve_move target (31,40) mode WANDER -> (28,41); OA attacker 30, hp_before 7, damage 23, DEFEAT.
- def2 s45 #5 t1300: ENTITY_ACT {}; engaged [30]; no decision on 1299 or 1300; stored target (25,25), last staged tick 1295, fused_strategic_pass:670; resolve_move target (25,25) mode REGROUP -> (26,26); OA attacker 30, hp_before 20, damage 23, DEFEAT.
- urban s46 e24 t2418: a decision ran on 2418 itself, not 2416: ENTITY_MOVE reason BRACKETING target 16, nav target_set (31,21), from tactical.py:evaluate_entity_intent:528 via get_bracketing_position(ally 3); no decision on 2417 (task at the start of 2418: ENTITY_ACT {}); resolve_move target (31,21) mode REPOSITION -> (30,21); OA attacker 16, hp_before 17, damage 17, DEFEAT. The tick-start stored target was (25,25), last staged tick 2417, fused_strategic_pass:670. e24 is in group 10034 [3,24].

Limits: a positional `mode` argument shows as None in `resolve_move` rows where it was passed positionally (read the caller stack, and the mode printed above is the one in the row); the nav-write source is the last staged NavigationUpdate creation, not an applied-write log; the line numbers are those of the traced tree.

## Writer diff vs 5c6990e51

Full diffs: `writer_diff_<sha>_to_5c6990e51.diff` here (files: pipeline_phases/movement.py, movement.py, intelligence.py, candidate_selector.py, tactical.py, combat.py, positioning.py).

- src/engine/pipeline_phases/movement.py (route_movement_intent), src/engine/candidate_selector.py, src/engine/positioning.py: unchanged from all three evidence shas.
- src/engine/movement.py (resolve_move and its OA call): unchanged from 83004a122. From 3300928e8 and aa209f2d6 it changed by extracting `is_evasive_flight` and `live_action_style` (the skip_oa predicate, same expression) and the OA call site moves from :324 to :332; the call arguments are the same.
- src/engine/combat.py: changed from 3300928e8 and aa209f2d6 only by passing `hit_damage_set` into the update; the OA selection is untouched.
- src/engine/tactical.py: changed from 3300928e8 (5 hunks) and aa209f2d6 (8 hunks), the flight guard and its helpers; the 5.2 bracketing block that produced e24's step is not in any hunk.
- src/systems/strategic_systems/intelligence.py: changed from all three: typed exception handlers with logging, comment edits, and one logic change at the fast-path hunk (~:392): the objective-owns-the-direction test now covers an entity-typed objective (#862). The nav-target writes at :670 and :678 are unchanged lines.
