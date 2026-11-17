---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT
artifact_type: test_plan
---

# Test plan — TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT

- T1 (static): raw night readers outside calendar.py = 0.
- T2: night share = 50% per day (full 2400-tick unit proof; spy only if designer rules R2 so).
- Unit: time_of_day/is_night at 599,600,1799,1800,2399,2400,2999,3000,4200 -> N,D,D,N,N,N,N,D,N.
- Behavioural: SleepScorer, evaluate_biological_needs, get_routine_utility_boost identical at t and t+2400.
- Existing: tests/unit/core/test_calendar.py, tests/unit/strategic/test_biological_needs.py, tests/unit/world/test_calamity_raid.py, test_global_raid_retired.py, ai scorer tests.
- Hard checks on CI-equivalent run (determinism, conservation, hard laws, liveness, extinction line); heavy runs only after HOST FREE.
