---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT

## Title
The starvation record misses meals that come without an accepted intent result, so V3's last_meal_tick and UNTRIED_STEP can be wrong

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Requested by rpg-designer on 2026-11-03, from rpg-planner-ubuntu's pinned trace of crowded s42 e30 (base, end hash equal to the set). e30's record reads "last meal t721, ways attempted []", while hunger dropped at t1071 and t1391.

rpg-planner read src/observability/starvation_record.py:230-244 on main: `_note_attempts` returns early while hunger is below `_escalated_hunger`, and sets `_last_meal` only when an `intent_results` entry is accepted and its way is CARRIED_FOOD or INN_MEAL. A meal delivered any other way, or while not escalated, is invisible.

## Scope
1. Record every meal by its hunger effect and its writer (the code path that lowered hunger), with or without an intent result.
2. Keep attempts pressing-only, as now.
3. Tests: a meal with no intent result updates last_meal_tick; a meal below the escalated line does too; an attempt below the line still doesn't count.
4. Re-read the V3 records affected once fixed (e30, e37, e34, the known entries in tools/test_architecture/rpg_gate_known.yaml).

Until fixed, UNTRIED_STEP and last_meal_tick are caveated on every V3 record. Fails still count (rpg-designer).

## Out of Scope
- The t1391 drop (-19.9 = INN_MEAL_HUNGER, 16 tiles from the inn, no charge, gold 195): possibly a service delivered at a distance. It waits for the replay's writer and would be its own defect and ticket.
- The cap's fourth project (the escalated-need exemption, intelligence.py:1770, by design).

## Acceptance Criteria
- The tests in Scope 3 pass.
- A pinned run shows e30's record updated by its later meals, hash unchanged (the recorder is observability; state is not touched).
- The known entries' notes are re-checked, and any that rested on "never attempted" are stated to the owner.
- Hot-loop: maybe; the recorder runs per entity update applied. Under the perf pause (#715 6556861718), timing is NOT MEASURED; say so at close.

## Related Tickets
- TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX
- TCK-20261019-GATE-VALIDITY-CHECKS-FIRE-THROUGH-THE-REAL-KERNEL-AND-V3-SEES-EVERY-STARVATION-DEATH (done)
- TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-06/07), docs/observability/

## Related Stored Artifacts
- Gate issue #669; ubuntu's e30 trace (path to come with #828's evidence).

## Related Code Areas
- src/observability/starvation_record.py (`_note_attempts`, `_sample`, `_death`)
- tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- Which writer lowered e30's hunger at t1071 and t1391: the replay names it.
- Dispatch needs an owner yes.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
