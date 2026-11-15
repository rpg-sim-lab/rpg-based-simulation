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

Added 2026-11-15 from HOLD stage 2 (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP; hold_spy_v7 69e529f9; cells /mnt/data2/rpg-measure/holdmove/stage2/cells/{fix,base}_frontier_marches_s44_v7.json; fix tree b9d78c427). rpg-designer ruled this its own finding, separate from the HOLD fix and from TCK-20261114-A-COLLAPSED-SLEEPER-WALKS-UNDER-A-LIVE-SLEEP-TASK; it is the same loop as above, so it is recorded here rather than as a new ticket. Working name: "A collapsed grazer is woken by hunger every ten ticks, gathers, and collapses again without eating or sleeping off its debt".
- Fix fm s44, e64 (wild_creature): for about 2,400 ticks it repeats a ~30-tick cycle: collapse SLEEP (10 ticks), then INTERACT gather (11), then idle ENTITY_ACT (9), then SLEEP again. Sleep debt stays about 98 against a wake line of 58.8. Hunger wakes it as soon as debt dips under 98 (decision 2.115), so the sleep never runs off the debt. hp falls 20 -> 14, which looks like starvation drain [I].
- Fix fm s44, e65: same shape at t4965-5000. Debt 98.1, hp 13. Its episode is too short for a trace, so the cycle match is inferred [I].
- Base fm s44, e64: also in a live collapse SLEEP at t5000 under HOLD, per lane A's field check. So the loop is very likely present without the HOLD fix too [I]; the trace should confirm.
- Trace questions from rpg-designer (read-only, later, not blocking HOLD): (a) does it ever actually EAT inside the loop? (b) is the same loop in base s44?

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
