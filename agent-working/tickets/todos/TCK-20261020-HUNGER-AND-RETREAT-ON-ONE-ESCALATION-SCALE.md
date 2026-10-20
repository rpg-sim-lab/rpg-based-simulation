---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Title
Put both survival pressures on one escalation scale: combat_retreat gets the need-pull escalation once hp is in its own consequence band

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
This is backlog, parked by the designer on 2026-10-20. Build it only if data shows a subject eating into a fatal attack.

V3 step (ii), on rpg-v3-starvation-threat at 70402779d, keeps the escalated hunger pull under a present threat once hunger is past STARVING_LINE (95). At the goal level, that pull is 155-160: raw hunger plus ESCALATION_AMPLITUDE 60 (need_pull.py). CombatRetreatScorer is 100·(1−hp_ratio) + 50·panic − 30·bravery, with a ceiling of 150, so the starving pull beats every reachable retreat score. The designer ruled the weighing is by immediacy: an acting threat still pre-empts in the tactical pass. The long-run unification it noted is to escalate retreat the same way, so both pressures saturate on one scale and the appraised threat decides.

## Scope
- Apply the existing ESCALATION_AMPLITUDE and smoothstep to combat_retreat once hp is past its consequence line. No new constant.
- Measure it as its own step: paired 3 × 42-46, crowded first. Retreat changes in every world.

## Out of Scope
- Any change to the hunger pull or to tactical ordering.

## Acceptance Criteria
- At hunger 95+, a strong enough appraised threat makes retreat outscore hunger, pinned by a unit test.
- The paired measurement passes the stop line, or the result goes to the owner.

## Related Tickets
- the V3 step (ii) ticket on rpg-v3-starvation-threat (SURV-07, memo row 83)

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1
- docs/world_rules SURV-07

## Related Stored Artifacts
- none

## Related Code Areas
- src/ai need_pull.py (ESCALATION_AMPLITUDE, smoothstep)
- scorers.py CombatRetreatScorer (~213-240)

## Assumptions / Open Questions
- The trigger is evidence of a fatal eat-under-attack. Without it, this stays parked.

## Implementation Notes
After v1, only if the trigger is seen.

## Test Summary

## Files Changed

## Completion Summary
