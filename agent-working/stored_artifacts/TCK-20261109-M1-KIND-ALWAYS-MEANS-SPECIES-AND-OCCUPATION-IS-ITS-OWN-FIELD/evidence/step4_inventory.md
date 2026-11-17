---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD
phase: open
artifact_type: investigation
date: 2026-11-17
tags: []
---

# Step 4 inventory: what `kind` writers fall through, what the fixtures write, the allowlist candidates, the profiles that would be refused (read-only, on origin/main f433a9530)

Evidence only. No code changed. Anything marked PROPOSAL is a suggestion for the designer, not a ruling.

## Counts
| Table | Count |
|---|---|
| 1. A2 fall-through | 10 labels fall through (hero, monster, world_boss, ancient_sentinel, entity, stronghold, bandit, bear, harpy, golem) + 3 silent writer-level defaults (`or "human"`, builder default `"hero"`, classic compile with no species) ; 26 label values resolve (16 classic role labels, 10 spawn/camp labels) |
| 2. src/certification, src/perf, src/testing writers | 27 kind-writing rows (20 certification, 6 perf, 1 testing) + 3 builders that write the implicit default `"hero"` (perf/scenarios.py:339, 390; observability/readiness/harness.py:100) |
| 3. Proposed non-living allowlist | 6 candidate values (stronghold, world_boss, ancient_sentinel, PRESSURE_TARGET, actor/ACTOR, entity); 0 have an existing owning ticket that fits, all marked "to file" |
| 4. Profiles refused once code defaults go | (i) 0 data/content profiles, 0 data worlds; 4 test profiles + 149 test compile calls (43 files) + 3 tools; (ii) 0 production, 3+ test paths; (iii) 1 src caller + 4 test calls rely on the default `"monster"` |
| 5. B7 "GOBLIN" | The target and the victim are BOTH `"GOBLIN"`: it matches today and 3 tests depend on it |

## Method and limits
Scripts beside this file reproduce every count (`python3 -I <script>` from the repo root):
- `step4_scan_writers.py [src|tests]`: AST scan; `.kind(<1 arg>)` builder calls (A), `EntityState(kind=)` (B), `replace(x, kind=)` (C), `V2EntityBuilder(` in a function with no `.kind(` (D, approximate: a builder configured in another function is not seen), spawner call sites (E). src: A36 B4 C3 D3 E9; tests: A1003 B113 C12 D429 E58 (610 files). C rows in tests include non-entity `kind=` (interaction, building); only src C rows were read (apply_plan.py:217 and patches.py:160 are interaction/region kind, boss.py:153 is the entity).
- `step4_scan_worlds.py`: reads `data/worlds/*/resolved/{world.resolved.yaml,compile_context.json}` (24 worlds, 241 populations). "Has a species" means `compile_context.json entities[<population id>].species_id` is non-empty, which is exactly the value `compiler.py:760-761` copies. These are the checked-in resolved files, NOT a fresh compile.
- `step4_scan_content.py`: `species.yaml` (14 ids: human wolf goblin spider orc elf dwarf undead troll lizardfolk dragonkin slime spirit small_plant_eater; verified), `entity_archetypes.yaml` (30; the key is `species`, not `species_id`), `populations.yaml` (16), `world_modules/*.yaml` (24, 5 `population_recipes`).
- `step4_scan_tests.py`: label reach in `tests/` (2319 files), carry-forward and compile-call checks. `step4_scan_compile_callers.py`: `WorldCompiler.compile` / `ResolvedEntityProfile(` callers. `step4_scan_fixtures.py`: Table 2 rows with enclosing function.
- "Quoted-literal files" is a text count and over-counts (any quoted string); "writer position" is the AST count.
- NOT covered: dynamic access (`getattr(x, name)`), string-built kinds, `frontend/`, `data/` files other than worlds/content, `tools/` writers other than compile callers, a runtime compile of each world (not run), and test fixtures that write world YAML to a temp dir. A test-compile count of 149 is the CALL count; only calls whose spec has populations reach a kind writer (rendering tests such as `tests/unit/rendering/*` likely compile no populations; not measured).
- Line numbers for `.kind(` are the line of the `.kind` token (they differ by one from the start of a multi-line chain).

## Table 1. A2: every writer label, with what resolves

Rule used: (a) the population/profile's declared species_id, (b) a same-id archetype with a `species`, (c) a declared content mapping label->species. The only existing declared mapping of that shape is `species.yaml camp_spawn_kind` (goblin: goblin_warrior line 74; orc: orc_warrior line 125), which maps species->label; reading it backwards is a PROPOSAL.

### 1a. Falls through (no species from a, b or c)
| label | writer file:line | why it falls through | worlds that reach it | tests that reach it |
|---|---|---|---|---|
| `hero` | src/systems/world_systems/generator.py:139 (`spawn_hero`); src/core/builder.py:95 (builder default `self._kind = "hero"`); src/domains/campaigns/runner.py:69 (`role = "hero"`) | no population; no same-id archetype (the hero archetype is `adventurer_hero`, species human); no mapping | none by `spawn_hero` (only called from src/certification/scenarios.py:51). The runner builds from a campaign spec (`world_pack`), not data/worlds. The 10 worlds' `hero` populations resolve via (a) human and are NOT this row | `spawn_hero(`: 20 call sites, 14 files (e.g. tests/unit/world/test_difficulty_scaling.py:8,20,34,38; tests/unit/core/test_occupation_field.py:127). `.kind("hero")`: 422 sites, 195 files. Builder default (no `.kind(` in the function): 429 sites, 139 files. Runner: tests/integration/campaigns/test_phase9_campaign_runner.py, test_phase9_life_arc_campaigns.py, tests/perf/test_phase9_campaign_semantic_budget.py, tests/unit/core/test_occupation_field.py:177 |
| `monster` | generator.py:147 (`spawn_monster` default `kind="monster"`), generator.py:176 (`spawn_natural_creature_offspring` default) | a default, no species | none in src except src/certification/scenarios.py:74 (`build_team_battle`, scenarios COMBAT_ARENA_5V5 / STRESS_50V50, scenarios.py:521-524) | default `spawn_monster(`: tests/unit/core/test_engine_integrity.py:111, tests/unit/engine/test_mid_run_adds_never_reuse_an_entity_id.py:29, tests/unit/progression/test_species_base_stats_preserved.py:305; default `spawn_natural_creature_offspring`: tests/unit/world/test_natural_creature_reproduction.py:71; `.kind("monster")`: 56 sites, 39 files; arena tests via COMBAT_ARENA_5V5/STRESS (tests/arena/test_arena_stress.py, test_arena_startup.py) |
| `world_boss` | src/world/calamity.py:82; src/world/boss.py:153 (`replace(boss, kind="world_boss")`) | boss label; not a species id, no archetype, no mapping | none: both spawn branches are inert unless `ENABLE_WORLD_BOSS_SPAWN` is ON (default OFF, src/domains/optimization/feature_flags.py:18; src/world/calamity.py:80). Boss spawn needs a LAIR place or calamity; LAIR places exist in generated_frontier_3_42 and simq_scale_stress_seed42 | writer position: tests/unit/engine/test_canonical_hash_covers_world_components.py:57, tests/unit/world/test_boss_gate_reachability.py:37-38, tests/unit/world/test_world_dynamics.py; paths via `BossService` 5 files, `ENABLE_WORLD_BOSS_SPAWN` 10 files (test_world_boss_spawn_flag.py, test_calamity_trigger_rules.py, test_spawned_entity_validity.py, ...); 16 files quote the literal |
| `ancient_sentinel` | src/world/boss.py:146 (`spawn_monster(kind="ancient_sentinel")`), replaced by `world_boss` at boss.py:153 before it reaches state; its occupation stays `ancient_sentinel` | label only | same as world_boss (boss.py spawn branch) | no writer-position test; 3 files quote it (tests/unit/observability/test_entity_kind_constants.py:13,20; test_event_extractor_world.py:313-315; tests/unit/core/test_occupation_field.py:133) |
| `entity` | src/domains/campaigns/orchestrator.py:821 (`cf.kind or "entity"`) | code default for an empty carried kind | none (survivors rebuild from a saved record) | fixtures that WRITE `kind="entity"`: tests/integration/scenarios/test_campaign_runtime.py:60, tests/integration/scenarios/test_social_memory.py:56, tests/unit/social/test_social_memory.py:266, tests/unit/kernel/test_executor_parity.py:31, tests/mechanic_scenarios/test_perception_pipeline_wiring.py:125 (24 files quote it) |
| `stronghold` | NO src writer on main (removed by D71, TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71, done). Reader only: src/world/environment.py:86 | non-living, no writer | none | tests/unit/world/test_aura.py (the only file; writes it as a fixture) |
| `bandit`, `bear`, `harpy`, `golem` | NO src caller passes them. They are keys of `SPAWN_KIND_CATALOG_FACTION` (generator.py:27-38) | not in species.yaml; no same-id archetype (archetypes are `bandit_scout`, `bandit_cutpurse`) | none | tests/unit/world/test_spawn_monster_catalog_faction.py:16 (CAMP_KINDS), :90 (parametrized `spawn_monster(kind=...)`); `bandit` as a quest victim only in tests/unit/quest/test_quest_relation_projection.py:125 |

### 1b. Silent writer-level defaults (the label is whatever the input is, so it can fall through)
| writer file:line | behaviour | reach |
|---|---|---|
| src/worldassembly/entity_spawner.py:129 `profile.species_id or "human"` (and :144 `occupation=profile.species_id or "human"`) | a profile with no species silently becomes human | via `_spawn_one` when `profile.archetype_id` is empty (entity_spawner.py:92-95), AND via the `except Exception` at entity_spawner.py:106-108 that swallows any archetype resolve failure and falls to this guard. Worlds: none (all 241 data populations carry a species). Tests: Table 4(i) |
| src/worldbuilding/compiler.py:765 `.kind(pop_spec.role.lower())` | label comes from the population's role; species exists only if `context` was passed and the population is in `context.entities` | 6/6 src callers pass a context (`step4_scan_compile_callers.py`); 3 tools do not; 149 test calls do not (Table 4(i)) |
| src/core/builder.py:95 | a builder never given `.kind()` builds kind `"hero"` | counted in row `hero` above |

### 1c. Labels that DO resolve
| label(s) | writer file:line | species from |
|---|---|---|
| 16 classic role labels: alpha, blacksmith, guard, guardian, hero, leader, mage, merchant, predator_hunter, raider, ranger, scout, sentinel, shaman, wild_creature, worker | compiler.py:765 via `pop_spec.role.lower()` | (a): all 241 populations in the 24 data worlds have a non-empty `compile_context.json` species_id. Species per label: alpha wolf; blacksmith/guard/hero/mage/merchant/worker human; guardian spirit; leader goblin(9) orc(1); predator_hunter spider(7) wolf(10); raider goblin(9) orc(7); ranger elf; scout human(8) goblin(19) lizardfolk(6); sentinel undead; shaman lizardfolk; wild_creature small_plant_eater. NOTE one label maps to several species (leader, raider, scout, predator_hunter), so label->species is not a function: the species must come from the population, never from the label |
| any archetype species | src/entities/contract_builder.py:41 -> src/entities/archetype_factory.py:97 | (b)/(a): `arch.species_id` (archetype key `species`); all 30 archetypes declare one, all in species.yaml |
| `goblin` | generator.py:321 (`spawn_goblin`) | is itself a species id |
| `dragonkin` | boss.py:258 (lair occupant) | is itself a species id (species.yaml:245) |
| `wolf spider troll slime goblin orc` (camp kinds) | camp.py:72 (`kind=camp.kind`); camp creature_kind validated by `CAMP_NEST_CREATURE_RACES` (recipe.py:16, schema.py:38) | species ids. Authored in 14 worlds (20 camps: goblin or wolf only in data) |
| `goblin_warrior`, `orc_warrior` | camp.py:98 (`CampService.spawn_kind`, camp.py:25-28) | NOT species ids and not archetype ids: resolve only by reading `species.camp_spawn_kind` backwards (c, PROPOSAL). Also test-written (Table 1 tests below) |
| `goblin_raider` | no src writer; key of `SPAWN_KIND_CATALOG_FACTION` and `SPAWN_CADENCE_EXCLUDED_KINDS` | (b): same-id archetype, species goblin. Test writer position: tests/unit/ai/test_guild_need_scorer.py |
| entity.kind pass-through | creature_territory.py:60 (`kind=entity.kind`), reproduction_humanoid.py:88 (`a.kind`), camp.py (above) | inherits the parent's kind; a species at step 4. EXCEPTION: creature_territory re-spawns any anchored MONSTER-role entity (creature_territory.py:44-48), so an anchored `world_boss` would pass `world_boss` on |

Tests writing `goblin_warrior` / `orc_warrior`: tests/unit/world/test_spawn_monster_catalog_faction.py:19-66, tests/unit/world/test_natural_creature_reproduction.py:57,272,292, tests/integration/optimization/test_component_patch_apply_parity.py:115, tests/unit/ai/test_way_in_range.py (10 and 2 files quote them).

PROPOSAL (not a ruling): add a declared `label -> species` row to content for `goblin_warrior`, `orc_warrior`, `goblin_raider` (derive from `camp_spawn_kind` / archetype) and for `hero` (spawn_hero takes the species of a named archetype, e.g. `adventurer_hero`).

## Table 2. src/certification, src/perf, src/testing writers (`step4_scan_fixtures.py`)

Dependencies found by reading the consumers (72 files reference these builders; `.kind`/role assertions grep'd in all of them): NO test asserts `kind == "HERO"|"MONSTER"|"GOBLIN"|"actor"|"hero"|"monster"` on a fixture entity. Hostility in these scenarios comes from `faction` (HERO_GUILD vs MONSTER_HORDE), not kind. Dependencies that DO exist:
- tests/unit/core/test_occupation_fixture_writers.py:12-51 asserts, for all three directories, that every `.kind(X)` chain sets `occupation` to the same expression, and (line 51-56) that every certification-built entity has `occupation == kind`. It must be re-keyed at step 4 (its docstring says the scan is re-run before step 4).
- tests/unit/core/test_occupation_field.py:128, 133-135, 177 assert `kind == occupation == "hero"` for `spawn_hero` / campaign runner entities.
- tests/arena/test_arena_quests.py (3 tests) depends on the `GOBLIN` kind equality (Table 5).
- Lower-case `"hero"` (build_integrated_loop, all perf) is what the `kind == "hero"` readers match (calamity.py:99, extraction/combat.py:82, event_shapers.py:337); upper-case `"HERO"` never matches them, so certification arenas do not exercise those readers today.

| file:line | literal | function / entity in the scenario | faction / role set in chain | PROPOSAL |
|---|---|---|---|---|
| certification/scenarios.py:22 | PRESSURE_TARGET | PressureInjector.inject_entities: dummy entities for the RAM/queue pressure scenarios | none | allowlist (non-living target) or human; to file |
| :51 | spawn_hero default | build_team_battle: team hero | HERO_GUILD via spawn_hero | human (needs spawn_hero to take a species) |
| :74 | spawn_monster default `monster` | build_team_battle: team monster | MONSTER_HORDE | goblin (or a declared arena monster species) |
| :107 / :119 | HERO / MONSTER | build_progression_test: attacker / victim (has MONSTER_TOOTH item) | HERO_GUILD / MONSTER_HORDE | human / goblin |
| :148 / :159 | MONSTER / HERO | build_mortality_test | MONSTER_HORDE / HERO_GUILD | goblin / human |
| :187, :198 / :209 | HERO, HERO / MONSTER | build_tactical_test: 2 heroes, 1 monster | HERO_GUILD / MONSTER_HORDE | human, human / goblin |
| :240, :252 / :263 | HERO, HERO / MONSTER | build_social_test: 2 heroes, 1 monster | same | human, human / goblin |
| :293 / :317 | HERO / GOBLIN | build_quest_battle (COMBAT_ARENA_QUESTS): quester / quest target | HERO_GUILD / MONSTER_HORDE + role MONSTER | human / goblin (set `target_kind` at :309 together, Table 5) |
| :360 / :372 | HERO / GOBLIN | build_regional_control_test | HERO_GUILD+HERO / MONSTER_HORDE+MONSTER | human / goblin |
| :417 / :438 | actor / actor | GameplayInjector.build_movement_test / build_harvest_test: the one worker | none | human |
| :479 | hero | build_integrated_loop: crafting hero | none | human |
| perf/scenarios.py:36 | hero | build_idle_state (role HERO) | HERO_GUILD | human |
| :78 | hero | build_resource_state (role WORKER, but kind hero) | HERO_GUILD | human |
| :145 | hero | build_movement_state | HERO_GUILD | human |
| :192 / :216 | hero / monster | build_combat_arena_state | HERO_GUILD / MONSTER_HORDE | human / goblin |
| :265 | hero | build_strategic_state | HERO_GUILD | human |
| testing/scenario_runner.py:53 | `actor_spec.get("role", "HERO")` | execute(): first actor of a scenario spec dict; the spec's `role` string is written as kind | none | the spec declares a species (content) or it is a typed refusal; no `"HERO"` default. tests/unit/strategic/test_scenario_runner.py asserts only `len(spec["actors"]) == 1` |
| perf/scenarios.py:339, :390; observability/readiness/harness.py:100 | (none: builder default `hero`) | 339 and harness.py:100: entity_count heroes with no `.kind`; 390: `replace_identity(monster.identity)` clones a monster and ends with kind `hero` (a latent mislabel) | n/a | name the species explicitly (390: copy the source entity's kind) |

PROPOSAL note: "goblin" / "human" are placeholders; the species brings species-keyed behaviour (diet, body model, needs via `get_kind_properties`), so the measurement arm must confirm the fixtures' assertions still hold. A species with an empty diet or no needs would be the least disruptive for arenas; the designer picks.

## Table 3. PROPOSED non-living allowlist (PROPOSALS)
| kind value | where it comes from | proposed owner |
|---|---|---|
| `stronghold` | no writer since D71 (TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71, done, agent-working/tickets/done/); reader src/world/environment.py:86; fixture tests/unit/world/test_aura.py | PROPOSAL: do not allowlist; retire the reader and fixture. No open ticket names it (TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES.md does not mention stronghold): to file |
| `world_boss` | calamity.py:82, boss.py:153; boss feature deferred (feature_flags.py:11-18) | to file. Context only: agent-working/tickets/backlogs/epic-20-calamity-system.md (backlog, not a ticket); TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT.md (todos) lists the boss branch as out of its scope (line 36) |
| `ancient_sentinel` | boss.py:146, transient (replaced at :153) | to file with world_boss; or stop writing it (the spawn_monster call can pass the final label) |
| `PRESSURE_TARGET` | certification/scenarios.py:22 | to file (certification fixtures), or give it a species |
| `actor`, `ACTOR` | certification/scenarios.py:417,438; 79 `ACTOR` + 43 `actor` writer sites in 32+17 test files | to file: test-fixture policy (a test helper that supplies a species) rather than an allowlist entry |
| `entity` | orchestrator.py:821 fallback; state.py:153,211 (`kind: str = ""` for pre-field records) | PROPOSAL: not an allowlist entry; an empty carried kind is a typed refusal (old record format). Owner: to file |
| `monster`, `hero` as code defaults | generator.py:147,176; builder.py:95 | PROPOSAL: remove defaults, not allowlist. No ticket |

Other dummy kinds written by tests (not src): TEST, TEST_ALIVE, TEST_DEAD, target, npc, villager, peasant, mob, agent, X, a, unknown, OBSTACLE, mutated, ORIGINAL (counts in `step4_scan_writers.py tests`); tests as a whole write 1003 `.kind(` literals in 610 files, so the test fixtures need a policy, not 610 allowlist rows.

## Table 4. Profiles/paths that would be refused once code defaults go

How "no species" was decided: a data population has no species iff `compile_context.json entities[pop id].species_id` is empty; an archetype iff its `species` key is empty; a module recipe iff it has neither `species_id` nor an archetype; a test profile iff its `ResolvedEntityProfile(` call passes no `species_id` (AST, then read in place; one AST false positive, test_entity_spawner_legacy_guard.py:29, supplies `species_id="human"` through a defaults dict).

### (i) entity_spawner.py:129 `profile.species_id or "human"`, and the classic compile with no species
| source | has no species | count |
|---|---|---|
| data/worlds/** (24 worlds, 241 populations) | none | 0 |
| data/content/entities/entity_archetypes.yaml | none | 0 of 30 |
| data/content/entities/populations.yaml | none (all 16 members name an archetype with a species) | 0 of 16 |
| data/content/world_modules/*.yaml `population_recipes` | none | 0 of 5 (all say `species_id: human`) |
| `ResolvedEntityProfile(` in src | resolver.py:1051 (archetype), :1085 (recipe species) | 0 (but an archetype that fails to resolve is swallowed at resolver.py:1040-1047 and yields `species_id=getattr(pop_recipe, ...)` which is None for archetype-based pops: a latent silent path) |
| `ResolvedEntityProfile(` in tests | tests/integration/worldassembly/test_world_entity_spawner.py:247,268,319 (position tests, no species, no archetype -> legacy guard -> "human"); tests/unit/core/test_occupation_field.py:121 (`no_species`, asserts `occupation == kind`) | 4 |
| `WorldCompiler.compile` with no `context` (so no species, kind = role label) | src: 0 of 6 callers. tools: tools/calibrate_rendering.py:81, tools/review_pipeline_check.py:70, tools/visual_assets_sample_map.py:139 (3 of 10). tests: 149 of 211 calls in 43 files (list from `step4_scan_tests.py`, biggest: tests/unit/worldbuilding/test_world_compiler.py 54, test_place_wiring.py 16, test_worldbuilding_strategy.py 8, rendering tests 19) | 3 + 149 |
Note: when a context IS passed, `compiler.py:762` already calls `require_declared_diet` (src/worldbuilding/diet_declaration.py:16), which refuses a species-less population today (InvalidWorldSpecError). So the step-4 compile refusal is already live for every context-bearing compile; it is NEW only for context-less compiles. The open ticket TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE.md (agent-working/tickets/todos/) already lists these tests for a different reason (starting purses). Tests that assert on the old role-string kind of a context-less compile: tests/unit/worldbuilding/test_world_compiler.py:108,125 and test_worldbuilding_strategy.py:149 (`e.kind == "monster"`).

### (ii) orchestrator.py:821 `cf.kind or "entity"`
- Production: a saved survivor can have an empty kind only for a record written before the field existed: `EntityCarryForward.kind: str = ""` (state.py:153) and `from_dict` `d.get("kind", "")` (state.py:211). New records copy `entity.kind` (orchestrator.py:544), which is never empty (`EntityState.kind` has no default; `EntityState(` without `kind=`: 0 of 4 in src, 0 of 113 in tests). Checked-in saved campaigns with a survivor record: not searched (data/ other than worlds/content not covered).
- Tests: 17 `EntityCarryForward(` constructions without `kind=` (default ""): tests/integration/scenarios/test_campaign_runtime.py:175, test_social_memory.py:236,265; tests/unit/domains/campaigns/test_campaign_orchestrator.py:346,349,654,811,897,924,967,997; test_campaign_state.py:37; test_carry_forward_occupation.py:15; test_fame_wiring.py:100,140; test_plan_revision.py:15,127. Only those that reach `_build_initial_state` reconstruction matter (test_campaign_orchestrator.py and the integration scenarios; not individually verified). Tests whose fixtures write kind `entity`: Table 1.

### (iii) generator.py default `kind="monster"`
- src callers relying on it: 1 (certification/scenarios.py:74, `build_team_battle`: COMBAT_ARENA_5V5, COMBAT_ARENA_STRESS_50V50; consumers tests/arena/test_arena_stress.py, test_arena_startup.py, tests/perf).
- Test callers: spawn_monster default 3 (tests/unit/core/test_engine_integrity.py:111; tests/unit/engine/test_mid_run_adds_never_reuse_an_entity_id.py:29; tests/unit/progression/test_species_base_stats_preserved.py:305), `spawn_natural_creature_offspring` default 1 (tests/unit/world/test_natural_creature_reproduction.py:71), `spawn_humanoid_offspring` positional kind 1 (tests/unit/core/test_occupation_field.py:151).
- Also `spawn_hero` / `spawn_goblin` take no kind: 20 and 11 test call sites.

## Table 5. B7 `target_kind "GOBLIN"` (src/certification/scenarios.py:297-317)
- The scenario is COMBAT_ARENA_QUESTS = `ArenaInjector.build_quest_battle` (scenarios.py:279-336; registered :401, dispatched :534).
- Quest: `metadata={"target_kind": "GOBLIN"}` at scenarios.py:309. Victim: `V2EntityBuilder(12).kind("GOBLIN")` at scenarios.py:317 (occupation "GOBLIN" at :318). The victim kind is upper-case "GOBLIN" too, so the strings are equal.
- Kill credit: `QuestResolutionSystem.evaluate_combat_victory` (src/engine/quests.py:52) gets `victim_kind = target.kind` from combat_actions.py:78 (and aoe_actions.py:89). Paths 1-3 need `target_archetype_id` / `target_faction_id` / `target_projected_label` in the quest metadata; this quest has none, so Path 4, quests.py:146-147 (`metadata["target_kind"] == victim_kind`), is the one that matches. `"GOBLIN" == "GOBLIN"` is True: it matches today.
- Consumers (all assert the quest DOES complete):
  - tests/arena/test_arena_quests.py:47 `test_arena_quest_progression_paid_by_a_funded_treasury`: `quest.current_value == 1.0` (line 55), `quest_status == QuestStatus.REWARDED` (57), gold 50 paid from treasury, level 2.
  - :72 `test_arena_quest_reward_is_owed_when_the_treasury_is_short`: `REWARDED`, an OWED record of 50 `QUEST_REWARD`, level 2.
  - :88 `test_arena_quest_with_no_giver_pays_experience_only`: `REWARDED`, level 2.
  - Expectation `get_scenario_expectations("COMBAT_ARENA_QUESTS")` (scenarios.py:556-570) only asks conformance (`FailureKind.NONE`, deterministic); it does not depend on quest state. tests/unit/core/test_occupation_fixture_writers.py:51-56 builds the scenario and asserts `occupation == kind`.
- So the designer's B7 note ("change it to goblin at step 4; it never matched") is wrong for the premise: it matches, and changing only `target_kind` to "goblin" while the victim stays "GOBLIN" would stop the credit and fail 3 tests (quest would stay ACTIVE, 0 credit). The two literals (scenarios.py:309 and :317, and :372 for the regional scenario, which has no quest) must change in one edit together with the occupation at :318/:373.
- Other test cases of `target_kind` use lower-case "goblin" (tests/unit/quest/test_quest_relation_projection.py:163,174,184) with a hand-made victim.

## Discrepancies with step-1 evidence and the designer rulings
1. B7 premise ("GOBLIN never matches", step-1 row 9 / B7 and step-1 rulings B7): false. The victim kind is also "GOBLIN" (scenarios.py:317), so the quest credit works and tests/arena/test_arena_quests.py (3 tests) relies on it. Lane C reports it to rpg-planner as the rulings ask (a test-expectation change).
2. Step-1 table A row 7 ("EvolutionSystem always writes `kind_set`"): no production writer of an entity `kind_set` exists in src (`kind_set=` writers are region updates only: src/engine/world_dynamics.py:317). The observability comment at event_shapers.py:1065 is stale; `KindPatch`/`EntityUpdate.kind_set` have no entity writer to constrain at step 4 other than a guard.
3. Not in step-1 A2: `V2EntityBuilder` default kind `"hero"` (src/core/builder.py:95), a code default the ruling forbids. 3 src builders (perf/scenarios.py:339, 390; readiness/harness.py:100) and 429 test sites use it.
4. Step-1 A2 lists `stronghold` as a writer; none exists since D71 (only environment.py:86 reads it, one test fixture writes it).
5. Rulings say a profile with no species "currently silently becomes human": for context-bearing compiles the diet rule (`diet_declaration.py:16`, `compiler.py:762`) already refuses it; the `"human"` default is only on the `WorldEntitySpawner` path, plus the swallowed archetype error at entity_spawner.py:106-108 and resolver.py:1040-1047.
6. Rulings say newborns get `occupation` None, but all three offspring spawners set `occupation=kind` (generator.py:207, 241, 287); `entity_spawner.py:144` writes `profile.species_id or "human"` into occupation (step-2 stopgap noted in its comment). These are step-2 placeholders for step 4 to replace, not discrepancies in intent, but spawn_natural/humanoid offspring will need `occupation=None`.
7. Rule (b) says "archetype that declares species_id": the archetype YAML key is `species` (resolver.py:515 reads `arch.species`).
8. Rule (c) has no existing "declared label->species" content: only the reverse `camp_spawn_kind` (goblin_warrior, orc_warrior). Labels bandit, bear, harpy, golem have no species and no writer in src (only a catalog table and one test).
9. Step-1 doc comment on `EntityCarryForward` (state.py:111) says reconstruction falls back to bare `EntityState` defaults `kind="entity"`; `EntityState.kind` has no default (state.py:897) — stale wording, no behaviour effect.
