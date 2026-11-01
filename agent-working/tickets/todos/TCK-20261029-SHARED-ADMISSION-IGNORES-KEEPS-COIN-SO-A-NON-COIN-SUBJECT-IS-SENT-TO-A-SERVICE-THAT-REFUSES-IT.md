---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT

## Title
service_building refuses a subject without keeps_coin, but the shared admission, ways_in_reach and the scorers do not check it, so a non-coin subject is offered an inn meal or bed it can never get

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane B found this while planning ONE-ADMISSION (TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY). service_building requires keeps_coin(entity), while the admission function, ways_in_reach, EatScorer and FatigueScorer do not. Designer ruling (A), 2026-10-29: it stays out of ONE-ADMISSION, which pins the mismatch with one explicit test that names this ticket, and it becomes this ticket with its own paired run.

## Scope
1. COUNTS FIRST, with no behaviour change. List which kinds lack keeps_coin but have a diet the inn meal fits. On main, 3 worlds × s42-46 × 5000t, count how often such a subject is sent to an inn or bed and refused there. This is the hero-22 loop shape: dispatch, refusal, re-goal. Send the counts to rpg-planner, who passes them to rpg-designer.
2. Fix: keeps_coin goes into the shared admission function, so that service, ways_in_reach, scorers and the starvation record all follow it. Non-coin kinds then judge their own ways (forage, hunt, carried food) per SURV-06's per-kind declaration.
3. Replace ONE-ADMISSION's pinned-disagreement test with an agreement case, remove the docstring note, and add the divergence entry and Bible/parity updates.
4. Paired run: expected to differ ONLY for non-coin kinds. A change in any coin-keeping kind is a STOP to the designer.

## Out of Scope
- The payment law (CLAMP/ATOMIC) and the price rules.
- Reach bounds (TCK-20261029-HUNGER-SIDE-WAYS-HAVE-NO-DISTANCE-BOUND).
- Turning a repeated service failure into a blocker (TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER).

## Acceptance Criteria
- The counts table is delivered before any code.
- The admission grid covers keeps_coin yes/no, and admission == the real service outcome for every cell.
- No non-coin subject is dispatched to an inn meal or bed that the service would refuse (a kernel test).
- The paired run is reported, with coin-keeping kinds unchanged or a STOP.

## Related Tickets
- TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY (ONE-ADMISSION; must land first)
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER (same loop shape)

## Related Docs
- docs/plans/rpg_design_roadmap/ survival-needs (SURV-06, AGENCY-03)
- docs/mechanics/03_economic_laws.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/d73/trace3/ (hero 22 loop)

## Related Code Areas
- service_building / keeps_coin, src/engine/service_admission.py (from ONE-ADMISSION), ways.py, scorers.py

## Assumptions / Open Questions
- Sequence: after ONE-ADMISSION, independent of EARN.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
