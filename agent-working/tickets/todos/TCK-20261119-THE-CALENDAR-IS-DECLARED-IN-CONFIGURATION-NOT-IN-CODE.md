---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE

## Title
The calendar (ticks per day, days per season, seasons per year, the night bounds) is declared in a validated configuration file and read only through the calendar helpers, not hard-coded in src/core/calendar.py

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
OWNER DIRECTION (#715, relayed by lead-planner-u24 on 2026-11-19; the owner's words): "TICKS_PER_DAY = 2400, in src/core/calendar.py should not declare here, all the simulation configuration should defined and configued in a file to allow us to change if need".

Filed by rpg-planner as a FILING ONLY. Nothing is dispatched yet.

Today (inspected, main c505357b3) src/core/calendar.py:10-18 hard-codes TICKS_PER_DAY = 2400, DAYS_PER_SEASON = 30, SEASONS_PER_YEAR = 4, the derived TICKS_PER_FANTASY_YEAR, NIGHT_START_TICK = 1800 and NIGHT_END_TICK = 600. Nine src modules import them. Raw copies outside the helper remain, for example state_presenter.py:437 and :451 (`tick // 2400`).

## Scope
Stage 1, the calendar itself (behaviour-neutral):
1. Declare the calendar in a NEW file, data/content/calendar.yaml, with its own schema class (for example CalendarProfile) registered in the content matrix and validator, like DefaultCompileProfile in defaults.yaml.
   - Why not defaults.yaml: that file holds compile-time fallbacks for units, resources and vaults. The calendar is a world law that every system reads, and it gets its own file and validation.
   - Load-time validation: positive integers; night bounds inside [0, TICKS_PER_DAY); derived values (ticks per fantasy year) are computed, never declared twice.
2. Code reads these values ONLY through the calendar helpers: is_night, time_of_day, the day bands, fantasy_years_to_ticks and the tick-per-day accessors.
   - Every current importer of the constants moves to the helpers.
   - Every raw copy (state_presenter.py:437/:451 and any others the scan finds) moves to the helpers.
3. The loaded calendar enters the run's identity: the run manifest, the env digest and the gate's config record. Runs on different calendars are then never compared as like for like.
4. A source-scan test: once the move is done, no tick-scale calendar literal (2400, 1800, 600, 30, 4 as calendar units, or 288000) remains outside the config and the calendar helper module. It follows the existing source-scan test pattern. Unrelated uses of those numbers are excluded by an explicit, reviewed list, never by loosening the scan.

Stage 2, after the temporal audit (TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS scope 7):
5. Move into configuration only the tick-based tuning constants that the audit's inventory marks as configuration, meaning the ones that must scale with the day. This is NOT a blind sweep of every tick literal. Each moved constant keeps its value and gets the same identity and scan treatment.

## Out of Scope
- Changing any calendar value. Any value change is a separate behaviour change, with re-pins and its own measurement.
- Reopening the 2,400 ticks/day decision (TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY).
- A shorter-day test profile. That's a follow-up, below.
- Balancing.

## Acceptance Criteria
- (1) BEHAVIOUR-NEUTRAL, with the same values, proven hash-equal. The final state hashes on the gate worlds must be identical before and after the move. That is a kernel run, so it needs an S9 record and kit preflight. Statics and targeted tests run after every src commit.
- (2) The calendar values a run loaded appear in its manifest and env digest. A test pins that two different calendar files give different run identities.
- (3) The source-scan test is green, and any exclusion is an explicit, reviewed list.
- (4) A missing or invalid calendar.yaml fails at content load with a typed error naming the field. There is no silent fallback to built-in values.
- Docs: Bible ch. 05 (tick-to-day time) cites the config file as the source. docs/engine/time_semantics.md does too, once it lands. The parity ledger entry for the calendar and the M1 clock review line are updated to point at the helpers.
- The perf NFR: the helpers read a value loaded once, never the file per call. State this in the PR.

## Related Tickets
- TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS (scope 7 decides stage 2)
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY (the 2,400 ticks/day decision; unchanged)
- TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT (night helper)
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC (clock review line; sequencing)

## Related Docs
- docs/mechanics/05_world_evolution.md (1 day = 2400 ticks), docs/engine/time_semantics.md (when it lands), docs/mechanics/content_usage_matrix.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/core/calendar.py; its importers in src/
- src/content/schema.py, src/content/matrix.py, src/content/validator.py (how defaults.yaml is registered)
- src/api/presenters/state_presenter.py:437/:451
- the run manifest, env digest and gate config record writers

## Assumptions / Open Questions
- LAYERING (it must be settled before code; architecture-reviewer, then rpg-designer): src/core may not import src/content (lint-imports). How do the helpers get the loaded values? The options:
  - (a) a small typed CalendarConfig in core, loaded once at content load and installed before any tick, with the helpers reading it. Its lifecycle and test isolation must be stated, because it is process-global.
  - (b) the calendar carried on the world or state config, with the helpers taking it as an argument. That's honest but touches every caller.
  - (c) core reads calendar.yaml itself, a plain file read with no content package, validated in core.
  No option is assumed here.
  - Input from lead-planner-u24 (2026-11-19; input only, not a ruling): it prefers (b).
    - Determinism and replay: the calendar lives in the state that the hash, checkpoint and replay already cover, so acceptance (2) comes almost free, and a restore gets the SAVED calendar.
    - The helpers already take world_time from state, so passing state or a small frozen CalendarSpec read off it is natural.
    - There's no process-global to leak between tests or between the cells of a multi-world process.
    - (a) is worth weighing only if (b)'s call-site churn is large (today: 9 importers plus 2 raw copies).
    - (c) breaks the layering rule.
    - Shape under (b): content loads calendar.yaml, the compiler puts a CalendarSpec on the world/state, and core helpers take it. A checkpoint saved before the change needs a fill rule in checkpoint_fields (default spec = today's values), plus an old-shape test like the other appended fields.
- SEQUENCING (rpg-planner): if stage 1 is small and proves hash-equal, it may ride as its own NEUTRAL M1 segment. Otherwise it goes after the current segment. This is decided at dispatch, after the boundary reconcile.

## Durable state, lifecycle and clocks
- New durable state: none in the world. The calendar is configuration, loaded once per run before tick 0 and never changed during a run.
- Its values are part of the run identity (acceptance 2).
- Clocks: this ticket defines how every domain-time reading is derived. It adds no clock.

## Implementation Notes
- FOLLOW-UP (owner lever, NOT in scope): once the audit says which constants must scale with the day, a "temporary shorter day/month/year" becomes a CONFIG PROFILE for test worlds: an alternate calendar.yaml selected per world or run, carried in the run identity. That's a behaviour change, with its own ticket, measurement and owner ask.

## Test Summary

## Files Changed

## Completion Summary
