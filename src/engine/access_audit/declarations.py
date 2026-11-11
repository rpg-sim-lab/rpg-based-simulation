"""Declared access of each Resolution step dispatched through ``pipeline.run_phase`` (stage 1; TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT).

Per step:
- ``entry``: the callable whose source the static scan reads (``module:Class.method``).
- ``reads_tick_start``: top-level state attributes the entry reads. **Statically derived, not observed** (no read-proxy; rpg-planner ruling 2026-11-10), from the entry function
  only, so a lower bound; pinned here so a new read in the entry fails ``test_declarations``.
- ``writes``: the update entries the step writes, ``eu:<EntityUpdate bucket>`` or ``su:<StateUpdate field>``; ``su:*`` = declared coarsely (the whole update).
  Compared against the OBSERVED writes by the audit report.
- ``source``: where the declaration came from: ``phase_graph`` (``PhaseDependencyGraph`` output domains, mapped to buckets), ``feasibility_review_s2`` (the review's section 2 table),
  or ``first_pass`` (written from the entry's name; the first thing the report should confirm or correct).
- ``sliding_state``: True when the step reads this tick's earlier deltas (``U``), not only tick-start state.

Steps the pipeline computes inline and wraps in a lambda that only merges (``diplomatic_transitions``, ``faction_sentiment``) have ``entry=None``: their work is in
``pipeline.py`` itself, outside ``run_phase``, so only their writes are declared."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Optional, Tuple


@dataclass(frozen=True)
class StepDeclaration:
    """One step's declared access (see the module docstring for each field)."""

    name: str
    entry: Optional[str]
    reads_tick_start: FrozenSet[str]
    writes: FrozenSet[str]
    source: str
    sliding_state: bool


def _d(row: Tuple[Any, ...]) -> StepDeclaration:
    """Build a declaration from a row ``(name, entry, reads, writes, source, sliding_state)``."""
    name, entry, reads, writes, source, sliding = row
    return StepDeclaration(name, entry, frozenset(reads), frozenset(writes), source, sliding)


DECLARATIONS: Dict[str, StepDeclaration] = {d.name: d for d in (
    _d(("trust_boundary", "src.engine.pipeline_phases.trust:TrustBoundaryPhase.strip", ('entity_updates', 'rejection_events', 'rejections_delta'), ('su:*',), "phase_graph", False)),
    _d(("actor_validity", "src.engine.pipeline_phases.actor_validity:ActorValidityPhase.resolve", ('entities', 'tick'), ('su:*',), "phase_graph", False)),
    _d(("memory_update", "src.domains.memory.phase:MemoryUpdatePhase.apply", ('entities', 'tick'), ('eu:strategic',), "phase_graph", False)),
    _d(("habit_bias_action_style", "src.domains.emotion.habit_phase:HabitBiasUpdatePhase.apply", ('entities',), ('eu:strategic',), "first_pass", False)),
    _d(("role_model_selection", "src.strategy.role_model_phase:RoleModelSelectionPhase.apply", ('entities', 'tick'), ('eu:cognition_bundle_set',), "feasibility_review_s2", False)),
    _d(("self_model", "src.cognition.self_model_phase:SelfModelUpdatePhase.apply", ('entities', 'pending_self_model_information_events', 'tick'), ('eu:cognition_bundle_set', 'eu:strategic'), "feasibility_review_s2", False)),
    _d(("information_belief", "src.domains.information.phase:InformationBeliefPhase.apply", ('entities', 'local_scars', 'regions', 'tick'), ('eu:strategic',), "phase_graph", False)),
    _d(("information_intent_execution", "src.engine.pipeline_phases.information_intent_execution:InformationIntentExecutionPhase.execute", ('entities', 'tick'), ('eu:strategic', 'eu:inventory'), "phase_graph", False)),
    _d(("cooperation", "src.domains.cooperation.phase:CooperationPhase.execute", ('entities', 'groups', 'periodic_due_ticks', 'social_cooperation_enabled', 'tick'), ('eu:social', 'eu:strategic'), "feasibility_review_s2", False)),
    _d(("contracts", "src.engine.pipeline_phases.contracts:ContractLifecyclePhase.resolve_expirations", ('entities', 'tick'), ('eu:social', 'eu:inventory', 'eu:strategic'), "phase_graph", False)),
    _d(("blacksmith", "src.engine.blacksmith:BlacksmithSystem.enforce", ('building_tiles', 'buildings', 'entities'), ('eu:inventory', 'su:resource_updates'), "phase_graph", False)),
    _d(("faction_awareness", "src.engine.faction_decision:FactionAwarenessService.compute_tension_updates", ('factions',), ('su:faction_updates',), "feasibility_review_s2", False)),
    _d(("information_propagation", "src.engine.faction_decision:InformationPropagationService.compute_propagation_events", ('factions', 'tick'), ('su:world_events_add',), "feasibility_review_s2", False)),
    _d(("military_conflict", "src.engine.military_conflict:MilitaryConflictPhase.execute", ('factions', 'regions', 'tick'), ('su:faction_updates', 'su:world_events_add'), "feasibility_review_s2", False)),
    _d(("action_routing", "src.engine.pipeline_phases.actions:ActionRoutingPhase.route", ('entities', 'tick'), ('eu:new_position', 'eu:moved_this_tick', 'eu:combat', 'eu:interaction', 'eu:task', 'eu:navigation'), "phase_graph", True)),
    _d(("position_swaps", "src.engine.pipeline_phases.movement:MovementPhase.resolve_position_swaps", ('entities',), ('eu:new_position', 'eu:moved_this_tick'), "phase_graph", True)),
    _d(("movement_routing", "src.engine.pipeline_phases.movement:MovementPhase.route_movement_intent", ('entities',), ('eu:new_position', 'eu:moved_this_tick', 'eu:navigation'), "phase_graph", True)),
    _d(("combat_engagement", "src.domains.combat_engagement.phase:CombatEngagementPhase.apply", ('entities', 'tick'), ('eu:combat', 'eu:strategic', 'eu:cognition_bundle_set', 'eu:property_updates'), "feasibility_review_s2", False)),
    _d(("interaction_routing", "src.engine.pipeline_phases.interactions:InteractionPhase.route_interaction_intent", ('entities',), ('eu:interaction',), "phase_graph", True)),
    _d(("interaction_enforcement", "src.engine.interaction:InteractionSystem.enforce", ('chests', 'corpses', 'entities', 'ground_items', 'resource_nodes', 'tick'), ('eu:inventory', 'eu:social', 'su:resource_updates', 'su:node_updates'), "phase_graph", True)),
    _d(("building_sabotage", "src.engine.sabotage:BuildingSabotageSystem.resolve", ('entities',), ('su:building_updates', 'eu:social'), "phase_graph", False)),
    _d(("town_resolution", "src.engine.town_resolution:TownResolutionSystem.resolve", ('buildings', 'entities', 'global_resources', 'owed', 'recent_world_events', 'regions', 'tick', 'town_tiles'), ('su:world_updates', 'eu:social', 'eu:inventory'), "phase_graph", True)),
    _d(("world_dynamics", "src.engine.world_dynamics:WorldDynamicsSystem.resolve_dynamics", ('chests', 'entities', 'feature_flags', 'next_entity_id', 'regions', 'tick'), ('su:*',), "phase_graph", True)),
    _d(("world_emergence", "src.domains.world_emergence.phase:WorldEmergencePhase.execute", ('entities', 'seed', 'tick'), ('su:*',), "phase_graph", False)),
    _d(("quest_rewards", "src.engine.pipeline_phases.quests:QuestRewardPhase.resolve", (), ('eu:reward', 'eu:identity', 'eu:inventory', 'eu:resource_transfers'), "phase_graph", True)),
    _d(("guild_visit", "src.engine.pipeline_phases.guild_visit:GuildVisitPhase.resolve", ('buildings', 'entities', 'feature_flags'), ('su:quest_registry_add', 'eu:strategic'), "first_pass", False)),
    _d(("shop", "src.engine.shop:ShopSystem.enforce", ('buildings', 'entities', 'tick'), ('eu:inventory', 'eu:social', 'su:resource_updates'), "phase_graph", True)),
    _d(("paid_information", "src.engine.pipeline_phases.paid_information:PaidInformationTransactionSystem.enforce", ('entities', 'information_providers', 'tick'), ('eu:inventory', 'eu:strategic', 'su:information_providers_update'), "first_pass", True)),
    _d(("resource_transactions", "src.engine.pipeline_phases.resources:ResourceTransactionPhase.resolve", (), ('eu:inventory', 'su:resource_updates'), "phase_graph", True)),
    _d(("evolution", "src.engine.evolution:EvolutionSystem.evaluate", ('entities', 'tick'), ('eu:identity', 'eu:attributes'), "phase_graph", True)),
    _d(("progression_conversion", "src.domains.progression.phase:ProgressionConversionPhase.execute", ('entities', 'progression_conversion_enabled'), ('eu:attributes',), "phase_graph", True)),
    _d(("strategic_intelligence", "src.systems.strategic_systems.intelligence:StrategicIntelligenceSystem.fused_strategic_pass", ('_has_hostiles_or_dead_cache', 'entities', 'tick', 'town_center', 'town_tiles'), ('eu:strategic', 'eu:task', 'eu:navigation', 'eu:identity'), "feasibility_review_s2", False)),
    _d(("belief_staleness_decay", "src.systems.strategic_systems.belief:BeliefCycleSystem.resolve_lead_staleness", ('entities', 'tick'), ('eu:strategic',), "feasibility_review_s2", False)),
    _d(("lead_contradiction", "src.engine.pipeline_phases.lead_contradiction:LeadContradictionSystem.enforce", ('entities', 'information_providers', 'tick'), ('eu:strategic',), "feasibility_review_s2", True)),
    _d(("near_death_hardening", "src.engine.pipeline_phases.hardening:NearDeathHardeningPhase.apply", ('entities', 'tick'), ('eu:combat', 'eu:attributes'), "phase_graph", True)),
    _d(("occupancy_resolution", "src.engine.pipeline_phases.occupancy:OccupancyPhase.resolve", ('entities', 'tick'), ('eu:new_position', 'eu:moved_this_tick', 'eu:navigation', 'su:rejections_delta'), "phase_graph", True)),
    _d(("lifecycle", "src.systems.lifecycle:LifecycleSystem.resolve_lifecycle", ('entities', 'tick'), ('su:*',), "phase_graph", True)),
    _d(("groups", "src.engine.pipeline_phases.groups:GroupPhase.resolve", ('entities', 'groups', 'region_loyalty_pressure', 'tick'), ('eu:group_id_set', 'eu:social', 'eu:strategic', 'su:groups_add', 'su:groups_add_or_update', 'su:groups_remove'), "phase_graph", True)),
    _d(("clan_lifecycle", "src.engine.pipeline_phases.clan_lifecycle:ClanLifecyclePhase.resolve", ('clans', 'entities', 'tick'), ('su:clan_updates',), "first_pass", True)),
    _d(("expired_offers", "src.systems.social_systems.contracts:ContractService.reap_expired_offers", ('entities', 'tick'), ('su:*',), "first_pass", False)),
    _d(("capacity_enforcement", "src.engine.pipeline_phases.capacity_enforcement:CapacityEnforcementPhase.enforce", ('entities', 'tick'), ('su:*',), "phase_graph", True)),
    _d(("diplomatic_transitions", None, (), ("su:faction_updates", "su:world_events_add"), "feasibility_review_s2", False)),
    _d(("faction_sentiment", None, (), ("su:faction_updates",), "feasibility_review_s2", True)),
)}
