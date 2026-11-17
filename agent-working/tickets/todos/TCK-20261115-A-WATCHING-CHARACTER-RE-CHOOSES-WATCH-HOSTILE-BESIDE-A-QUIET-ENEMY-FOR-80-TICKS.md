---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261115-A-WATCHING-CHARACTER-RE-CHOOSES-WATCH-HOSTILE-BESIDE-A-QUIET-ENEMY-FOR-80-TICKS
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-A-WATCHING-CHARACTER-RE-CHOOSES-WATCH-HOSTILE-BESIDE-A-QUIET-ENEMY-FOR-80-TICKS

## Title
A character beside an enemy that never attacks keeps re-choosing WATCH_HOSTILE for 76-84 ticks (the WATCH re-wait loop), a finding from HOLD stage 1

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
The owner ruled this a finding of its own (#715 6894565999, "(a) Stage 2, narrowed stop (Recommended)"; owner row .claude/handover/drafts/rpg-designer-hold-stage1-stop-owner-row.md, sha 595138ad8993). It comes from the HOLD stage-1 completion check (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP; hold_spy_v4 6b3edf17; fix tree 7b12b1f07, fm s42 5000 ticks, hash 8ba8c3a5):
- fm e32, hero, WATCH_HOSTILE t504-588 (84 ticks): beside a hostile for 75 ticks, 0 hits, hp 100. It walks only at t588.
- fm e44, scout, WATCH_HOSTILE t2522-2598 (76 ticks): beside a hostile for 76 ticks. Its one hit lands at t2598, the step away.
- Both are repeated watch decisions (an adjacency_wake re-wait), not a blocked walk. The character watches an enemy that isn't acting on it for over 80 ticks, instead of leaving, going about its objective, or engaging.
Data: /mnt/data2/rpg-measure/holdmove/cells_completion/fix_frontier_marches_s42_v4.json.

## Scope
1. Investigation first, read-only: what re-issues WATCH_HOSTILE each wake (notice_unengaged_hostile / adjacency_wake), and what an unengaged, non-acting adjacent hostile should cause under the rules (tactical_contract, decision 44, SURV and CONFLICT rows). Name the writer and its inputs per tick.
2. rpg-designer rules on the rule-level answer before any fix.
3. If a fix follows: the paired death-bar measurement, plus Bible, ledger and divergence entries in the same change.

## Out of Scope
- The HOLD fix itself and its stage 2.
- D1 and D2.

## Acceptance Criteria
- The writer of the repeated WATCH decision is named, with a trace that hash-matches its cell.
- A ruling on whether this is a defect, and if it is, a fix inside its stop rules.

## Related Tickets
- TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP (where it was found)

## Related Docs
- docs/engine/contracts/tactical_contract.md
- docs/mechanics/02_combat_laws.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py (WATCH_HOSTILE, adjacency_wake), src/engine/tactical_hold.py

## Assumptions / Open Questions
- Is a long watch of a non-acting enemy a defect, or intended caution? That's rpg-designer's call.
- It may move baselines, so it doesn't land while HOLD stage 2 is measuring.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
