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
P1

## Request Summary
**Raised to P1, first rpg item after v1 (designer, 2026-10-21).** This shape is behind two of the three v1 owned known reds (v1_disclosure N15), recorded under the user's v1 cutoff of 2026-10-21. In both, a starving subject at near-death hp keeps fleeing a present catalog-hostile (Tier 1, correct by design) until it starves, because hunger and flight are not on one escalation scale.
- crowded_frontier s46, raider 38 (orc_clan), STARVATION at t3778, step 2 f9b21b55b:
  - hp 3-7%, 0 gold, no food;
  - PANIC_RETREAT from leader 30 (goblin_warband, hp 131, 2-13 tiles away) on 131 of 198 ticks between t3580 and t3777, while the hunger project is current;
  - an unthreatened open way existed in 9 of 9 retreat samples (the inn in 6 of 9).
- frontier_living_world s44, worker 2 (town_council), STARVATION at t3736:
  - hp 0.1-1.4%; PANIC_RETREAT from leader 30, predator_hunter 34 and alpha 49 (all catalog-hostile) on 150 of 236 ticks;
  - town_return (about 163.5) beats hunger (160) only through TownScorer's low-hp term (about 59): a wound-driven return to safety, also Tier 1;
  - an unthreatened open way existed in 13 of 19 retreat samples.
- Probes: /mnt/data/scratch-rpg-implementer/probes_hs/ways_probe.py and tick_log.py; data in /mnt/data/scratch-rpg-implementer/paired_en2/wp_raider38.json, wp_worker2.json and paired_en/v3btr/.
- The parked safe-route step (TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1) moves only the objective, so it cannot clear a tactical panic. The design here has to put the two pulls on one scale.
- Related: worker 2's goblin leader sits 2-11 tiles away for about 200 ticks without engaging, which is C4's shape (a hunter beside a subject without engaging, decision 47).

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
