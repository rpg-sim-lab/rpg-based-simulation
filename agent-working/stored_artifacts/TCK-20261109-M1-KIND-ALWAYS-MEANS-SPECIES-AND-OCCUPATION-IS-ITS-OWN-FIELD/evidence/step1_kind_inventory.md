---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD
phase: open
artifact_type: investigation
date: 2026-11-16
tags: []
---

# Step 1 evidence: every entity-kind reader and every kind-keyed constant (rpg-implementer-3, 2026-11-16, on origin/main e72270894)

Rule work only: no code changed. The designer rules every row marked **unclear** and every constant in table B before step 3 (readers) and step 4 (constants).

## Method and limits
- `kindscan.py` (kept beside this file) lists every `<expr>.kind` attribute read in `src/` by its base expression (432 reads). `kindscan2.py` lists the candidate entity-side reads (`getattr(x, "kind")`, `x["kind"]`, `x.get("kind")`, and the attribute reads whose base names an entity). Each candidate was then read in place; reads whose base is a project, objective, contract, lead, blocker, concern, intent, status effect, building, node, region, place, option, requirement, turning point or cognition-graph node are NOT entity kinds and are excluded (they are different `kind` fields).
- Kinds that reach a reader by a local variable or a parameter (`kind`, `victim_kind`, `target_kind`, `spawn_monster(kind=...)`) are counted at the line where they leave an entity, plus the consumer listed in the row.
- NOT covered: `data/` and `config/` files, `frontend/`, `tests/` (the test fixtures write many kinds; step 4 needs them re-keyed too), and any dynamic access (`getattr(obj, name)` with a computed name). A reader missed by the scan would surface as an unexplained behaviour delta in step 4's measurement; this is the same risk the designer names for the one-step option.
- Counts: table A has 25 rows (each row can hold several lines of one file or one plumbing chain); table A2 has 11 writer rows; table B has 13 rows. These are row counts, not a claim that the scan is complete (see the limits above).

## A. Entity-kind readers (`EntityState.kind` read in `src/`)
Class: species (names the creature type) / occupation (names a job or role label) / faction / display (shown, logged or serialised; no decision branches on it) / unclear (needs the designer).

| # | file:line | what it does | class | note |
|---|---|---|---|---|
| 1 | src/api/presenters/state_presenter.py:129, 216, 250 | puts `entity.kind` in the API payload | display | the presenter step 2 extends (shows both `kind` and `occupation`) |
| 2 | src/core/export.py:45 | `EntityDTO(kind=ent.kind)` | display | DTO export |
| 3 | src/core/state.py:921 (`EntityState.to_canonical_dict`) | `"kind": self.kind` in the hashed dict | display | hash input; `kind` moves meaning at step 4 so every hash moves (designer: expected) |
| 4 | src/replay/fingerprint.py:58 | `f"{ent.kind}:"` in the replay fingerprint | display | hash input |
| 5 | src/domains/campaigns/orchestrator.py:544, 820 | survivor reconstruction copies `kind`, `role`, `faction`, `properties`, `traits` and rebuilds with `.kind(cf.kind or "entity")` | display | carry-through plumbing; **step 2 must also carry `occupation` here**, or a reconstructed survivor loses it (the 2026-09-11 rule: survivor identity-equivalent to a spawned entity) |
| 6 | src/entities/archetype_factory.py:142, 168 | `kind=entity.kind` when it copies an entity | display | carry-through; same: carry `occupation` |
| 7 | src/engine/patches.py:51-52, 794-795; src/engine/compactor.py:84; src/engine/apply.py:770; src/core/updates.py:201, 238, 270 | `EntityUpdate.kind_set` / `KindPatch` rewrite `kind` | display | plumbing. EvolutionSystem always writes `kind_set` (observability comment at event_shapers.py:1065); no other production writer found. Step 4 must keep `kind_set` from renaming species (D79) |
| 8 | src/engine/evolution.py:100-104 | `"goblin" in entity.kind.lower()` then `"1" in kind` / `"2" in kind` picks gear | unclear | species ("goblin") and a tier digit carried in the kind string ("goblin_warrior1"?). The digit is neither species nor occupation; the designer rules (tier = level/evolution?) |
| 9 | src/engine/domain/combat_actions.py:78; src/engine/domain/aoe_actions.py:89 | passes `target.kind` as the victim kind into quest kill credit | species | consumer src/engine/quests.py:145 compares it to `project.metadata["target_kind"]` (Path 4). Quest `target_kind` values: "wolf" (species) in quests/generator.py:83 and "GOBLIN" in certification/scenarios.py:297 (upper case: never matches today) |
| 10 | src/systems/social_systems/party_composition.py:52-66 | maps kind to a PartyRole: guard/sentinel/guardian/brute, healer/mage/shaman/druid, hero/ranger/hunter/scout, worker/merchant/citizen/blacksmith | occupation | role words only; step 3 reads `occupation` |
| 11 | src/world/calamity.py:99 | `entity.kind == "hero"` raises calamity on a hero death | occupation | designer already counts this one |
| 12 | src/observability/extraction/combat.py:82 | `kind == "hero"` | occupation | designer's list |
| 13 | src/observability/event_shapers.py:337 | `prior_ent.kind == "hero"` raises `hero_death_unrecorded` | occupation | designer's list |
| 14 | src/observability/event_shapers.py:1069, 1074, 1165, 1168; src/observability/extraction/progression.py:52, 57; src/observability/extraction/lifecycle.py:23, 38, 51, 60; src/observability/extraction/world.py:111; src/observability/starvation_record.py:104, 262 | emit `kind` / `previous_kind` / `new_kind` into events and records | display | |
| 15 | src/observability/event_shapers.py:1189 | `kind == "goblin_raider"` emits `raid_party_spawned` | unclear | one string that is species + role ("goblin" + "raider"); also constant table B2/B5 |
| 16 | src/observability/extraction/world.py:112 | `kind in BOSS_ENTITY_KINDS` emits boss-spawn events | unclear | table B3 (the labels there are occupation-like and species-like at once) |
| 17 | src/observability/event_shapers.py:1211; src/observability/extraction/resources.py:87 | `kind not in SPAWN_CADENCE_EXCLUDED_KINDS` excludes entities from the spawn cadence | unclear | table B2 |
| 18 | src/systems/world_systems/navigation.py:41 | `e.kind == "world_boss"` picks the boss as a flow-field anchor | unclear | "world_boss" is a label (occupation) the generator writes as `kind` |
| 19 | src/world/boss.py:85 | `entity.kind == "world_boss"` active living boss | unclear | same |
| 20 | src/world/boss.py:217 | `entity.kind == "dragonkin"` active lair occupant | unclear | "dragonkin" IS a species id (species.yaml:245) and is used here as the lair occupant's label |
| 21 | src/world/threat.py:30 | `e.kind == "world_boss"` boss exists in the region | unclear | same as 18 |
| 22 | src/world/environment.py:86 | `getattr(s, "kind") == "stronghold"` | unclear | designer's list; a non-living entity with a kind, needs the named allowlist at step 4 |
| 23 | src/world/creature_territory.py:52, 63 | looks up maturity rate by `entity.kind` and respawns with `kind=entity.kind` | unclear | species + role in one key ("goblin_warrior", "orc_warrior"); table B1 |
| 24 | src/world/reproduction_humanoid.py:57, 89 | pairs two entities only if `kind` is equal, and passes `a.kind` as the newborn's kind | unclear | designer's list. Today equal `kind` = equal role string, so humans pair by occupation and the child inherits the parent's occupation as `kind` |
| 25 | src/systems/world_systems/generator.py:67 (via `_catalog_faction_properties(kind)`) | maps a spawn kind to a catalog faction id | faction | not an entity read: it keys the spawned kind. Table B4. The designer's "faction: 0" counts entity-side reads; this is a keyed table |

Reads that are NOT entity kinds and were checked and excluded (a sample of the 400 others): `b.kind` in presenters/need_paths/blacksmith/shop/town_navigation/world_index/perf scenarios = building kind; `n.kind` = resource node; `s.kind in ("frozen","stunned")` (legality.py:161/195/265/341, actor_validity.py:59-60, combat.py:108, intelligence.py:904/974/1277, work_queue.py:33) = status effect; `req.kind`, `opp.kind`, `tp.kind`, `l.kind`, `c.kind`, `p.kind` (projects), `best_candidate.kind` (GoalKind), `option.kind` (ConversionKind), `place.kind`/`region.kind` (PlaceKind / region kind), `cond.kind` (scenario victory condition), cognition-graph `node["kind"]`.

## A2. Writers of `EntityState.kind` (what `kind` is set to, per build path)

| file:line | value written | class of the value |
|---|---|---|
| src/worldbuilding/compiler.py:766 | `pop_spec.role.lower()` | occupation (the classic compiler; the 3 gate worlds). The species is separately `properties["species_id"]` (compiler.py:760-761) |
| src/entities/contract_builder.py:41 | `arch.species_id` | species (archetype path) |
| src/entities/archetype_factory.py:98 | `contract.kind` | species (copies the contract above) |
| src/worldassembly/entity_spawner.py:130 | `profile.species_id or "human"` | species (a third build path; has a code default `"human"`, which the designer's step 4 refusal rule forbids) |
| src/systems/world_systems/generator.py:139 | `"hero"` | occupation |
| src/systems/world_systems/generator.py:165, 204, 238, 284 | the `kind` argument of `spawn_monster` / natural-creature / humanoid spawn functions | mixed: callers pass "world_boss" (calamity.py:84), "ancient_sentinel" (boss.py:149), "dragonkin" (boss.py:259), `entity.kind` (creature_territory.py:63), the default `"monster"`, or a parent's kind (reproduction_humanoid.py:89) |
| src/systems/world_systems/generator.py:321 | `"goblin"` | species-like |
| src/domains/campaigns/orchestrator.py:820 | `cf.kind or "entity"` | whatever the survivor carried; falls back to the literal "entity" |
| src/domains/campaigns/runner.py:69 | `role` | occupation |
| src/world/camp.py:72-76, 98 (`spawn_natural_creature_offspring(kind=camp.kind)`) | the camp's kind (`NEST_RACE_KINDS` = wolf, spider, troll, slime, camp.py:21) | species (all four are ids in species.yaml) |

## B. Kind-keyed constants and tables

| # | file:line | what is keyed by kind | keys | proposed class (designer rules) |
|---|---|---|---|---|
| B1 | src/world/creature_territory.py:22-25 | `TERRITORY_MATURITY_RATES` (maturity per kind) | goblin_warrior, orc_warrior; default 0.03 | species+role compound: "warrior" is the occupation, "goblin"/"orc" the species |
| B2 | src/observability/entity_kind_constants.py:8 | `SPAWN_CADENCE_EXCLUDED_KINDS` | None, world_boss, ancient_sentinel, goblin_raider, dragonkin | mixed occupation labels and one compound |
| B3 | src/observability/entity_kind_constants.py:6 | `BOSS_ENTITY_KINDS` | world_boss, ancient_sentinel, dragonkin | occupation-like labels; "dragonkin" also reads like a species |
| B4 | src/systems/world_systems/generator.py:27-38 | `SPAWN_KIND_CATALOG_FACTION` (spawn kind to catalog faction id) | goblin_warrior, goblin_raider, orc_warrior, bandit, goblin, dragonkin, wolf, slime, bear, harpy, golem | mixed: species (goblin, wolf, slime, bear, harpy, golem), compound (goblin_warrior, goblin_raider, orc_warrior) and an occupation (bandit); "world_boss is absent on purpose" per its comment |
| B5 | src/observability/event_shapers.py:1189 | literal branch `kind == "goblin_raider"` | goblin_raider | compound |
| B6 | src/quests/generator.py:83 | `QuestTemplate(..., target_kind="wolf")` | wolf | species (the comment says the archetype's species maps to `kind`; true on the archetype path only, so on the classic path a "wolf" role string would be needed today) |
| B7 | src/engine/quests.py:145 | `metadata["target_kind"] == victim_kind` | any | consumer of B6; also certification/scenarios.py:297 uses upper-case "GOBLIN" (never matches) |
| B8 | src/engine/evolution.py:100-104 | gear by `"goblin"` substring and a digit | goblin, 1, 2 | species + a tier digit |
| B9 | src/systems/social_systems/party_composition.py:58-65 | PartyRole by kind | guard, sentinel, guardian, brute, healer, mage, shaman, druid, hero, ranger, hunter, scout, worker, merchant, citizen, blacksmith | occupation |
| B10 | src/world/boss.py:85, 217; src/world/threat.py:30; src/systems/world_systems/navigation.py:41 | literal compares | world_boss, dragonkin | occupation-like labels |
| B11 | src/world/environment.py:86 | literal compare | stronghold | non-living entity kind |
| B12 | src/world/calamity.py:99; extraction/combat.py:82; event_shapers.py:337 | literal compares | hero | occupation |
| B13 | src/systems/world_systems/navigation.py:36-39 | `FlowFieldService.ANCHORS.get(target_kind)` and `target_kind == "WORLD_BOSS"` | TOWN, WORLD_BOSS, ... | not an entity kind (an anchor kind); listed so it is not re-found |

## C. What step 1 found that the ruling did not list (for the designer)
1. **Survivor reconstruction (row 5) and the archetype copy (row 6) are carry-through sites for `occupation`.** If step 2 only adds the field at build, a campaign survivor or a copied entity loses it. Step 2 will carry it at both, and I will say so in the step-2 report.
2. **A third build path** (`worldassembly/entity_spawner.py:130`) writes a species with a code default of `"human"`. The step-4 refusal rule ("a population with no declared species is a typed error") conflicts with that default.
3. **Row 8 (`evolution.py`)** reads a tier digit out of the kind string, which is neither species nor occupation; it needs a ruling.
4. **Quest target `"GOBLIN"`** (certification/scenarios.py:297) never equals any kind today (kinds are lower case).
5. **`dragonkin`** is an id in `data/content/living/species.yaml` (line 245), so it is a species as well as the lair occupant's label; `world_boss` and `ancient_sentinel` are not species ids. `stronghold`, `bandit`, `golem`, `bear`, `harpy` are not in species.yaml either (the file has human, wolf, goblin, spider, orc, elf, dwarf, undead, troll, lizardfolk, dragonkin, slime, spirit, small_plant_eater): table B4 keys several kinds that have no species entry.
