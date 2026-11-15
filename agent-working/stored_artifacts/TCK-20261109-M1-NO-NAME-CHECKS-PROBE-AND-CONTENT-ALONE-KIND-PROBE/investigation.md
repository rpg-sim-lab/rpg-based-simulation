---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE: investigation

## Inventory (origin/main 5ba65854c, after the review fixes and rulings below)
139 switches: 114 gating, 15 report-only, 10 excluded. The allowlist holds the 114 gating switches as 105 rows. Every report-only row is listed, for rpg-planner's row-by-row ruling.

By package: ai 15 (gating), content_semantics 28 (gating), core 2 (gating), domains 9 (gating), economy 2 (gating), engine 24 (gating), entities 10 (excluded), systems 34 (gating), world 15 (report-only)

| file:line | symbol | name | shape | status |
|---|---|---|---|---|
| ai/coming_of_age.py:27 | <module>[_CANDIDATE_ROLES] | EntityRole.GUARD | table | gating |
| ai/coming_of_age.py:27 | <module>[_CANDIDATE_ROLES] | EntityRole.SHOPKEEPER | table | gating |
| ai/coming_of_age.py:27 | <module>[_CANDIDATE_ROLES] | EntityRole.WORKER | table | gating |
| ai/coming_of_age.py:33 | <module>[_PERSONALITY_ATTR] | EntityRole.SHOPKEEPER | table | gating |
| ai/coming_of_age.py:34 | <module>[_PERSONALITY_ATTR] | EntityRole.WORKER | table | gating |
| ai/coming_of_age.py:35 | <module>[_PERSONALITY_ATTR] | EntityRole.GUARD | table | gating |
| ai/goals/adventure_scorer.py:64 | _resolve_cognition_profile_id | EntityRole.HERO | compare | gating |
| ai/goals/adventure_scorer.py:313 | AdventureGoalScorer._resolve_placeholder_target_pos | EntityRole.MONSTER | compare | gating |
| ai/goals/occupation_change_scorer.py:14 | <module>[_CANDIDATE_ROLES] | EntityRole.GUARD | table | gating |
| ai/goals/occupation_change_scorer.py:14 | <module>[_CANDIDATE_ROLES] | EntityRole.SHOPKEEPER | table | gating |
| ai/goals/occupation_change_scorer.py:14 | <module>[_CANDIDATE_ROLES] | EntityRole.WORKER | table | gating |
| ai/goals/occupation_change_scorer.py:16 | <module>[_ROLE_APTITUDE_ATTR] | EntityRole.SHOPKEEPER | table | gating |
| ai/goals/occupation_change_scorer.py:17 | <module>[_ROLE_APTITUDE_ATTR] | EntityRole.WORKER | table | gating |
| ai/goals/occupation_change_scorer.py:18 | <module>[_ROLE_APTITUDE_ATTR] | EntityRole.GUARD | table | gating |
| ai/goals/occupation_change_scorer.py:33 | OccupationChangeGoalScorer.score | EntityRole.CITIZEN | compare | gating |
| content_semantics/faction.py:120 | FactionSemanticsService.get_legacy_faction_bucket | 'GUILD' | compare | gating |
| content_semantics/faction.py:120 | FactionSemanticsService.get_legacy_faction_bucket | 'HERO' | compare | gating |
| content_semantics/faction.py:120 | FactionSemanticsService.get_legacy_faction_bucket | 'VILLAGE' | compare | gating |
| content_semantics/faction.py:122 | FactionSemanticsService.get_legacy_faction_bucket | 'HORDE' | compare | gating |
| content_semantics/faction.py:122 | FactionSemanticsService.get_legacy_faction_bucket | 'HOSTILE' | compare | gating |
| content_semantics/faction.py:122 | FactionSemanticsService.get_legacy_faction_bucket | 'MONSTER' | compare | gating |
| content_semantics/faction.py:124 | FactionSemanticsService.get_legacy_faction_bucket | 'COUNCIL' | compare | gating |
| content_semantics/faction.py:124 | FactionSemanticsService.get_legacy_faction_bucket | 'TOWN' | compare | gating |
| content_semantics/faction.py:142 | FactionSemanticsService.get_alignment_bucket | Faction.HERO_GUILD | compare | gating |
| content_semantics/faction.py:142 | FactionSemanticsService.get_alignment_bucket | Faction.TOWN_COUNCIL | compare | gating |
| content_semantics/faction.py:144 | FactionSemanticsService.get_alignment_bucket | Faction.MONSTER_HORDE | compare | gating |
| content_semantics/faction.py:173 | FactionSemanticsService.is_hostile | Faction.MONSTER_HORDE | compare | gating |
| content_semantics/faction.py:173 | FactionSemanticsService.is_hostile | Faction.MONSTER_HORDE | compare | gating |
| content_semantics/role.py:24 | RoleSemanticsService.get_legacy_entity_role | 'HERO' | compare | gating |
| content_semantics/role.py:26 | RoleSemanticsService.get_legacy_entity_role | 'SHOP' | compare | gating |
| content_semantics/role.py:26 | RoleSemanticsService.get_legacy_entity_role | 'STORE' | compare | gating |
| content_semantics/role.py:28 | RoleSemanticsService.get_legacy_entity_role | 'MONSTER' | compare | gating |
| content_semantics/role.py:30 | RoleSemanticsService.get_legacy_entity_role | 'CITIZEN' | compare | gating |
| content_semantics/role.py:30 | RoleSemanticsService.get_legacy_entity_role | 'CIVILIAN' | compare | gating |
| content_semantics/role.py:32 | RoleSemanticsService.get_legacy_entity_role | 'PEASANT' | compare | gating |
| content_semantics/role.py:32 | RoleSemanticsService.get_legacy_entity_role | 'WORKER' | compare | gating |
| content_semantics/role.py:34 | RoleSemanticsService.get_legacy_entity_role | 'GUARD' | compare | gating |
| content_semantics/role.py:65 | RoleSemanticsService.is_combatant | EntityRole.GUARD | compare | gating |
| content_semantics/role.py:65 | RoleSemanticsService.is_combatant | EntityRole.HERO | compare | gating |
| content_semantics/role.py:65 | RoleSemanticsService.is_combatant | EntityRole.MONSTER | compare | gating |
| content_semantics/role.py:72 | RoleSemanticsService.is_civilian | EntityRole.CITIZEN | compare | gating |
| content_semantics/role.py:72 | RoleSemanticsService.is_civilian | EntityRole.SHOPKEEPER | compare | gating |
| content_semantics/role.py:79 | RoleSemanticsService.is_worker | EntityRole.WORKER | compare | gating |
| core/builder.py:690 | V2EntityBuilder.birth_record | EntityRole.HERO | compare | gating |
| core/builder.py:690 | V2EntityBuilder.birth_record | EntityRole.HERO | compare | gating |
| domains/adventure/generator.py:135 | AdventureRouteGenerator.generate | EntityRole.MONSTER | compare | gating |
| domains/adventure/scoring.py:229 | AdventureRouteScorer.score | EntityRole.HERO | compare | gating |
| domains/adventure/scoring.py:456 | AdventureRouteScorer.score | EntityRole.HERO | compare | gating |
| domains/cooperation/evaluators.py:164 | PartnerFitEvaluator.evaluate | 'VANGUARD' | compare | gating |
| domains/cooperation/evaluators.py:167 | PartnerFitEvaluator.evaluate | 'SUPPORT' | compare | gating |
| domains/cooperation/evaluators.py:170 | PartnerFitEvaluator.evaluate | 'STRIKER' | compare | gating |
| domains/cooperation/providers.py:130 | PartnerCandidateProvider.get_candidates | 'SUPPORT' | compare | gating |
| domains/cooperation/providers.py:132 | PartnerCandidateProvider.get_candidates | 'VANGUARD' | compare | gating |
| domains/culture/deriver.py:89 | CultureDeriver.derive | 'HERO' | compare | gating |
| economy/vacancy.py:12 | <module>[_PRODUCTION_RELEVANT_ROLES] | EntityRole.SHOPKEEPER | table | gating |
| economy/vacancy.py:12 | <module>[_PRODUCTION_RELEVANT_ROLES] | EntityRole.WORKER | table | gating |
| engine/biological_needs.py:38 | <module>[_PERSON_ROLES] | EntityRole.CITIZEN | table | gating |
| engine/biological_needs.py:38 | <module>[_PERSON_ROLES] | EntityRole.HERO | table | gating |
| engine/biological_needs.py:38 | <module>[_PERSON_ROLES] | EntityRole.SHOPKEEPER | table | gating |
| engine/biological_needs.py:39 | <module>[_PERSON_ROLES] | EntityRole.GUARD | table | gating |
| engine/biological_needs.py:39 | <module>[_PERSON_ROLES] | EntityRole.WORKER | table | gating |
| engine/combat_rewards.py:35 | CombatRewardClassificationService[_CLASSIFICATIONS] | EntityRole.MONSTER | table | gating |
| engine/combat_rewards.py:42 | CombatRewardClassificationService[_CLASSIFICATIONS] | EntityRole.HERO | table | gating |
| engine/evolution.py:100 | EvolutionSystem.evaluate | 'goblin' | compare | gating |
| engine/evolution.py:109 | EvolutionSystem.evaluate | EntityRole.HERO | compare | gating |
| engine/legality.py:525 | LegalityServiceV2.get_entity_priority | EntityRole.HERO | compare | gating |
| engine/legality.py:526 | LegalityServiceV2.get_entity_priority | EntityRole.MONSTER | compare | gating |
| engine/military_conflict.py:139 | MilitaryConflictPhase._build_guard_index_by_region | EntityRole.GUARD | compare | gating |
| engine/occupancy_snapshot.py:33 | OccupancySnapshot.from_state | EntityRole.HERO | compare | gating |
| engine/occupancy_snapshot.py:35 | OccupancySnapshot.from_state | EntityRole.MONSTER | compare | gating |
| engine/tactical.py:348 | TacticalDecisionSystem.evaluate_entity_intent | 'PROTECTOR' | compare | gating |
| engine/tactical.py:348 | TacticalDecisionSystem.evaluate_entity_intent | 'VANGUARD' | compare | gating |
| engine/tactical.py:402 | TacticalDecisionSystem.evaluate_entity_intent.target_score | 'VANGUARD' | compare | gating |
| engine/tactical.py:502 | TacticalDecisionSystem.evaluate_entity_intent | 'SKIRMISHER' | compare | gating |
| engine/tactical.py:540 | TacticalDecisionSystem.evaluate_entity_intent | 'VANGUARD' | compare | gating |
| engine/tactical.py:561 | TacticalDecisionSystem.evaluate_entity_intent | 'PROTECTOR' | compare | gating |
| engine/tactical.py:614 | TacticalDecisionSystem.evaluate_entity_intent | 'VANGUARD' | compare | gating |
| engine/tactical.py:629 | TacticalDecisionSystem.evaluate_entity_intent | 'SKIRMISHER' | compare | gating |
| engine/tactical.py:638 | TacticalDecisionSystem.evaluate_entity_intent | 'SKIRMISHER' | compare | gating |
| engine/tactical.py:764 | TacticalDecisionSystem.evaluate_entity_intent | 'VANGUARD' | compare | gating |
| entities/identity_resolver.py:14 | <module>[_ROLE_COMPAT] | EntityRole.HERO | table | excluded |
| entities/identity_resolver.py:15 | <module>[_ROLE_COMPAT] | EntityRole.SHOPKEEPER | table | excluded |
| entities/identity_resolver.py:16 | <module>[_ROLE_COMPAT] | EntityRole.MONSTER | table | excluded |
| entities/identity_resolver.py:17 | <module>[_ROLE_COMPAT] | EntityRole.CITIZEN | table | excluded |
| entities/identity_resolver.py:18 | <module>[_ROLE_COMPAT] | EntityRole.WORKER | table | excluded |
| entities/identity_resolver.py:19 | <module>[_ROLE_COMPAT] | EntityRole.GUARD | table | excluded |
| entities/identity_resolver.py:23 | <module>[_FACTION_COMPAT] | Faction.HERO_GUILD | table | excluded |
| entities/identity_resolver.py:24 | <module>[_FACTION_COMPAT] | Faction.MONSTER_HORDE | table | excluded |
| entities/identity_resolver.py:25 | <module>[_FACTION_COMPAT] | Faction.TOWN_COUNCIL | table | excluded |
| entities/identity_resolver.py:26 | <module>[_FACTION_COMPAT] | Faction.NEUTRAL | table | excluded |
| systems/lifecycle_systems/lifecycle.py:215 | LifecycleSystem.resolve_lifecycle | EntityRole.CITIZEN | compare | gating |
| systems/social_systems/party_composition.py:58 | PartyCompositionScorer.infer_party_role | 'brute' | compare | gating |
| systems/social_systems/party_composition.py:58 | PartyCompositionScorer.infer_party_role | 'guard' | compare | gating |
| systems/social_systems/party_composition.py:58 | PartyCompositionScorer.infer_party_role | 'guardian' | compare | gating |
| systems/social_systems/party_composition.py:58 | PartyCompositionScorer.infer_party_role | 'sentinel' | compare | gating |
| systems/social_systems/party_composition.py:60 | PartyCompositionScorer.infer_party_role | 'druid' | compare | gating |
| systems/social_systems/party_composition.py:60 | PartyCompositionScorer.infer_party_role | 'healer' | compare | gating |
| systems/social_systems/party_composition.py:60 | PartyCompositionScorer.infer_party_role | 'mage' | compare | gating |
| systems/social_systems/party_composition.py:60 | PartyCompositionScorer.infer_party_role | 'shaman' | compare | gating |
| systems/social_systems/party_composition.py:62 | PartyCompositionScorer.infer_party_role | 'hero' | compare | gating |
| systems/social_systems/party_composition.py:62 | PartyCompositionScorer.infer_party_role | 'hunter' | compare | gating |
| systems/social_systems/party_composition.py:62 | PartyCompositionScorer.infer_party_role | 'ranger' | compare | gating |
| systems/social_systems/party_composition.py:62 | PartyCompositionScorer.infer_party_role | 'scout' | compare | gating |
| systems/social_systems/party_composition.py:65 | PartyCompositionScorer.infer_party_role | 'blacksmith' | compare | gating |
| systems/social_systems/party_composition.py:65 | PartyCompositionScorer.infer_party_role | 'citizen' | compare | gating |
| systems/social_systems/party_composition.py:65 | PartyCompositionScorer.infer_party_role | 'merchant' | compare | gating |
| systems/social_systems/party_composition.py:65 | PartyCompositionScorer.infer_party_role | 'worker' | compare | gating |
| systems/strategic_systems/intelligence.py:1454 | StrategicIntelligenceSystem.evaluate_strategic_intent | EntityRole.CITIZEN | compare | gating |
| systems/world_systems/generator.py:28 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'goblin_warrior' | table | gating |
| systems/world_systems/generator.py:29 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'goblin_raider' | table | gating |
| systems/world_systems/generator.py:30 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'orc_warrior' | table | gating |
| systems/world_systems/generator.py:31 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'bandit' | table | gating |
| systems/world_systems/generator.py:32 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'goblin' | table | gating |
| systems/world_systems/generator.py:33 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'dragonkin' | table | gating |
| systems/world_systems/generator.py:34 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'wolf' | table | gating |
| systems/world_systems/generator.py:35 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'slime' | table | gating |
| systems/world_systems/generator.py:36 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'bear' | table | gating |
| systems/world_systems/generator.py:37 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'harpy' | table | gating |
| systems/world_systems/generator.py:38 | <module>[SPAWN_KIND_CATALOG_FACTION] | 'golem' | table | gating |
| systems/world_systems/navigation.py:41 | FlowFieldService.get_flow_direction | 'world_boss' | compare | gating |
| systems/world_systems/routine.py:138 | RoutineService.get_role_utility_boost | EntityRole.SHOPKEEPER | compare | gating |
| systems/world_systems/routine.py:140 | RoutineService.get_role_utility_boost | EntityRole.HERO | compare | gating |
| systems/world_systems/routine.py:142 | RoutineService.get_role_utility_boost | EntityRole.WORKER | compare | gating |
| systems/world_systems/routine.py:144 | RoutineService.get_role_utility_boost | EntityRole.GUARD | compare | gating |
| world/boss.py:85 | BossService.check_for_boss_spawn._is_active_living_boss | 'world_boss' | compare | report-only |
| world/boss.py:217 | BossService.check_for_lair_spawn._is_active_living_lair_occupant | 'dragonkin' | compare | report-only |
| world/calamity.py:99 | CalamityService.apply_calamity_consequences | 'hero' | compare | report-only |
| world/creature_territory.py:45 | CreatureTerritoryService.process_territories | EntityRole.MONSTER | compare | report-only |
| world/environment.py:83 | EnvironmentService.get_aura_multipliers | Faction.HERO_GUILD | compare | report-only |
| world/occupation_config.py:8 | <module>[BASE_OCCUPATION_DENSITY] | EntityRole.SHOPKEEPER | table | report-only |
| world/occupation_config.py:9 | <module>[BASE_OCCUPATION_DENSITY] | EntityRole.WORKER | table | report-only |
| world/occupation_config.py:10 | <module>[BASE_OCCUPATION_DENSITY] | EntityRole.GUARD | table | report-only |
| world/region_threat_classifier.py:158 | RegionThreatClassifier._classify_legacy._is_hostile_bucket | Faction.MONSTER_HORDE | compare | report-only |
| world/region_threat_classifier.py:162 | RegionThreatClassifier._classify_legacy._is_friendly_bucket | Faction.HERO_GUILD | compare | report-only |
| world/region_threat_classifier.py:162 | RegionThreatClassifier._classify_legacy._is_friendly_bucket | Faction.TOWN_COUNCIL | compare | report-only |
| world/regional_sovereignty.py:48 | RegionalSovereigntyService.process_taxation | EntityRole.HERO | compare | report-only |
| world/regional_sovereignty.py:82 | RegionalSovereigntyService.apply_sovereignty_debuffs | EntityRole.HERO | compare | report-only |
| world/regional_sovereignty.py:88 | RegionalSovereigntyService.apply_sovereignty_debuffs | Faction.MONSTER_HORDE | compare | report-only |
| world/threat.py:30 | ThreatService.process_threat_evolution | 'world_boss' | compare | report-only |

## Review fixes and rulings applied (testing-planner relaying rpg-planner, 2026-11-15)
1. **Missed shapes** (review of 067ef9956): `party_composition.py` `infer_party_role` (`kind = (getattr(entity, "kind", "") or "").lower(); if kind in (...)`) was not found. Now `getattr(x, "<word>", d)` counts as `x.<word>` and a local name counts when assigned earlier in the same function from such an expression (one step; `or ""`, `.lower()`, `if/else` looked through). `kind = lead.kind; kind == "x"` stays unfound. Effect: +16 gating rows, all in `party_composition.py`; +17 rows in `content_semantics` (then report-only). No other row appeared.
2. **src/runtime** moved to EXCLUDE (bootstrap.py only, startup wiring). No row there today.
3. **Birth record** `core/builder.py:690` (`parent_a_role == HERO and parent_b_role == HERO`) promoted to gating by a data entry, `PROMOTED_GATING = {(file, symbol)}`; src/core stays report-only. A stale promotion fails.
4. **Compat maps** `entities/identity_resolver.py` `_ROLE_COMPAT`, `_FACTION_COMPAT` (10 rows) are reasoned exclusions at file+symbol level (`REASONED_EXCLUSIONS`), reported as `excluded`, with the ruling's reason; a stale exclusion fails. The condition that closes the hole: a resolved id compared to a string literal is a switch. `role_id` and `faction_id` already matched (any receiver); `species`, `archetype` (with `_id` / `_name`) were added as subject words. **New rows from these words: 0.** Checked by grep over the SCAN packages for `(role_id|faction_id|species_id|archetype_id|species|archetype)` compared with a literal: the only hits are `species_hostility == "high"` (a hostility level, not a species name; `content_semantics/relation.py:248-250`, correctly not matched) and `get_alignment_bucket(faction_id) == "defender"` (a bucket name, not an id; correctly not matched). The projected ids ("hero", "monster_horde", ...) are not compared to literals in SCAN today. Synthetic tests pin that `e.role_id == 'guard'`, `faction_id in (...)`, `species_id`, `archetype_id`, `species`, `archetype` are found. No archetype noise to list.
5. **src/content_semantics** moved to SCAN (gating): +29 gating rows (the `RoleSemanticsService` / `FactionSemanticsService` legacy maps and `is_civilian` / `is_worker` / `is_combatant`).
6. **src/world and src/core** stay report-only; rpg-planner expects `world/boss.py:217` and `world/region_threat_classifier.py:158` to become gating in its review.
7. One false positive found by the sample and fixed: a dict bound to `provider_calls_by_kind` (`world/providers/requirements.py`, a call counter keyed `"resources"`/`"services"`) matched the loose table-name test. Table names now need role, faction, species, archetype or entity/monster/creature/npc kind at the end of the name. Cost: a local table named `role_scores` (`progression/leveling.py:165`, keyed `VANGUARD`...) is not found; recorded below.

## Hand-checked sample (every 14th row from the 3rd, 10 rows, drawn on this 139-row inventory)
True positive = a role, kind or faction name in a branch, a membership test, or a name-keyed table, read at its line.

| row | verdict |
|---|---|
| ai/coming_of_age.py:27 `EntityRole.WORKER` (`_CANDIDATE_ROLES`) | true positive (name tuple read by `role in`) |
| content_semantics/faction.py:120 `'HERO'` | true positive (`"HERO" in f`, a legacy faction-name map) |
| content_semantics/role.py:26 `'STORE'` | true positive (`"STORE" in r`, a legacy role-name map) |
| core/builder.py:690 `EntityRole.HERO` | true positive (`parent_a_role == EntityRole.HERO`), promoted to gating |
| engine/biological_needs.py:38 `EntityRole.SHOPKEEPER` | true positive (`_PERSON_ROLES` name tuple) |
| engine/tactical.py:402 `'VANGUARD'` | true positive (`entity.combat.tactical_role == "VANGUARD"`) |
| entities/identity_resolver.py:23 `Faction.HERO_GUILD` | true positive as a name table; ruled `excluded` (identity projection) |
| systems/social_systems/party_composition.py:62 `'hunter'` | true positive (`kind in ("hero", "ranger", "hunter", "scout")`; the shape the review added) |
| systems/world_systems/generator.py:34 `'wolf'` | true positive (spawn table keyed on kind name) |
| world/environment.py:83 `Faction.HERO_GUILD` | true positive (`entity.identity.faction == Faction.HERO_GUILD`), report-only |

Result: 10 of 10 true positives. An earlier draw (before fix 7) found the one false positive above. Recall was checked by a grep of every `EntityRole.` / `Faction.` use in SCAN against the scan (what was not found: assignments, docstrings, builder arguments), and by the reviewer's `infer_party_role` case.

## Known limits
- A switch spelt another way (`monster_type == "goblin"`), a name read via `EntityRole.__members__`, and a `kind` on a receiver that is not entity-like are not found.
- The probe sees only string literals and the two legacy enums (`EntityRole`, `Faction`). No other entity-kind enum exists in `src/` today (the `*Kind` enums are item, lead, place and skill kinds); recorded as a limit.
- A local name is followed one assignment deep inside one function only.
- A local table not named for role, faction, species, archetype or entity kind is not found (`progression/leveling.py` `role_scores`, keyed on tactical role names).
