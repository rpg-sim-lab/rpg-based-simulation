---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-07
tags: []
---

# combined_run: two measurement scripts (rpg-planner-ubuntu, 2026-11-07)

- `percause_check.py` (sha256 083f9b356103...): per-cause death bar over `tools/rpg_measure/arm_child.py` results, same ruler as `paired.py`; reads `<cache>/results/<sha12>-<child>-<ticks>/<world>_<seed>.json`, exit 2 (REFUSED) on a missing cell.
- `starv_trace.py` (sha256 6e373af4fc02...): per-tick trace of named entities in one cell, built exactly like `arm_child.py`; prints `MATCH` or `MISMATCH` against the cell's `final_hash` (exit 0 or 3), death rows with the typed cause, and `V3_RECORD_MISSING` when a traced id starved without a recorder record.
- `starv_trace2.py` (sha256 1f2429e269b6...): `starv_trace.py` plus per-tick group fields (gid, gleader, gsize, gtarget) and attacker fields, for the FED test.
- Positive control of `starv_trace.py`: tree 3533fde7135b, crowded_frontier s42 1000t, ids 30 1 10: `MATCH 8259e502ae16 vs cell 8259e502ae16`, death rows e10 COMBAT t471 and e1 HAZARD t528 (2026-11-07).
- Run both from the arm's `git archive` tree with `PYTHONHASHSEED=0` and `PYTHONPATH` set to that tree; the scripts are copied byte-identical from the measurement host's scratch.


## Combined run result (rpg-planner-ubuntu, 2026-11-07)

Base 4a1be4bd47908409e9b40c17ce1025c9636759a3 (ENG), new 7384a28c9f3d3622c4f936854020d6237e05b40b (the churn fix re-synced on that base); 3 worlds x seeds 42-46 x 5000t, `tools/rpg_measure/arm_child.py` (child 72320cac), pinned `build_kernel`, PYTHONHASHSEED=0. Ubuntu ran crowded_frontier and frontier_living_world (`comb_half.sh` sha256 f710bf8aefb9…, log sha256 16c5eb2022f8…); u24 lane C ran urban_political (branch rpg-combined-run-u24-urban 7c1dd511c, 11 cells, sha256 list checked before and after the copy into the ubuntu cache).
- All 15 base cells equal their e844 references; the seed-42 base repeat equals its base in every world; 0 STOP, 0 capped cells.
- `git diff --name-only 4a1be4bd4 3078d71d9 -- src data config` is empty (ENG's final adds no src/data/config change to the measured base).
- Carry to main with ENG and #837: same sequential world, not same source. #837 is parity only and leaves sequential results unchanged (owner-approved design); its 4 pre-fix sequential pins equal fixed sequential (crowded s45 2200t, crowded s42, frontier s42, urban s42; pre-fix = 9eeb0fd97 src, fixed = e5c0c176a, per #837's review notes); it changes no data/ or config. Void rule: if any later post-#837 run of a combined-run cell gives a different final_hash, the carry is void and goes back to rpg-designer.
- Walls are not cost figures: on this VM identical code swings by 36% or more.

### `paired --collected` (all 30 cells; output sha256 234edccb4077…)
People deaths base -> new: crowded_frontier 164 -> 169 (+5, SE 0.71, no drift); frontier_living_world 122 -> 106 (-16, SE 1.24, REPORT-ONLY, fewer); urban_political 57 -> 55 (-2, SE 1.33, no drift). No extinction STOP.

### `percause_check.py` (blob af87cb61, `--known crowded_frontier:46:9`; output sha256 e8ddf5686cfd…)
TIER1_NOT_FIRED in every world.
- crowded_frontier: HAZARD 21 -> 25 TIER2 (s42 2 -> 11, s44 5 -> 6); COMBAT 82 -> 88 TIER2 (s43-s46 up); DEFEAT 61 -> 55 report-only.
- frontier_living_world: HAZARD 44 -> 31, COMBAT 75 -> 66 (report-only), DEFEAT 32 -> 26; no Tier 2.
- urban_political: HAZARD 11 -> 13 TIER2 (s44 e22, e4); COMBAT 24 -> 25 TIER2 (s42 e1, e16, e24, e6, e8); DEFEAT 22 -> 17.
- Known entry crowded_frontier s46 e9: ABSENT on the new arm.
- Unmatched new-arm starvations: crowded_frontier s45 e31 (hero) and frontier_living_world s45 e53 (wild_creature).

### Crowded s45 arm trace (`starv_trace2.py`, sha256 1f2429e269b6…)
Tree 7384a28c9f3d, ids 31 1 11 12 33 5 6 7: `MATCH 2209d09642c0 vs cell 2209d09642c0`. Rows (sha256 005a54f05673…) are held in the measurement host's scratch, not committed.
- The 7 COMBAT death rows carry the cell's cause. e31's death row reads cause null at t2439, where the cell and its V3 record say STARVATION; this is not explained.
- e31 (hero), starved t2439. V3 verdict UNTRIED_STEP: no way attempted; INN_MEAL and FORAGE in reach at death; last_meal_tick null (a caveated recorder field; the meal check saw one hunger drop at t810). Its food need was displaced by injury: hp 83 -> 8 in t1397-1500, first hit by raider 15 on a tile it held before joining group 10043. The group target 15 followed e33's own pick, so the shared target was its own attacker (reachability only). NOT FED.
- COMBAT victims, each read over its last 60+ ticks, all NOT FED: e6, its own BRACKETING pick (one re-engage a tick after the group target was set is disclosed); e33, the leader's own pick; e5 and e7, their own hunger walks to the inn; e11, no group; e1 and e12, no changed step shown (each stood on the inn tiles taking hits while grouped; the writer of that idle act is not recorded).
- Untraced by rpg-designer's scope, disclosed: crowded s44 (+3 COMBAT, HAZARD hero e32), and the crowded s43 and s46 victims.

### Known entries accepted by the owner (#715 6702815851)
crowded_frontier s45 e31 under LOW-HP-RETREAT and frontier_living_world s45 e53 under CREATURE-BOTH-NEEDS; each expires when its fix lands or on 2026-11-30. testing-planner adds the entries.

### Traces held on u24 (cited, not restated)
Relayed word for word from lead-planner-u24 via lead-planner (2026-11-07); each sha256 computed by lead-planner-u24. Held on u24 under /mnt/data2/scratch-c3/, not transferred.

(1) Urban Tier 2, urban_political s42 (COMBAT) and s44 (HAZARD), 5000t
Pass 1, starv_trace.py 59f8ed96, run_trace.log:
- trace_base_s42.jsonl 047203ea729076272949c62414009038642aa489fb02f024a621ce89aee05e15. MATCH 9673dcef26b2 vs cell 9673dcef26b2
- trace_arm_s42.jsonl 4db714e22d6eed09a1d3d129dd85ab281be4e1657f7c4479214abd79050204b4. MATCH 02d9a849caf2 vs cell 02d9a849caf2
- trace_base_s44.jsonl 10e385f48446dee85f9b984a9c32d206449e544faec3c8e9d2f4017e1d7811ce. MATCH 38de907b8deb vs cell 38de907b8deb
- trace_arm_s44.jsonl e97824c78be8af11bb735f44ed35eb301c9871f92ac358476292deebdb547e2d. MATCH 745c2a24072d vs cell 745c2a24072d
Pass 2, starv_trace2 1f2429e2, run_trace2.log, same four MATCH lines:
- trace2_base_s42.jsonl 876dab1565eb5e49a9c38ce6667d21457291f9c7b0d4b0f7201ee3c9ec3599bb
- trace2_arm_s42.jsonl d8caabedefc1a1e7396a61606a2ae66f1f69d8ef25f8bbf24219b97fa4e9024d
- trace2_base_s44.jsonl a4ce1811bcd54cd217aa8bac2e1a2ea40677784065f7c95eb48e7ff85f796830
- trace2_arm_s44.jsonl 3b93c8ccaa210fb5710b47ecf67518c8e63cb8ee213eea31856fc1a10bebe7be
Verdict (rpg-planner's closing message, as relayed; not a rpg-designer ruling): 0 FED, 7 NOT FED (s42 COMBAT e6, e16, e24, e1, e8; s44 HAZARD e22, e4). e16's provisional FED was withdrawn on direct reads. The probe_e16 counterfactual was INCONCLUSIVE and is not the basis.

(2) crowded_frontier s42 base/arm, starv_trace2, run_crowded.log
- crowded/trace2_base_crowded_s42.jsonl 87ec34814a0ae8bc595819cdbb9f14ed590b764d22849912173fec92f5fcbe58. MATCH 84d59e28fc8a vs cell 84d59e28fc8a
- crowded/trace2_arm_crowded_s42.jsonl 84b1995dc0cc89d99459c02b7dbd4dfc02328ae8cdfa6e843a6b650e8d2c0335. MATCH c5f6398be896 vs cell c5f6398be896
Verdict: 0 FED, 11 NOT FED, 2 NOT SHOWN (e1's walk, e32's retreat route), disclosed. The HAZARD cluster is the known H1 gap.

(3) frontier_living_world s45 e53, arm only, starv_trace2, run_fliving.log
- fliving/trace2_arm_fliving_s45.jsonl 69c90c9cfa8939412b9ef652a8ec109519f4b16b039e8b6d0475e9f10b563da2. MATCH 17f4697e9f2a vs cell 17f4697e9f2a
Verdict: NOT FED. Cause STARVATION: e47's last hit at t2566 left hp 1, and drain took the last point at t2572. Known-entry candidate under TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH, accepted at #715 6702815851. e47's approach is NOT SHOWN.

(4) crowded_frontier s45 arm, dissolution-reason re-run, run_groups.log
- cf45/groups_arm_cf45.json 6174a907937fadbe1dd6e771741f7263af06a8a9602fc9543bb07fe1499fd1e5. Log line: DONE 2209d09642c0d93d15ee376238f96cd1d14395d1f4cc6b234e67994053b34e76 (the full final_hash, equal to the cell's).
Verdict: no STOP. None of 10049, 10053, 10054, 10088 or 10089 is BINDING_CONTRACT_MISSING. Four are BINDING_CONTRACT_NOT_ACTIVE/FULFILLED and 10054 is MEMBERS_BELOW_TWO; all five are contract-bound.

(5) AC 4 leadership-check re-run, a separate output, run_groups2.log
- cf45/groups2_arm_cf45.json 1940f906b37e0ff90da7d32345ab952d7bbed3231debaf93e75ed8ad8ea2f108. Log line: DONE 2209d09642c0d93d15ee376238f96cd1d14395d1f4cc6b234e67994053b34e76
Verdict: AC 4 holds on all 5 groups; last_leadership_check_tick is stamped at formation (first-live − 1). formation_tick is 0 everywhere because nothing in src writes it, a separate P3 defect outside #828.

Caveat (u24): (4) and (5) print DONE <final_hash>, not "MATCH vs cell"; the value equals the cell's 2209d096… exactly.
