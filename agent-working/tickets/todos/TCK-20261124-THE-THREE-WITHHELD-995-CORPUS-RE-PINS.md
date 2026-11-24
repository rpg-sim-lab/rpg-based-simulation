---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261124-THE-THREE-WITHHELD-995-CORPUS-RE-PINS
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-THE-THREE-WITHHELD-995-CORPUS-RE-PINS

## Title
The three corpus re-pins withheld from #995 (urban SOCIAL, hero COGNITION, unit ECONOMY) are re-pinned once guard (ii) is clean

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Deferred outside #995 by the owner's scope freeze (#715 7132422805). The three slow corpus re-pins (urban SOCIAL, hero COGNITION, unit ECONOMY) stay withheld until guard (ii) is clean, as recorded in rpg-planner's handover. The W read (7090280198) failed P2 urban, so there is no guard (ii) yet.

## Scope
1. After #995 and #996 merge, re-measure guard (ii) on main.
2. If it is clean, re-pin the three rows with the owner's yes (a changed expectation), one owner ask covering all three.

## Out of Scope
- Any other corpus pin.

## Acceptance Criteria
1. Guard (ii) is clean, recorded with its run S9.
2. The owner's yes is recorded on #715, and the three pins match the measured values.

## Related Tickets
- #995 (rpg-free-meal-atomic)
- TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN
- TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT (related, not a duplicate: a different row, urban_political_selfmodel_probe 200t WORLD, and a bisect, not a re-pin)
- overlap scan: 2 hits; the second, TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2, is not a duplicate (a CI job exit code, not a pin value).

## Related Docs
- docs/simulation_quality/ (corpus grades)

## Related Stored Artifacts
- none yet

## Related Code Areas
- tests/ corpus diversity pins (exact ids recorded by lane A at planning)

## Assumptions / Open Questions
- Lane A's inspected read (2026-11-24, at a31bbe1bf), all in tests/unit/worldassembly/test_corpus_diversity.py:
  - urban SOCIAL: test_urban_political_seed42_1000t_social_grade_stability (l.888), row urban_political_seed42_1000t, SOCIAL 51.887 -> 37.831932773109244;
  - unit ECONOMY: test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability (l.786), row unit_selfmodel_pilot_seed42_1000t, ECONOMY 0.4079822616407982 -> 0.30831643002028397;
  - the two values were measured at e293a8c71 by grade_rows.py (ef35c736) under owner ruling 7097550602;
  - hero COGNITION: test_hero_guild_routing_seed42_1000t_cognition_grade_stability (l.767), row inferred as hero_guild_routing_seed42_1000t. It's NOT confirmed and has NO measured value; lane A's step 2 covered only the 2 rows above.
- These long_run params skip in CI (data/calibration is not in git).
- Guard (ii) isn't defined in the repo: divergence 2.223 and the town-heal ticket only say "rpg-designer re-reads guard (ii)" in the W urban cell. Get the definition from rpg-designer or the #781 materials before planning.

## Durable state, lifecycle and clocks
No durable state.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
