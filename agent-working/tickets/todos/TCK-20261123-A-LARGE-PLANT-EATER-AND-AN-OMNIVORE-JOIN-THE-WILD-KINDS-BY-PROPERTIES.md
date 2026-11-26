---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261123-A-LARGE-PLANT-EATER-AND-AN-OMNIVORE-JOIN-THE-WILD-KINDS-BY-PROPERTIES
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-LARGE-PLANT-EATER-AND-AN-OMNIVORE-JOIN-THE-WILD-KINDS-BY-PROPERTIES

## Title
A large generic plant-eater and a generic omnivore join the wild kinds, declared by properties only

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
OWNER DIRECTION, #715 7097866207 (lead-planner-u24, 2026-11-23). The owner asked: "where is the deer/boar/etc like normal animals?", then answered: "yes, file the plant-eater and omnivore ticket". Filed only; there is no dispatch.

The lead's facts (inspected at main):
- the species content (data/content/living/species.yaml) holds one prey kind only, `small_plant_eater`;
- decision 45 (10-09) asked for "a few generic animal archetypes (for example a small and a large plant-eater)". Only the small one was built: TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50 put "A second archetype" out of scope, and no ticket picked it up;
- decision 50: named species (deer, boar, ...) wait until after the foundation is hardened.

## Scope
1. A LARGE GENERIC PLANT-EATER (deer-like) species entry, declared by coarse properties only (decisions 46 and 50, roadmap §12.2): body size, power, believed danger (common_knowledge), diet, senses, drive. No named species.
2. A GENERIC OMNIVORE (boar-like) species entry, the same way. Its diet includes plant and meat.
3. Whether either fights back comes from its properties, through CONFLICT-03 and later the Step B judge_power seam (TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM), never from a name.
4. Their yields come from the approved per-kind table (#715 7097769107) by body model: quadruped gives hide and bone, with quantities by size. No species override unless the designer's values need one.
5. Placement by biome (ecologies / populations data) as the designer proposes it.
6. rpg-designer PROPOSES the property values and the biome placement. They go to the owner as VALUES before any data change.
7. Bible ch05 (ecology) and ch01 where the kind model is named, world rules, and parity updated in the same change.

## Out of Scope
- Named species (deer, boar, ...): they wait for decision 50.
- New behaviour code. If a property the designer wants is not yet read by behaviour, that is a separate ticket, not a name check here.
- Wild births (TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND) and the predator fallback (TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT): tied, not done here.

## Acceptance Criteria
1. The owner's approval of the designer's values is recorded on #715 (id to be recorded), and data matches it exactly.
2. Both kinds are data-only: no kind name appears in logic (a static or unit check).
3. The omnivore eats both plant and meat through the existing diet gate; the large plant-eater eats plants only (tests with a failing control each).
4. Fighting back follows properties through CONFLICT-03: a test where the same kind's choice changes when only its power/danger properties change.
5. A kill of each yields hide and bone per the approved table by size (once the kill-loot ticket has landed; before then, meat only, as today).
6. Measurement: the extinction-line reading (roadmap §12.5) over a W cell pair, with kills grouped by MOTIVE (owner rule). rpg-designer reads it.

## Related Tickets
- TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50 (done; the small one; "a second archetype" out of scope there)
- TCK-20261123-A-KILL-LEAVES-TYPED-LOOT-OF-FOOD-AND-RESOURCES-ON-THE-CORPSE (yields)
- TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT (wild food for predators; its hunt limit and easier prey, #715 7094165498)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (decisions 67/70, a systemic_foundation item)
- TCK-20261121-A-SMALL-PLANT-EATER-STARVES-IN-FRONTIER-LIVING-WORLD-WITHOUT-TRYING-TO-FORAGE (the persistence finding: the small plant-eater was gone by t1750)
- TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM (Step B judge_power seam)
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS (decision 62, fight dispositions)

## Related Docs
- docs/plans/systemic_world/roadmap.md §12.2 (kind property model), §12.5 (systemic_foundation done criteria, extinction line)
- docs/mechanics/05_world_evolution.md (ecology)
- docs/guidelines/intentional_divergences.md 2.107 (hunting, diet gate, first plant-eater)
- docs/world_rules/scenarios/life-body-batch-05.md LB-S20, LB-S21

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50/

## Related Code Areas
- data/content/living/species.yaml (small_plant_eater, l.307), body_models.yaml, items.yaml
- data/content/world/ecologies.yaml, data/content/entities/populations.yaml

## Assumptions / Open Questions
- The designer's values (size, power, danger, diet, senses, drive, biomes) are open until the owner approves them.
- Whether an existing body model (e.g. a larger quadruped) fits, or a new one is needed, is the designer's call.
- Order: after the kill-loot ticket, so yields land once; the predator fallback ticket may want these kinds as its easier/larger prey.

## Durable state, lifecycle and clocks
No new durable state: species entries are content. Population numbers change only by births and deaths (LB-S21 law).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
