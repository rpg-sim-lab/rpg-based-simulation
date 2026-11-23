---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261121-THE-BLOCKER-BACKOFF-WINDOW-IS-HARD-CODED-IN-CORE-NOT-DECLARED-IN-DATA
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-THE-BLOCKER-BACKOFF-WINDOW-IS-HARD-CODED-IN-CORE-NOT-DECLARED-IN-DATA

## Title
The blocker backoff window (100 ticks, doubling, capped at 800) is hard-coded in src/core/strategic.py, not declared in data

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Found by rpg-designer during the F2 v2.2a review (2026-11-21, finding E); rpg-designer ruled it a separate ticket, not F2 scope. The owner's rule (#715 6997644382) is that tuning values live in data files with load validation. On origin/main, src/core/strategic.py holds BLOCKER_BACKOFF_BASE_TICKS = 100 and BLOCKER_BACKOFF_CAP_TICKS = 800 (around :336-337). The suppression window is min(BASE << (failure_count - 1), CAP). It came in with #958 (2df2a59a6). Inspected only: git grep, by rpg-planner.

## Scope
1. Declare the two values in data with load validation. Per rpg-designer's ruling on the F2 settings (2026-11-21), use a one-record catalog family that is part of the catalog fingerprint and read through the warmed catalog, bound once and invalidated when the warmed catalog changes (the wayround_settings pattern). The natural home is data/content/strategy/blocker_settings.yaml, beside access_giveup_limit (branch-born on rpg-stalemate-nav until F2 merges).
2. LAYERING FIRST: the constants sit in src/core, and src/core may not import src/content (lint-imports). How core reads a loaded value is the layering decision of TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE; this ticket waits for it.
3. No behaviour change: the values stay 100 and 800. Prove it with a unit test that the loaded values equal them and the existing backoff tests unchanged and green.

## Out of Scope
- Changing the numbers, or the doubling.
- F2's own settings (blocker_settings access_giveup_limit, wayround_settings), which F2 carries.

## Acceptance Criteria
1. The two values are read from data, validated at load (ints >= 1, cap >= base), and part of the run identity (the catalog fingerprint).
2. src/core keeps its layering (lint-imports clean, no new ignore row).
3. The existing backoff tests are unchanged and green; a new test pins the loaded values to 100 and 800.

## Related Tickets
- TCK-20261119-THE-CALENDAR-IS-DECLARED-IN-CONFIGURATION-NOT-IN-CODE (the layering decision; blocks this)
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (F2; the finding's source and the settings pattern)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blockers)
- docs/guidelines/intentional_divergences.md (the #958 entry)

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/strategic.py (BLOCKER_BACKOFF_BASE_TICKS, BLOCKER_BACKOFF_CAP_TICKS)
- src/content/ (the loader), data/content/strategy/

## Assumptions / Open Questions
- Whether "cap >= base" is the right load check (both are tick counts in the same unit), for rpg-designer.

## Durable state, lifecycle and clocks
The values are content, part of the catalog fingerprint. No new durable state. The suppression_until_tick clock is unchanged.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
