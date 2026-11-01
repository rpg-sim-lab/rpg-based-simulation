---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261031-AN-INN-BED-IS-CHARGED-TWICE-PER-HOLD
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-AN-INN-BED-IS-CHARGED-TWICE-PER-HOLD

## Title
An inn bed is charged twice per hold: the worker result and the actions phase both merge the REST service delta

## Status
OPEN (counts first; found by lane B during F3; seated by rpg-planner 2026-10-31; not dispatched)

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane B (F3, rpg-sleeper-lodges) found in a real kernel tick on main 6fdfdf555 that a REST at a beds=0 inn charges the bed twice per hold: gold 50 -> 30 where one charge is 10 (50 -> 40). The worker result and the actions phase both merge the same service delta. F3 reproduces main's per-hold charge on its lodging path on purpose (charge parity, so F3's paired runs measure where a subject sleeps, not a cheaper inn); this ticket owns the defect.

## Scope
Phase 1 (counts first, read-only): (1) confirm the double merge with file:line for both merge points; (2) is it per hold or per tick of a held REST, and does it also hit EAT, WORK pay or other TOWN_SERVICE deltas; (3) on the 15-run set (3 gate worlds x s42-46, 5000t, base at or after 6fdfdf555): total gold charged by inns vs the single-charge expectation, and subjects whose double charge left them unable to pay a later meal or bed. Report to rpg-planner, then rpg-designer.
Phase 2: fix after the counts; it moves gold and so hashes; V1 conservation and the free-meal entry (TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL) are read against it.

## Out of Scope
- F3 (keeps parity with main until this lands; then F3's lodging path is re-read).
- Decision 73 (#781, the free meal).

## Acceptance Criteria
(Phase 2) One charge per service delivery through one merge point, at the price law (EXCH-02, decision 37: 10 per bed); parity row class Bug Fix; a test in a real kernel tick; V1 green; paired run with every gold diff attributed.

## Related Tickets
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE; TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL; #781

## Related Docs
- docs/mechanics/03_economic_laws.md (atomic conservation)

## Related Stored Artifacts
- lane B repro (rpg-sleeper-lodges, test notes)

## Related Code Areas
- src/systems/building_services.py; the worker result merge and the actions phase merge (to locate)

## Assumptions / Open Questions
- Sequencing relative to #781 (both move inn gold): rpg-planner proposes after F3 and before #781; an owner order question only if it must jump the queue.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
