---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-19
---

# Final rule text: why each monster kind fights (decision 62)

ACCEPTED by the owner on 2026-11-19 (#715 6985558474): the recommended option on all eight questions (`owner_batch.md`). The real edits are applied to the docs in the same commit as this file; each section shows the exact before (verbatim at origin/main 51a6516cf) and after. The slime declares no reason (Q4); text for options not chosen is removed.

## 1. World-rules catalog, `docs/world_rules/capability-progression/conflict-combat.md`

### 1a. Bullet under "Still open" (lines 101-102)

BEFORE:
```
  - Monster factions keep faction hostility as an interim (decision 62), until milestone 1's
    declared drives.
```

AFTER:
```
  - Monster factions keep faction hostility until the code step of TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS lands. The accepted rule (CONFLICT-05, owner 2026-11-19, #715 6985558474) regards a monster kind by its declared reason to fight; faction hostility remains a reason to fight only between people-kinds.
```

### 1b. Bullet "Scope of the change, by milestone"

BEFORE:
```
  - **Scope of the change, by milestone (decided by the owner directly, 2026-10-11; row 62 of the
    memo).** In the hunting batch, only a kind with a diet in a faction declared wild
    (`wild_beast_pack`, `wild_fauna`) drops faction hostility and goes by the appraisal. Monster
    factions (`undead_remnants`, `dragon_cult`, `spirit_court` and others) keep faction hostility
    for now, which is disclosed as interim. In milestone 1, each monster kind declares why it
    fights as a property read generically (decision 46): the undead hate the living, a spirit
    guards a place, and a troll or dragonkin hunts by its diet and the appraisal. That drive
    replaces faction hostility for monsters too, leaving faction as a reason to fight only
    between people. **Alternatives not taken:** every non-people kind at once (the undead,
    slimes and spirits have no diet and would ignore people until a drive exists); wild
    animals only, for good (monsters would stay enemies by a label).
```

AFTER:
```
  - **Scope of the change, by milestone (decided by the owner directly, 2026-10-11; row 62 of the memo; completed in milestone 1 by CONFLICT-05).** In the
    hunting batch, only a kind with a diet in a faction declared wild dropped faction hostility and went by the appraisal. In milestone 1,
    every non-people kind goes by its declared reason to fight (CONFLICT-05): the undead hate the living, a spirit guards a place, a troll
    or dragonkin hunts by its diet and the appraisal. Faction is a reason to fight only between people-kinds (a species with the trait `keeps_coin_and_trades`, 2.103).
    **Alternatives not taken:** every non-people kind at once in the hunting batch (the undead, slimes and spirits had no diet
    and would have ignored people until a drive existed); wild animals only, for good (monsters would stay enemies by a label).
```

### 1c. New entry CONFLICT-05, inserted after CONFLICT-04 (before "Inherited / Applied Foundational Rules")

BEFORE: (no entry)

AFTER:
```
## CONFLICT-05 — Each non-people kind declares why it fights; a faction label never decides a monster's fight

> A kind that is not a people-kind (a people-kind is a species with the trait `keeps_coin_and_trades`, 2.103) fights for a reason its content declares. The reason is one of a closed set: it hates the
> living, it guards a place, or it hunts by its diet. Hostility toward and from such a kind is derived from that reason and from the
> appraisal (CONFLICT-03), never from the faction it belongs to. Faction enmity remains a reason to fight between people-kinds only.

- **Where it is declared.** A species field `fight_reasons`, a closed set (`hates_living`, `guards_place`, `hunts_by_diet`), validated at content load.
- **Reasons.**
  - `hates_living`: the kind engages a perceived body whose body model declares `living`. `living` is a REQUIRED body-model property with no
    default: true for flesh bodies, false for spirit and amorphous bodies.
  - `guards_place`: the kind engages a perceived body, not of its own species, within a reach declared per species in content, of its home
    tile. The home tile is set at spawn to the spawn tile and never changes. It keeps no territory record; revisit when places land (milestone 1, item 4).
  - `hunts_by_diet`: the existing PREDATION appraisal (hungry, the diet can eat the body, the hunter believes it can overcome it); no other trigger.
- **People regard a declared aggressor as hostile.** A people-kind regards a body as an aggressor when THAT body's declared reason names it, so a guard
  still answers an undead sentinel with no faction label.
- **Permission is symmetric (extends CONFLICT-03).** An attack is permitted in both directions whenever either side's declared reason names the other.
- **The same species is never a target**, as `relation` does today (`src/engine/hostility.py:87-88`). This replaces "a faction does not hunt its own".
- **No declared reason: the kind only fights back.** The content-load check requires a reason of any monster kind that gets an archetype, and refuses
  a value outside the closed set. The slime declares nothing now: no slime archetype exists.
- **One source of hostility for a monster pair (species relations).** For any pair where either side is a non-people kind, the declared reason is the
  only hostility source. `species_relations` keeps people-people pairs only; a load-time check refuses an entry naming a non-people kind; the existing
  monster entries are removed in the same change, each listed in the ticket with its current effect.
- **Alternatives not taken:** the reason as a drive weight (a band, not a vocabulary); derive it from a trait name (a name check, decision 46);
  keep the invader verdict for monsters (a label decides); defence and appraisal only for people (the largest unmeasured behaviour change); coexisting species relations (two sources for one fact).
- **Disposition:** Accepted by the owner on 2026-11-19 (#715 6985558474), the recommended option on all eight questions. Not implemented yet: until the code step of TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS lands, monsters keep faction hostility (divergence 2.107, INTERIM).
```

## 2. Divergence record, `docs/guidelines/intentional_divergences.md`, entry 2.107

The T1 doc-truth fix is applied (section 7). The INTERIM sentences ("INTERIM, not the rule ... M1 changes that one function.") STAY until the code step: the behaviour has not changed, so the entry cannot close yet. The code step replaces them with:
```
**Closed by milestone 1** (decision 62, CONFLICT-05, TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS): the wild-faction gate is gone. Every non-people kind goes by its declared reason to fight; people-kinds keep faction hostility among themselves. `is_wild_creature` is replaced by a property read of the declared reason.
```

## 3. Mechanics Bible, `docs/mechanics/02_combat_laws.md`, new paragraph after the Friendly Fire item (line 119)

BEFORE: (no paragraph)

AFTER:
```
**Who is hostile to a non-people kind (CONFLICT-03, CONFLICT-05, decision 62; accepted 2026-11-19, #715 6985558474; implemented by the code step of TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS, until then the code reads faction hostility for monsters, divergence 2.107).** A kind that is not a people-kind (a species without the trait `keeps_coin_and_trades`, 2.103) is hostile by its
declared reason to fight (it hates the living, it guards a place, or it hunts by its diet), never by the faction it belongs to. The
friendly-fire test above reads the same declared reason for such a kind and the catalog faction only between two people-kinds.
```

## 4. Mechanics Bible, `docs/mechanics/04_strategic_cognition.md`, line 435 (prefix of the Catalog hostility bullet)

BEFORE (prefix, verbatim):
```
*   **Catalog hostility, not the legacy enum**: every perception-side "is this an enemy" test uses `content_semantics.faction.are_entities_hostile` (real distance, `combat_engaged=True`) and "is this an ally" uses `are_entities_allied` (same resolved catalog faction), never `identity.faction ==/!=` on the four-value legacy `Faction` enum, which collapses content factions.
```

AFTER (prefix):
```
*   **Catalog hostility between people, declared reasons for monsters** (CONFLICT-05, accepted 2026-11-19; implemented by the code step of TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS, until then monsters are judged by faction): every perception-side "is this an enemy" test goes through the one shared hostility predicate: `content_semantics.faction.are_entities_hostile` (real distance, `combat_engaged=True`) decides between two people-kinds, and a non-people kind is judged by its declared reason to fight. "Is this an ally" uses `are_entities_allied` (same resolved catalog faction), never `identity.faction ==/!=` on the four-value legacy `Faction` enum, which collapses content factions.
```
(The rest of the bullet, the `Sites:` list, is unchanged.)

## 5. Parity ledger, `docs/parity_ledger/combat_movement.yaml`

Deferred to the code step: COMB-334 gains the monster-reason evidence and test path; one new P1 entry per declared reason, with `test_path` set when its test lands.

## 6. Kernel spec, `docs/plans/systemic_world/m1_kernel_spec_items_2_6.md` (per rpg-designer F5; `authoritative_pipeline.md` is not the kernel spec)

Checked against CONFLICT-05 (read at 51a6516cf): the spec is NOT silent, and it agrees. No change drafted. The points:
- Item 2, point 7 (:255-256): "Name branches this replaces (run 3, with why-it-fights): hostility.py's same-faction no-predation, and the faction-first ordering for monsters. Faction keeps deciding for PEOPLE (memo row 47)." Consistent with CONFLICT-05: the same-faction no-predation line (`hostility.py:90`) retires here, while the same-species rule (`hostility.py:87-88`) stays (Q7).
- Item 6 R2 catalog text (:268): "Hostility between kinds comes from each kind's declared reason to fight (why-it-fights) and from the appraisal; between people, from declared faction relations keyed by id." Consistent. Both texts must be defined once: when R2 is written, it should cite CONFLICT-05 instead of restating it (rule: one fact, one document).
- Item 6 R2 spec points 1-2 retire `get_legacy_faction_bucket` and the MONSTER family; the camp offspring's "monster_horde" id (trace_camp_troll.md) is among what they remove, and births retires the path anyway.
Open item for rpg-planner: item 2's reading of "faction-first ordering for monsters" assumes the monster branch is retired by why-it-fights; CONFLICT-05 is that retirement.

## 7. Doc-truth fix applied now (T1): divergence 2.107, independent of the owner's answers

This one is a real edit on the branch (`docs/guidelines/intentional_divergences.md`, entry 2.107, the bullet at ~:3257), not a proposal.

BEFORE (verbatim at 51a6516cf):
```
The five monster kinds that keep faction hostility under this rule, because they are not wild creatures (they belong to invader, rival or neutral factions, or have no diet): troll, undead, dragonkin, slime, spirit; people-kinds (human, goblin, orc, elf, dwarf, lizardfolk) keep it among themselves.
```

AFTER (as committed):
```
The monster kinds that keep faction hostility under this rule are those that are not wild creatures (a kind with no diet, or a kind in a faction that is not of the wild alignment): undead, dragonkin, slime and spirit, and a troll in a non-wild faction; people-kinds (human, goblin, orc, elf, dwarf, lizardfolk) keep it among themselves. **The data troll is wild:** `swamp_troll` (`data/content/entities/entity_archetypes.yaml:298-301`) is in `wild_beast_pack` (alignment `wild`) and has a diet, so it goes by appraisal. **A non-wild troll is reachable only as a camp offspring:** `spawn_natural_creature_offspring` (`src/systems/world_systems/generator.py:208`) gives it the legacy MONSTER_HORDE enum and no `faction_id`, which resolves to the invader bucket (`src/entities/identity_resolver.py:24,118-128`, `src/content_semantics/faction.py:122,144-145`); it is spawned only with `ENABLE_CAMP_NEST_SPREAD` (`src/world/camp.py:71`, default OFF, `src/domains/optimization/feature_flags.py:196`) or `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (`src/world/camp.py:85`, default OFF, `feature_flags.py:174`), and births (TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND) retires both when it lands. No data world places a troll outside `wild_beast_pack`. On main, `ENABLE_CAMP_NEST_SPREAD` is ON in exactly one place, `config/simulation_quality/profiles/camp_maturity_calibration_pilot.yaml:2` (the unit-tier calibration world `camp_maturity_calibration_pilot`, not a gate world), and `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` is ON nowhere; the caveat goes away when births retires both flags.
```
