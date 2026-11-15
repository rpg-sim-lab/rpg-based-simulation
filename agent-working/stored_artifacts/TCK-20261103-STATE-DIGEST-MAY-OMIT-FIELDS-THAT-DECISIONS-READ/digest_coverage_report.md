---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
phase: inprogress
date: 2026-11-15
tags: [testing, determinism]
---

# TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ: per-field digest coverage report (item 1)

Generated from tests/architecture/state_digest_allowlist.yaml by `report()` in tests/architecture/test_state_digest_covers_every_field.py. Samples: urban_political s42 t0, crowded_frontier s42 t60. GAP rows are rpg-planner's omission list for the v4 question; the unexercised list is "not proven"; the no_reader rows are for the unwired triage.

```
# 120 GAP rows, 33 EXCLUDE rows, 3 unexercised
## GAP
state.buildings[].inventory.items[].properties [F] src/entities/identity_resolver.py:39
state.buildings[].inventory.max_weight [F] src/core/builder.py:255
state.chests[].items[].properties [F] src/entities/identity_resolver.py:39
state.corpses[].items[].properties [F] src/entities/identity_resolver.py:39
state.current_mode [B] 
state.entities[].cognition.commitment.abandoned_commitments[].id [F] unlocated
state.entities[].cognition.commitment.abandoned_commitments[].penalty [F] unlocated
state.entities[].cognition.commitment.abandoned_commitments[].tick_abandoned [F] unlocated
state.entities[].cognition.commitment.active_commitments[].created_tick [F] src/domains/commitment/impact.py:19
state.entities[].cognition.commitment.active_commitments[].deadline_tick [F] src/domains/commitment/pressure.py:19
state.entities[].cognition.commitment.active_commitments[].id [F] src/domains/commitment/impact.py:19
state.entities[].cognition.commitment.active_commitments[].kind [F] src/domains/commitment/impact.py:19
state.entities[].cognition.commitment.active_commitments[].strength [F] src/domains/commitment/impact.py:19
state.entities[].cognition.commitment.active_commitments[].target_id [F] src/domains/commitment/impact.py:19
state.entities[].cognition.commitment.contract_obligations [F] unlocated
state.entities[].cognition.commitment.party_obligations [F] unlocated
state.entities[].cognition.commitment.quest_obligations [F] unlocated
state.entities[].cognition.memory.causal.entries[].confidence [F] src/domains/chronicle/renderer.py:42
state.entities[].cognition.memory.causal.entries[].event_id [F] src/domains/campaigns/behavior_change.py:24
state.entities[].cognition.memory.causal.entries[].event_kind [F] src/systems/world_systems/events.py:189
state.entities[].cognition.memory.causal.entries[].future_advice [F] src/domains/adventure/scoring.py:348
state.entities[].cognition.memory.causal.entries[].interpreted_causes [F] unlocated
state.entities[].cognition.memory.causal.entries[].region_id [F] src/domains/chronicle/renderer.py:42
state.entities[].cognition.memory.causal.entries[].tick [F] src/domains/chronicle/renderer.py:42
state.entities[].cognition.memory.combat.opponent_stats[].confidence [F] src/domains/combat_engagement/phase.py:154
state.entities[].cognition.memory.combat.opponent_stats[].estimated_power [F] src/domains/combat_engagement/perception.py:105
state.entities[].cognition.memory.combat.opponent_stats[].known_skill_ids [F] src/domains/combat_engagement/learning.py:45
state.entities[].cognition.memory.combat.opponent_stats[].last_updated_tick [F] src/core/group_record.py:70
state.entities[].cognition.memory.combat.opponent_stats[].outcomes [F] src/systems/strategic_systems/intelligence.py:7
state.entities[].cognition.memory.combat.opponent_stats[].salience [F] src/systems/strategic_systems/learning.py:21
state.entities[].cognition.memory.combat.opponent_stats[].subject_key [F] src/domains/combat_engagement/perception.py:106
state.entities[].cognition.memory.combat.opponent_stats[].uncertainty [F] src/domains/combat_engagement/risk_evaluator.py:72
state.entities[].cognition.memory.experience.records [F] src/engine/checkpoint_fields.py:107
state.entities[].cognition.memory.spatial.dangerous_routes [F] unlocated
state.entities[].cognition.memory.spatial.failed_search_locations [F] unlocated
state.entities[].cognition.memory.spatial.known_resource_sites [F] src/domains/memory/spatial_update.py:67
state.entities[].cognition.memory.spatial.safe_routes [F] unlocated
state.entities[].cognition.memory.spatial.visited_regions[].familiarity [F] src/domains/memory/spatial_update.py:28
state.entities[].cognition.memory.spatial.visited_regions[].is_dangerous [F] src/domains/memory/spatial_update.py:46
state.entities[].cognition.memory.spatial.visited_regions[].region_id [F] src/domains/memory/spatial_update.py:28
state.entities[].cognition.memory.spatial.visited_regions[].visit_count [F] unlocated
state.entities[].cognition.motivation.role_fit.party_role_tags [F] src/domains/motivation/evaluator.py:36
state.entities[].cognition.motivation.role_fit.quest_tags [F] src/domains/motivation/evaluator.py:40
state.entities[].cognition.motivation.role_fit.skill_tags [F] src/domains/motivation/evaluator.py:32
state.entities[].cognition.relationships.private_trust[].bond_strength [F] unlocated
state.entities[].cognition.relationships.private_trust[].entity_id [F] unlocated
state.entities[].cognition.relationships.private_trust[].value [F] unlocated
state.entities[].cognition.subjective.knowledge.facts[].subject [F] src/cognition/common_knowledge.py:51
state.entities[].cognition.subjective.knowledge.unknowns[].subject [F] src/cognition/knowledge_model.py:93
state.entities[].cognition.subjective.perception.ignored_signals[].reason [F] unlocated
state.entities[].cognition.subjective.perception.ignored_signals[].signal_id [F] src/domains/perception/filter.py:87
state.entities[].cognition.subjective.perception.ignored_signals[].tick [F] unlocated
state.entities[].cognition.subjective.perception.perceived_entities[].confidence [F] unlocated
state.entities[].cognition.subjective.perception.perceived_entities[].entity_id [F] unlocated
state.entities[].cognition.subjective.perception.perceived_entities[].kind [F] unlocated
state.entities[].cognition.subjective.perception.perceived_entities[].position [F] unlocated
state.entities[].cognition.subjective.perception.perceived_opportunities[].kind [F] unlocated
state.entities[].cognition.subjective.perception.perceived_opportunities[].opportunity_id [F] unlocated
state.entities[].cognition.subjective.perception.perceived_resources[].confidence [F] unlocated
state.entities[].cognition.subjective.perception.perceived_resources[].kind [F] unlocated
state.entities[].cognition.subjective.perception.perceived_resources[].node_id [F] src/core/update_models/world.py:22
state.entities[].cognition.subjective.perception.perceived_resources[].position [F] unlocated
state.entities[].cognition.subjective.perception.perceived_services[].position [F] unlocated
state.entities[].cognition.subjective.perception.perceived_services[].service_id [F] src/core/registries.py:159
state.entities[].cognition.subjective.perception.perceived_threats[].position [F] src/engine/work_wake.py:3
state.entities[].cognition.subjective.perception.perceived_threats[].threat_id [F] unlocated
state.entities[].cognition.subjective.perception.perceived_threats[].threat_level [F] unlocated
state.entities[].equipment.durability [F] src/world/providers/services.py:36
state.entities[].identity.cooldowns [E] src/engine/tactical.py:704, src/engine/domain/skill_actions.py:48
state.entities[].identity.craft_target [E] src/core/updates.py:137
state.entities[].identity.latest_intent_results [E] src/systems/strategic_systems/work_queue.py:56
state.entities[].identity.traits [E] src/systems/social_systems/appraisal.py:146
state.entities[].identity.veterancy_points [E] src/progression/veterancy.py:34
state.entities[].inventory.items[].properties [F] src/entities/identity_resolver.py:39
state.entities[].inventory.max_weight [F] src/core/builder.py:255
state.entities[].self_model.capabilities.estimates[].capability_key [F] unlocated
state.entities[].self_model.knowledge.facts[].subject [F] src/cognition/common_knowledge.py:51
state.entities[].self_model.knowledge.unknowns[].subject [F] src/cognition/knowledge_model.py:93
state.entities[].self_model.needs.active_needs[].key [F] src/cognition/self_model_phase.py:194
state.entities[].stamina.current [E] src/systems/strategic_systems/work_queue.py:88
state.entities[].stamina.exhaustion_penalty [E] src/systems/strategic_systems/work_queue.py:88
state.entities[].stamina.exhaustion_threshold [E] src/systems/strategic_systems/work_queue.py:88
state.entities[].stamina.max_stamina [E] src/systems/strategic_systems/work_queue.py:88
state.entities[].stamina.regen_rate [E] src/systems/strategic_systems/work_queue.py:88
state.entities[].stamina.rest_regen_rate [E] src/systems/strategic_systems/work_queue.py:88
state.entities[].strategic.profile.detour_breadth [F] src/systems/strategic_systems/detour.py:71
state.entities[].strategic.profile.interruption_resistance [F] src/systems/strategic_systems/intelligence.py:1091
state.entities[].strategic.profile.max_active_projects [F] src/town/guild.py:90
state.entities[].strategic.profile.max_candidate_zones [F] src/engine/pipeline_phases/capacity_enforcement.py:113
state.entities[].strategic.profile.max_committed_intentions [F] src/engine/pipeline_phases/capacity_enforcement.py:128
state.entities[].strategic.profile.max_concerns [F] src/systems/strategic_systems/detour.py:190
state.entities[].strategic.profile.max_hypotheses [F] src/systems/strategic_systems/detour.py:200
state.entities[].strategic.profile.max_leads [F] src/strategy/leads.py:28
state.entities[].strategic.profile.max_turning_points [F] src/engine/patches.py:492
state.entities[].strategic.profile.reserved_detour_depth [F] src/core/builder.py:450
state.entities[].strategic.profile.resistance_multiplier [F] src/systems/strategic_systems/intelligence.py:1091
state.entities[].strategic.projects[].created_tick [F] src/town/guild.py:90
state.entities[].strategic.projects[].failure_count [F] src/systems/strategic_systems/detour.py:89
state.entities[].strategic.projects[].id [F] src/town/guild.py:90
state.entities[].strategic.projects[].lock_until_tick [F] src/systems/strategic_systems/intelligence.py:1095
state.entities[].strategic.projects[].score [F] src/town/guild.py:90
state.entities[].timeline [E] src/domains/cooperation/phase.py:38
state.ground_items[].dropped_tick [F] src/engine/world_dynamics.py:360
state.ground_items[].source_entity_id [F] src/systems/strategic_systems/detour.py:297
state.groups[].member_ids [F] src/systems/social_systems/group_service.py:16
state.home_storage[].items[].properties [F] src/entities/identity_resolver.py:39
state.home_storage[].max_weight [F] src/core/builder.py:255
state.movement_cache [A] 
state.next_entity_id [D] 
state.next_item_instance_id [D] 
state.next_node_id [D] 
state.pending_information_responses [D] 
state.pending_self_model_information_events [D] 
state.pressure_signals [C] 
state.processed_transaction_ids [C] 
state.rejection_registry [C] 
state.route_plans [D] 
state.terrain [B] 
state.town_entity_ids [D] 
state.transient_claims [F] src/domains/campaigns/survivor_placement.py:78
## unexercised (not proven), by component
state.entities[].strategic: beliefs
state.information_source_profiles: state.information_source_profiles
state.regions[]: population_cohorts
## no_reader (for the unwired triage)
state.entities[].cognition.memory.social.coop_outcomes
state.entities[].cognition.relationships.known_partners
state.entities[].cognition.subjective.time.delay_risks
state.transaction_trace
```
