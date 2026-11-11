---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, engine, determinism, planning]
---

# Step declarations (DRAFT): every Resolution step, declared and observed

Companion to `next_generation_engine_contract_spec.md` §1.1 (draft 2), for `TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC`.
Written by architecture-planner-u24, 2026-11-11.

- **What it is:** one row per step that `pipeline.run_phase` dispatches (43 steps). It is the **starting** `StepDecl` for each
  step, not its final one: each stage that converts a step settles that step's row first (spec §3.4).
- **Sources:**
  - the declarations of the access audit, `src/engine/access_audit/declarations.py` at main `5c6990e51`;
  - the observations in `next_generation_engine_access_audit_report.md` (#863: 6 cells, 5000 ticks each, two gate worlds);
  - the ordinal, which is the step name's first line in `src/engine/pipeline.py` at `5c6990e51`.
  The table was generated from those files by a script, not typed by hand.
- **Markers:**
  - **†** observed but not declared;
  - **°** declared but never observed in 30000 ticks;
  - unmarked, declared and observed.
  A **†** is not proof that a step writes outside its remit. The audit diffs each step's input update against its result, so a
  bucket the step only re-copies or compacts also shows as a write (report, attribution caveat).
- **Not exercised:** 8 steps sit behind a flag that is OFF on the gate worlds. Their rows are declarations only, with no evidence
  (spec §3.4, rule 3).
- **Reads** come from a non-transitive static scan of the entry function only. They are a lower bound, not a check.
- **§5 items seen** come from the report's Tier 1 watch list. **Bold** marks real state written outside the update, or a mutation
  of the input update. The rest are lazy caches filled on first read.
- **The "reads this tick's deltas" column is the audit's `sliding_state` field.** It says the step reads earlier deltas at all.
  The spec's `sliding` is narrower: unit k reads the deltas of units before k in the same step. Each stage sets `sliding`.
- **Unit / order** is filled only where the spec already argues it (§4, §8). Each stage fills in the rest.

| # | step (`pipeline.py` line) | exercised on gate worlds | reads this tick's deltas (audit field) | writes: declared + observed | reads (static, entry only) | §5 items seen | unit / order |
|---|---|---|---|---|---|---|---|
| 1 | trust_boundary (`:137`) | yes | no | eu:biological†, eu:readiness_delta†, eu:resource_transfers†, su:*° | entity_updates, rejection_events, rejections_delta | - | at its stage |
| 2 | actor_validity (`:138`) | yes | no | su:*° | entities, tick | - | at its stage |
| 3 | memory_update (`:157`) | **no**: `ENABLE_MEMORY_UPDATE` OFF | no | eu:strategic (declared only) | entities, tick | - | at its stage |
| 4 | habit_bias_action_style (`:172`) | **no**: `ENABLE_HABIT_BIAS_ACTION_STYLE` OFF | no | eu:strategic (declared only) | entities | - | at its stage |
| 5 | role_model_selection (`:185`) | **no**: `ENABLE_ROLE_MODEL_IMITATION` OFF | no | eu:cognition_bundle_set (declared only) | entities, tick | - | at its stage |
| 6 | self_model (`:194`) | **no**: `ENABLE_SELF_MODEL_COGNITION` OFF | no | eu:cognition_bundle_set, eu:strategic (declared only) | entities, pending_self_model_information_events, tick | - | at its stage |
| 7 | information_belief (`:203`) | yes | no | eu:property_updates†, eu:self_model_bundle_set†, eu:strategic | entities, local_scars, regions, tick | _region_index_cache | at its stage |
| 8 | information_intent_execution (`:210`) | **no**: `ENABLE_INFORMATION_INTENT_EXECUTION` OFF | no | eu:inventory, eu:strategic (declared only) | entities, tick | - | at its stage |
| 9 | cooperation (`:219`) | yes | no | eu:property_updates†, eu:social, eu:strategic, su:metric_counters† | entities, groups, periodic_due_ticks, social_cooperation_enabled, tick | _readonly_entities_cache; **entities[*].timeline** | entity / state_entities |
| 10 | contracts (`:224`) | yes | no | eu:inventory°, eu:social, eu:strategic | entities, tick | - | at its stage |
| 11 | blacksmith (`:225`) | yes | no | eu:inventory°, su:resource_updates° | building_tiles, buildings, entities | - | at its stage |
| 12 | faction_awareness (`:241`) | yes | no | su:faction_updates° | factions | - | at its stage |
| 13 | information_propagation (`:251`) | **no**: `ENABLE_INFORMATION_HUB_ACCUMULATION` OFF | no | su:world_events_add (declared only) | factions, tick | - | at its stage |
| 14 | diplomatic_transitions (`:282`) | yes | no | su:faction_updates, su:world_events_add° | no scan | - | at its stage |
| 15 | military_conflict (`:292`) | yes | no | su:faction_updates°, su:world_events_add° | factions, regions, tick | - | at its stage |
| 16 | action_routing (`:299`) | yes | yes | eu:biological†, eu:cognition_bundle_set†, eu:combat, eu:group_id_set†, eu:interaction, eu:moved_this_tick, eu:navigation, eu:new_position, eu:readiness_delta†, eu:resource_transfers†, eu:social†, eu:stamina_update†, eu:strategic†, eu:task, eu:wound_update†, su:rejection_events†, su:rejections_delta†, su:world_events_add† | entities, tick | - | entity / ascending_id |
| 17 | position_swaps (`:300`) | yes | yes | eu:moved_this_tick, eu:navigation†, eu:new_position, eu:property_updates†, eu:stamina_update† | entities | _occupancy_map_cache | at its stage |
| 18 | movement_routing (`:301`) | yes | yes | eu:cognition_bundle_set†, eu:combat†, eu:moved_this_tick, eu:navigation, eu:new_position, eu:property_updates†, eu:resource_transfers†, eu:stamina_update†, su:metric_counters†, su:rejections_delta† | entities | _occupancy_map_cache; _region_index_cache; **route_plans**; **transient_claims** | at its stage |
| 19 | combat_engagement (`:322`) | yes | no | eu:cognition_bundle_set, eu:combat°, eu:property_updates, eu:strategic | entities, tick | world_indexes | at its stage |
| 20 | interaction_routing (`:334`) | yes | yes | eu:interaction | entities | _corpse_map_cache; _ground_item_map_cache; _node_map_cache | at its stage |
| 21 | interaction_enforcement (`:335`) | yes | yes | eu:interaction†, eu:inventory°, eu:resource_transfers†, eu:social°, su:node_updates°, su:rejections_delta†, su:resource_updates° | chests, corpses, entities, ground_items, resource_nodes, tick | - | at its stage |
| 22 | building_sabotage (`:336`) | yes | no | eu:social°, su:building_updates° | entities | - | at its stage |
| 23 | town_resolution (`:341`) | yes | yes | eu:combat†, eu:inventory°, eu:social°, su:building_updates†, su:metric_counters†, su:resource_updates†, su:world_updates° | buildings, entities, global_resources, owed, recent_world_events, regions, tick, town_tiles | _building_region_map_cache; _region_index_cache | at its stage |
| 24 | world_dynamics (`:344`) | yes | yes | eu:combat†, eu:strategic†, su:* | chests, entities, feature_flags, next_entity_id, regions, tick | _region_index_cache; **input update in place: su:world_updates** | at its stage |
| 25 | world_emergence (`:351`) | **no**: `ENABLE_WORLD_EMERGENCE` OFF | no | su:* (declared only) | entities, seed, tick | - | at its stage |
| 26 | quest_rewards (`:359`) | yes | yes | eu:identity°, eu:inventory°, eu:resource_transfers°, eu:reward° | - | - | at its stage |
| 27 | guild_visit (`:365`) | yes | no | eu:strategic, su:quest_registry_add° | buildings, entities, feature_flags | - | at its stage |
| 28 | shop (`:367`) | yes | yes | eu:inventory°, eu:social°, su:resource_updates° | buildings, entities, tick | _building_map_cache | at its stage |
| 29 | paid_information (`:371`) | yes | yes | eu:inventory°, eu:strategic°, su:information_providers_update° | entities, information_providers, tick | - | at its stage |
| 30 | resource_transactions (`:373`) | yes | yes | eu:biological†, eu:combat†, eu:identity†, eu:intent_results†, eu:interaction†, eu:inventory, eu:readiness_delta†, eu:resource_transfers†, eu:strategic†, su:building_updates†, su:corpses_add_or_update†, su:corpses_remove†, su:node_updates†, su:rejection_events†, su:rejections_delta†, su:resource_updates, su:transaction_trace†, su:world_events_add† | - | - | at its stage |
| 31 | evolution (`:377`) | yes | yes | eu:attributes°, eu:identity° | entities, tick | **input update in place: eu:combat, eu:identity, eu:property_updates** | at its stage |
| 32 | progression_conversion (`:383`) | **no**: `ENABLE_PROGRESSION_EVOLUTION` OFF | yes | eu:attributes (declared only) | entities, progression_conversion_enabled | - | at its stage |
| 33 | strategic_intelligence (`:394`) | yes | no | eu:identity°, eu:interaction†, eu:navigation, eu:property_updates†, eu:strategic, eu:task° | _has_hostiles_or_dead_cache, entities, tick, town_center, town_tiles | _region_list_cache; _spatial_grid_cache | world plan, then entity / candidate_list |
| 34 | belief_staleness_decay (`:404`) | yes | no | eu:strategic | entities, tick | - | at its stage |
| 35 | lead_contradiction (`:405`) | yes | yes | eu:strategic° | entities, information_providers, tick | - | at its stage |
| 36 | near_death_hardening (`:406`) | yes | yes | eu:attributes°, eu:cognition_bundle_set†, eu:combat | entities, tick | - | at its stage |
| 37 | occupancy_resolution (`:408`) | yes | yes | eu:moved_this_tick, eu:navigation, eu:new_position, su:rejection_events†, su:rejections_delta | entities, tick | - | at its stage |
| 38 | lifecycle (`:410`) | yes | yes | eu:active†, eu:cognition_bundle_set†, eu:intent_results†, eu:interaction†, eu:inventory†, eu:lifecycle†, su:* | entities, tick | - | at its stage |
| 39 | groups (`:412`) | yes | yes | eu:group_id_set, eu:social°, eu:strategic, su:groups_add, su:groups_add_or_update, su:groups_remove°, su:next_group_id_set† | entities, groups, region_loyalty_pressure, tick | - | at its stage |
| 40 | clan_lifecycle (`:414`) | yes | yes | su:clan_updates° | clans, entities, tick | - | at its stage |
| 41 | expired_offers (`:421`) | yes | no | eu:identity†, eu:strategic†, su:*° | entities, tick | - | at its stage |
| 42 | capacity_enforcement (`:423`) | yes | yes | eu:strategic†, su:* | entities, tick | - | at its stage |
| 43 | faction_sentiment (`:438`) | yes | yes | su:faction_updates | no scan | - | at its stage |
