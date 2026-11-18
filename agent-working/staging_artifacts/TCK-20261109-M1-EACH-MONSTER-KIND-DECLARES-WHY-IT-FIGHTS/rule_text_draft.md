---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: rule_text_draft
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Draft rule text: why each monster kind fights (decision 62)

DRAFT. Not accepted. Every AFTER below is written on the recommended option of each owner question in `plan.md` (Q1 A, Q2 A, Q3 A, Q4 A, Q5 B, Q6 A, Q7 A). If the owner picks another option, the AFTER changes; nothing here is a ruling. Rule questions go to rpg-designer via rpg-planner and the leads.

BEFORE blocks are quoted verbatim from origin/main 51a6516cf.

## 1. World-rules catalog, `docs/world_rules/capability-progression/conflict-combat.md`, CONFLICT-03

### 1a. Bullet under "Still open" (lines 101-102)

BEFORE:
```
  - Monster factions keep faction hostility as an interim (decision 62), until milestone 1's
    declared drives.
```

AFTER:
```
  - Monster kinds are regarded by their declared reason to fight, not by faction (decision 62, milestone 1; CONFLICT-05). Faction hostility
    remains a reason to fight only between people-kinds.
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
  - **Scope of the change, by milestone (decided by the owner directly, 2026-10-11; row 62 of the memo; completed in milestone 1).** In the
    hunting batch, only a kind with a diet in a faction declared wild dropped faction hostility and went by the appraisal. In milestone 1,
    every non-people kind goes by its declared reason to fight (CONFLICT-05): the undead hate the living, a spirit guards a place, a troll
    or dragonkin hunts by its diet and the appraisal. Faction is a reason to fight only between people-kinds (kinds that keep coin and
    trade). **Alternatives not taken:** every non-people kind at once in the hunting batch (the undead, slimes and spirits had no diet
    and would have ignored people until a drive existed); wild animals only, for good (monsters would stay enemies by a label).
```

### 1c. New entry, inserted after CONFLICT-04 (before the section that follows it)

BEFORE: (no entry)

AFTER:
```
## CONFLICT-05 — Each non-people kind declares why it fights; a faction label never decides a monster's fight

> A kind that does not keep coin and trade fights for a reason its content declares. The reason is one of a closed set: it hates the
> living, it guards a place, or it hunts by its diet. Hostility toward and from such a kind is derived from that reason and from the
> appraisal (CONFLICT-03), never from the faction it belongs to. Faction enmity remains a reason to fight between people-kinds only.

- **Reasons.** `hates_living`: the kind engages a perceived body the content marks as living. `guards_place`: the kind engages a perceived
  body within a fixed reach of its home tile; it keeps no territory record (territory is milestone 2). `hunts_by_diet`: the existing
  PREDATION appraisal (hungry, the diet can eat the body, the hunter believes it can overcome it); no other trigger.
- **Permission is symmetric (CONFLICT-03).** An attack is permitted in both directions when either side's declared reason names the
  other. A people-kind regards a body as an aggressor when that body's declared reason names it, so a guard still answers an undead
  sentinel without a faction label.
- **A kind never regards its own species as a target** (no cannibalism in milestone 0); this replaces "a faction does not hunt its own".
- **A kind with no declared reason fights only back.** The content-load check refuses a monster kind that declares a reason outside
  the closed set.
- **Alternatives not taken:** the reason as a drive weight (a band, not a vocabulary); derive it from a trait name (a name check,
  decision 46); keep the invader verdict for monsters (a label decides).
- **Disposition:** PROPOSED — awaits the owner. Implemented by TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS.
```

## 2. Divergence record, `docs/guidelines/intentional_divergences.md`, entry 2.107 (one sentence group inside a bullet)

BEFORE (verbatim):
```
**INTERIM, not the rule** (owner, 2026-10-11, the D47 scope amendment, CONFLICT-03): the owner ruled the narrow scope (a non-people kind with a diet in a faction declared wild) for now; M1 widens the one shared predicate to every non-people kind by declared drive (undead hate the living, spirits guard a place, troll and dragonkin hunt by diet). **The predicate is `is_wild_creature` in `src/engine/hostility.py`** (read by `faction_hostile` and `attack_allowed`); M1 changes that one function.
```

AFTER (applied by the code step, in the same change as the behaviour):
```
**Closed by milestone 1** (decision 62, CONFLICT-05, TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS): the wild-faction gate is gone. Every non-people kind goes by its declared reason to fight; people-kinds keep faction hostility among themselves. `is_wild_creature` is replaced by a property read of the declared reason.
```

## 3. Mechanics Bible, `docs/mechanics/02_combat_laws.md`, new paragraph after the Friendly Fire item (line 119)

BEFORE: (no paragraph)

AFTER:
```
**Who is hostile to a non-people kind (CONFLICT-03, CONFLICT-05, decision 62).** A kind that does not keep coin and trade is hostile by its
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
*   **Catalog hostility between people, declared reasons for monsters**: every perception-side "is this an enemy" test goes through the one shared hostility predicate (CONFLICT-05): `content_semantics.faction.are_entities_hostile` (real distance, `combat_engaged=True`) decides between two people-kinds, and a non-people kind is judged by its declared reason to fight. "Is this an ally" uses `are_entities_allied` (same resolved catalog faction), never `identity.faction ==/!=` on the four-value legacy `Faction` enum, which collapses content factions.
```
(The rest of the bullet, the `Sites:` list, is unchanged.)

## 5. Parity ledger, `docs/parity_ledger/combat_movement.yaml`

Applied by the code step: COMB-334 gains the monster-reason evidence and test path; one new P1 entry per declared reason, `test_path` set when its test lands. No YAML is drafted now because the test paths do not exist yet.

## 6. Kernel spec, `docs/engine/authoritative_pipeline.md`

Searched: it holds no hostility text (only the Sovereignty Law line at 101, kill-based influence). No change proposed. If rpg-planner means another file by "kernel spec", name it.
