---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-01
tags: [cooperation, social]
---

# Investigation

## Defect
A pair that formed a group re-forms and loses it about every 2 ticks. Found by the group-id verification; the cycle is older than the id fix (same pattern on base 6fdfdf555).

## Evidence (all s42, 2000t, audit_mode, FULL; base 6fdfdf555 vs branch edb638b6a; all 6 hashes equal run18)
Raw copied to `evidence/out6/` (run6.log, six jsonl, run6.sh) and `evidence/trace/` (crowded 19/33 traces, compact table, chain summary, trace_contract.py, trace6.sh). Scratch originals under /data/vboxuser/Work/groups_base/out6 and out_trace; the 2 MB chain raw is not copied.
- Formations base -> branch: crowded_frontier 225 -> 571, frontier_living_world 185 -> 1035, urban_political 96 -> 839. Whole tick +5.1%, +35.6%, +14.6% (earlier timing runs).
- Contract-missing dissolutions: 192 -> 464, 141 -> 831, 50 -> 626. FULFILLED: 15 -> 84, 26 -> 156, 35 -> 201. Expired: 0 in all.
- On the branch 1,916 of 1,921 contract-missing dissolutions end a group formed the tick before; none of the 2,304 across the 6 runs is before t100.

## One-cycle trace (crowded_frontier, entities 19 and 33, edb638b6a; trace_contract.py)
Control: forms at t102,104,...,114 and dissolutions t101,103,...,115 equal the out6 rows tick for tick.
- Contract cnt_recruit_19_33_39 (source 19, target 33) sits only on 19's map, ACTIVE, expiry 140, t94-t115; no remove or rewrite in the window.
- Group 10006, leader 19. At t100 the election gate (`tick - last_leadership_check_tick(0) >= 100`) opens; sociability 33 = 0.3606, 19 = 0.0667, gap 0.29 >= 0.2; leader 19 -> 33 (GP.resolve row, LeadershipChangedEvent).
- t101 dissolution read looks up the contract id on 33's map: absent -> contract_invalid -> dissolved at 101.
- t102 formation reads `entity_a` = 19's map: ACTIVE; new group 10008, leader 19 (`groups.py:322`), same contract; election runs the same tick (last_chk 0, gate open) -> leader 33; t103 dissolves; repeat every 2 ticks. Group ids 10008, 10010, 10011, 10012 ... (counter steps past taken ids).
- Pending updates folded into the check for the leader (33) at t101/103/105/107: beliefs, social, combat, cognition bundle, property_updates (and task/stamina at t105); none touches strategic.contracts. The formation update does not consume the contract; the contract id is copied onto the new group record.
- Chain cnt_recruit_1_8_542 (t540-646): 52 formations of [1,8], 51 dissolutions, 52 elections 1 -> 8 (sociability 0.845 vs 0.258); the contract stays on entity 1's map ACTIVE until expiry 643; the replica finds it absent on leader 8's map in 50 live-group ticks.
- Base 6fdfdf555, pair 19/33: elections 19 -> 33 at t100,102,...; groups with leader 33 and the same contract dissolve at 101,103,...: same cycle.
- Blockers: entity 19 gains one `block_no_partner_19_<tick>` blocker per tick (0 -> 6 over t102-108), grouped or not; flat in the 1,8 chain. Separate ticket.
- About 12 ACTIVE recruit contracts for 19->33 at t94 (cnt_recruit_19_33_39,54,...,74): duplicates ticket.

## Not traced
Why the election has no cooldown after formation beyond the default 0; the dissolution branch shown is a replica of groups.py:159-166 (the executed branch is the same code path, the replica reads the same two sources).

## Lifecycle pin (event-extractor characterization) and the contract counts (2026-11-01)
Evidence in `evidence/fixture/` (cnt_run.py, out json, hash logs, lag run).
- Pin: lifecycle_full_coverage_world s42 200t moves 99 rows in each of all_off_light, all_off_normal and off_ENABLE_PUSH_EVENT_SHAPERS_PHASE2 (297 config rows); first moved call 101, none before 100; dungeon_crawl and the corpus move 0.
- Why as_built and default_flags move 0 while the rollback configs move 99: with the push shapers ON (the default) `extract()` emits only 4 lines over the whole run on this scenario and none of group_joined/group_expelled/cooperation_event/contract_milestone_completed (those events come from the push shapers elsewhere); the rollback configs bring the in-extract emission back, so they carry them (9870 lines, of which 106 group_expelled, 108 group_joined, 2768 contract_milestone_completed, 1017 cooperation_event before the change). A pin that does not move under a behaviour change here means the default path does not carry the events, not that the behaviour is unchanged.
- contract_milestone_completed 2768 -> 1805 (-963): the shaper re-scans every ACTIVE contract each tick, so it follows the ACTIVE count. Measured (lifecycle_full_coverage_world s42 200t, before edb638b6a vs after d7c3a5f0e): sum of ACTIVE contracts over ticks 2419 -> 1265 (-48%), mean 12.1 -> 6.3, max 26 -> 12, ACTIVE at t150 17 -> 5 and t200 25 -> 3, contracts created 44 -> 27, max ACTIVE contracts for one pair 24 -> 6. So fewer contracts once a pair stays grouped (the pair stops re-offering while it is in a group), which is what the milestone drop follows; the drop (-35%) is not exactly proportional to the ACTIVE-tick drop (-48%) because milestones fire at contract ages, not per active tick. Feeds TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE.
- Expiry: ACTIVE contracts at `tick >= expiry_tick` become FULFILLED in `resolve_expirations` (contracts phase, before the groups phase); FULFILLED group ends are mostly duration ends. The `tick > expiry_tick` EXPIRED branch in `_binding_end` is a backstop for a contracts phase that did not run on the expiry tick; EXPIRED was never recorded in the measured runs (to be reported from the re-measure).
- MEMBERS_BELOW_TWO split (lifecycle 200t after tree): 2 dissolutions, both "other member dropped, cause not dead and not distance" (holder was the leader and held the contract; the dropped member had left by another path); the re-measure splits by distance vs dead/inactive and flags a dropped holder. A holder drifting out of a pair currently records MEMBERS_BELOW_TWO when the holder is not the leader; planner raises the precedence question with the designer.
