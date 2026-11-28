---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
artifact_type: investigation
date: 2026-11-18
tags: []
---

# newborn_archetype table by the D3 rule (rulings d3 table 6df73509)

Computed at the births branch head from `paired.WORLDS` compiled at seed 42 (seed 43 gives the same bodies), no ticks run. t0 reference = per gate world, the count-weighted mean hp and atk of the species' bodies that are not leader/alpha/boss. Distance = max(|hp-hp0|/hp0, |atk-atk0|/atk0). **The "mean of a multi-body species" reading is my interpretation (the rule names one t0 body); confirm it.**

| species | t0 mean hp/atk (frontier / urban / crowded) | chosen | distance of chosen (frontier / urban / crowded) | alternatives (distance, frontier world) | status |
|---|---|---|---|---|---|
| human | 93.75/10.04 / 93.0/9.43 / 96.25/10.79 | village_worker (100/10) | 0.067 / 0.075 / 0.073 | frontier_guard 0.28, adventurer_hero 0.28, apprentice_mage 0.394, blacksmith 0.502, merchant 0.602, healer 0.602, bandit_scout 0.793 | chosen, closest in all three worlds |
| goblin | 37.5/9.75 / none / 37.5/9.75 | goblin_raider (40/10) | 0.067 / - / 0.067 | goblin_archer 0.128, goblin_scout 0.179 | chosen; CHANGED from goblin_scout by the rule |
| wolf | 45/12 / none / none | hungry_wolf (45/12) | 0.0 | alpha_wolf excluded | chosen |
| spider | 50/14 (frontier only) | cave_spider (50/14) | 0.0 | none | chosen |
| orc | 150/18 (crowded only) | orc_brute (150/18) | 0.0 | orc_warchief excluded (leader) | chosen |
| small_plant_eater | 20/3 (frontier only) | wild_small_plant_eater (20/3) | 0.0 | none | chosen |
| dwarf | no t0 reference | PLACEHOLDER (only rule-1 option: dwarven_hunter 95/13; provisional: no t0 reference) | n/a | none | rule 5: no t0 reference, not picked; placeholder here, nothing in content YAML |
| troll | no t0 reference | PLACEHOLDER (only rule-1 option: swamp_troll 260/28; provisional: no t0 reference) | n/a | none | rule 5: no t0 reference, not picked; placeholder here, nothing in content YAML |
| elf | no t0 reference | NOT PICKED; rule-1 options: forest_ranger 95/13, forest_druid 85/4 | n/a | | rule 5: no reproduction_profile in content until rpg-designer-ubuntu fills the pick, so no elf births |
| lizardfolk | no t0 reference | NOT PICKED; rule-1 options: lizardfolk_scout 70/18, lizardfolk_shaman 70/14 | n/a | | rule 5: no reproduction_profile until rpg-designer-ubuntu fills the pick |

No species is more than 50% off t0 (disclosure threshold): none of the chosen with a t0 reference is. dwarf and troll cannot be measured (no t0 reference); troll swamp_troll is 260 hp/28 atk against humans at about 94/10.

Rule 5 (b5554f6b): elf, dwarf, troll and lizardfolk have no t0 body in any gate world, so no parents there and no M1 figure or bar moves. Their species.yaml carries no reproduction_profile or newborn_archetype until the designer fills the pick (marked provisional: no t0 reference); the rule-2 revisit goes on the births name-branch/retirement backlog line and the PR lists them with the Q6 territory line and the interim newborn role row.

## Q17 picks (rpg-designer-ubuntu, c32eb73f; Q16 count-weighted mean accepted)

All four ship with a reproduction_profile and a newborn_archetype, each marked **provisional: no t0 reference** (reference = count-weighted mean of the species' members in populations.yaml, then rule 2): elf = forest_ranger (distance 0.0; druid 0.69); lizardfolk = lizardfolk_scout (0.029 against 70/17.5; shaman 0.20); dwarf = dwarven_hunter (only option); troll = swamp_troll (only option; disclose as a large body, 260/28, with no gate-world parents). The "Rule 5" paragraph and the PLACEHOLDER/NOT PICKED rows above are superseded by this section.
