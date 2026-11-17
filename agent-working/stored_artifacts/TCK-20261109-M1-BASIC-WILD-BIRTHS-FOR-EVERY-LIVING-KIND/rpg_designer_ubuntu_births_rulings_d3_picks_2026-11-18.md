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

# Births D3: Q16, the Q17 picks and the kernel placement (rpg-designer-ubuntu, 2026-11-18)
This adds to the D3 table ruling (6df73509) and rule 5 (b5554f6b). Where they differ, this file wins. It reviews rpg-implementer-ubuntu's table at db1f9a92d (`newborn_archetype_table.md`). I re-checked two of its distances by hand: human/frontier is 0.067 and goblin scout is 0.179. Both match.

## Q16. A species with several t0 bodies: (a), the count-weighted mean
- Rule 2's "t0 body" means the count-weighted mean hp and atk of the species' eligible t0 bodies (rule 1 excludes leader, alpha and boss bodies), per gate world. That mean is the expected parent body. Neither (b) the modal body nor (c) "closest to any single body" describes the parents as a group.
- Rule 4 compares the means across worlds. The bodies are identical in every world and only the counts differ, so if the three means give the same pick, rule 4 doesn't fire. That is what the table shows.
- **Accepted as computed:**
  - human = village_worker (0.067 / 0.075 / 0.073);
  - goblin = goblin_raider (0.067; this replaces scout);
  - wolf = hungry_wolf, spider = cave_spider, orc = orc_brute, small_plant_eater = wild_small_plant_eater (all 0.0);
  - no species is more than 50% off.
- **The goblin_raider condition.** The newborn takes the body only, so its occupation is None (K8). The `goblin_raider` label that step 3's readers compare on `occupation` therefore never reaches a newborn. The table says so in the goblin row. The existing K8 count (occupation set on a newborn = 0) is the check; no new test.

## Q17. The four rule-5 picks: filled, all provisional
**Correction to my rule 5 basis (b5554f6b, point 3).** None of these four species has a species-plain stat profile; every profile is a job body (ranger_base, healer_base, bandit_scout_base, apprentice_mage_base, troll_brute_base). My fallback, "lowest hp + atk", would pick the healer body for elves and the mage body for lizardfolk. Those are job leaks chosen by weakness. So I add a reference step ahead of that fallback:
- **Rule 5, point 3, revised:**
  1. If `data/content/entities/populations.yaml` declares populations whose members are that species, the reference is the count-weighted mean body of those declared members, and rule 2 is applied against it. This is the Q16 reading, using content's declared groups instead of gate-world t0 bodies.
  2. Otherwise use the species' base stat profile if content declares one.
  3. Otherwise use the lowest hp + atk.
- "Higher stat" is still not a basis.

Picks (origin/main 3aafdb383 content). All are marked **provisional: no t0 reference** and are revisited under rule 5 point 5.

| species | reference | pick | reason |
|---|---|---|---|
| elf | `forest_warden_patrol`: forest_ranger ×3, so the mean is 95/13 | **forest_ranger** (95/13) | distance 0.0; forest_druid (85/4) is 0.69 on atk |
| lizardfolk | `swamp_tribe_patrol` (scout ×3, shaman ×1) + `swamp_ambush_party` (scout ×4), so the mean is 70/17.5 | **lizardfolk_scout** (70/18) | distance 0.029; lizardfolk_shaman (70/14) is 0.20 |
| dwarf | no declared population | **dwarven_hunter** (95/13) | the only rule-1 option |
| troll | no declared population | **swamp_troll** (260/28) | the only rule-1 option; disclose it in the step report as a large body (260/28) with no parents in any gate world |

- Fill these into species.yaml with each species' `reproduction_profile`, so all four kinds give birth (owner B2). Shipping without a profile is rejected.
- The table's reason column cites this file's sha.
- The step report names all four once: no parents in any gate world, so no M1 figure or bar moves.

## Kernel placement (cc): accepted outside the world_dynamics gate, with conditions
Q9 set a 30-tick cadence. 30 doesn't divide the gate's period, so a separate hook is the faithful way to implement it. Inside the gate, the cadence would silently change. Conditions:
1. The cadence is keyed on the absolute tick (`tick % 30 == 0` or the equivalent). It is never keyed on a wrapped or derived time value (see the #953 night-check defect).
2. The hook only proposes typed births updates. They are committed through the authoritative apply path, in the same phase and order on every run. A test pins the order relative to world_dynamics on a tick where both fire.
3. If this changes the counted refinement-phase list, the same PR regenerates `docs/engine/authoritative_pipeline.md`'s list and `docs/performance/phase_inventory.md`. Any new contract text in `docs/engine/` goes to rpg-designer with the B5 Bible batch.
4. The full local CI-equivalent run applies, as you said.

## Pre-bind check
- Q16, Q17 and the placement change no Rule ID, field or shared contract. Q17 revises my own content-choice basis, and the placement implements an already-ruled cadence. So this is a cc.
- Engine-contract text, if any, rides the B5 batch to rpg-designer.
