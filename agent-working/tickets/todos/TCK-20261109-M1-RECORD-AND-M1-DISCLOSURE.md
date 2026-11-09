---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-RECORD-AND-M1-DISCLOSURE
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-RECORD-AND-M1-DISCLOSURE

## Title
Record milestone 1 on one commit: a green gate, the cumulative watch read, m1_disclosure.md, and 5k and SimQ anchors re-recorded

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Roadmap §12.5 "Done when" items 2-6 and "Prerequisites of the record".

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. On one recorded commit: the rpg gate is GREEN, with zero unowned and zero expired validity fails (done item 2).
2. The decision-76 cumulative watch against v1 shows no stop, or every stop is ruled by the owner (done item 3).
3. Every milestone 1 ticket and every repair started is closed or moved out by owner ruling (done item 4).
4. Write docs/plans/systemic_world/m1_disclosure.md in the v1 disclosure format (done item 5).
5. Re-record the 5k behaviour test and the SimQ anchors, or record an owner-accepted staleness with a due date within 14 days (done item 6).

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).
- Changing any §12.5 criterion: that needs an owner ruling and a memo row.

## Acceptance Criteria
- All of §12.5 done items 1-6 hold on one commit, stated with evidence.
- The prerequisites are met (see Implementation Notes).

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE
- TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0 (done; F3's fix)
- TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID (done; F4)

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md
- docs/plans/systemic_world/v1_disclosure.md (format)

## Related Stored Artifacts
None.

## Related Code Areas
tools/test_architecture/ (gate), SimQ anchors

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
2026-11-09 prerequisite check (rpg-planner):
- F3, the §12.5 prerequisite TCK-20261023-CHECKPOINT-RESTORE-DRAWS-STATELESS-RANDOMS-FROM-SEED-ZERO, is met on main by #848 (66d08dd56, TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0). Both change src/engine/scenario_checkpoint.py the same way: the restore RNG is built with `base_seed=state.seed`.
- The 10-23 ticket was never on main. Its fix d690c808a sits only on the local branch rpg-checkpoint-restore-randoms (worktree .claude/worktrees/f3), which has no remote and is superseded. Deleting it is the owner's call.
- F4 (TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID) is done.
- F5 stays P3.

## Test Summary

## Files Changed

## Completion Summary
