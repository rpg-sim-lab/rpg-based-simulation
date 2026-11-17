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
