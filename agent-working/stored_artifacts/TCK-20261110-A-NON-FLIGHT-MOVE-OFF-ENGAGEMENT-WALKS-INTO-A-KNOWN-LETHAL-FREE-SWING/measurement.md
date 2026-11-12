---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
phase: done
artifact_type: investigation
date: 2026-11-11
tags: []
---

# Measurement record: rule S1 (2.204)

Base main 5c6990e51 (origin/main had moved to 0d6c5dba6 with no RPG src change); fix head 824483949. Pinned runner, PYTHONHASHSEED=0, arm_child sha 72320cac, spy sha 84e78113…125d, driver `drive_v3.sh` sha 50ed36d9…c81ff (the run order is in `progress.txt`; the first driver start was stopped by the old PIN STOP and the stop rule was then changed by rpg-designer). Cell results: `/mnt/data2/rpg-measure/results/5c6990e51c2c-72320cac-5000-nonflight/` and `/824483949cec-72320cac-5000/`. Per-cell figures: `measurement_cells.json`.

## Plain-twin hash checks (all MATCH)
crowded s42 e0e20c2044d7; crowded s43 609683ccdf2b; urban s42 1cd06fd261a2.

## 5-seed sums, base → fix
- crowded: COMBAT 118→125, DEFEAT 26→16, HAZARD 16→17, STARVATION 0→2, ALL 160→160.
- urban: hash-identical to base in all five seeds (COMBAT 34, HAZARD 11, DEFEAT 4; 0 held steps).

## Ruling (rpg-designer, 2026-11-11, a session message to rpg-planner; not an owner record)
"The Tier 1 trip is per world × cause on 5-seed sums: a rise of at least max(2, ceil(10% of base)) AND up in at least 3 of 5 seeds. That is the standing bar, fixed before any rows (design §Measurement and the standing rules). Tier 2, including the HELD-LINKED and FED tests, applies only to subjects of a tripped cause. In P2, no world × cause tripped, so no subject was tested and none can be FED or a STOP. Lane B's per-cell reading was not the test. Its linked rows are disclosed below, not ruled. The test is not changed after the result."

## Held steps and pins (crowded; calls = ticks)
s42 73 (longest 71), s43 70 (65), s44 3 (2), s45 38 (34), s46 8 (6). Pins of 50+ ticks: s42 e3 71 ticks from t2740, survives; s43 e33 65 ticks from t1449, dies COMBAT t2774. Both hp not observable; no linked death. Stop rule: record every pin of 50+ ticks; STOP at 500+, at the last tick, on an hp fall or on a linked death.

## Disclosed rows
- s42 e14: base DEFEAT; fix COMBAT t329, held t323/t325, hp 6, attacker 34 (the intended relabel).
- s45 e11: 1 held-linked death where base survives (untested, below the bar): held t1926 (hp 2, attacker 36, last hit 12), dies COMBAT t1935, base alive at the end. Base death tick not in the cell files.
- s45 e5: held 2117-2150 (hp 14→17), STARVATION t2161, base DEFEAT. Cited for TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW, later ruled NO CHANGE (a correct hold; rpg-designer, 2026-11-12).
- The hp-per-held-tick trace (held_hp_trace.py, 44245e0b…, approved) was not run: no tripped subject.

## Wall times (informational, not a perf measurement)
Base s: crowded 434/454/339/609/720, urban 369/314/332/362/331. Spied s: crowded 509/540/390/423/806, urban 346/292/296/337/312. Plain fix twins s: crowded s42 510, crowded s43 560, urban s42 402.

## frontier_marches (added after the corpus test failed under S1)
Cells: s42-46 x 5000, pinned runner, base 5c6990e51 against fix 824483949 (b95a77961 and 9c0b93b4e have the same src). 5 plain base cells, 5 spied fix cells (spy 84e78113…125d), plain fix twins for s42 and s44; driver `drive_v4.sh` d83b11f9…. Outputs: base cells in `/mnt/data2/rpg-measure/results/5c6990e51c2c-72320cac-5000-fm/`, fix cells in `/mnt/data2/rpg-measure/results/824483949cec-72320cac-5000/` (`frontier_marches_*.json`, `spy_frontier_marches_*.json`).
- Hash checks (spied = plain fix twin): s42 908eb3bb1441 MATCH; s44 edd02c8872a2 MATCH.
- 5-seed sums, base → fix: COMBAT 154→163, DEFEAT 35→20, HAZARD 43→45, all 232→228. No STARVATION in either arm.
- Held steps (calls = ticks): s42 519 (longest 461), s43 20 (4), s44 11 (5), s45 8 (2), s46 11 (3).
- First fix DEFEAT per seed: s43 t109, s45 t210, s46 t697, s42 t1393, s44 t1475.
- Extinction: the shaman goes from 1 alive to 0 on the 5-seed sums (s44 e47 is alive in base and dies COMBAT at t1491 in fix). rpg-designer classed it DRIFT on 2026-11-12 (a session message). owner ruling #715 6812076549.
- Alive at t5000 per role, frontier_marches 5-seed sums, base → fix (recounted by rpg-designer and rpg-planner, 2026-11-12; the two zero-alive roles are from my own count of the same cell files): shaman 1→0 (the extinction; DRIFT), hero 3→2, leader 2→1, raider 10→8, wild_creature 11→9, worker 5→10, scout 5→8, guard 4→5, predator_hunter 41→43, sentinel 21→21, alpha 5→5, blacksmith 0→0, merchant 0→0.
- Trace 1 (s44, t1470-1495, `free_swing_trace_win.py` 61a181a5…): base MATCH bfba15098d9f, `/mnt/data2/scratch-b/traces/t1_base.json` sha256 6017a6ece14c63d43bcdea2eeb469ad036ff4e346c2eb9fa71bc44de5280c5a9; fix MATCH edd02c8872a2, `t1_fix.json` sha256 0d6b9ad86e8d4453b111b63e031c3c19bf426db9dd40c530649d09d1eee28ad5; killer re-run with e40 and e39 added, MATCH edd02c8872a2, `t1_fix_k40.json` sha256 35b28a5db111b6d266efc28424dbdd708d8c17f0df132e7ca4f54fe6a016d64c. Fix e47 stays at (39,24), engaged with e39 and e40; e39 hits it for 18 twice at t1488 (hp 26→8), e40 kills it at t1491 with 18 twice. e46 (hp 12) is held at (38,21) at t1489. Base e47 is alive at hp 59-60, engaged with nobody.
- Trace 2 (s42 e31 pin, `held_hp_trace.py` 44245e0b…): MATCH 908eb3bb1441, `/mnt/data2/scratch-b/traces/hp_fm42.json` sha256 c9dc1103ae1fa1aa87c9dd6f9da2970aadca1b5ef376b8ce1dc10d7c2e72dbaf. e31 is held on 511 ticks across t1500-2371, 461 of them consecutive (t1500-1960); hp never falls during the pin (1 → 4, then 10 at t2371); last felt blow attacker 49, damage 17 throughout; DEFEAT at t2407. The felt-lethal test stays true throughout because hp stays under 17. The DEFEAT at t2407 was to e48, a hostile that had never hit it. The hold was correct: the remembered hit (49, 17) still exceeded hp, and a sleeping or collapsed hostile still lands the free swing (only a dead, inactive, lodged, frozen or stunned one does not). TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW was ruled NO CHANGE (rpg-designer, 2026-11-12) and closed by design. It reopens only on a traced hold where the free swing would not have been lethal.
- Plain fix s44 twin: 676 s, hash edd02c8872a2 = the spied hash.
## Corpus test change (disclosed)
`test_defeat_deaths_are_recorded_in_unscripted_corpus_play` ran frontier_marches s42 and needs a terminal DEFEAT inside its 400-tick window; under S1 the fix has none there. It now runs s43 with the window kept at 400. In the test's own pinned kernel: fix s43 has 1 DEFEAT by t400 (first at t110); base s42 has 2 by t400 (first at t90). The earlier figure of 8 by t400 did not reproduce on 5c6990e51 (2 measured), so it was stale. rpg-designer ruling, 2026-11-12, session message.
