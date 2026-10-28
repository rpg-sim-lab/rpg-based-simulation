---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY

## Title
ways_in_reach and can_use_inn_meal count a priced inn meal or bed as open for a subject that cannot pay, so the V3 judge and EatScorer disagree about what is open

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found by the D73 (#781) traces from rpg-implementer-2, on tree 58c0821dc (src = 7cfd2cc0c). Files: /mnt/data/scratch-rpg-implementer-2/d73/trace2/.
- ways_in_reach (src/ai/goals/ways.py:50) adds INN_MEAL when inn_in_reach and can_use_inn_meal hold.
- can_use_inn_meal (src/engine/appraisal.py:86) checks only the diet, never gold.
- starvation_record._judged_ways (src/observability/starvation_record.py:75) returns the same map. So V3 counts INN_MEAL as open for a subject with gold 0, when the meal costs 5.
- EatScorer separately returns NO_AFFORDABLE_WAY below the price, so the decision code and the judge disagree.
- Gate run 40734781335 shows the two new V3 fails: urban s42 scout 17 and urban s46 hero 22.

rpg-designer ruling (2026-10-29). Sources: survival-needs.md SURV-06 l.335-350, and the SURV-07 amendment of memo row 27, l.750-790: "whether a way is open is judged for the subject (a meal it cannot pay for is not open to it; AGENCY-03)."
- A price-aware "open" is the correct meaning, not a gate workaround.
- Change the SHARED definition, not the judge alone. AGENCY-03 allows one meaning of "open".
- This is its own ticket. It lands BEFORE D73 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1), because it changes decision inputs.

## Scope
- First, before any code: list every consumer of ways_in_reach and can_use_inn_meal (at least scorers.py, building_services.py, domain/core_actions.py, starvation_record.py, ways.py), and say what each does with a way that is closed by price. Send the list to rpg-designer through rpg-planner.
- INN_MEAL is open only if gold >= the meal price. The inn bed is open only if gold >= REST_PRICE_GOLD. Read both prices from the same source the inn charges (src/engine/service_prices.py / building_services). No new constant. Rough rest and home stay free.
- V3 judge verdict, so a relabel cannot turn the gate green. The judge records, next to the ways, the opening steps in reach and whether each was tried: work_in_reach, and any forage way the subject's kind has.
  - A starvation where the meal was closed by price, but an opening step the subject could take was in reach and never taken, is still a FAIL: "opening step untried" (row 27: the pull goes to the step).
  - Only "no open way AND no step it can take" is SURV-06's poverty outcome, which is not a fail.
- FOLDED IN (rpg-designer, 2026-10-29): TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR. An unaffordable inn bed is not open, so the fatigue goal stops naming it, and a subject with no home in bed_reach rests in place (rough rest, Bible 04 l.40). That is the same definition change, so it gets one paired run.
  - (a) f400's acceptance carries over as a named test: a broke, tired subject with no home in reach does not walk to the inn bed, and rests in place.
  - (b) The consumer list marks the fatigue/bed consumers separately from the hunger/meal ones, so the paired run can attribute a change to the bed or the meal.
- Paired run, 3 gate worlds x s42-46 x 5000t, against its parent (decision 76). The free meal is still ON, so the effect may be small. The run shows it.

## Out of Scope
- Removing the free meal (D73).
- Making a broke subject actually earn: TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO.

## Acceptance Criteria
- The consumer list has been ruled on by rpg-designer before any code changes.
- The named f400 test (a) passes.
- Unit tests: below the price is closed, at the price is open, above is open, for both meal and bed. Undeclared diet keeps the legacy behaviour.
- The judge and EatScorer agree on open/closed for the same subject and tick (one test through the real kernel).
- The V3 verdict has "opening step untried" as a FAIL and poverty as a non-fail, with tests for both.
- Bible 04 and the parity ledger are updated. The divergence class is Bug Fix, citing row 27 and AGENCY-03.
- Paired run with no unowned STOP. The two urban fails stay fails unless the trace shows work was out of reach.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (D73, #781; lands after this ticket)
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
- TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR
- TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-06, SURV-07 row-27 amendment)
- docs/mechanics/04_strategic_cognition.md (Standing Needs Escalate)
- docs/guidelines/intentional_divergences.md 2.142

## Related Stored Artifacts

## Related Code Areas
- src/ai/goals/ways.py, src/engine/appraisal.py, src/observability/starvation_record.py, src/ai/goals/scorers.py, src/engine/building_services.py, src/engine/domain/core_actions.py, src/engine/service_prices.py

## Assumptions / Open Questions
- Sequence: before D73. Independent of :1610. Not dispatched.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
