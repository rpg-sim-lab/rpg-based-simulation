---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261123-A-KILL-LEAVES-TYPED-LOOT-OF-FOOD-AND-RESOURCES-ON-THE-CORPSE
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-KILL-LEAVES-TYPED-LOOT-OF-FOOD-AND-RESOURCES-ON-THE-CORPSE

## Title
A kill's corpse carries resources from body properties beside its meat, and a quest-evidence category is defined for the quest ticket

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
OWNER DIRECTION, #715 7097367374: "one kill can feed the body -> a kill spawn loot, the loot contain the quest item (if the killer holding a quest related to that) and the other parts (which can be considered as food) and other resources".

rpg-designer RULED, 2026-11-23, relayed to rpg-planner, that the loot model gets its OWN ticket and that TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST depends on it. The reasons:
1. Loot follows every kill (hunting, defence, a fight, a quest), and most kills hold no quest.
2. The quest ticket needs only one hook from it: a typed quest-evidence slot.
3. The food side has to land, and be measured, alone. Moving meat into loot changes who can eat it and when, which is a #995-class hunger risk.

## Scope
CORRECTED by rpg-designer, 2026-11-23: the loot already EXISTS. It is the corpse's inventory. carcass.py body_meat puts meat on it at death (BODY_AT_DEATH); the dead body's coin and goods move to it (Bible 03 l.134); the sinks are CORPSE_FOOD, CORPSE loot and CORPSE_DECAY. This ticket adds NO new container.
1. The corpse inventory gains RESOURCE items at death, beside the meat, through the same death step and ledger. body_models.yaml gains `yields: [{item, quantity}]`, empty by default, and one `body_yield` sits next to body_meat. The ledger records BODY_AT_DEATH per item and CORPSE_DECAY, with RESOURCE_DECAYED alongside MEAT_DECAYED.
2. A QUEST_EVIDENCE item category is DEFINED here but never produced here; only the quest ticket produces it. It cannot be eaten or sold: one category check in the shop law refuses its sale.
3. Kind-neutral, from body properties, never a kind name. Kinds with no flesh declare their own yield, or none. Decision 44's own-kind rule for eating stays where it is.
4. The take rule is UNCHANGED: anyone eats or loots, as on main.
5. Hash control: with every `yields` empty, the plain run equals the base.
6. For the implementer to verify (inspected, not verified): whether the legacy undeclared diet would take a non-food item. If it would, the diet gate gains one "has a food_class" check.
7. Owner questions, from the designer's draft at main-checkout .claude/handover/drafts/rpg-designer-kill-loot-design-questions.md (dbae3e67), through the lead:
   - 4 design questions: which kinds yield in slice 1; whether to use hide and bone; whether yield is independent of the cause of death; whether resources rot with the corpse.
   - 3 data values, as numbers: hide 0/1/2 by size, bone 0/1/2, and the values (hide 2, bone 1, kept below a meal).
   OWNER-APPROVED, #715 7097645868, all as recommended:
   - Which bodies: the kinds in current worlds, by declared size band.
   - Items: hide and bone.
   - Cause: none; every death yields the same.
   - Rotting: with the corpse at death + 100.
   - Hide: small 0 / medium 1 / large 2.
   - Bone: small 0 / medium 1 / large 2.
   - Base value: hide 2 gold, bone 1 gold. A large body yields 6 gold, about one shift; the owner saw this before choosing.
   OWNER CORRECTION AND DIRECTION, #715 7097661739 and 7097668921. These WIDEN the "which bodies" and "items" answers above:
   - Yields depend on what a body is MADE OF, not on size alone. Each body model declares its items (meat, hide, bone or none). Size sets only the quantity, using the approved numbers. A body with no flesh yields no meat and no hide.
   - Drops differ BY KIND, as fits a fantasy world. Examples only, not values: a skeleton gives bone and no meat; a spirit gives nothing, or a spirit-only item; a winged reptile gives scale; a spider gives silk. Kinds have their own origins, not only natural species.
   - The mechanism is rpg-designer's choice, from data, never from name checks. One option is a per-species `yields` override of the body model's default, which also solves undead sharing `spirit_body` with true spirits (inspected at main).
   - rpg-designer drafts a PER-KIND TABLE (item, quantity by size, base value). It goes to the owner as numbers BEFORE data. The approved values (hide 0/1/2, bone 0/1/2, hide 2 g, bone 1 g) stand wherever those items appear.
   PER-KIND TABLE OWNER-APPROVED, #715 7097769107, all as recommended (draft main-checkout .claude/handover/drafts/rpg-designer-kill-loot-yield-table.md, 8fb98144):
   - Mechanism: each body model has a default `yields`; a species `yields` REPLACES it; each item has one `quantity_by_size` table in items.yaml. No names in code.
   - Body defaults: humanoid bone; quadruped hide + bone; arachnid silk; winged_reptilian scale + bone; amorphous slime_gel; spirit none.
   - Species overrides: lizardfolk scale + bone; troll hide + bone; undead bone, and no meat.
   - Humanoids yield by what they are made of, like every kind: a killed human, elf or dwarf yields bone 1.
   - Spirit: nothing.
   - New items: silk 1/2/3 at 2 g; scale 0/1/2 at 3 g; slime_gel 1/2/3 at 1 g. Kept: hide 0/1/2 at 2 g and bone 0/1/2 at 1 g. Small bodies keep hide and bone at 0. A body is worth at most 8 g (dragonkin).
8. Bible ch03 and ch05, world rules and parity, updated in the same change.

## Out of Scope
- Filling QUEST_EVIDENCE, the quest match, and quest-item rules (TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST).
- Prices for resources.

## Acceptance Criteria
1. The owner's answers are recorded (#715 7097645868), and data matches them exactly: the per-kind table (owner-approved, #715 7097769107) by what each body is made of; quantities by size band; hide and bone at 0/1/2 with values 2 and 1 wherever they appear. No name checks in code.
2. A kill's corpse inventory gains its RESOURCE items from body properties beside unchanged meat. With all yields empty, the run hash equals the base (tests, plus a failing control).
3. Resources decay with the corpse (RESOURCE_DECAYED). QUEST_EVIDENCE is refused by the shop law. No kind name appears in the logic (a static or unit check).
4. Measurement: a W cell pair (hunger kit) with P2 HARD on food, plus kills → loot → taken counts grouped by MOTIVE, not diet (the owner's combat-motive rule). rpg-designer reads it.

## Related Tickets
- TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST (depends on this ticket)
- TCK-20261123-A-BODY-KEEPS-ITS-FOOD-AND-SELLS-ONLY-FOR-A-PURPOSE-IT-HAS-FOR-THE-COIN
- TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT (carcass availability)

## Related Docs
- docs/mechanics/03_economic_laws.md; docs/mechanics/05_world_evolution.md; data body_models.yaml

## Related Stored Artifacts
- #715 7097367374 (owner direction)

## Related Code Areas
- the authoritative death step; corpse lifecycle; scavenging (SCAVENGE step); body_models meat_yield

## Assumptions / Open Questions
- rpg-designer drafts the design questions when this ticket is filed.
- Order: the backlog, ahead of the quest ticket. No dispatch.

## Durable state, lifecycle and clocks
No new durable container: RESOURCE items live in the existing corpse inventory, with its existing lifecycle (made at death, decaying at death + 100) and ledger. The new data is `yields` in body_models.yaml.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
