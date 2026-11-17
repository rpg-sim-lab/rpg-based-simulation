---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
artifact_type: investigation
date: 2026-11-17
tags: []
---

# Investigation: births (read at origin/main 3aafdb383)

- Old paths: `reproduction_humanoid.py` (flag ENABLE_REPRODUCTION_HUMANOID_PATH, cadence 200, radius 10 Euclid via `nearby_entities`, cooldown 400, scarcity gate, role/faction = CITIZEN/TOWN_COUNCIL always); `camp.py` natural-creature (flag ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH, camp maturity >= 80 and tick % 30 == 0, parentless, `short_clock_age`, generic 50-HP tier stats, gold from tier) and nest spread (ENABLE_CAMP_NEST_SPREAD, 500-tick raid cadence). All three default OFF, so removal moves no default-flag run.
- Hunger: `BiologicalComponent.hunger` 0-100, higher hungrier; update field `BiologicalUpdate.hunger_delta`. Rates per biological tick = 0.1 x {none 0, very_low 0.3, low 0.5, medium 1.0, high 1.5}. Stage lines: hungry 70, weakened 85, starving 95 (engine/starvation.py).
- Species: 14; hunger none = undead, dragonkin, slime, spirit (no births, owner B2). Others get a profile.
- Cooldowns: `reproduction_cooldowns` is written only by the old humanoid service (and one lifecycle test), never pruned. No remove field existed on `LifecycleUpdate`.
- Time: 2400 ticks a day; CHILD ends at 3,456,000 ticks (ai/life_stage.py), so an age-0 newborn never reaches ADULT inside a run.
- t0 body provenance: archetype path (`ArchetypeEntityFactory`, stats from stat_profile via contract) versus classic compile (`worldbuilding/compiler.py`, stats from the population's resolved profile, no `archetype_id` property). Which the gate worlds use is the first pre-code check.
- The step-4 own-job runner (run_step4.sh, spy) is not on this host; `tools/rpg_measure/paired.py` and `arm_child.py` exist and are the base for the new runner.
- Not read: creature_territory (gated OFF, untouched), calamity (untouched).

## Step-1 results (2026-11-17, 3aafdb383; compile of paired.WORLDS at seed 42, no ticks run)
- Bodies: frontier_living_world 55 (goblin GUARD 4 / MONSTER 5, human GUARD 9 / SHOPKEEPER 6 / WORKER 9, small_plant_eater 6, spider 5, undead 6, wolf 5; 2 camps), urban_political 30 (human only, 3 HERO), crowded_frontier 38 (goblin 9, human 24, orc 5; 1 camp). All ADULT, age 0, hunger 0.0, none with `archetype_id`.
- Eligible kinds at t0 with >= 2 adults: human, goblin, wolf, spider, small_plant_eater (frontier); human, goblin, orc (crowded); human (urban). Undead present, no births by design.
- Roles: goblins and humans mostly civil roles (GUARD, SHOPKEEPER, WORKER); only MONSTER mothers give MONSTER newborns, others give CITIZEN (the Coming-of-Age roll never runs inside a run, newborns stay CHILD).
- Apply order and id behaviour as in plan G2; spatial query metric as in plan section 2.
