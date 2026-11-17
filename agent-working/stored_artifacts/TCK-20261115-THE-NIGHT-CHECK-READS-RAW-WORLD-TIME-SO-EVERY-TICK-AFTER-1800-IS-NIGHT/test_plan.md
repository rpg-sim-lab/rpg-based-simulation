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
- Per PR: CI plus the hard validity rows of an rpg-gate-report dispatch on the pushed head (planner starts it). The extinction line is read on the host at the run-2 domain boundary (owner 6937306315), not in CI. Heavy runs only after HOST FREE.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: every night check uses the time of day; tick 2400+k classified as k | unit | helper grid + readers at t and t+k days (SleepScorer, evaluate_biological_needs, get_routine_utility_boost) + static scan | ticket AC; owner Q1(a) #715 6937049127 | night = 1200 of every 2400 ticks; readers equal across days; 0 raw night literals outside calendar.py | `pytest -n 1 tests/unit/core/test_time_of_day.py` |
| AC2: unit tests at 599,600,1799,1800,2399,2400,2999,4200 | unit | parametrized grid | ticket AC | N,D,D,N,N,N,N,N (plus 3000 D) | `pytest -n 1 tests/unit/core/test_time_of_day.py` |
| AC3: paired run | n/a | replaced by the unit proof (designer ruling R2); CI + rpg-gate-report hard validity rows | planner relay | no sim run for this item | CI-equivalent run, own slot |
| AC4: docs and ledger in the same change | review | doc check | ticket AC | survival-needs, Bible 04, STRAT-351, divergence 2.209 | `parity_ledger_writer.py --check docs/parity_ledger/strategic_cognition.yaml` |
