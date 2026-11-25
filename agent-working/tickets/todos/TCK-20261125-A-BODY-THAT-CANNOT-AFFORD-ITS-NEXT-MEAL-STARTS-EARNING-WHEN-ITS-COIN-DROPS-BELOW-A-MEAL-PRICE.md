---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261125-A-BODY-THAT-CANNOT-AFFORD-ITS-NEXT-MEAL-STARTS-EARNING-WHEN-ITS-COIN-DROPS-BELOW-A-MEAL-PRICE
phase: open
date: 2026-11-25
tags: []
---

# TCK-20261125-A-BODY-THAT-CANNOT-AFFORD-ITS-NEXT-MEAL-STARTS-EARNING-WHEN-ITS-COIN-DROPS-BELOW-A-MEAL-PRICE

## Title
A body that cannot afford its next meal starts earning when its coin drops below a meal's price, not when hunger presses

## Status
BLOCKED (held for the owner's cognition documents, #715 7151855673)

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Owner #715 7151845769 (the answer to 7151832034, "Merge, fix next (Recommended)"): #995 merges with its urban P2 FAIL recorded, and this ticket is filed before that merge. HELD, do not start: owner direction #715 7151855673 ("after this, I want to revise and maybe rework the entire strategy, thinking and cognition component of entities, I will hand you documents later"). This ticket, like the other cognition-area follow-ups, waits until it is checked against the owner's documents.

The #995 W re-measure (base main 0a4fbfd55 vs fix be85a25a1, hunger kit v3.5, 24,000 t, s42) failed P2 in urban_political: 10 of 20 base free-meal users crossed the hunger line late (designer read W995E_READ.md 5db098d5). Report-only, fix vs base: weakened body-days 13.84 vs 0.90, end humans 15 vs 20 (other deaths 16 vs 11, mostly combat; starvation deaths 0 vs 0).

The trace (kit v8, pre-registered read 0d4c3012 plus Amendment 1 796436d8; read TRACE_V8_READ.md f254b4e8, read_v8.json 551019df) found one class in every decidable episode (6 of 7, category MIXED as written; owner Q2 "MIXED as written"):
- After a paid meal (-5 gold, -60 hunger) the body holds 0-4 gold, below the price of 5.
- It starts its hunger project's EARN step only once hunger presses (60.5-72.8), with 450-690 t left before the line.
- The wage (+6) or sale arrives AFTER the line in 6 of 7 episodes. A held WORK shift is not woken by hunger (scheduler.py:74), but waking would not help: it cannot pay until the wage lands.
- No missing hunger trigger, no eat attempt in the window, 0 #996 (navigation memory) ticks.

So the earn step starts too late for its pay to land before the line. This ticket makes a body plan to earn as soon as its coin cannot buy the next meal.

## Scope
0. First, check this ticket against the owner's strategy/cognition documents (#715 7151855673) when they arrive; re-scope or close it if they replace this mechanism.
1. The designer rules the trigger before any code: earn when coin < the cheapest reachable meal price (the ticket's subject), with the alternatives named in the owner ask kept open for that ruling (wage timing, or price vs wage).
2. Implement the ruled rule in the strategic/decision layer (strategy owns when to start the earn step; no tactical score stacking).
3. Tests: a body fed to 0 hunger with gold < price starts its earn step before hunger presses; one with gold >= price does not; the earn step's existing "finishes before the starvation line" guard (2.151) is kept.
4. Re-measure: the same W cells (hunger kit v3.5) on main with this fix; P2 urban is the bar.

## Out of Scope
- The meal price, wage amount and starting gold values (data tuning; TCK-20261124-BUILDINGS-AND-FACTIONS-START-WITH-GOLD).
- Quests as a way to earn (TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST).
- Waking a held WORK shift on hunger (not the cause: it cannot pay before the wage).
- The three withheld corpus re-pins (TCK-20261124-THE-THREE-WITHHELD-995-CORPUS-RE-PINS); they wait for a clean guard (ii).

## Acceptance Criteria
1. The designer's ruling on the trigger is recorded before implementation.
2. Unit tests for the three cases in Scope 3 pass.
3. The W re-measure passes P2 in urban_political s42 under its own S9, read by the designer with the pre-registered rule.
4. Divergence 2.218 (or a new entry) names the rule; the parity ledger is updated.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#995; the measured fail this follows).
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO (done; 2.151 the earn step).
- TCK-20261109-A-CROWDED-HERO-STARVES-WITH-NO-WAY-TRIED-AFTER-ITS-LAST-MEAL (similar shape after a last meal; not the same cause until traced).
- TCK-20261124-BUILDINGS-AND-FACTIONS-START-WITH-GOLD, TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST, TCK-20261124-THE-THREE-WITHHELD-995-CORPUS-RE-PINS.
- overlap scan: search_docs 6 hits, none duplicate (the hits are the done earn-step ticket, its divergences 2.102/2.151, a scenario and the roadmap).

## Related Docs
- docs/guidelines/intentional_divergences.md 2.151, 2.218.
- docs/mechanics/03_economic_laws.md, docs/mechanics/04_strategic_cognition.md.

## Related Stored Artifacts
- /mnt/data2/rpg-measure/freemeal_pre/w995e_designer_read/W995E_READ.md (5db098d5).
- /mnt/data2/rpg-measure/freemeal_pre/trace_v8_designer_read/TRACE_V8_READ.md (f254b4e8), read_v8.json (551019df).
- Pre-registered read: trace_v8_preregistered_read/TRACE_V8_READ_PREREG.md (0d4c3012), Amendment 1 (796436d8).
- Purse read: purse_designer_read/PURSE_READ.md (56ae88e6): after t6000 the city's 30 entities hold 29-58 coin in all.

## Related Code Areas
- src/ai/goals/ (the hunger need project's EARN step), src/engine/work_shift.py, src/engine/tactical_objective.py, src/engine/scheduler.py (l.74, the need wake).

## Assumptions / Open Questions
- Which price is "a meal's price" when two inns are reachable (the cheapest reachable, or inn_in_reach's pick): the designer rules.
- Measurement-kit defect to fix in the next pre-registered read (not code): the trace read's window for an episode with no prior meal began at t0, but t0 can never be a row (the first post-apply row is t1), so 25@1901 was not decidable only for that reason. The next read starts such windows at t1. The owner kept the category MIXED as written (Q2).

## Durable state, lifecycle and clocks
To be filled at design: the rule reads current gold and current prices only; no new durable state is expected.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
