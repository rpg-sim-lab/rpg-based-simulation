---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE
phase: open
date: 2026-11-01
tags: [cooperation, social]
---

# TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE

## Title
One pair can hold about 12 ACTIVE recruit contracts at once, each with a new id. Count it across the runs first; P2 if material.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found in the churn trace; rpg-designer asked for this finding, counts first, P2 if material. Crowded_frontier, s42, tree edb638b6a: at t100 entity 19 holds exactly 12 ACTIVE recruit contracts with target 33: `cnt_recruit_19_33_39`, then `_54` to `_74` in steps of 2. Expiry is the id's suffix plus 101. If the suffix is the creation tick (a reading, not traced), these were created at t39 and t54-74, before the pair's first contract-missing dissolution at t101, so the churn is not their only source.

strategic.contracts per living at t2000, base 6fdfdf555 to branch edb638b6a: 55 to 48, 30 to 30, 10 to 41 (crowded_frontier, frontier_living_world, urban_political). A gate on concurrent pending offers already exists (TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST, Mechanics Bible chapter 04); whether it should cover accepted contracts has not been checked.

## Scope
1. Counts: ACTIVE recruit contracts per pair at t500, t1000 and t2000, 3 worlds, before and after the churn fix.
2. If material, trace which path creates a second contract for a pair that already holds one ACTIVE.
3. Send the counts to rpg-designer via the leads, then fix as ruled.

## Out of Scope
- Which contract binds a group: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS records one at formation.
- The contract's time limit.

## Acceptance Criteria
1. Counts are in investigation.md with run, seed and commit.
2. rpg-designer's ruling is recorded word for word before any fix, or the ticket closes by disposition if the counts are not material.
3. Fix criteria are set from that ruling, with a positive control.

## Related Tickets
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (found here; rpg-designer's ruling is word for word in that ticket)
- TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST (pending-offer gate)
- TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK (same finding round)

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/cooperation/phase.py
- src/systems/social_systems/ (recruit contract creation; exact site not yet cited)

## Assumptions / Open Questions
- Note for the binding fix: formation takes the first contract by sorted id. With several ACTIVE for one pair, the group ends when that one ends, and could re-form on the next. The re-measure's re-formation count will show this.
- Not dispatched.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary

## Evidence added 2026-11-01 (profile inside GroupPhase.resolve, frontier_living_world s42 2000t, pinned FULL, on the churn tree with step (a), a6902557b; raw /data/vboxuser/Work/groups_base/out_profA/frontier_profile.json)
`_formation_partner` calls per window (t<=666, 667-1333, >=1334): 53,049 / 160,805 / 178,874. `_gather_formation` per call: 4.5 / 9.7 / 15.1 us (cProfile-inflated). Consistent with contracts per ungrouped entity rising; contracts were not counted per window, so this is not shown. Base's loop also scans every contract with no break, so the scan is not new to the churn fix. When this ticket's counts run, count contracts per ungrouped entity per 1000t, including at 5000t, since a rising scan would show in 5000t tick time.
