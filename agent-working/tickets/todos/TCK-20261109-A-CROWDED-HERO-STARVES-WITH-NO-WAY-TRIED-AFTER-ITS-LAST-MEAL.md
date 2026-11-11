---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261109-A-CROWDED-HERO-STARVES-WITH-NO-WAY-TRIED-AFTER-ITS-LAST-MEAL
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-A-CROWDED-HERO-STARVES-WITH-NO-WAY-TRIED-AFTER-ITS-LAST-MEAL

## Title
Crowded_frontier s45 hero 31 starves at t2439 with no way tried after its last meal, on main and on the LOW-HP fix

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
crowded_frontier s45 hero 31 starves at t2439 on main and on the LOW-HP fix (tree f4d68046d). Its record reads last meal t810, no way attempted, verdict UNTRIED_STEP (recorder 777ede6e2). It is out of the LOW-HP fix's reach: the fix arm's record is identical to the base arm's.

## Scope
1. Trace on the pinned runner why no way is attempted between t810 and t2439 (the ways in reach at the death record are INN_MEAL, FORAGE and WORK_SHIFT).
2. Name the cause, then decide the fix or record the owner's ruling.

## Out of Scope
- The low-hp retreat and panic-freeze sites (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE).
- The starvation recorder (done in #850).

## Acceptance Criteria
- The cause is named, and the fix or the owner's ruling is recorded.
- The known entry for crowded_frontier/45 entity 31 in tools/test_architecture/rpg_gate_known.yaml is deleted when the fix lands.

## Related Tickets
- Owner's filing ruling: #715 comment 6735771688 ("(a) New ticket owns e31").
- TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
- TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT (done in #850)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-06/07)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE/evidence/cells.json (the fix arm's s45 record)

## Related Code Areas
- src/observability/starvation_record.py (the record)
- src/engine/tactical.py, src/engine/tactical_objective.py (the need path)

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes
Not started.

## Test Summary

## Files Changed

## Completion Summary
