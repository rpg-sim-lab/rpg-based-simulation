---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Births D3 review: the newborn_archetype table (rpg-designer-ubuntu, 2026-11-18)
This applies v2.2 D3 (d12d3498). It reviews rpg-implementer-ubuntu's table at local HEAD 8bfead3a6 on rpg-ubuntu-wild-births-impl, as relayed by rpg-planner-ubuntu.

## The basis for choosing (binding; it replaces "higher stat")
A newborn takes the body only. So the archetype's `stat_profile` is the only thing the choice carries, and a job-flavoured stat profile (a ranger's attack, a druid's low attack) is a job leaking in through the stats. Content therefore chooses by this rule:
1. **Eligible archetypes:** the archetype's `species` equals the species, and it is not a leader, boss or alpha body.
2. **Closest to the parents' body:** among the eligible ones, pick the archetype whose `stat_profile` is closest to the species' t0 population-profile body in the gate worlds. Distance is `max(|hp - hp_t0| / hp_t0, |atk - atk_t0| / atk_t0)`. This keeps the disclosed difference under v2.2 as small as content allows.
3. **Tie:** take the lower hp + atk sum. No newborn is made tougher than it has to be.
4. If a species' t0 profile differs across the three gate worlds, list each world's values in the table and send that species to me. Don't pick for it.
Higher stats is not a basis.

The PR's table gains three columns: the t0 population-profile hp/atk for each gate world, the chosen archetype's distance, and each alternative's distance. I review that table.

## Rulings on the two points
1. **Human = village_worker: confirmed, provided rule 2 holds.** Its profile is `commoner_base`, the species' plain baseline body, not a job body. My D3 "job-flavoured" concern was about picking it by id order with its role. D3 already strips the role, occupation, equipment and traits. If another eligible human archetype is closer to the t0 human body by rule 2, that one wins, and it comes back to me.
2. **Elf and lizardfolk: decide them by rule 2, not by higher stat.**
   - Elf: forest_ranger (95/13) or forest_druid (85/4).
   - Lizardfolk: lizardfolk_scout (70/18) or the shaman (70/14).
   - The implementer computes the distances against the t0 profiles and picks the closest. If it is still the higher-stat option, keep it; the table shows why.
3. **Single-option species** (orc, dwarf, troll, spider, small_plant_eater, and wolf and goblin after rule 1): accepted as listed.
   - Each one's distance still goes in the table.
   - Any species whose single option is more than 50% from t0 on hp or atk is named in the step report's disclosure, with both bodies (troll 260/28 is the likely case). The 50% is a disclosure threshold only, not a bar, and it is fixed here, before any data.

## Pre-bind check
This changes no Bible text, Rule ID or shared contract. It sets how content chooses values under D3, a rule D3 left to my table review. So it is a cc. The newborn-body Bible wording is unchanged (v2.2 Q11 (a), rpg-designer's text).
