---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT
artifact_type: plan
tags: []
---

# Plan (PROPOSAL for the designer's approval; no code): calibrate the perception gate's data values (PERC 3a)

Plan phase only. Evidence label: COMPUTED from the gate's own arithmetic (src/world/perception/gate.py:122-200, src/engine/perception_signals.py), cross-checked against the executed probe (perc02b_gap/probe_c.out: medium still at 10 tiles by day conf 0.216; small still at 2 tiles by day 0.0). The script is /mnt/data2/rpg-measure/perc02b_gap/calib_table.py, output calib_table.out. Nothing was run in the simulation.

## The gate's arithmetic (today)
score = sense x signal x max(0.05, 1 - 0.02 d) x terrain(1.0) x (0.5 + 0.5 x alertness(default 0.5)) = sense x signal x factor(d) x 0.75; perceived when score >= 0.2 (`_PERCEPTION_THRESHOLD`). Baseline observer: vision medium (0.6). At night vision drops `NIGHT_VISION_STEPS` = 2 rungs (owner Q2(a), #715 6937049127: KEEP) to low (0.3). A still body: visibility by size (small low 0.3, medium medium 0.6, large high 0.9), noise low 0.3, scent medium 0.6. The other channels of a baseline observer cannot reach 0.2 on a still body (hearing 0.6x0.3x0.75 = 0.135; smell 0.3x0.6x0.75 = 0.135), so only vision matters: small day best 0.135 < 0.2 (never); medium at night 0.3x0.6x0.75 = 0.135 (never beyond touch).

## Constraint that rules out the simple fix
Lowering only the threshold to admit a still small body (Option B below, T = 0.06) also opens the still-hearing and still-smell channels (0.135) and lets a medium body be seen at 38 tiles by day: "none at 40" fails and "still" stops meaning anything. The threshold must stay ABOVE 0.135 (the still-noise/smell ceiling), so the size levels have to rise.

## Proposal (recommended: Option C)
Move four values to data (AC4), the first four of these to the new one-record catalog family `data/content/perception/perception_settings.yaml` (a family like engagement_settings.yaml, so the values are in the catalog fingerprint; schema-validated; read through the warmed catalog, no file read at tick time):
- `perception_threshold`: 0.2 -> **0.15** (must exceed 0.135, the still-noise/smell ceiling; a 10% margin: any later change to default alertness or the level map must re-check it; a load validator refuses a threshold at or below that ceiling, computed from the same constants).
- `distance_falloff_per_tile`: 0.02 -> **0.04** (and `distance_factor_min` 0.05 unchanged).
- `night_vision_steps`: 2 (UNCHANGED, owner-ruled; moved to data only).
- `size_visibility`: small low -> **medium_high**, medium medium -> **high**, large high -> **very_high** (one rung up each; `perception_signals._SIZE_VISIBILITY`, `_UNDECLARED_VISIBILITY` medium -> high with it).
The level ladder (`_LEVEL_TO_FLOAT`, shared with the pressure resolver) and the default alertness (0.5) stay in code.

Why C and not A (one rung up and T = 0.15 but fall-off 0.02): A meets AC1-AC3 but a moving body is heard at 22 tiles (today 12) and a still small body is seen at 27 by day: perception beyond any decision radius (10) and a large shift in what the 10-tile outer bound means. C keeps a moving body heard at 11 tiles (today 12).

## The table (score vs threshold; * = perceived; baseline observer, still target, alertness 0.5, no night vision; touch at d = 1 is separate)

=== TODAY: threshold T=0.2; size->visibility {'small': 'low', 'medium': 'medium', 'large': 'high'}
size   | night | d=2    d=3    d=4    d=6    d=8    d=10   d=12   d=16   d=20   d=30   d=40  | farthest perceived (tiles)
small  | day   | 0.130   0.127   0.124   0.119   0.113   0.108   0.103   0.092   0.081   0.054   0.027  | 0
small  | night | 0.065   0.063   0.062   0.059   0.057   0.054   0.051   0.046   0.041   0.027   0.013  | 0
medium | day   | 0.259*  0.254*  0.248*  0.238*  0.227*  0.216*  0.205*  0.184   0.162   0.108   0.054  | 12
medium | night | 0.130   0.127   0.124   0.119   0.113   0.108   0.103   0.092   0.081   0.054   0.027  | 0
large  | day   | 0.389*  0.381*  0.373*  0.356*  0.340*  0.324*  0.308*  0.275*  0.243*  0.162   0.081  | 25
large  | night | 0.194   0.190   0.186   0.178   0.170   0.162   0.154   0.138   0.121   0.081   0.040  | 0
(* = perceived; touch at distance 1 is separate and unchanged)
moving body heard (hearing medium x noise medium) farthest: 12 tiles (today: 12)
still-body hearing score at d=0: 0.135; smell 0.135 -> channel closed while T > 0.135: closed
AC1 day small>=4 FAIL, medium>=8 PASS, large>=12 PASS, none at 40 PASS
AC2 night small>=2 FAIL, medium>=2 FAIL; AC3 order large>medium>small (strictly, same distance) PASS

=== OPTION C (size levels one rung up, threshold 0.15, distance fall-off 0.04 per tile): threshold T=0.15; size->visibility {'small': 'medium_high', 'medium': 'high', 'large': 'very_high'}
size   | night | d=2    d=3    d=4    d=6    d=8    d=10   d=12   d=16   d=20   d=30   d=40  | farthest perceived (tiles)
small  | day   | 0.310*  0.297*  0.283*  0.256*  0.229*  0.202*  0.175*  0.121   0.067   0.017   0.017  | 13
small  | night | 0.155*  0.148   0.142   0.128   0.115   0.101   0.088   0.061   0.034   0.008   0.008  | 2
medium | day   | 0.373*  0.356*  0.340*  0.308*  0.275*  0.243*  0.211*  0.146   0.081   0.020   0.020  | 15
medium | night | 0.186*  0.178*  0.170*  0.154*  0.138   0.121   0.105   0.073   0.040   0.010   0.010  | 6
large  | day   | 0.414*  0.396*  0.378*  0.342*  0.306*  0.270*  0.234*  0.162*  0.090   0.022   0.022  | 16
large  | night | 0.207*  0.198*  0.189*  0.171*  0.153*  0.135   0.117   0.081   0.045   0.011   0.011  | 8
(* = perceived; touch at distance 1 is separate and unchanged)
moving body heard (hearing medium x noise medium) farthest: 11 tiles (today: 12)
still-body hearing score at d=0: 0.135; smell 0.135 -> channel closed while T > 0.135: closed
AC1 day small>=4 PASS, medium>=8 PASS, large>=12 PASS, none at 40 PASS
AC2 night small>=2 PASS, medium>=2 PASS; AC3 order large>medium>small (strictly, same distance) PASS

=== OPTION A (size levels one rung up, threshold 0.15): threshold T=0.15; size->visibility {'small': 'medium_high', 'medium': 'high', 'large': 'very_high'}
size   | night | d=2    d=3    d=4    d=6    d=8    d=10   d=12   d=16   d=20   d=30   d=40  | farthest perceived (tiles)
small  | day   | 0.324*  0.317*  0.310*  0.297*  0.283*  0.270*  0.256*  0.229*  0.202*  0.135   0.067  | 27
small  | night | 0.162*  0.159*  0.155*  0.148   0.142   0.135   0.128   0.115   0.101   0.068   0.034  | 5
medium | day   | 0.389*  0.381*  0.373*  0.356*  0.340*  0.324*  0.308*  0.275*  0.243*  0.162*  0.081  | 31
medium | night | 0.194*  0.190*  0.186*  0.178*  0.170*  0.162*  0.154*  0.138   0.121   0.081   0.040  | 12
large  | day   | 0.432*  0.423*  0.414*  0.396*  0.378*  0.360*  0.342*  0.306*  0.270*  0.180*  0.090  | 33
large  | night | 0.216*  0.211*  0.207*  0.198*  0.189*  0.180*  0.171*  0.153*  0.135   0.090   0.045  | 16
(* = perceived; touch at distance 1 is separate and unchanged)
moving body heard (hearing medium x noise medium) farthest: 22 tiles (today: 12)
still-body hearing score at d=0: 0.135; smell 0.135 -> channel closed while T > 0.135: closed
AC1 day small>=4 PASS, medium>=8 PASS, large>=12 PASS, none at 40 PASS
AC2 night small>=2 PASS, medium>=2 PASS; AC3 order large>medium>small (strictly, same distance) PASS

=== OPTION A' (size levels one rung up, threshold 0.14): threshold T=0.14; size->visibility {'small': 'medium_high', 'medium': 'high', 'large': 'very_high'}
size   | night | d=2    d=3    d=4    d=6    d=8    d=10   d=12   d=16   d=20   d=30   d=40  | farthest perceived (tiles)
small  | day   | 0.324*  0.317*  0.310*  0.297*  0.283*  0.270*  0.256*  0.229*  0.202*  0.135   0.067  | 29
small  | night | 0.162*  0.159*  0.155*  0.148*  0.142*  0.135   0.128   0.115   0.101   0.068   0.034  | 8
medium | day   | 0.389*  0.381*  0.373*  0.356*  0.340*  0.324*  0.308*  0.275*  0.243*  0.162*  0.081  | 32
medium | night | 0.194*  0.190*  0.186*  0.178*  0.170*  0.162*  0.154*  0.138   0.121   0.081   0.040  | 15
large  | day   | 0.432*  0.423*  0.414*  0.396*  0.378*  0.360*  0.342*  0.306*  0.270*  0.180*  0.090  | 34
large  | night | 0.216*  0.211*  0.207*  0.198*  0.189*  0.180*  0.171*  0.153*  0.135   0.090   0.045  | 18
(* = perceived; touch at distance 1 is separate and unchanged)
moving body heard (hearing medium x noise medium) farthest: 24 tiles (today: 12)
still-body hearing score at d=0: 0.135; smell 0.135 -> channel closed while T > 0.135: closed
AC1 day small>=4 PASS, medium>=8 PASS, large>=12 PASS, none at 40 PASS
AC2 night small>=2 PASS, medium>=2 PASS; AC3 order large>medium>small (strictly, same distance) PASS

=== OPTION B (size levels as today, threshold 0.06) - shows why not: threshold T=0.06; size->visibility {'small': 'low', 'medium': 'medium', 'large': 'high'}
size   | night | d=2    d=3    d=4    d=6    d=8    d=10   d=12   d=16   d=20   d=30   d=40  | farthest perceived (tiles)
small  | day   | 0.130*  0.127*  0.124*  0.119*  0.113*  0.108*  0.103*  0.092*  0.081*  0.054   0.027  | 27
small  | night | 0.065*  0.063*  0.062*  0.059   0.057   0.054   0.051   0.046   0.041   0.027   0.013  | 5
medium | day   | 0.259*  0.254*  0.248*  0.238*  0.227*  0.216*  0.205*  0.184*  0.162*  0.108*  0.054  | 38
medium | night | 0.130*  0.127*  0.124*  0.119*  0.113*  0.108*  0.103*  0.092*  0.081*  0.054   0.027  | 27
large  | day   | 0.389*  0.381*  0.373*  0.356*  0.340*  0.324*  0.308*  0.275*  0.243*  0.162*  0.081* | 42
large  | night | 0.194*  0.190*  0.186*  0.178*  0.170*  0.162*  0.154*  0.138*  0.121*  0.081*  0.040  | 35
(* = perceived; touch at distance 1 is separate and unchanged)
moving body heard (hearing medium x noise medium) farthest: 38 tiles (today: 12)
still-body hearing score at d=0: 0.135; smell 0.135 -> channel closed while T > 0.135: OPEN
AC1 day small>=4 PASS, medium>=8 PASS, large>=12 PASS, none at 40 FAIL
AC2 night small>=2 PASS, medium>=2 PASS; AC3 order large>medium>small (strictly, same distance) PASS

## Acceptance map for Option C
- AC1 (day, baseline, still, no touch): small seen out to 13 (needs >= 4), medium 15 (>= 8), large 16 (>= 12); at 40 none (scores 0.017-0.022 against 0.15).
- AC2 (night): still medium out to 6 and still small out to 2 (>= 2 for both); a moving body is still heard further through noise (11 tiles, today 12).
- AC3: large > medium > small at every distance, day and night.
- AC4: threshold, fall-off, night steps and size visibility in data, loaded and validated (schema integers/floats in range; load check: threshold > the still-noise/smell ceiling computed from the ladder, night steps >= 0, fall-off in (0, 0.1], size map values on the ladder and strictly increasing small < medium < large).

## What C moves beyond the ticket's four rows (for the designer to weigh, none measured)
1. Every channel's reach changes: fall-off doubles (shorter) and the threshold drops (longer). Net for a medium sense x medium signal (a moving body's noise): 12 -> 11 tiles. For a species with a strong sense (a high-smell or high-vibration profile) the reach changes the same way; a table over every shipped species profile x signal level (old vs new reach, day and night) is the first code-phase deliverable, for the designer's approval before the own-job.
2. Bodies currently invisible to ordinary observers (small and still, medium at night) become perceived inside the reach above: more hostile and prey sightings, hunts, flee episodes. This is the point of the ticket; it is BALANCE (Phase 3) and reported, not gated. The own-job signal (ticket AC): perceived hostiles/prey, hunts and engagements started, 3 gate worlds s42 1000 t, base vs fix; a collapse to 0 = STOP.
3. 3b's strict xfails S3/S4 (test_expanded_goals) flip when this lands (the goblin at (2,2): d = 2 Chebyshev, 4 Manhattan; Manhattan is what the gate uses; small medium_high day at d=4 scores 0.283).
4. Hand-built fixtures at the default clock (world_time 0 is night) see less at night: tests that were set to a day clock in 3b are unaffected; any other fixture that depends on a still body at 2+ tiles at night now passes.

## Test plan (no run now)
A table test over (size x distance x day/night) pinning the rows above for the baseline observer, the three ordering/AC assertions, a refusal test for each load check (threshold at or below the ceiling, night steps negative, non-monotone size map), a fingerprint test, and the 02a tests that read `_PERCEPTION_THRESHOLD`/`NIGHT_VISION_STEPS` re-pointed at the settings accessor (tests/unit/world/test_perc02a_senses_signals_night.py lines 14, 102-106, 141).

## Docs
Bible ch04 (perception paragraph), world rule PERC-02 (the sense-range note), a divergence (next free number on main), a parity entry, the content matrix row, mechanisms.yaml (sense_gated_detection text), known limits (the 10% margin to the still-noise ceiling).

## Questions for the designer (before code)
1. Option C values (T 0.15; fall-off 0.04; size levels one rung up), or a different split between threshold, fall-off and size levels?
2. Is a still small body at 13 tiles by day (and 2 at night) right for "an ordinary observer"? (AC1 asks >= 4 / >= 8 / >= 12 and AC2 >= 2; C overshoots the minimum by about 1-9 tiles by day.)
3. May the fall-off change (which shortens every other channel's reach) ride in this ticket, or do you prefer A (fall-off 0.02, moving bodies heard at 22 tiles)?
4. The 10% margin (0.135 vs 0.15): accept with the load check, or raise the margin by lowering the still-noise/smell signal levels instead?
