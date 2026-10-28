---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR
phase: open
date: 2026-10-28
tags: []
---

# TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR

## Title
A subject that cannot pay the bed price still chooses the inn bed as its way to rest (SleepScorer has no gold check)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
D73 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1) makes the inn bed one paid transfer: gold 10, hp +5 and readiness +10, all or nothing (owner decision 73, memo row 73). It also refuses the bed at service time when the subject holds less than `REST_PRICE_GOLD`. To keep one variable per step, D73 deliberately left SleepScorer/FatigueScorer ungated (divergence 2.142). So a broke subject can still pick the inn bed as its way to rest, travel there, and get only the base rest effect. Nothing is free, but the travel and the choice are wasted.

## Scope
- Gate the inn-bed way in the sleep/fatigue scorer on `entity.inventory.gold >= REST_PRICE_GOLD` (read from `src/engine/service_prices.py`), mirroring EatScorer's `NO_AFFORDABLE_WAY`.
- Update the sleep-project tests that D73 found would move (town_return vs fatigue).
- Measured as its own behaviour step (decision 76: 3 gate worlds x 5 seeds x 5000 ticks against its parent).

## Out of Scope
- Prices and effects (decided, row 73).
- The flight relabel step and the hunger-capacity work.

## Acceptance Criteria
- A subject below the bed price is never offered the inn bed as its rest way. A subject at or above the price is offered it as before.
- Tests pin both cases plus the access reason.
- Paired-step report against its parent; divergence 2.142's SleepScorer note is updated to say this is resolved.
- SimQ criterion (row 82): the outcome is already carried by the accepted/rejected REST transfer, so no new event type.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (D73, parent)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md rows 73, 76, 82
- docs/guidelines/intentional_divergences.md 2.142
- docs/world_rules/life-body/survival-needs.md (SURV-06)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1/ (after D73 closes)

## Related Code Areas
- src/ai/goals/scorers.py (sleep/fatigue scorer)
- src/engine/service_prices.py
- src/engine/building_services.py

## Assumptions / Open Questions
- Order relative to M1: rpg-planner sequences it after D73 lands, and it is not dispatched yet.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
