---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT
artifact_type: investigation
---

# Investigation — TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT

## Night readers (origin/main bb26e4e5f), all raw `world_time >= 1800 or world_time < 600`
1. src/ai/goals/scorers.py:90 — SleepScorer, +30 utility at night.
2. src/systems/world_systems/routine.py:35 — evaluate_biological_needs, sleep urgency +0.3.
3. src/systems/world_systems/routine.py:113 — get_routine_utility_boost("sleep"), boost x2 at night.
No other reader (grep of src for world_time comparisons, `% 2400`, `is_night`, `night`).

## Callers
- intelligence.py:588 passes `state.tick % 2400` (already wrapped); intelligence.py:912 passes raw `state.world_time` (wrong after t=1800; deeper issue 4, own Phase-3 ticket TCK-20261117-INTELLIGENCE-RAW-TIME-PATHS-ARE-UNCALLED — route through is_night, do not delete).

## Clock
kernel.py:527 world_time+1, no wrap; state.py:1313 default 0; TICKS_PER_DAY=2400 in src/core/calendar.py:10 (pinned by tests/unit/core/test_calendar.py). Night window [1800,2400)+[0,600) = 50% of a day. Today: ticks 0-599 night, 600-1799 day, 1800+ night forever.

## TICKS_PER_DAY copies
Only src/world/raid.py:10 (=100); read nowhere in src. RaidService is an empty shell after D70; tests/unit/world/test_calamity_raid.py and test_global_raid_retired.py import it (hasattr checks), so keep the class and delete the constant. Docstring mention at src/api/presenters/state_presenter.py:439 is fixed.
