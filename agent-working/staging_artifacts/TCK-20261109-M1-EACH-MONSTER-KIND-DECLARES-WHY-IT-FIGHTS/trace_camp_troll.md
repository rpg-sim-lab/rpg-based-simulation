---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Trace 2: camp-spawned trolls (read at origin/main 51a6516cf)

## Is it live on main?
No, not by default.
- The spawn is `CampService.process_camps`, nest-spread branch, `src/world/camp.py:71`: it needs `flags["ENABLE_CAMP_NEST_SPREAD"] == "ON"`, a camp whose `kind` is in `NEST_RACE_KINDS` (:21: wolf, spider, troll, slime), maturity >= 80 and 500 ticks since the last raid. The flag defaults OFF (`src/domains/optimization/feature_flags.py:196`). The comment at :68 says it is OFF by default and retired with the M1 births.
- A second path, `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (camp.py:85 onward), also defaults OFF (feature_flags.py:174) and calls the same `spawn_natural_creature_offspring`.
- D70 removed the other camp spawning (camp.py:68 comment).
- Tests that turn the flags ON: `tests/unit/world/test_camp_lifecycle.py`, `test_natural_creature_reproduction.py`, `test_world_dynamics.py`, `test_calamity_magical_demonic_reproduction.py`; the pilot world `camp_maturity_calibration_pilot` mentions the nest flag. No gate world sets it (not checked against the run configs, which I did not read).

## What faction does the offspring get?
`spawn_natural_creature_offspring` (`src/systems/world_systems/generator.py:176`, identity built at :208) sets the legacy enum `faction=Faction.MONSTER_HORDE` and no `faction_id` property.
- `EntityIdentityResolver` falls to Path 3 (`identity_resolver.py:118-128`): `_FACTION_COMPAT[MONSTER_HORDE]` = the string "monster_horde" (:24).
- `get_alignment_bucket("monster_horde")` finds no catalog faction, maps through `get_legacy_faction_bucket` ("MONSTER" in the id, faction.py:122) to MONSTER_HORDE, and returns "invader" (faction.py:144-145).

## Can it be non-wild? Yes, always.
A camp-spawned troll (and wolf, spider or slime) has alignment "invader", not "wild". `is_wild_creature` (hostility.py:47-54) is therefore False for it, so with the flag ON it keeps the faction verdict and is hostile to every non-invader, including wild fauna, the very case decisions 47 and 62 meant to remove. Only the data-placed `swamp_troll` (wild_beast_pack) is wild.
So the "troll keeps faction hostility" line of 2.107 is true for the camp-offspring troll, flag ON, and false for the archetype troll. The interim gap is real but dormant while both reproduction flags are OFF.

## Consequence for the code step
- The predicate that replaces `is_wild_creature` must read the species' declared reason, so a camp-spawned troll and the archetype troll behave identically (the declared reason is on the species, not on the faction).
- The offspring's content faction is a separate gap (it should carry a content `faction_id`), outside this ticket; mention to the births owner.
