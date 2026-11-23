---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM

## Title
Three bodies starve to death with ways untried (V3) once #991 stops the illegal town heal: the cause is unread

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Exposed by PR #991 (TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES).
- The gate diff (testing-planner, #715 7076501395, plus the newest lead-planner comment): PR head 4e6a06fa5 (run 44998631861) against main 613a8365b (run 44998634291).
- 109 rows moved, consistent with starving bodies in town now dying.
- The gate is RED with three NEW unowned V3 rows, starvation deaths with ways untried:

| world | seed | entity | kind | tick | untried |
|---|---|---|---|---|---|
| frontier_living_world | 45 | 5 | human | 3472 | BUY, FORAGE, HUNT_EAT_RAW, INN_MEAL, WORK_SHIFT |
| crowded_frontier | 45 | 30 | goblin | 3618 | as recorded by the gate |
| frontier_living_world | 42 | 30 | goblin | 2588 | FORAGE, INN_MEAL |

rpg-designer ruled them EXPOSED, pre-existing defects, not a #991 regression. #991 only removes a heal past the line the law forbids (D36/D42), and these bodies were stuck before 95 and kept alive until now.

CAUSE UNREAD: the gate documents carry only id, kind, tick and the untried list. They hold no project, objective, step or wage fields, so no attribution can be made (ubuntu lead, 2026-11-22).

Two candidate causes, named and NOT claimed:
1. #781's earn_then_buy never-exit step: the step stays open and never pays, so the next step is blocked (trace kit v4 stage 2 is running and will show the mechanism).
2. Step A's resolved objective that keeps pulling (TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT). FLW/42 goblin 30 is the SAME body as the O3 stage-2 subject. Under #991 it starves at t2588, 22 ticks before the hunt killed it at t2610 on main's arm. rpg-designer's stage-2 read shows it held a RESOLVED fatigue objective for most of its window, so its not-eating may share Step A's cause.

## Scope
1. When #781's v4 stage-2 read is in: decide per row whether the mechanism matches earn_then_buy (then merge into #781's earn fix), Step A (then merge into Step A), or neither (then a read-only trace of these rows with its own S9).
2. Once the cause fixes land: re-run the gate. The three rows must be gone, or re-attributed with a cause.

## Out of Scope
- Any change to #991's heal gate. It is correct and is not to be changed to hide these rows.
- Any fourth V3 row in a later run. It is not covered here and needs its own read.

## Acceptance Criteria
1. Each of the three rows has a read cause (inspected/executed), linked to the ticket whose fix removes it.
2. The gate re-run after those fixes shows the rows gone or re-attributed.
3. The known entry for these rows is removed when they are.

## Known entry (for the owner packet on #991; testing-planner scopes it)
- It names exactly the three rows above (world, seed, id, tick, kind, untried list) and cites this ticket.
- It expires on the EARLIER of: this ticket's cause fixes landing (when the gate re-runs), or 2026-12-15.
- Not covered: any other row.
- Also in the same packet: RETIRE the #989 e55 entry (FLW s42 e55) with the reason "superseded: under #991 e55 no longer dies at this tick; the defect stays open under its ticket and shows as its own row if it recurs". The e55 ticket (TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE) stays OPEN.

## Related Tickets
- TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES (#991, the exposer)
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781, the earn_then_buy read)
- TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (Step A)
- TCK-20261122-AN-ARENA-OF-PREDATORS-AND-PREY-SHOWS-HOW-ATTACKED-BODIES-REACT
- TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE (e55; stays open)

## Related Docs
- docs/mechanics/01_entity_anatomy.md (Staged Starvation D36, Natural Healing D42)
- docs/world_rules/life-body/survival-needs.md (SURV-02, SURV-07)

## Related Stored Artifacts
- The gate runs 44998631861 and 44998634291 (GitHub); testing-planner's notes on ubuntu (town_heal_991_moved_rows.md, sha256 340ef0b4…)

## Related Code Areas
- src/ai/goals/opening_steps.py (earn_then_buy); the strategic objective lifecycle

## Assumptions / Open Questions
- Whether one cause covers all three rows is unknown.

## Durable state, lifecycle and clocks
None.

## Implementation Notes
- 2026-11-22, rpg-designer's read of the #781 v4 stage-2 trace (trace_full_v4_designer_read/read_notes.txt): at a SHOP, `_hunger_arrival` ends the project as a finished sell visit before the meal and work branches (src/engine/building_arrival.py:43-66), so a broke subject never gets its takeable shift and loops. That is a CANDIDATE for FLW/45 human 5 (untried includes WORK_SHIFT and BUY). It is NOT for FLW/42 goblin 30 (untried FORAGE, INN_MEAL, no work), whose candidate stays Step A. The rows merge only if the post-fix gate run removes them.

## Test Summary

## Files Changed

## Completion Summary
