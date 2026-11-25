---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261123-A-NEED-PROJECT-ENDED-AT-A-BUILDING-THAT-CANNOT-SERVE-IT-IS-RECORDED-AS-COMPLETED
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-NEED-PROJECT-ENDED-AT-A-BUILDING-THAT-CANNOT-SERVE-IT-IS-RECORDED-AS-COMPLETED

## Title
A need project ended at a building that cannot serve it now is recorded as COMPLETED while the need is still unmet

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
rpg-designer ruled during #995's case-(c) fix (2026-11-23) that this is its own ticket, so #995's re-measure isn't held up.

In src/engine/building_arrival.py, `_end_project` writes status COMPLETED when a subject's need project ends at a building that can't serve it now. One example: a subject at a SHOP with nothing to sell and a meal in reach (2.223). The need is still unmet, so COMPLETED is false durable meaning.

The fatigue branch already writes the honest form: ABANDONED plus a typed `ProjectEnd.WAY_CLOSED`. #995's follow-up (25a1f4e4f) fixed the work-building site by RE-POINTING the same project to the consume way, through `work_shift.repoint_to_consume`.

## Scope
- Every `_end_project` call site in building_arrival.py. Per site, choose one of:
  (a) the honest end: a status other than COMPLETED, plus a typed ProjectEnd reason;
  (b) the re-point through `repoint_to_consume`, where a consume way is open.
- Evidence: count, in the #995 re-measure cells (w995d), how many need-project ends were written COMPLETED with the need unmet.

## Out of Scope
- The work-building path (fixed in #995).

## Acceptance Criteria
- No need-project end is written COMPLETED while its need is unmet. A test per site, and a mutant.
- Any changed existing expectation is an OWNER ASK, in particular the re-point option at the shop for tests/…/test_a_subject_that_can_pay_for_a_meal_in_reach_still_ends_the_shop_visit (2.223).
- Docs: 2.223 and 2.224, the ch04 arrival paragraph, parity.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#995; its case-(c) fix and 25a1f4e4f)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.223, 2.224; docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None yet.

## Related Code Areas
src/engine/building_arrival.py (_end_project, _hunger_arrival, the fatigue branch), src/engine/work_shift.py (repoint_to_consume)

## Assumptions / Open Questions
- Which option per site is rpg-designer's ruling, made at dispatch. A re-point that changes a pinned test is an owner ask.
- Dispatch after #995 lands.

## Durable state, lifecycle and clocks
A project's end status and its typed ProjectEnd reason are durable. This ticket makes them true; there is no new field.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
