---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT
artifact_type: plan
---

# Plan — TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT

## Plan Status
Approved for setup by rpg-planner; code held until designer rulings R1 (int vs state signature), R2 (unit proof vs spy for T2), R3 (small extinction-line/liveness run).

## Steps
1. src/core/calendar.py: NIGHT_START_TICK=1800, NIGHT_END_TICK=600, `time_of_day(world_time:int)->int`, `is_night(world_time:int)->bool` (signature pending R1).
2. Route the 3 readers through is_night; intelligence.py:588 passes state.world_time (drop `% 2400`); intelligence.py:912 untouched beyond that.
3. Delete raid.py TICKS_PER_DAY; fix the state_presenter.py:439 docstring.
4. Tests (no expectation edits): calendar helper at 599,600,1799,1800,2399,2400,2999,3000,4200; the three readers equal at t and t+2400; static test: no raw night literal in src outside calendar.py.
5. Docs: survival-needs.md:906, Bible 04, parity ledger (diffs to planner first, writer --check only), divergence 2.209 (Bug Fix).
6. done_checker, mechanism-registry advisory, PR ask via planner.

## Scope guards
No change to day length, night window or bias size. Species/kind reads: none added.
