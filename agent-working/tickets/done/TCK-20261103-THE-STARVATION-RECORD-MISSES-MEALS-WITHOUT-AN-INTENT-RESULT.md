---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT
phase: done
date: 2026-11-03
tags: []
---

# TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT

## Title
The starvation record misses meals that come without an accepted intent result, so V3's last_meal_tick and UNTRIED_STEP can be wrong

## Status
DONE

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

2026-11-07 interim condition, agreed by rpg-planner and the ubuntu side under the owner's cost rule (#715 6697776913): there is no recorder fix for now. Until this ticket lands, any V3 starvation in a combined or paired run gets a manual meal check from the trace rows before it counts, as e30's did. The gap stays named here. Applied in the ENG+churn combined run: s45/e53 (meal rows at t788, t838, t918 and t2308, none in its last 200 ticks; trace sha 69c90c9c…) and the urban traces. (Carried here from seat-notes commit 30f4ad06f on rpg-hit-wake by rpg-planner's ruling; the pinned-runner ticket hunk of that commit stays on rpg-hit-wake.)

2026-11-09 close (rpg-implementer). The interim manual-check condition above ENDS WITH THIS FIX: a V3 starvation no longer needs a manual meal check for the meals the recorder now sees (all four writers below). SYNC RULE (rpg-planner's ruling): this ticket's text above was carried here from seat-notes commit 30f4ad06f on rpg-hit-wake. Whichever of the two branches lands second resolves the modify/delete conflict on this ticket by KEEPING THE DELETE (the done/ copy holds the text). The pinned-runner ticket hunk of 30f4ad06f stays on rpg-hit-wake only.

Meal writers (every path that lowers hunger): carried_meal (core_actions.py:54, CARRIED_FOOD), the free meal in eat_update (:67, a direct update with no transfer, so no intent result), corpse_meal (:89, CORPSE_FOOD), the inn meal (building_services.py:80, TOWN_SERVICE). Nothing else lowers hunger; hunger_set has no writer. A hunger drop is a meal. Finding outside scope, filed as TCK-20261109-AN-INN-MEAL-DOES-NOT-STAMP-LAST-MEAL-TICK: the inn meal does not stamp the authoritative biological.last_meal_tick.

Change: `StarvationRecorder._note_attempts` stamps the last meal and clears the trail on any hunger drop, escalated or not, with or without an intent result; attempts stay pressing-only; `_attempted_way` maps CORPSE_FOOD to SCAVENGE. Observability only: no state field, no behaviour change.

Re-read of known entries (one cell, by the owner's depth rule #715 6731764470): crowded_frontier s45, base e755dc3d1 vs fix ba05f8c01 through the wrapper in evidence/. End hash 2209d096... equal in both arms and equal to lane C's arm_child base. e31: last_meal_tick None -> 810, ways attempted [] -> [], UNTRIED_STEP unchanged; its known-entry note holds. e37 is alive at 5000t on e755dc3d1 (no record); its entry (starved t2338 on 36d4fd78e) did not reproduce there. e30, e9 and e53 were NOT re-read: each is re-read with its own fix or the 2026-11-30 decision. rpg_gate_known.yaml is untouched (testing-planner owns it). Evidence is hash-equal on one cell plus the unit tests.

Timing is NOT MEASURED (the perf pause, #715 6556861718). The recorder runs per entity update applied (hot-loop: maybe).

## Test Summary
4 new tests in tests/unit/observability/test_starvation_death_record.py (a meal with no intent result; a meal below the escalated line; an attempt below the line does not count; a corpse meal is a SCAVENGE attempt and a meal); the meal and corpse tests fail on the old recorder. 33 passed with test_starvation_verdict.py and rpg_gate/test_v8_fires.py. No new real-kernel case. One pinned crowded_frontier s45 pair, hash-equal.

## Files Changed
src/observability/starvation_record.py; tests/unit/observability/test_starvation_death_record.py; staged artifacts and evidence under agent-working/stored_artifacts/TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT/; new ticket TCK-20261109-AN-INN-MEAL-DOES-NOT-STAMP-LAST-MEAL-TICK; rpg-planner's milestone 1 filing (cb2a693eb) rides along.

## Completion Summary
The starvation record counts every meal by its hunger drop and maps a corpse meal to SCAVENGE. See Implementation Notes for the writers, the sync rule and the evidence.
e31's known entry still holds (UNTRIED_STEP either way; only its last meal changed, none -> t810). e37 is alive at 5000t on main, so its entry's case did not occur; that goes to testing-planner and the owner via rpg-planner, and rpg_gate_known.yaml is not edited here. e30, e9 and e53 were NOT re-read. Timing was NOT MEASURED (the perf pause). The fix is hash-equal on one cell (crowded_frontier s45) plus unit tests. The milestone 1 filings (624f0322d, a76cb1630) ride with this close; the second branch to land keeps the delete of the todos/ ticket copies.
