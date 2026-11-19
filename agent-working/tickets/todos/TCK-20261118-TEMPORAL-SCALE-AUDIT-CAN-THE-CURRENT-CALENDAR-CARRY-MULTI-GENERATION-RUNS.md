---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS

## Title
Temporal-scale audit: can the approved 2,400-ticks/day calendar practically carry multi-generation simulation? Compare a few ticks/day values with biological compression under the current calendar, and recommend

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Owner direction #715 6967725212 (2026-11-18, the owner's own text, a "modified Option 4"): start a temporal-scale audit now, in parallel with M1.

The problem, in numbers from main (src/core/calendar.py, src/core/state.py):
- TICKS_PER_DAY = 2400. TICKS_PER_FANTASY_YEAR = 288,000 (120 days). The default max_age is 70 years, about 20.2M ticks.
- Measurement runs are 1,000 to 5,000 ticks (0.4 to 2 days). A 5,000-tick cell takes about 9 minutes on u24 (lane A's own-job, 2026-11-18).
- So a year takes about 9 h of compute, and a lifetime about 25 days. Births, gestation, growing up and marriage happen on a scale no run reaches today.
- The owner's example: at 2,400/day, a target of 50,000 ticks per generation means reproductive maturity in about 21 in-game days.

## Scope
The terms, all from the owner's text:
1. Keep 2,400 ticks/day (TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY, 2026-08-29) as the approved baseline. Do NOT change the calendar or formally reopen that decision.
2. Sensitivity analysis only: evaluate a small number of alternative ticks/day values, with no implementation.
3. Compare those against BIOLOGICAL COMPRESSION under the existing calendar (shorter life stages, gestation and lifespans per species, measured in days instead of years).
4. Measure all of these together, per scenario:
   - ticks per generation;
   - meaningful actions per generation: relationships, education or skill growth, survival, reproduction, other experiences;
   - wall-clock execution time (from the owner-approved engine profile, #715 6967441209);
   - cross-system consistency: which systems assume a day length, such as routines, sleep, meals, hunger rates, travel, cadences and seasons, and what breaks under each scenario.
5. Keep REDUCING TICKS/DAY and ACCELERATING BIOLOGICAL AGING distinct. They change simulation semantics differently and are not interchangeable.
6. Output: a recommendation document. Either the current calendar is sufficient (with which biological compression), or there is strong evidence to revisit the 08-29 decision. The options are written for the owner.
7. TICK-CONSTANT INVENTORY (owner, #715 6997605774, 2026-11-19, "Send both (Recommended)"). This is the first deliverable, and it costs nothing: no runs.
   - List every tick-valued constant in src/ and data/content: durations, cadences, cooldowns, windows, timeouts, rates per tick, life stages, gestation and maturity.
   - For each, give its file:line, its value in ticks, and its real-time meaning at 2400 ticks/day: hours, days or years of calendar time.
   - Mark each one REALISM-TUNED (it matches a believable real-world duration) or WINDOW-FITTED (chosen so that the event happens inside a test or gate run window).
   - Name the clock each one is read on, per the M1 clock review line.
   - It pairs with docs/engine/time_semantics.md once P1 lands, and is filed as a table in the recommendation doc.
   - A long-run checkpoint read was NOT approved (same comment). This ticket schedules no new run for it.
   - WIDENED by the owner's settings-in-data rule (2026-11-19, M1 epic working rules). The same inventory also lists the other existing numeric TUNING values in src (rates, thresholds, prices, radii), not only tick ones. Each is marked a setting (to move to data/) or a code invariant, with a reason. They move in stages under TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE's conditions.
   - Known seeds (inspected, main c505357b3):
     - SUSPENSION_TTL_TICKS = 200 (src/core/strategic.py:541, N10, divergence 2.212). rpg-designer reads it as a tuning value, so it goes to data.
     - EAT_PRICE_GOLD = 5 and REST_PRICE_GOLD = 10 (src/engine/service_prices.py:7-8).

## Out of Scope
- Any constant or calendar change, any architecture redesign, any speculative implementation.
- M1 births, which continues independently. Long-term population balancing waits for this decision.

## Acceptance Criteria
- One recommendation doc covering, per scenario: ticks/generation, meaningful actions/generation, wall-clock per generation and cross-system consistency. Reduced ticks/day and accelerated aging are kept as separate axes.
- Every number cites its source (code constant, engine-profile measurement, or a run with an S9 record).
- The owner gets options with a recommendation. No code changes.

## Related Tickets
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY (the 2,400 ticks/day decision; the baseline)
- TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION (aging in fantasy-year units)
- TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK (ubuntu, on origin/rpg-ubuntu-planner-filings, 5729bed5e): linked, not duplicated
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (births continues; it keeps durations as named per-species values via the calendar helpers)
- TCK-20261117-EVERY-WORLD-STARTS-AT-MIDNIGHT-SO-EVERY-SHORT-RUN-IS-DARK (also a day-length consequence)

## Related Docs
- docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md (§5, §9, §17)
- docs/plans/rpg_design_roadmap (the "Temporal axis" section)
- docs/mechanics/05_world_evolution.md (tick-to-day time)

## Related Stored Artifacts
- The external review the owner shared: tmp/temporal-problem-suggestion-ext-ai.md (owner-side file, cited in #715 6967725212)

## Related Code Areas
- src/core/calendar.py, src/core/state.py (LifecycleComponent.max_age_ticks), src/systems/lifecycle_systems/lifecycle.py, src/ai/life_stage.py, src/engine/cadence.py

## Assumptions / Open Questions
- Owners: rpg-designer owns the lifecycle and mechanics numbers. The architecture side (cross-system consistency, wall-clock) needs architecture-planner-u24, which is not running on u24 now (lead-planner-u24 is telling the owner). rpg-planner scopes the work and files the ticket.
- Which ticks/day alternatives to test: rpg-designer proposes 2 or 3 values before any analysis.
- Whether any measurement run is needed, beyond the engine profile and code reading, is decided per question. Each run needs its own S9.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
