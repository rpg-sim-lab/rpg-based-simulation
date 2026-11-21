---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261120-A-TOWN-RETURN-PROJECT-NEVER-COMPLETES-WHEN-ITS-TARGET-IS-REACHED
phase: open
date: 2026-11-20
tags: []
---

# TCK-20261120-A-TOWN-RETURN-PROJECT-NEVER-COMPLETES-WHEN-ITS-TARGET-IS-REACHED

## Title
A town_return project stays ACTIVE after its subject reaches the town centre: no path ends it on arrival, so it holds a project slot that points at nothing

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during #781 (D73 + SEEK_WORK) by rpg-implementer's seek_work control (executed on tree 2556ecac5; raw JSON /mnt/data2/rpg-wt/freemeal-logs/seek_work_control.json). rpg-designer ruled on 2026-11-20 that it is NOT part of #781; rpg-planner filed it.
- In the control, after SEEK_WORK's arrival end (WAY_CLOSED at t20), the generic TownScorer created a town_return project targeting town_center (t30). The subject was already at the centre. The project stayed ACTIVE until t120, with the subject idle and never eating.
- Lane A's inspection on main (no run): there is no completion path for a REACH_LOCATION town_return on arrival.
  - tactical_objective._reach_location_step is a no-op at a target with no node and no building.
  - The strategic scan's completion branches (intelligence.py about :1463-1501) cover harvesting, hunger < 20, fatigue < 20 and career change. With the blocker, entity-target and guild-arrival ends, none covers town_return.
- So this reads as a pre-existing never-exit hold. It has not yet been seen on main in a run; the evidence is the inspection plus the #781 trace.

## Scope
1. Confirm it on main by execution: a subject that takes a town_return project and reaches the centre. Its own S9 if a kernel run is needed.
2. If confirmed, end the project on arrival with an existing typed end (as SEEK_WORK does with WAY_CLOSED), or another end that rpg-designer rules.
3. Whether TownScorer should also not create a town_return for a subject already at the centre is a separate ruling for rpg-designer.

## Out of Scope
- #781 (D73 / SEEK_WORK).
- TownScorer's utility formula.

## Acceptance Criteria
- An execution shows the bug on main (or refutes it).
- If confirmed: a town_return ends on arrival, with a test, and the hold count goes to 0 in the kit column below.
- Hash change disclosed with a divergence entry, if any.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781; its kit v3.5 adds the report-only column `townreturn_held_at_target`)
- TCK-20261117-RECOVER-SCORER-FALLS-BACK-TO-THE-TOWN-CENTRE-AT-ANY-DISTANCE (related town-centre fallback)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (goal hierarchy, projects)

## Related Stored Artifacts
- /mnt/data2/rpg-wt/freemeal-logs/seek_work_control.json

## Related Code Areas
- src/ai/goals/scorers.py (TownScorer); src/engine/tactical_objective.py (_reach_location_step); src/systems/strategic_systems/intelligence.py (project completion)

## Assumptions / Open Questions
- Whether other REACH_LOCATION project kinds share the same gap.

## Durable state, lifecycle and clocks
The project record is durable. The fix adds a lifecycle end (ended_by) through the existing typed project end, with no new field.

## Implementation Notes
- Report-only evidence, 2026-11-21 (executed by rpg-implementer, inspected by rpg-planner; read-only probe probe_town_return_base.py sha256 fa4223988add4846…, on a fresh git archive of ae2f837cb, with src loaded from that tree). The leashed coin-keeper setup of tests/unit/ai/test_seek_work_step.py (home (0,0), leash_radius 5, town centre (20,20), hunger 80, gold 0) gets proj_town_return_500, reach_location town_center (20,20), on the base. That target is OUTSIDE the leash (manhattan 40 > 5, the opening_steps.py:97-98 rule). So the generic TownScorer fallback can give a range-bound subject a TOWN_RETURN project it may not be able to complete. This ticket's fix should say whether a leash-excluded target is ended, skipped or left to the leash readers (M1 item 6). It is evidence, not a ruling.

## Test Summary

## Files Changed

## Completion Summary
