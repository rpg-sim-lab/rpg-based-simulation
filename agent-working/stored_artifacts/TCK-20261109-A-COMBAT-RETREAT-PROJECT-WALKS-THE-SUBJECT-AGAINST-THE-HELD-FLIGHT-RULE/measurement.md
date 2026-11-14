---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
phase: done
date: 2026-11-13
tags: []
---

# Measurement: does ANY stored target step beside a hostile, and what does holding it cost? (shape iii, 2.206)

Trees: base c73d76bad (main at dispatch; src, data, config, tools/rpg_measure and tools/test_architecture identical to cd83111c5, whose plain fm s42 908eb3bb1441 and crowded s42 e0e20c2044d7 are the base twins), fix ea6417079 (parked branch `rpg-stored-target-engaged-step`, never pushed). Pinned runner (PYTHONHASHSEED=0, arm_child sha 72320cac…), 5000 ticks, MemoryMax=1G. Owner approvals: dispatch #715 6813573421; "(a) build and measure, then decide" #715 6818590421 (freeze limit); "(b) No change" #715 6842890741. rpg-designer ruled the S2 stop final (2026-11-13, session message).

## Step 1: the stored-target spy on main (stored_target_spy.py sha256 8a122160ed40bc9af7cc641eb56ac059deae81ed89ab5fcbbf04c083c16a55ef, designer-approved, args only)

Main 6e065265f, both cells hash-matched their plain twins (fm s42 908eb3bb1441, crowded s42 e0e20c2044d7), 0 exceptions; outputs /mnt/data2/rpg-measure/storedtarget/ (frontier_marches_42.json 9913d653f6c5…, crowded_frontier_42.json b25ba450224d…).
- fm s42: 1063 undecided calls beside a Legality-engaged hostile (299 stepped); 667 calls where the gate returned None; 372 of the 400 kept rows are ENTITY_ACT with an empty payload.
- crowded s42: 173 rows (80 stepped); 779 gate-None calls; 152 of 153 ENTITY_ACT rows with an empty payload.
- Designer's reading of the stepped rows: a perceived but not engaged adjacent hostile swings almost every time (fm 63/64, crowded 75/75); a not-perceived one almost never (fm 1/68). The target-naming gap (`hostility.is_engaged`: either side's payload `target_id` names the other) is the cost; the perception gap is not. Shapes (i) and (ii) were rejected; shape (iii) was ruled.
- Code read: the gate is `MovementCandidateSelector.movement_target` (src/engine/candidate_selector.py:152-179), `engaged_adjacent_hostile` needs `is_engaged`; the opportunity attack uses `LegalityServiceV2.get_engaged_hostiles` (legality.py:553-578), which does not. Writers of the stored targets: `fused_strategic_pass` (src/systems/strategic_systems/intelligence.py:670, 678, 649, 400/406), `route_movement_intent` with a stored WANDER mode (src/engine/pipeline_phases/movement.py), and src/core/updates.py merge. Readers of the gate predicate: candidate_selector.py:177 (gate), :224 (`move_ends_here`), scheduler.py:106 (Decision-32 wake, unengaged meaning).

## Step 2: S2 with the fix spy (stored_target_fix_spy.py sha256 9b3d3ca8fa3ad6f39636788c878218ea95925764b74780b913225ad682e27ece, designer-approved, both arms)

Driver st_s2_drive.sh (sha256 c98553331a3c1c7ff0cd…) with st_s2_check.py (c570b3f70c4cbbdb2cd9…), twins option A (one s42 plain twin per world per arm; the base fm and crowded twins reused from cd83111c5). Results /mnt/data2/rpg-measure/stored_target_s2/:

| cell | final hash | sha256 of the JSON (prefix) |
|---|---|---|
| plain base urban_political s42 | 1cd06fd261a2 | 4826848da8a0d9193b32 |
| plain fix frontier_marches s42 | 1c38ad9b2809 | eb374707a3708ba68205 |
| plain fix crowded_frontier s42 | 53cea37777c6 | 9fde0e81347b03de0efe |
| plain fix urban_political s42 | 8adec2d2c0bc | 6c29ca740fbdb6c8ea77 |
| spied base frontier_marches s42 | MATCH 908eb3bb1441 | c48cb8e7beea44227f5ff3588226426474d937897225f2a2d50fd2b7f6e521dc |
| spied fix frontier_marches s42 | MATCH 1c38ad9b2809 | fcab40cb66f5c74287e204b2884461ad1145d94ab3c81ca596ecd87263b4fcc6 |

The plain fix crowded s42 cell shows wall=54914 s: the host was suspended (the user journal records 5 min 59 s of CPU for that scope); the result is valid.

**Both spied cells: 0 exceptions, decision hooks present.**

| fm s42 | base | fix |
|---|---|---|
| gate-hold ticks (pairs, runs) | 377 (85, 158) | 9440 (133, 915) |
| runs of 20+ ticks | 1 | 31 |
| freeze_stop_ge50_no_hit | 0 | 23 |
| holds still in force at the last tick | 0 | 3 |
| branch totals | stored_or_live 377 | stored_or_live 5429, target_set_no_move_task 4011 |
| move_ends_here True (distinct tick/subject) / with a decision within 2 ticks | 1907 / 512 | 1145 / 350 |
| brain decisions, strategic / tactical | 8413 / 15824 | 7741 / 17625 |
| undecided steps, movement_phase: calls / OA damage taken | 299 / 835 | 317 / 34 |
| S1 pins of 50+ ticks | 1 | 0 |

Longest fix holds with 0 hits landed by the hostile: subject 7 vs 68, t3549-4349 (801 ticks; stored_or_live 401, target_set_no_move_task 400); subject 11 vs 68, t3731-4517 (787); subject 49 vs 68, t2142-2927 (786); subject 7 vs 68, t2363-3147 (785); subject 61 vs 30, t1472-2165 (694). Still held at the last tick: 11 vs 68 (t4919-4999, 81 ticks), 7 vs 68 (t4751-4999, 249), 48 vs 68 (t4701-4999, 299).

The stop was the owner's freeze limit (#715 6818590421: a hold of 50+ ticks in which the hostile lands no hit, or any hold still held at the last tick). It tripped in the first fix cell, so S2 ended after 2 of the 30 spied runs; **28 spied cells were never run**. The designer ruled the stop final; the owner chose NO CHANGE (#715 6842890741).

## Not established

- The fix removes undecided free-swing damage on fm s42 (835 to 34 over 299 and 317 undecided steps), but it was not measured in the other worlds or seeds, and the DEFEAT/COMBAT/STARVATION bars were never evaluated.
- **Loop hypothesis (UNTRACED, unconfirmed):** the long holds look like a held subject and a hostile that repeatedly re-decide into the held step (the `target_set_no_move_task` branch alternates with `stored_or_live` in the longest holds: 401/400 for 7 vs 68). The trace that would test it (fm s42 fix, subject 7 vs 68, t3549-3600, free_swing_trace_win.py 61a181a5, args only) was not run, because the owner chose no change before it.

## Findings, not tickets

- fm's 149 rows of a catalog-hostile adjacent neighbour that the subject does not perceive at distance 1 (perception failing at distance 1): handed to the producer investigation.
- 4 crowded and 3 fm rows took swing damage while NOT stepping (the step failed with LEGAL, occupancy or exhaustion): noted only.
- A pinned subject choosing WANDER into a held step instead of HOLD_BETWEEN_BLOWS (HOLD-mode ruling), and e49's FLEE_THREAT RETREAT `resolve_move` returning null with no failure_reason (producer-per-ActionIntent investigation), from the recency close.
