---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100
phase: done
date: 2026-11-15
tags: []
artifact_type: report
---

# Closing run for TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100 (2026-11-15)

Run by rpg-implementer-2 (lane B) on rpg-planner's HOST FREE, read-only. Owner go: #715 6889629052; order set by 6892133979.

## Setup
- Tree: git archive of origin/main 746417022cb6caea2b795a522018c7a394ce8b32. Main was 1dbf8b6a8 when the report came in; #923 changed only a test and ticket files, so the behaviour is the same.
- World cells: frontier_living_world and crowded_frontier, s42, 2000 ticks, pinned build. The run_conditions record classified PINNED (tools/test_architecture/pinned_runner.py). Each cell ran twice; the twins are hash-equal and their JSONs identical.
  - frontier_living_world final hash e99d369365aab2eca10fc427e54d68f9f467980e8c7f79f71f2046a68acfcdcb
  - crowded_frontier final hash 8596e6b3ac1c70ec5317c9ad4b052e54c6b1882cb4b039f9c52e3a426244d843
- Peak RSS: about 220 MB per world cell, 146 MB for behavioral_5k. Available memory at each start was 4404 to 5081 MB.
- A completion is a live entity's hunger or sleep debt dropping between ticks, counted per entity-tick (the 10-07 definition).

## AC1: entities eat and sleep. PASS
- frontier_living_world:
  - eat: 50 in total, above 0 in every 100-tick bucket from t=900 on except 1700-1800;
  - sleep: 5113 in total, 0 until t=1100, then 16, 107, 79, 382, 797, 974, 1013, 821, 924.
- crowded_frontier:
  - eat: 21 in total, above 0 from t=1000 on except buckets 1300, 1600, 1700 and 1800 (also 0 at 900);
  - sleep: 1785 in total, 0 until t=1400, then 156, 536, 271, 101, 478, 243.
- Completions are above 0 in the buckets after the thresholds, as the AC requires. Not every bucket is above 0. Sleep starts at t=1100 and t=1400, which is not the hunger line at about t=950. That onset is recorded as an observation, not as a failure of this AC.

## AC2: starvation is not the majority cause and nobody dies out by t=1100. PASS
- frontier_living_world: STARVATION 0, COMBAT 14, HAZARD 5. Alive at t=900, 1100, 1200 and 2000: 43, 38, 38 and 36 of 55.
- crowded_frontier: STARVATION 0, COMBAT 26, HAZARD 4. Alive: 15, 11, 9 and 8 of 38.
- On 10-07 it was STARVATION 36 of 51 and 30 of 39, with nobody alive at t=1100.

## AC3: the behavioral_5k horizon is stated. PASS (stated, with a caveat)
- urban_political s42, 5000 ticks, through tests/regression/test_behavioral_5k.py::collect_behavioral_metrics, called unchanged. MetricsService.extract_metrics was wrapped to record the alive counts. The mean of the every-100 samples, 20.42, equals the function's alive_avg.
- Alive per 100 ticks: 28, 23, then 22 flat to t=1600, 21 at t=1700, 20 at t=2200, and 19 from t=2800 to t=5000. At t=900 to 1200 it is 22.
- The horizon is 5000 ticks, well past t≈950, and there is no collapse at the starvation line. The old 13.3 to 5.5 collapse is not reproduced (alive_avg 20.42).
- Caveat: this run is NOT_PINNED. The test's own build uses ConcurrentExecutionAdapter with a 500 ms budget; the governor is PinnedNormalGovernor and audit_mode is on. It ran once, with no twin. It states the horizon, as the AC asks; it is not pinned behaviour evidence.

## Scratch
The scratch is on /mnt/data2/rpg-measure/nobody-eats/ and is not deleted; deleting it is the owner's call.
