---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-HUNGER-SIDE-WAYS-HAVE-NO-DISTANCE-BOUND
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-HUNGER-SIDE-WAYS-HAVE-NO-DISTANCE-BOUND

## Title
inn_in_reach, work_in_reach, shop_sale_in_reach and forage count the nearest place on the whole map as "in reach" for a leash-0 subject, so "in reach" means "exists"

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane B found this while building the PRICED-WAY consumer list (main f102085e0). It is confirmed by the crowded s46 worker 1 trace, where inn 20003 was "in reach" from 11 tiles away.
- ways.py:42 inn_in_reach uses nearest_building with no distance bound. The only bound is the leash test (way_in_range), which does nothing for people because their leash_radius is 0.
- work_shift.nearest_work (work), the BUY shop sale and forage (the nearest food node with charges) are the same: leash only.
- Bounded ways, for comparison: bed (SLEEP_DEBT.bed_reach 30, FatigueScorer), scavenge (SCAVENGE_RADIUS 20) and hunt (HUNT_RADIUS 10).
EatScorer and the starvation record share the unbounded seam, so the V3 judge can call a way open when it is too far to reach before the starvation line.

## Scope
1. COUNTS FIRST, with no behaviour change. For persons in the 3 worlds × s42-46 × 5000t, at each hunger decision: the distance to the nearest inn, work building and shop, and how many eat trips go beyond 20 and 30 tiles. Send the counts to rpg-planner, who passes them to rpg-designer. The designer sets the bound from the counts.
2. Then implement the ruled bound in the shared seam, so that ways_in_reach, EatScorer and starvation_record all follow it.
   - The designer leans towards reusing bed_reach 30 for town services (inn, work, shop), with no new constant, so that "within reach" means one thing for people's buildings, and keeping forage at its own 20.
   - Alternative: an arrival-adjusted bound, "reachable before the line" (walk ticks × rate, from SURV-07's in-time clause). This is a bigger change. The counts decide between them.
3. Divergence entry, Bible/parity updates, and a paired run (a decision-input change is expected to move outcomes).

## Out of Scope
- Price or admission rules (TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY, retitled ONE-ADMISSION-RULE).
- Scavenge and hunt radii, and the bed bound (already bounded).
- Leashed kinds.

## Acceptance Criteria
- The counts table is delivered and the designer's ruling on the bound value is recorded in this ticket before any code.
- One bound definition is used by every hunger-side "in reach" field. There is no per-consumer constant.
- A test: a leash-0 subject with the only inn beyond the bound has INN_MEAL not in reach, and has it in reach at the bound.
- The paired run is reported, with any STOP routed to the designer.

## Related Tickets
- TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY (the source finding; reach was moved out of it)
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO (sequence after: EARN's arrival dispatch makes a far work building matter)
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (worker 1 at 11 tiles)

## Related Docs
- docs/mechanics/01_entity_anatomy.md (biological pressures)
- docs/plans/rpg_design_roadmap/ survival-needs (SURV-07, AGENCY-03)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/c1610/w1c/ (worker 1 execution trace)

## Related Code Areas
- src/.../ways.py:42-50, scorers.py:93-131, work_shift.nearest_work, starvation_record.py:75/:214

## Assumptions / Open Questions
- The bound value is the designer's call after the counts.
- Sequence: after EARN.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary

- **2026-11-01 evidence (F3; rpg-designer):** F3 made "full = closed" real, so far beds became reachable choices. In urban s44, subject 17 lodged at building 20006 at (65,23), about 40 tiles from the town centre (25,25), beyond the bed_reach 30 lean. It then walked a long town-return through a hostile patrol and died (ruled divergence). The bed-choice fact at t1794 (which beds buildings served it, their distances, and whether a nearer one was open) is to come from lane B. Bed choice by distance, and later exposure, belongs to this ticket. Counts first.
  - **Correction 2026-11-01 (lane B replay):** the choice was made at fatigue-project adoption (t404), with the subject at (65,32). 20006 (distance 9, 10 free beds) was the NEARER open building; 20003 is at distance 27.5. No other beds building exists. So the bed pick is not at fault. The exposure is the town-return leg from (65,22) to (25,25), and that leg is what this ticket counts.
  - **Re-routed 2026-11-01 (rpg-designer):** the town-return leg belongs to the TOWN-RETURN-BLIND finding, not to this ticket. If 20006 is inside the town region, it becomes a new P2 counts-first ticket, A-TOWN-RETURN-SENDS-A-SUBJECT-ALREADY-IN-TOWN-TO-THE-CENTRE. If not, it is a content or region question for the designer. The fact is pending from lane B.
- **2026-11-01 correction (rpg-planner):** lane B's entity-tagged re-run shows subject 17's (25,25) target came from intelligence.py:670's active-objective redirect for a resolve_blocker (blocker_congestion) project, not the town-return fallback (:678). The town-return re-route above is withdrawn; this leg goes to TCK-20261101-A-CONGESTION-BLOCKER-RESOLUTION-SENDS-A-SUBJECT-TO-THE-TOWN-CENTRE (designer ruling, P3, counts-first).
