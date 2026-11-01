---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-01
tags: []
---

# Evidence: step-1 proof runs and the four trace pairs on 59f0e78bd (vs base c9b9a50f4)

Written by rpg-implementer-ubuntu. The corrections in the section "Corrections" below come from rpg-planner-ubuntu (its review of this evidence, 2026-11-01), who checked 16, 6's end and death ticks, 17 and 14 in the raw rows; I did not re-derive them and name the source for each.

## What is in here
- `proof_runs_s42/`: the three step-1 PROOF runs (s42 in each of crowded_frontier, frontier_living_world, urban_political on 59f0e78bd, m15.py output). They exist only to show that the hashes equal the fc22ae71f runs (66101cd32511, a872018bf494, ae41db137ac7). `frontier_living_world_s42.json` is that proof run; it is NOT the traced pair (the traced frontier pair is s43). Log: `proof3.log`, script `proof3.sh`.
- `pair_rows/`: the m15.py per-run rows of the four traced pairs, base and branch (urban s42, urban s44, crowded s42, frontier s43), from the 15-run set (out15/); the analysis scripts read formations, dissolutions and deaths from them. (Added after the planner noticed that the urban s44 and frontier s43 files were missing.)
- `urban_s42_victims_6_16_17.txt`, `urban_s44_victim_14.txt`, `crowded_s42_hazard_cluster.txt`, `frontier_s43_hazard_cluster.txt`: analysis output per pair. `trace_pair2.py`, `trace_set.sh`, `analyze_trace.py`, `analyze_hazard.py`: the scripts. The raw per-tick jsonl (160 MB) is not copied: /data/vboxuser/Work/groups_base/out_trace2/<world>_s<seed>/{base,branch}.jsonl.
- Controls: every traced run's hash and death list equal the 15-run set's row for that pair.

## Corrections (source: rpg-planner-ubuntu)
1. Hazard outcomes. My test only looked at the final chase target. Crowded s42 has an earlier leg: shared target 35 on three pair groups from t364-368, entity 35 dies at t431, and then every one of them re-picks 34. So "the group's shared target was never 34" does not settle 1, 6 or 7. Corrected outcomes:
   - Crowded s42, victim 1: NOT SHOWN (shared 35 at t365, idle, own target 35 at t370).
   - Crowded s42, victim 6: NOT SHOWN (shared 35 at t368, idle, target 35 at t375).
   - Crowded s42, victim 7: NOT SHOWN (shared target and own target both at t364).
   - Crowded s42, victims 5, 13, 2: FAIL stands.
   - Frontier s43, victim 5: FAIL, not NOT SHOWN. It chased 17 ungrouped from t396, before group 10044 formed at t416; my "walk starts t446" is only a re-plan of that chase.
   - Frontier s43, victim 1: NOT SHOWN stands (shared 17 at t386, then own target 17 at t390, under group 10038).
   - Frontier s43, victim 7: NOT SHOWN stands (same tick as the shared target).
   - Urban victims 6, 16, 17, 14: the FAILs stand (the planner checked them in the raw rows); frontier 8, 13, 3: FAIL as reported.
2. I wrote that the group_bias term in `target_score` is "a minor factor". That is wrong and the wording is withdrawn. In src/engine/tactical.py:428 the sort key is `(not_adjacent, group_bias, is_current_target, -capability_confidence, h.combat.hp, dist * pressure_dist_mod, h.id)`: group_bias is second, right after adjacency, so it outranks the current target, capability, hp and distance whenever the group's shared target equals the candidate. Whether it applied to a given follower is what the NOT SHOWN rows leave open.
3. Entity 6 (urban s42), end of its group and death: the out15 `dis` row for group 10009 [6,18] (cnt_recruit_18_6_173, BINDING_CONTRACT_NOT_ACTIVE / FULFILLED) has dissolution tick 274 (`dis[0]`, the tick the groups phase recorded it, `state.tick` of the phase); the traced per-tick snapshots are post-apply states, so the first snapshot without the group is t275. Death is t328 in the death rows (the post-apply tick, `new.tick`). So the gap is 54 ticks counting the dissolution tick against the death tick (328 - 274) and 53 ticks counting the first snapshot without the group (328 - 275). Both are more than 50, so the group's end is outside the 50-tick window on either reading. My report used 53 (snapshot reading) and wrote the group end as t275.

## Not checked (unchanged from my report)
Why entities 34 (crowded s42) and 17 (frontier s43) stand where they do; whether the route cost applies to these moves (route_search.py documents no hazard weight; not traced); the individual target_score components for any victim.
