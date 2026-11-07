---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK
phase: open
date: 2026-11-01
tags: [cooperation, social]
---

# TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK

## Title
An entity with no partner gets one new strategic blocker per tick, with a new id each time, so strategic.blockers may grow without bound. Count it first.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found in the churn trace; rpg-designer asked for this finding, counts first, lean P2. Trace on crowded_frontier, s42, tree edb638b6a: entity 19's strategic.blockers rise by one per tick over t102-108 (0, 0, 1, 2, 3, 4, 5, 6), ids `block_no_partner_19_<tick>`, from the cooperation DEFER_NO_PARTNER path, in grouped and ungrouped ticks alike. The implementer read the source of the path; I checked the id and the count only. In the `cnt_recruit_1_8_542` chain, blockers stay flat at 1 (entity 1) and 2 (entity 8), so this is not every entity.

strategic.blockers per living at t2000, base 6fdfdf555 to branch edb638b6a: crowded_frontier 170 to 88 (3 and 11 survivors, so weak), frontier_living_world 63 to 132, urban_political 27 to 58. Raw: /data/vboxuser/Work/groups_base/out6/ and out_trace/ (scratch). Whether this blocker explains that rise is a lean, not measured. Note that the rise itself comes with the churn on the branch, so re-count after the churn fix.

## Scope
1. Counts, after the churn fix lands: blockers per living by id family at t500, t1000 and t2000 in the 3 worlds; how many are `block_no_partner_*`; whether any are ever removed or expire.
2. Trace why the id carries the tick and what resolves or reaps a blocker.
3. Send the counts to rpg-designer via the leads, then fix as ruled.

## Out of Scope
- The churn fix itself.
- Other blocker families, unless the counts say they are the carrier.

## Acceptance Criteria
1. Counts are in investigation.md with run, seed and commit.
2. rpg-designer's ruling is recorded word for word before any fix.
3. Fix criteria are set from that ruling, with a positive control.

## Related Tickets
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (found here; rpg-designer's ruling is word for word in that ticket)
- TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE (same finding round)

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/cooperation/ (DEFER_NO_PARTNER; exact site not yet cited)
- src/core/strategic.py

## Assumptions / Open Questions
- Priority is the designer's lean; the counts may change it.
- Not dispatched. Counts need a go for the run set unless the churn ticket's re-measure can carry the field.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
