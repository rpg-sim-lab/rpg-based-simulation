---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Investigation: why each monster kind fights (decision 62, phase 1, docs only)

Base: origin/main 51a6516cf. No src/ or content edits in this phase.

## 1. Which kinds are "monsters"

The people marker is the species trait `keeps_coin_and_trades` (memo row 62). Species in `data/content/living/species.yaml`:

| Species | people (trait) | body diet | drive profile | Today |
|---|---|---|---|---|
| human, goblin, orc, elf, dwarf, lizardfolk | yes | plant/meat/prepared | various | faction hostility among themselves (stays, §12.3) |
| wolf, spider | no | meat / plant+meat | territorial_predator | wild creature when in a `wild` faction: appraisal only (decision 47, shipped) |
| small_plant_eater | no | plant, graze | cautious_forager | wild creature (wild_fauna): appraisal only |
| **troll** | no | plant/meat/prepared | territorial_predator | wild creature only if its faction is `wild` (archetype `swamp_troll` is `wild_beast_pack`: already appraisal); else faction hostility |
| **undead** | no | none | undead_purpose_bound | faction hostility (`undead_remnants`, invader) |
| **spirit** | no | none | ritual_fixated | faction hostility (`spirit_court` neutral, or members of undead_remnants / moon_cult / forest_wardens) |
| **dragonkin** | no | meat | disciplined_protector | faction hostility (`dragon_cult`, invader) |
| **slime** | no | none | territorial_predator | faction hostility unless in `wild_beast_pack` (common_species lists slime; no slime archetype exists) |

The M1 set is therefore troll, undead, spirit, dragonkin, slime: the five kinds divergence 2.107 names as interim. Only `undead_sentinel`, `spirit_guardian`, `dragon_cult_champion` and `swamp_troll` exist as archetypes. No slime archetype exists.

**Finding 1.** Divergence 2.107 says "troll keeps faction hostility". True only for a troll outside a `wild` faction. The one troll archetype is in `wild_beast_pack` and already goes by appraisal. Per-world check needed before any measurement claim (worlds may assign other factions).

## 2. Every read of a faction label in hostility decisions (file:line, origin/main 51a6516cf)

Predicate home, `src/engine/hostility.py`:
- :47 `is_wild_creature` (def); :54 is its alignment-bucket read (`== "wild"`). This is the one function M1 changes (2.107).
- :63-64 `faction_hostile` skips the verdict for a wild creature either side.
- :73-78 resolves both faction ids and calls `is_hostile_compat`.
- :90 `relation` drops PREDATION between same-faction members (`get_faction_id_str` equality).
- :113-114 `attack_allowed` ignores the verdict for a wild creature either side.

Faction semantics, `src/content_semantics/faction.py`:
- :158-184 `is_hostile`: alignment law, invader vs everything not invader; legacy `MONSTER_HORDE` bucket fallback.
- :195-240 `is_hostile_compat`: perspective/relationship projection ("enemy", "threat", "intruder") else `is_hostile`.
- :71 `are_entities_hostile`: the wrapper most call sites use.

Legality, `src/engine/legality.py`:
- :256-267 `_attack_permitted` (CONFLICT-03 symmetric declared-hostility rule), using `get_faction_id_str` + `is_hostile_compat`; legacy fallback compares `identity.faction`.
- :493, :568 two more direct `are_entities_hostile` calls.

**Finding 2. Call sites that bypass `hostility.py` and ask the faction question directly** (13 production sites, so "no monster hostility reads a faction label" cannot be met by editing `hostility.py` alone):
`src/domains/combat_engagement/phase.py:303-312` (own faction hoist + `is_hostile_compat`), `src/engine/combat_rewards.py:87-91`, `src/engine/combat.py:500`, `src/engine/cognition.py:47,143`, `src/engine/tactical_threat.py:71`, `src/ai/goals/scorers.py:186`, `src/ai/goals/scorers_support.py:23`, `src/domains/cooperation/providers.py:111`, `src/systems/world_systems/intake.py:35`, `src/systems/strategic_systems/intelligence.py:156,452`, `src/engine/legality.py:493,568`.
This is the deferred TCK-20261107-A-COMBAT-ENGAGE-PROJECT-TARGETS-A-BODY-TACTICAL-NEVER-SEES-AS-HOSTILE ("one hostility predicate is its fix lean"). Overlaps lane B step 5 (hostility.py, appraisal.py, legality.py).

Reads that are NOT hostility decisions and are out of scope (listed so nobody widens): `src/engine/serves.py:45` (a building's controller vs a subject; people only), `src/domains/faction/sentiment.py:74,82` (faction-scale sentiment bookkeeping), `src/world/influence.py:43`, `src/world/environment.py:30` (hazard immunities per faction), `src/content_semantics/personality.py:59` (bravery bias per alignment).

Data that carries the label today: `data/content/social/factions.yaml` (alignment_bucket), `faction_relationships.yaml` and `perspectives.yaml` (monster factions as enemy/threat groups), `entity_archetypes.yaml` (`faction` per archetype).

## 3. What "why it fights" means per kind (decision 62 wording; options, not rulings)

- **undead** ("hate the living"): no diet, drive `purpose_fixation: very_high`, `hunger: none`, `fear: none`. A standing aim at living bodies. Needs a definition of "living" (see Q2).
- **spirit** ("guards a place"): drive `ritual_fixated`. Needs a "place". M1 item 4 (places from perception and memory, decision 56) is the home of places; §12.4 (territory) is out of scope. See Q3.
- **troll, dragonkin** ("hunts by diet"): diets exist (troll plant/meat/prepared, dragonkin meat). The appraisal (PREDATION: hungry, diet can eat it, believes it can overcome it) already implements this for wild creatures. So "hunts by diet" is the existing appraisal with the wild-faction gate removed.
- **slime**: not named by decision 62. It has no diet and drive `territorial_predator`. Needs an owner line (Q4).

## 4. Risks to flag

- Removing the invader alignment verdict removes the only reason a settlement guard attacks an undead sentinel on sight. Appraisal alone gives WARY/THREATENING (avoid, never engage). See Q5.
- Ceiling: `legality.py` LegalityServiceV2 535/554 and `verify_attack_legality` 68/87. Hostility logic must be extracted, not added.
- Overlap with lane B step 5 files (head 7549105d7); whoever lands second resolves mechanical conflicts only.
- `TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK` edits generator.py spawn_* and adds a content-load check; coordinate where new monster content fields sit.
- PERC-02a: night and tick are required keyword-only everywhere; add no defaults.
