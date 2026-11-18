---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
phase: inprogress
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS

## Title
Each monster kind declares why it fights, replacing faction hostility for monsters (decision 62)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1, decision 62: "the undead hate the living, a spirit guards a place, a troll hunts by diet."

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. Declare a fight reason per monster kind in content.
2. Hostility for monsters reads the fight reason, not the faction.
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- No monster hostility reads a faction label.
- Each declared fight reason has a test.
- Tests for the new behaviour, plus the parity ledger and Bible updates in the same change.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261107-A-COMBAT-ENGAGE-PROJECT-TARGETS-A-BODY-TACTICAL-NEVER-SEES-AS-HOSTILE (deferred; one hostility predicate is its fix lean)

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
src/domains/combat_engagement/, hostility predicates, content

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

- Owner decisions on the rule (rpg-designer review applied, owner batch at 0bfed107e): #715 6985558474. All eight questions answered on the recommended option (below). The rule text is accepted; the code step is not dispatched and waits on SPLIT-INTELLIGENCE-PY and the legality ceiling, then merges in its domain-3 segment.

### Owner answers
Owner answers, #715 6985558474 (lead-planner, 2026-11-19), the recommended option on all eight:
- Q1 (A): a new species field `fight_reasons`, closed set (hates_living, guards_place, hunts_by_diet), validated at content load.
- Q2 (A): a REQUIRED body-model property `living`, no default (true for flesh; false for spirit and amorphous bodies).
- Q3 (A): a spirit guards its home tile: it engages a perceived body not of its own species within a reach declared per species in content. The tile is set at spawn and never changes, no territory record; revisit when places land.
- Q4 (C, declare nothing): slime declares nothing now (no slime archetype exists). With no declared reason a slime only fights back, and the content-load check requires a reason of any monster kind that gets one.
- Q5 (B): a people-kind regards a body as an aggressor when THAT body's declared reason names it, so guards keep clearing undead with no faction label.
- Q6 (A): attack permission is symmetric whenever either side's reason names the other (extends CONFLICT-03).
- Q7 (A): the same species is never a target, as relation does today.
- Q8 (A): REPLACE. For any pair where either side is a non-people kind, the declared reason is the only hostility source; species_relations keeps people-people pairs only; a load-time check refuses a non-people entry; the monster entries are removed in the same change, each listed in the ticket with its current effect.

## Durable state, lifecycle and clocks
- Durable field: a guard's home tile (`guards_place` only), a coordinate on the body.
- Creation: spawn sets it to the spawn tile; one writer (the spawn path); creation is idempotent across two passes (the same spawn tile).
- Update: it never changes; there is no merge and no replace after spawn.
- Exit and bound: none to exit; it dies with the body, so one per guarding body.
- Clearing: removed with the entity; no other writer clears it.
- Checkpoint/replay: it survives both, as part of the body.
- Clock: none. The reach is a content number declared per species, not a code constant. Reasons themselves (the declared `fight_reasons`) are content, not state.

## Implementation Notes
- 2026-11-22, the owner's direction (#715 7078469868, relayed by lead-planner-u24), scoped by rpg-designer: fight dispositions differ by kind, declared from properties and kind-neutral in code. This ticket owns the declaration. SLICE 1, which TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN (Step B) DEPENDS on:
  - a typed per-kind `fight_disposition` in content with the values ALWAYS_FLEES, FIGHTS_BACK (the visible default for an undeclared kind, AGENCY-08) and STRIKES_FIRST_IF_CAN_WIN;
  - a load-time validation;
  - a declared value for every existing kind, chosen from its properties. It's proposed as a per-kind TABLE that's owner-visible before it lands.
  Later slices: AGGRESSIVE (strikes first by nature) and GUARDS / TERRITORIAL, which need territory or motive data. Order: Step A → this slice 1 → Step B → TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM.

Phase 1 (rule text) is accepted; see the owner answers under Assumptions. The code step has not started.
### Species relations entries removed by the code step (Q8)

`data/content/social/species_relations.yaml`: the ten entries naming wolf, spider, troll, undead or dragonkin on either side are REMOVED in the code step's change (not ignored); the 14 people-people entries stay; a load-time check refuses any future entry naming a non-people kind. People-kind = a species with the trait `keeps_coin_and_trades` (2.103), so goblin, orc and lizardfolk entries stay. Current effect of each (relation.py:246-249, step 3.5, upgrade-only, and only through `faction_hostile` and attack legality, the two paths that pass species):

| entry (source -> target) | hostility axis | upgrade it makes today |
|---|---|---|
| wolf -> human | medium_contextual | label below threat becomes threat |
| human -> wolf | medium_contextual | label below threat becomes threat |
| spider -> human | medium_contextual | label below threat becomes threat |
| human -> spider | medium_contextual | label below threat becomes threat |
| troll -> human | high | label below enemy becomes enemy |
| human -> troll | medium_contextual | label below threat becomes threat |
| undead -> human | high | label below enemy becomes enemy |
| human -> undead | high | label below enemy becomes enemy (the second route, besides the invader verdict, by which people attack undead; Q5's aggressor reading replaces it) |
| dragonkin -> human | medium_contextual | label below threat becomes threat |
| human -> dragonkin | low_base_contextual | label below threat becomes threat |

For a wolf or spider (and a wild troll) the entry is already moot on the `faction_hostile` path, which returns before the context is built (`hostility.py:63`); it still applies in `LegalityServiceV2._attack_permitted`. The code step re-lists each entry's effect measured, if the tier requires it.


## Test Summary

## Files Changed

## Completion Summary
