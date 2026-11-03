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
- The meal path itself: the replay showed it works (see Implementation Notes).
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
- Answered by the replay: corpse meals (see Implementation Notes).
- Dispatch needs an owner yes.

## Implementation Notes
2026-11-03 replay result (rpg-planner-ubuntu, relayed by lead-planner-u24, not checked by rpg-planner): e30's two silent drops were corpse meals (src/engine/domain/core_actions.py:89 `corpse_meal`, source_kind CORPSE_FOOD, on the action path), not the inn and not at a distance. The meal path is fine; decision 44 isn't touched. The recorder gap is sharper than first stated: `_attempted_way` has no CORPSE_FOOD mapping, so SCAVENGE reads untried even when the subject scavenged, and last_meal_tick misses every meal but CARRIED_FOOD and INN_MEAL. e30's true last meal is t1390, not t721. On ubuntu's read V3 likely stays red for e30 on FORAGE alone. Scope adds: map CORPSE_FOOD to SCAVENGE in `_attempted_way`, with a test.

## Test Summary

## Files Changed

## Completion Summary
