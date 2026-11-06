---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261103-BROKE-HUNGRY-WORKERS-STILL-TAKE-NO-SHIFT-ON-MAIN
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-BROKE-HUNGRY-WORKERS-STILL-TAKE-NO-SHIFT-ON-MAIN

## Title
After #789, broke hungry frontier workers still take no work shift and starve about 1900 ticks with every way open: counts first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by lane A's probe B (frontier s43 and s45, pinned, base 65d43dfa9 and ENG head e844e2845, hashes equal to paired). Requested by rpg-designer on 2026-11-03. It is a main finding, not ENG's: both arms are identical on these subjects.

Seven frontier workers starve about 1900 ticks each, 12804 starving ticks in total, the same on both arms. On those ticks, from direct reads:
- gold 0;
- ways open: BUY, FORAGE, INN_MEAL and WORK_SHIFT on 7204 ticks, FORAGE, INN_MEAL and WORK_SHIFT on 4675;
- inn in reach and within 20 tiles 100%;
- hostile in view 77%;
- current project FATIGUE 8098 of 12804, HUNGER 4706;
- WORK-shift ticks 0 in every kind on both arms;
- never-eat 7 of 18 episodes;
- median ticks from pressing to first meal 284.

#789 (TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO, merged 2026-10-30, 3b16d1cab) was meant to make a broke hungry subject take paid work. Either that path doesn't reach these workers, or something outbids it (FATIGUE holds 63% of their ticks). Decision 73's precondition (the free meal goes) depends on it. rpg-designer: "It may matter more for V3 than anything ENG does."

## Scope
Counts first, no fix shape:
1. For these workers, at starving-line ticks: goal scores, winner and runner-up (HUNGER, FATIGUE, WORK, earn path), WORK_SHIFT attempts and refusals with reason, and whether #789's path is ever selected. Lane A's probe B rerun on s42, s44 and s46 adds the fields; s43 and s45 need the same fields where missing.
2. Across standard worlds and seeds on main: shift counts by kind, and broke-hungry subjects by outcome (earned and ate, ate free, starved).
3. Why the inn meal is open yet unused at gold 0 (is the free meal served to them?), with file:line.

## Out of Scope
- ENG's evidence (unchanged by this; both arms equal).
- The fix shape (rpg-designer, after counts).

## Acceptance Criteria
- Counts 1-3 reported, [D]/[I] marked, and rpg-designer rules.
- Hot-loop: no for counts.

## Related Tickets
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO (done, #789)
- TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR
- TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED (A')
- TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL
- TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md (decision 73)
- docs/world_rules/life-body/survival-needs.md

## Related Stored Artifacts
- /mnt/data2/scratch-eng/ab_*_frontier_living_world_{43,45}.json (lane A, scratch)

## Related Code Areas
- src/ai/goals/scorers.py, src/systems/strategic_systems/work_queue.py, src/engine/building_services.py

## Assumptions / Open Questions
- Dispatch needs an owner yes; ordered by rpg-planner after the V3 ruling.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
