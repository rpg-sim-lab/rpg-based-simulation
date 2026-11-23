---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261123-A-BODY-KEEPS-ITS-FOOD-AND-SELLS-ONLY-FOR-A-PURPOSE-IT-HAS-FOR-THE-COIN
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-BODY-KEEPS-ITS-FOOD-AND-SELLS-ONLY-FOR-A-PURPOSE-IT-HAS-FOR-THE-COIN

## Title
A body keeps its food for eating and sells food only when it has a purpose for the coin

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
OWNER DIRECTION, #715 7094165498, item 2 (routed by lead-planner-u24): "Selling food to buy food loses food - instead, why they don't keep the food for later eat, only sell when there actually a purpose to do with money."

The lead's code read at 13844fee8 found that selling 5 berries (150 hunger if eaten) raises 5 gold, which buys one 60-hunger meal.

What the code does today (inspected at cdb0d4f09):
- `src/engine/shop_sale.py:24`: `FOOD_KEPT_HUNGER_RECOVERY = 60.0`. A subject keeps one meal's worth of food; everything above it counts as spare.
- `shop_sale.py:33`: `spare_quantity` returns held minus ceil(60 / recovery) for food.
- `src/ai/goals/opening_steps.py` `_earn_then_buy_step` (SELL, EXCH-02): the step is open whenever spare goods exist and a shop's purse covers one unit. It sits on the hunger ladder, so the coin's only purpose is the next meal.
- So food is sold to buy food. Nothing types why the coin is wanted.

## Scope
1. Food is kept for eating. Spare food is not sold to fund hunger, because eating it serves hunger directly.
2. Food is sold only when the body has a purpose for the coin: a named spend it cannot already afford. rpg-designer defines "a purpose" from typed state only, with no reason strings and no hunger threshold standing in for it.
3. Non-food goods keep today's SELL rules unless the designer rules otherwise.
4. Mechanic-scenario tests:
   - a hungry body holding spare berries eats them and does not sell them;
   - a body with a typed coin purpose sells its surplus;
   - one failing control on the base.
5. Bible ch03 (EXCH-02) and world rules, plus the parity ledger entry, are updated in the same change.

## Out of Scope
- Prices, the price law and shop purses.
- Hunting changes: those are folded into TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT.
- Earning by a shift or a quest (#995, TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST).

## Acceptance Criteria
1. The designer's definition of "a purpose for the coin" is recorded: typed, with its owner type and lifecycle.
2. A body never sells food to fund the meal it could eat from that food (a test plus a failing control).
3. A sale happens only under a typed purpose, and the purpose is visible in inspection.
4. A measured run reports the effect on starving body-days and on shop sales against the base, read by rpg-designer.
5. Bible, world rules and parity are in parity.

## Related Tickets
- TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT (the same owner direction, item 1)
- #995 rpg-free-meal-atomic (the EARN to CONSUME re-point; it touches the same ladder)
- TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST

## Related Docs
- docs/mechanics/03_economic_laws.md; the EXCH-02 world rule; docs/world_rules/life-body/survival-needs.md

## Related Stored Artifacts
- #715 7094165498 (owner direction)

## Related Code Areas
- src/engine/shop_sale.py; src/ai/goals/opening_steps.py (SELL / EARN_THEN_BUY); src/engine/shop.py

## Assumptions / Open Questions
- Whether a body eats held food before trying the ladder is to be read (inspected) by the investigator. It decides whether rule 1 is a SELL gate only, or also needs a change on the eating side.
- Order: systemic_foundation backlog, behind #995 and #996 unless the owner rules it ahead. No dispatch until they settle.
- `FOOD_KEPT_HUNGER_RECOVERY` is a tuning constant in code; it moves to data if it survives the change.

## Durable state, lifecycle and clocks
A coin purpose, if the designer makes it durable, needs a typed model, an owner, a lifecycle, inspection and tests. To be filled at scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
