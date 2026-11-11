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
- s45 e5: held 2117-2150 (hp 14→17), STARVATION t2161, base DEFEAT. Evidence for TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW.
- The hp-per-held-tick trace (held_hp_trace.py, 44245e0b…, approved) was not run: no tripped subject.

## Wall times (informational, not a perf measurement)
Base s: crowded 434/454/339/609/720, urban 369/314/332/362/331. Spied s: crowded 509/540/390/423/806, urban 346/292/296/337/312. Plain fix twins s: crowded s42 510, crowded s43 560, urban s42 402.
