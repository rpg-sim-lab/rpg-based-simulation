---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261119-LAIR-SPAWNED-COPIES-LOSE-THE-PARENTS-CATALOG-FACTION
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-LAIR-SPAWNED-COPIES-LOSE-THE-PARENTS-CATALOG-FACTION

## Title
Lair-spawned copies lose the parent's catalog faction because SPAWN_KIND_CATALOG_FACTION is keyed by an occupation literal

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by rpg-implementer-2 (inspected) in the step-5 (#965) trace; rpg-designer filed it as P3 on 2026-11-19 (flag OFF, no shipped profile).

- The lair spawn at src/systems/world_systems/creature_territory.py:65 calls `spawn_monster(species=entity.kind, occupation=entity.identity.occupation)`.
- World wolves are archetype-built with occupation = role_id: "predator_hunter" and "alpha" (data/content entity_archetypes.yaml:3-22).
- `_catalog_faction_properties(occupation)` (generator.py:67-70) maps only the literal keys in SPAWN_KIND_CATALOG_FACTION (wolf, slime, bear, harpy, golem). So the copy gets no faction_id and keeps Faction.MONSTER_HORDE, while its compiled parent is wild_beast_pack.
- Result: the copy is not wild (`is_wild_creature` is False), and it is judged by faction hostility instead of appraisal (decision 47), unlike its parent.

The path is gated by ENABLE_CREATURE_TERRITORY_LIFECYCLE, which is OFF by default (feature_flags.py:148), and no shipped profile turns it on.

It's the same "spawn_monster builds a body that doesn't match its compiled parent" class as TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK, at the same spawn sites.

## Scope
1. rpg-designer rules the fix shape BEFORE any code. The open options:
   - (i) a copy inherits the parent's faction_id;
   - (ii) the catalog faction is keyed by species (species_of), not by an occupation literal, as the kind=species rule implies.
2. Fix plus tests:
   - a lair copy of a compiled wild wolf, with the flag ON, has the parent's faction and is_wild_creature True;
   - a non-wild parent's copy is unchanged.
3. Divergence and parity: update 2.216's Disclosed sentence ("see this ticket") and COMB-358's v2_evidence if wildness of runtime copies changes.

## Out of Scope
- Turning ENABLE_CREATURE_TERRITORY_LIFECYCLE on in any profile.
- The senses check (sibling ticket) and why-it-fights' removal of faction from monster fights.

## Acceptance Criteria
- A lair copy's catalog faction equals its parent's, per the ruled shape. A test pins it with the flag ON.
- No shipped-world behaviour changes while the flag is OFF; state this in the PR.
- Any existing test-expectation change is an owner ask.

## Related Tickets
- TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK (sibling; same spawn sites)
- TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD (#965; where it was found; divergence 2.216)
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS (keeps faction for wild-alignment detection)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.216, docs/parity_ledger/combat_movement.yaml COMB-334 / COMB-358, docs/world_rules/capability-progression/conflict-combat.md CONFLICT-03

## Related Stored Artifacts
- None.

## Related Code Areas
- src/systems/world_systems/creature_territory.py, src/systems/world_systems/generator.py (SPAWN_KIND_CATALOG_FACTION, _catalog_faction_properties, spawn_monster), src/engine/hostility.py (is_wild_creature)

## Assumptions / Open Questions
- The fix shape, (i) or (ii), is rpg-designer's ruling, made before code.
- Not yet executed: lane B's scratch pytest for #965 (a lair spawn with the flag ON) will execute this finding. Cite its output sha here when it lands.

## Durable state, lifecycle and clocks
No new durable state. faction_id is set once at spawn, in identity properties, as it is today. No clock is read.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
