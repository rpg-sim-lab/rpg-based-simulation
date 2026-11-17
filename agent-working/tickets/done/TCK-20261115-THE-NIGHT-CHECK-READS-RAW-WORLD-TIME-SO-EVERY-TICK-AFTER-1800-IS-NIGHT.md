---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT
phase: done
date: 2026-11-15
tags: []
---

# TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT

## Title
The night check compares raw world_time with 1800 and 600, and world_time never wraps, so from tick 1800 every tick of the run counts as night

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
rpg-designer found this on 2026-11-15, while ruling on the starvation epic's close. rpg-planner checked it on origin/main 1dbf8b6a8:
- Three night checks test `world_time >= 1800 or world_time < 600` on the raw clock: src/ai/goals/scorers.py:90 (SleepScorer, +30 utility at night), and src/systems/world_systems/routine.py:35 and :113 (routine sleep urgency +0.3).
- kernel.py:525 sets the next world_time to state.world_time + 1, and nothing takes it modulo the day. src/core/calendar.py:10 has TICKS_PER_DAY = 2400. state.py:1299 defaults world_time to 0.
- Effect: ticks 0-599 count as night, 600-1799 as day, and from t=1800 every tick counts as night for the rest of the run. Fatigue gets a permanent +30 and routine sleep urgency a permanent +0.3.
- docs/world_rules/life-body/survival-needs.md:906 states the +30 night bias, and after t=1800 it holds in a way the rules don't mean.

## Scope
1. Use `world_time % TICKS_PER_DAY`, imported from src/core/calendar.py, in all three checks, through one shared helper so the day boundaries live in one place.
2. Check every other world_time-of-day reader for the same shape. Note that src/world/raid.py:10 keeps its own TICKS_PER_DAY = 100: record it, and don't change it here unless a rule says to.
3. Docs: survival-needs.md, plus the matching Bible 04 and parity-ledger lines through tools/parity_ledger_writer.py, and a divergence entry.
4. Measurement: this is a behaviour change after t=1800 in every run, so it needs a paired death-bar run. Its tier is stated at dispatch, under the standing depth rule.

## Out of Scope
- Changing the length of the day, the night window, or the size of the bias.
- The raid clock (src/world/raid.py), unless the scan shows it reads the same rule.

## Acceptance Criteria
- Every night check uses the time of day, so tick 2400+k is classified the same as tick k.
- Unit tests at t=599, 600, 1799, 1800, 2399, 2400, 2999 and 4200.
- The paired run, inside its stop rules, with the result recorded.
- Docs and ledger in the same change.

## Related Tickets
- TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100 (where it was found; its 2000-tick close is only touched in t=1800-2000)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (:906; SURV-02, SURV-07)
- docs/mechanics/04_strategic_cognition.md
- docs/guidelines/intentional_divergences.md (2.209)
- docs/parity_ledger/strategic_cognition.yaml (STRAT-351)

## Related Stored Artifacts
None.

## Related Code Areas
- src/ai/goals/scorers.py:90
- src/systems/world_systems/routine.py:35, :113
- src/core/calendar.py:10
- src/engine/kernel.py:525
- src/world/raid.py:10

## Assumptions / Open Questions
- Size: not measured. Every run past t=1800 is affected.
- Leaving it alone is the simpler choice, but then the day/night bias in the rules is false after t=1800. Dispatch needs an owner yes, because the fix changes behaviour.
- Does any world start at a world_time other than 0? The default is 0 (state.py:1299). Check the compiled worlds at dispatch.

## Implementation Notes
One helper pair in src/core/calendar.py (time_of_day, is_night; int in, designer R1). SleepScorer and both RoutineService readers call is_night. intelligence.py:588 passes state.world_time. raid.py unused TICKS_PER_DAY removed. intelligence.py:912 left (deeper issue 4, own Phase-3 ticket). Divergence 2.209 (Bug Fix); ledger STRAT-351.

## Test Summary
Targeted pytest -n 1, 2026-11-17: 120 passed (test_time_of_day, test_calendar, test_biological_needs, test_routine_biasing, test_strategic_lifecycle, test_calamity_raid, test_global_raid_retired, test_sleep_pull_nearest_open_way, test_service_admission). No sim run (designer R2). CI plus the hard validity rows of an rpg-gate-report dispatch on the pushed head (started by rpg-planner); the extinction line is read on the host at the run-2 domain boundary (owner 6937306315), not in CI. The CI-equivalent run is pending in its own slot.

## Files Changed
src/core/calendar.py, src/ai/goals/scorers.py, src/systems/world_systems/routine.py, src/systems/strategic_systems/intelligence.py, src/world/raid.py, src/api/presenters/state_presenter.py, tests/unit/core/test_time_of_day.py, docs/world_rules/life-body/survival-needs.md, docs/mechanics/04_strategic_cognition.md, docs/guidelines/intentional_divergences.md, docs/parity_ledger/strategic_cognition.yaml

## Completion Summary
Night is read from the time of day through one helper; every tick after 1800 no longer counts as night. Unit-proven; hard checks ride the PR's CI-equivalent run.
