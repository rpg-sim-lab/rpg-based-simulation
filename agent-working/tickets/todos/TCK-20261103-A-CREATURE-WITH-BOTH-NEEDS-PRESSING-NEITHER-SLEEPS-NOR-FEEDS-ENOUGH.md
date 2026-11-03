---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH

## Title
A wild creature with hunger and sleep both pressing collapses again and again instead of sleeping or feeding enough: counts first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Requested by rpg-designer on 2026-11-03 from lane A's probe A (frontier s43 and s45, pinned, base 65d43dfa9 and ENG head e844e2845, hashes equal to paired).

On ENG's head, more wild creatures survive in frontier. The survivors fall into a loop with both needs pressing and collapse repeatedly: e844 s45 has 117 collapses from 4 subjects (64, 44, 5, 4), s46 134 from 5. On base, those herd members are dead by the end.

Direct reads:
- in the 200t before each collapse, rest was refused by in_danger on 0.6% of pressing-debt ticks, with no acting hostile and none on a gate wait;
- 96% of collapses come with hunger pressing too;
- actions: no action 9222, INTERACT (forage) 7809, SLEEP 6369;
- forage is open on every sampled pressing tick, and node supply is equal between arms;
- under both pressing: failed forage ("insufficient readiness"), FLEE_THREAT, REST.

Lane A's reading [I]: a pre-existing loop that only shows because they survive.

This is A' territory for non-persons, where two pressing needs don't resolve.

## Scope
Counts first:
1. Fatigue vs forage goal scores at each tick with both needs pressing (the probe recorded actions, not scores).
2. What "insufficient readiness" refuses, and why it repeats.
3. How often each creature completes a sleep or a meal between collapses; whether collapse resets anything that restarts the loop.
4. Seeds beyond s43 and s45; base vs ENG head.

## Out of Scope
- ENG's gate: rpg-designer counts its wild_creature watch as answered, not cleared, and ENG's row discloses this.
- A' for persons (TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED).

## Acceptance Criteria
- Counts 1-4 reported, [D]/[I] marked; rpg-designer rules on shape.
- Hot-loop: no for counts.

## Related Tickets
- TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED (A')
- TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED (ENG)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-02, SURV-07); docs/mechanics/01_entity_anatomy.md (staged sleep debt)

## Related Stored Artifacts
- /mnt/data2/scratch-eng/ab_*_frontier_living_world_{43,45}.json (lane A, scratch)

## Related Code Areas
- src/engine/sleep_debt.py, src/engine/opening_steps.py (`_forage_step`), src/ai/goals/scorers.py

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
