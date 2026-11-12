# Compliance IDs: AUTH-005, AUTH-006, AUTH-007, INFRA-122
# Compliance IDs: TOWN-001, TOWN-002, TOWN-131, TOWN-156, TOWN-157, TOWN-159, TOWN-160, TOWN-161, TOWN-162, TOWN-163
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from src.core.models.quests import QuestOpportunity, QuestOpportunityStatus
    from src.core.state import (
        ChestState,
        CorpseState,
        EntityState,
        GroundItemState,
        GroupRecord,
        LocalScarState,
        OwedRecord,
        StatusEffectState,
    )
    from src.engine.intent.action_intent import ActionIntent
    from src.engine.policy import GovernorPolicy
from src.core.dirty import DirtySet
from src.core.group_update_merge import merge_group_fields
from src.core.movement_modes import MovementMode
from src.core.spawn_source import SpawnSource
from src.core.state import ItemInstance, LifeStage
from src.core.update_models.body import (  # noqa: F401  (re-exported)
    AttributeUpdate,
    BiologicalUpdate,
    InteractionUpdate,
    LifecycleUpdate,
    RewardUpdate,
    TaskUpdate,
)
from src.core.update_models.buildings import BuildingUpdate  # noqa: F401  (re-exported: updates.py is where callers import it from)
from src.core.update_models.combat import (  # noqa: F401  (re-exported)
    CombatIntent,
    CombatUpdate,
    EquipmentUpdate,
    StaminaUpdate,
    WoundUpdate,
)
from src.core.update_models.inventory import InventoryUpdate, ItemInstanceUpdate
from src.core.update_models.quests import QuestUpdate
from src.core.update_models.resources import ResourceTransferIntent
from src.core.update_models.social import RejectionEvent, SocialBondUpdate, SocialUpdate  # noqa: F401  (re-exported)
from src.core.update_models.strategic import StrategicUpdate  # noqa: F401  (re-exported)
from src.core.update_models.world import (  # noqa: F401  (re-exported)
    NO_OWNER_SENTINEL,
    CampUpdate,
    ChestUpdate,
    ClanUpdate,
    FactionUpdate,
    QuestOpportunityRewardIntent,
    ResourceNodeUpdate,
    WorldUpdate,
    decode_owner_faction_id_set,
)


@dataclass(frozen=True, slots=True)
class NavigationUpdate:
    """Updates to movement intent and pathfinding."""
    target_set: Optional[tuple[float, float]] = None
    target_clear: bool = False
    path_set: Optional[List[tuple[float, float]]] = None
    moved_recently_set: Optional[bool] = None
    movement_mode_set: Optional[MovementMode] = None
    failure_reason: Optional[str] = None
    clear_target: bool = False
    clear_path: bool = False
    
    # Phase 4 additions
    wait_count_delta: int = 0
    oscillation_count_delta: int = 0
    last_position_set: Optional[tuple[float, float]] = None
    region_id_set: Optional[str] = None
    step_ready_tick_set: Optional[float] = None  # D75: the earliest tick of the entity's next step
    lodged_in_set: Optional[int] = None  # F3: the building the subject lodges in from this tick (a lodge claim until `grant_beds` grants it)
    lodged_in_clear: bool = False  # F3: the subject leaves the building it lodges in

    def is_noop(self) -> bool:
        return (self.target_set is None and not self.target_clear and self.path_set is None and self.step_ready_tick_set is None and 
                self.moved_recently_set is None and self.movement_mode_set is None and 
                self.failure_reason is None and not self.clear_target and not self.clear_path and 
                self.wait_count_delta == 0 and self.oscillation_count_delta == 0 and 
                self.last_position_set is None and self.region_id_set is None and self.lodged_in_set is None and not self.lodged_in_clear)

    def merge(self, other: NavigationUpdate) -> NavigationUpdate:
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.target_set is not None: changes["target_set"] = other.target_set
        if other.target_clear: changes["target_clear"] = True
        if other.path_set is not None: changes["path_set"] = other.path_set
        if other.moved_recently_set is not None: changes["moved_recently_set"] = other.moved_recently_set
        if other.movement_mode_set is not None: changes["movement_mode_set"] = other.movement_mode_set
        if other.failure_reason is not None: changes["failure_reason"] = other.failure_reason
        if other.clear_target: changes["clear_target"] = True
        if other.clear_path: changes["clear_path"] = True
        if other.wait_count_delta != 0: changes["wait_count_delta"] = self.wait_count_delta + other.wait_count_delta
        if other.oscillation_count_delta != 0: changes["oscillation_count_delta"] = self.oscillation_count_delta + other.oscillation_count_delta
        if other.last_position_set is not None: changes["last_position_set"] = other.last_position_set
        if other.region_id_set is not None: changes["region_id_set"] = other.region_id_set
        if other.step_ready_tick_set is not None: changes["step_ready_tick_set"] = other.step_ready_tick_set
        changes.update(other._lodging_changes())
        return replace(self, **changes)

    def _lodging_changes(self) -> Dict[str, Any]:
        """What a merge takes from this update for the lodging fields (F3): the claim's building, and the leave flag."""
        return {**({"lodged_in_set": self.lodged_in_set} if self.lodged_in_set is not None else {}), **({"lodged_in_clear": True} if self.lodged_in_clear else {})}

    
@dataclass(frozen=True, slots=True)
class IdentityUpdate:
    """Updates to characteristics or knowledge."""
    role_set: Optional[int] = None
    faction_set: Optional[int] = None
    recipes_learned: list[str] = field(default_factory=list)
    craft_target: Optional[str] = None
    evolution_level_set: Optional[int] = None
    life_stage_set: Optional[LifeStage] = None
    class_id_set: Optional[str] = None
    evolution_points_delta: int = 0
    veterancy_points_delta: int = 0
    breakthroughs_add: list[str] = field(default_factory=list)
    unspent_ap_delta: int = 0
    unspent_ap_set: Optional[int] = None
    learned_skills: list[str] = field(default_factory=list)
    traits_add: list[str] = field(default_factory=list)
    traits_remove: list[str] = field(default_factory=list)
    cooldown_updates: Dict[str, int] = field(default_factory=dict) # skill_id -> tick_ready
    territory_maturity_delta: float = 0.0

    def is_noop(self) -> bool:
        return (self.role_set is None and self.faction_set is None and not self.recipes_learned and
                self.craft_target is None and self.evolution_level_set is None and
                self.life_stage_set is None and self.class_id_set is None and
                self.evolution_points_delta == 0 and self.veterancy_points_delta == 0 and
                not self.breakthroughs_add and self.unspent_ap_delta == 0 and
                self.unspent_ap_set is None and not self.learned_skills and
                not self.traits_add and not self.traits_remove and not self.cooldown_updates and
                self.territory_maturity_delta == 0.0)

    def merge(self, other: IdentityUpdate) -> IdentityUpdate:
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.role_set is not None: changes["role_set"] = other.role_set
        if other.faction_set is not None: changes["faction_set"] = other.faction_set
        if other.recipes_learned: changes["recipes_learned"] = sorted(set(self.recipes_learned + other.recipes_learned))
        if other.craft_target is not None: changes["craft_target"] = other.craft_target
        if other.evolution_level_set is not None: changes["evolution_level_set"] = other.evolution_level_set
        if other.life_stage_set is not None: changes["life_stage_set"] = other.life_stage_set
        if other.class_id_set is not None: changes["class_id_set"] = other.class_id_set
        if other.evolution_points_delta != 0: changes["evolution_points_delta"] = self.evolution_points_delta + other.evolution_points_delta
        if other.veterancy_points_delta != 0: changes["veterancy_points_delta"] = self.veterancy_points_delta + other.veterancy_points_delta
        if other.breakthroughs_add: changes["breakthroughs_add"] = sorted(set(self.breakthroughs_add + other.breakthroughs_add))
        if other.unspent_ap_delta != 0: changes["unspent_ap_delta"] = self.unspent_ap_delta + other.unspent_ap_delta
        if other.unspent_ap_set is not None: changes["unspent_ap_set"] = other.unspent_ap_set
        if other.learned_skills: changes["learned_skills"] = sorted(set(self.learned_skills + other.learned_skills))
        if other.traits_add: changes["traits_add"] = sorted(set(self.traits_add + other.traits_add))
        if other.traits_remove: changes["traits_remove"] = sorted(set(self.traits_remove + other.traits_remove))
        if other.cooldown_updates: changes["cooldown_updates"] = {**self.cooldown_updates, **other.cooldown_updates}
        if other.territory_maturity_delta != 0: changes["territory_maturity_delta"] = self.territory_maturity_delta + other.territory_maturity_delta
        return replace(self, **changes)


    
    


@dataclass(frozen=True, slots=True)
class StatusEffectUpdate:
    """New status effects and effect removal."""
    effects_add: List[StatusEffectState] = field(default_factory=list)
    effects_remove: List[str] = field(default_factory=list)  # status `kind` values to remove

    def is_noop(self) -> bool:
        """True when no status effect is added or removed."""
        return not self.effects_add and not self.effects_remove

    def merge(self, other: StatusEffectUpdate) -> StatusEffectUpdate:
        """Fold `other` in: the add and remove lists concatenate."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.effects_add: changes["effects_add"] = self.effects_add + other.effects_add
        if other.effects_remove: changes["effects_remove"] = self.effects_remove + other.effects_remove
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class EntityUpdate:
    """
    Authoritative update for a single entity.
    Logic ID: TOWN-001 (Action proposals are typed intents)
    Logic ID: TOWN-002 (Every side effect is represented as a typed update bucket)
    """
    entity_id: int
    kind_set: Optional[str] = None
    new_position: Optional[tuple[float, float]] = None
    moved_this_tick: bool = False
    readiness_delta: float = 0.0
    active: Optional[bool] = None
    interaction: Optional[InteractionUpdate] = None
    resource_transfers: List[ResourceTransferIntent] = field(default_factory=list)
    identity: Optional[IdentityUpdate] = None
    attributes: Optional[AttributeUpdate] = None
    inventory: Optional[InventoryUpdate] = None
    strategic: Optional[StrategicUpdate] = None
    biological: Optional[BiologicalUpdate] = None
    social: Optional[SocialUpdate] = None
    quest: Optional[QuestUpdate] = None
    reward: Optional[RewardUpdate] = None
    lifecycle: Optional[LifecycleUpdate] = None
    combat: Optional[CombatUpdate] = None
    equipment: Optional[EquipmentUpdate] = None
    navigation: Optional[NavigationUpdate] = None
    task: Optional[TaskUpdate] = None
    stamina_update: Optional[StaminaUpdate] = None
    wound_update: Optional[WoundUpdate] = None
    status_effect_update: Optional[StatusEffectUpdate] = None
    group_id_set: Optional[int] = None
    self_model_bundle_set: Optional[Any] = None
    cognition_bundle_set: Optional[Any] = None
    intent_results: List[IntentResult] = field(default_factory=list)
    property_updates: Dict[str, Any] = field(default_factory=dict)
    # TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE:
    # InformationBeliefPhase Branch B's routed self-model-query ActionIntent lives here now, never
    # in intent_results (typed for IntentResult only). InformationIntentExecutionPhase reads this
    # field directly; it is never merged toward entity.identity.latest_intent_results by any write
    # path, so a raw ActionIntent can no longer reach that IntentResult-typed durable field by
    # construction, regardless of whether InformationIntentExecutionPhase runs.
    pending_action_intent: Optional[ActionIntent] = None

    def is_noop(self) -> bool:
        return (self.kind_set is None and self.new_position is None and 
                not self.moved_this_tick and self.readiness_delta == 0.0 and 
                self.active is None and (self.interaction is None or self.interaction.is_noop()) and 
                not self.resource_transfers and (self.identity is None or self.identity.is_noop()) and 
                (self.attributes is None or self.attributes.is_noop()) and 
                (self.inventory is None or self.inventory.is_noop()) and 
                (self.strategic is None or self.strategic.is_noop()) and 
                (self.biological is None or self.biological.is_noop()) and 
                (self.social is None or self.social.is_noop()) and 
                (self.quest is None or self.quest.is_noop()) and 
                (self.reward is None or self.reward.is_noop()) and 
                (self.lifecycle is None or self.lifecycle.is_noop()) and 
                (self.combat is None or self.combat.is_noop()) and 
                (self.equipment is None or self.equipment.is_noop()) and 
                (self.navigation is None or self.navigation.is_noop()) and 
                (self.task is None or self.task.is_noop()) and 
                (self.stamina_update is None or self.stamina_update.is_noop()) and 
                (self.wound_update is None or self.wound_update.is_noop()) and
                (self.status_effect_update is None or self.status_effect_update.is_noop()) and
                self.group_id_set is None and self.self_model_bundle_set is None and
                self.cognition_bundle_set is None and not self.intent_results and
                self.pending_action_intent is None and
                not self.property_updates)

    def merge(self, other: EntityUpdate) -> EntityUpdate:
        """Merges another EntityUpdate into this one, summing deltas and preferring non-None sets."""
        if not other or other.is_noop():
            return self
        if self.entity_id != other.entity_id:
            raise ValueError("Cannot merge EntityUpdates for different entities")
            
        changes: Dict[str, Any] = {}
        if other.kind_set is not None: changes["kind_set"] = other.kind_set
        if other.new_position is not None: changes["new_position"] = other.new_position
        if other.moved_this_tick: changes["moved_this_tick"] = True
        if other.readiness_delta != 0.0: changes["readiness_delta"] = self.readiness_delta + other.readiness_delta
        if other.active is not None: changes["active"] = other.active
        if other.interaction: changes["interaction"] = self.interaction.merge(other.interaction) if self.interaction else other.interaction
        if other.resource_transfers: changes["resource_transfers"] = self.resource_transfers + other.resource_transfers
        if other.identity: changes["identity"] = self.identity.merge(other.identity) if self.identity else other.identity
        if other.attributes: changes["attributes"] = self.attributes.merge(other.attributes) if self.attributes else other.attributes
        if other.inventory: changes["inventory"] = self.inventory.merge(other.inventory) if self.inventory else other.inventory
        if other.strategic: changes["strategic"] = self.strategic.merge(other.strategic) if self.strategic else other.strategic
        if other.biological: changes["biological"] = self.biological.merge(other.biological) if self.biological else other.biological
        if other.social: changes["social"] = self.social.merge(other.social) if self.social else other.social
        if other.quest: changes["quest"] = self.quest.merge(other.quest) if self.quest else other.quest
        if other.reward: changes["reward"] = self.reward.merge(other.reward) if self.reward else other.reward
        if other.lifecycle: changes["lifecycle"] = self.lifecycle.merge(other.lifecycle) if self.lifecycle else other.lifecycle
        if other.combat: changes["combat"] = self.combat.merge(other.combat) if self.combat else other.combat
        if other.equipment: changes["equipment"] = self.equipment.merge(other.equipment) if self.equipment else other.equipment
        if other.navigation: changes["navigation"] = self.navigation.merge(other.navigation) if self.navigation else other.navigation
        if other.task: changes["task"] = self.task.merge(other.task) if self.task else other.task
        if other.stamina_update: changes["stamina_update"] = self.stamina_update.merge(other.stamina_update) if self.stamina_update else other.stamina_update
        if other.wound_update: changes["wound_update"] = self.wound_update.merge(other.wound_update) if self.wound_update else other.wound_update
        if other.status_effect_update: changes["status_effect_update"] = self.status_effect_update.merge(other.status_effect_update) if self.status_effect_update else other.status_effect_update
        if other.group_id_set is not None: changes["group_id_set"] = other.group_id_set
        if other.self_model_bundle_set is not None: changes["self_model_bundle_set"] = other.self_model_bundle_set
        if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] = other.cognition_bundle_set
        if other.intent_results: changes["intent_results"] = self.intent_results + other.intent_results
        if other.pending_action_intent is not None: changes["pending_action_intent"] = other.pending_action_intent
        if other.property_updates: changes["property_updates"] = {**self.property_updates, **other.property_updates}
        return replace(self, **changes)


def _merged_spawn_sources(first: "StateUpdate", others: List["StateUpdate"]) -> Dict[int, SpawnSource]:
    """The union of the declared spawn sources of ``first`` and ``others``; two different sources for one id is a producer error, never a silent drop."""
    merged = dict(first.entity_spawn_sources)
    for other in others:
        for add_id, source in other.entity_spawn_sources.items():
            if merged.setdefault(add_id, source) != source:
                raise ValueError(f"entity {add_id} has two different declared spawn sources")
    return merged


@dataclass(frozen=True, slots=True)
class StateUpdate:
    """
    A collection of authoritative changes to be applied to the world state.
    VERIFIED v2: action_proposals_as_intents
    """
    entity_updates: Dict[int, EntityUpdate] = field(default_factory=dict)
    entities_add: List[EntityState] = field(default_factory=list)
    entity_spawn_sources: Dict[int, SpawnSource] = field(default_factory=dict)  # the declared source of an add, keyed by the added entity's id (M0 gate V8); an add with none is unsourced
    entities_remove: List[int] = field(default_factory=list)
    nodes_add: List[ResourceNodeState] = field(default_factory=list)
    node_updates: Dict[int, ResourceNodeUpdate] = field(default_factory=dict)
    ground_items_add_or_update: List[GroundItemState] = field(default_factory=list)
    ground_items_remove: List[int] = field(default_factory=list)
    item_instances_add_or_update: List[ItemInstance] = field(default_factory=list)
    item_instance_updates: Dict[int, ItemInstanceUpdate] = field(default_factory=dict)
    corpses_add_or_update: List[CorpseState] = field(default_factory=list)
    corpses_remove: List[int] = field(default_factory=list)
    owed_add_or_update: List[OwedRecord] = field(default_factory=list)
    owed_remove: List[str] = field(default_factory=list)
    scars_add_or_update: List[LocalScarState] = field(default_factory=list)
    scars_remove: List[int] = field(default_factory=list)
    chest_updates: Dict[int, ChestUpdate] = field(default_factory=dict)
    chest_add_or_update: List[ChestState] = field(default_factory=list)
    building_updates: Dict[int, BuildingUpdate] = field(default_factory=dict)
    camp_updates: Dict[str, CampUpdate] = field(default_factory=dict)
    world_updates: Dict[str, WorldUpdate] = field(default_factory=dict)
    resource_updates: Dict[str, float] = field(default_factory=dict)
    home_storage_updates: Dict[int, InventoryUpdate] = field(default_factory=dict) # Milestone 5
    groups_add_or_update: List[GroupRecord] = field(default_factory=list)  # in-place updates of existing groups
    groups_add: List[GroupRecord] = field(default_factory=list)  # new records; an id already taken is rejected at apply, never replaced
    next_group_id_set: Optional[int] = None
    groups_remove: List[int] = field(default_factory=list)
    maturity_set: Optional[int] = None
    last_calamity_tick_set: Optional[int] = None
    grief_drained_tick_set: Optional[int] = None
    rng_checkpoint: Any = None
    transaction_trace: List[str] = field(default_factory=list)
    rejections_delta: Dict[str, int] = field(default_factory=dict) # Rejection counters for this tick
    pressure_signals_set: Optional[Dict[str, float]] = None
    current_mode_set: Optional[RuntimeMode] = None
    current_policy_set: Optional[GovernorPolicy] = None
    rejection_events: List[RejectionEvent] = field(default_factory=list) # Detailed rejection audit
    processed_transaction_ids: List[str] = field(default_factory=list)
    next_node_id_set: Optional[int] = None
    next_entity_id_set: Optional[int] = None
    next_item_instance_id_set: Optional[int] = None
    dirty_set: Optional[DirtySet] = None
    force_full_scan: bool = False
    sub_phase_costs: Dict[str, float] = field(default_factory=dict)
    metric_counters: Dict[str, int] = field(default_factory=dict)
    world_events_add: List["WorldEvent"] = field(default_factory=list)
    quest_registry_add: List["QuestOpportunity"] = field(default_factory=list)
    quest_registry_remove: List[str] = field(default_factory=list)
    quest_status_updates: Dict[str, "QuestOpportunityStatus"] = field(default_factory=dict)
    quest_opportunity_reward_intents: List["QuestOpportunityRewardIntent"] = field(default_factory=list)
    # E42D: provider reliability updates keyed by entity_id
    information_providers_update: Dict[int, "InformationProviderState"] = field(default_factory=dict)
    # E53Aa: Faction durable-state mutation records
    faction_updates: List[FactionUpdate] = field(default_factory=list)
    # Idea 40/M4: Clan durable-state mutation records
    clan_updates: List[ClanUpdate] = field(default_factory=list)

    def is_noop(self) -> bool:
        """True if this update contains absolutely no changes."""
        return (not self.entity_updates and not self.entities_add and not self.entities_remove and
                not self.nodes_add and not self.node_updates and not self.ground_items_add_or_update and
                not self.ground_items_remove and not self.corpses_add_or_update and
                not self.corpses_remove and not self.owed_add_or_update and not self.owed_remove and not self.scars_add_or_update and
                not self.scars_remove and not self.chest_updates and
                not self.chest_add_or_update and not self.building_updates and
                not self.camp_updates and not self.world_updates and
                not self.resource_updates and not self.home_storage_updates and
                not self.groups_add_or_update and not self.groups_add and self.next_group_id_set is None and not self.groups_remove and
                self.maturity_set is None and self.last_calamity_tick_set is None and self.grief_drained_tick_set is None and
                self.rng_checkpoint is None and not self.transaction_trace and
                not self.rejections_delta and self.pressure_signals_set is None and
                self.current_mode_set is None and self.current_policy_set is None and
                not self.rejection_events and
                not self.processed_transaction_ids and self.next_node_id_set is None and
                self.next_entity_id_set is None and not self.force_full_scan and
                not self.sub_phase_costs and not self.metric_counters and
                not self.world_events_add and not self.quest_registry_add and
                not self.quest_registry_remove and not self.quest_status_updates and
                not self.quest_opportunity_reward_intents and
                not self.information_providers_update and
                not self.faction_updates and
                not self.clan_updates and
                not self.item_instances_add_or_update and
                not self.item_instance_updates and
                self.next_item_instance_id_set is None)
    def merge(self, other: StateUpdate) -> StateUpdate:
        """Merge another StateUpdate into this one."""
        if not other or other.is_noop():
            return self
        return self.merge_many([other])

    def merge_many(self, others: Iterable[StateUpdate]) -> StateUpdate:
        """
        Merge multiple updates into this one with minimal intermediate allocations.
        Logic ID: TOWN-204 (Batch merge optimization)
        """
        # Filter no-ops
        valid_others = [o for o in others if o and not o.is_noop()]
        if not valid_others:
            return self
        # 1. Merge dictionaries
        new_entity_updates = dict(self.entity_updates)
        new_world_updates = dict(self.world_updates)
        new_node_updates = dict(self.node_updates)
        new_building_updates = dict(self.building_updates)
        new_camp_updates = dict(self.camp_updates)
        new_chest_updates = dict(self.chest_updates)
        new_home_storage_updates = dict(self.home_storage_updates)
        new_rejections_delta = dict(self.rejections_delta)
        new_resource_updates = dict(self.resource_updates)

        # Non-dict collections
        new_entities_add = list(self.entities_add)
        new_entities_remove = set(self.entities_remove)
        new_nodes_add = list(self.nodes_add)
        group_fields = merge_group_fields(self, valid_others)
        new_ground_items_add_or_update = list(self.ground_items_add_or_update)
        new_ground_items_remove = set(self.ground_items_remove)
        new_item_instances_add_or_update = list(self.item_instances_add_or_update)
        new_corpses_add_or_update = list(self.corpses_add_or_update)
        new_corpses_remove = set(self.corpses_remove)
        new_owed_add_or_update = list(self.owed_add_or_update)
        new_owed_remove = set(self.owed_remove)
        new_chest_add_or_update = list(self.chest_add_or_update)
        new_scars_add_or_update = list(self.scars_add_or_update)
        new_scars_remove = set(self.scars_remove)
        new_trace = list(self.transaction_trace)
        new_processed_ids = set(self.processed_transaction_ids)
        new_rejection_events = list(self.rejection_events)
        new_world_events_add = list(self.world_events_add)
        new_quest_registry_add = list(self.quest_registry_add)
        new_quest_registry_remove = list(self.quest_registry_remove)
        new_quest_status_updates = dict(self.quest_status_updates)
        new_quest_opportunity_reward_intents = list(self.quest_opportunity_reward_intents)
        new_information_providers_update = dict(self.information_providers_update)
        new_faction_updates = list(self.faction_updates)
        new_clan_updates = list(self.clan_updates)
        new_item_instance_updates = dict(self.item_instance_updates)

        # Single values
        maturity = self.maturity_set
        calamity = self.last_calamity_tick_set
        grief_drained = self.grief_drained_tick_set
        node_id = self.next_node_id_set
        ent_id = self.next_entity_id_set
        item_inst_id = self.next_item_instance_id_set
        rng = self.rng_checkpoint
        pressure = self.pressure_signals_set
        mode = self.current_mode_set
        policy = self.current_policy_set
        dirty = self.dirty_set
        sub_costs = dict(self.sub_phase_costs)

        new_metric_counters = dict(self.metric_counters)

        for other in valid_others:
            # Dictionaries
            for e_id, upd in other.entity_updates.items():
                new_entity_updates[e_id] = new_entity_updates[e_id].merge(upd) if e_id in new_entity_updates else upd
            for r_id, upd in other.world_updates.items():
                new_world_updates[r_id] = new_world_updates[r_id].merge(upd) if r_id in new_world_updates else upd
            for n_id, upd in other.node_updates.items():
                new_node_updates[n_id] = new_node_updates[n_id].merge(upd) if n_id in new_node_updates else upd
            for b_id, upd in other.building_updates.items():
                new_building_updates[b_id] = new_building_updates[b_id].merge(upd) if b_id in new_building_updates else upd
            for c_id, upd in other.camp_updates.items():
                new_camp_updates[c_id] = new_camp_updates[c_id].merge(upd) if c_id in new_camp_updates else upd
            for ch_id, upd in other.chest_updates.items():
                new_chest_updates[ch_id] = new_chest_updates[ch_id].merge(upd) if ch_id in new_chest_updates else upd
            for s_id, upd in other.home_storage_updates.items():
                new_home_storage_updates[s_id] = new_home_storage_updates[s_id].merge(upd) if s_id in new_home_storage_updates else upd
            for k, v in other.rejections_delta.items():
                new_rejections_delta[k] = new_rejections_delta.get(k, 0) + v
            for k, v in other.resource_updates.items():
                new_resource_updates[k] = new_resource_updates.get(k, 0.0) + v
            if other.metric_counters:
                for k, v in other.metric_counters.items():
                    new_metric_counters[k] = new_metric_counters.get(k, 0) + v

            # Lists / Sets
            new_entities_add.extend(other.entities_add)
            new_entities_remove.update(other.entities_remove)
            new_nodes_add.extend(other.nodes_add)
            new_ground_items_add_or_update.extend(other.ground_items_add_or_update)
            new_ground_items_remove.update(other.ground_items_remove)
            new_item_instances_add_or_update.extend(other.item_instances_add_or_update)
            new_corpses_add_or_update.extend(other.corpses_add_or_update)
            new_corpses_remove.update(other.corpses_remove)
            new_owed_add_or_update.extend(other.owed_add_or_update)
            new_owed_remove.update(other.owed_remove)
            new_chest_add_or_update.extend(other.chest_add_or_update)
            new_scars_add_or_update.extend(other.scars_add_or_update)
            new_scars_remove.update(other.scars_remove)
            new_trace.extend(other.transaction_trace)
            new_processed_ids.update(other.processed_transaction_ids)
            new_rejection_events.extend(other.rejection_events)
            new_world_events_add.extend(other.world_events_add)
            new_quest_registry_add.extend(other.quest_registry_add)
            new_quest_registry_remove.extend(other.quest_registry_remove)
            new_quest_status_updates.update(other.quest_status_updates)
            new_quest_opportunity_reward_intents.extend(other.quest_opportunity_reward_intents)
            new_information_providers_update.update(other.information_providers_update)
            new_faction_updates.extend(
                fu for fu in other.faction_updates if not fu.is_noop()
            )
            new_clan_updates.extend(
                cu for cu in other.clan_updates if not cu.is_noop()
            )
            for iid, upd in other.item_instance_updates.items():
                new_item_instance_updates[iid] = upd

            # Single values
            if other.maturity_set is not None: maturity = other.maturity_set
            if other.last_calamity_tick_set is not None: calamity = other.last_calamity_tick_set
            if other.grief_drained_tick_set is not None: grief_drained = other.grief_drained_tick_set
            if other.next_node_id_set is not None: node_id = other.next_node_id_set
            if other.next_entity_id_set is not None: ent_id = other.next_entity_id_set
            if other.next_item_instance_id_set is not None: item_inst_id = other.next_item_instance_id_set
            if other.rng_checkpoint: rng = other.rng_checkpoint
            if other.pressure_signals_set is not None: pressure = other.pressure_signals_set
            if other.current_mode_set is not None: mode = other.current_mode_set
            if other.current_policy_set is not None: policy = other.current_policy_set
            if other.dirty_set: dirty = dirty.merge(other.dirty_set) if dirty else other.dirty_set
            if other.sub_phase_costs:
                for k, v in other.sub_phase_costs.items():
                    sub_costs[k] = sub_costs.get(k, 0.0) + v

        return replace(self,
            entity_updates=new_entity_updates,
            world_updates=new_world_updates,
            node_updates=new_node_updates,
            building_updates=new_building_updates,
            camp_updates=new_camp_updates,
            chest_updates=new_chest_updates,
            home_storage_updates=new_home_storage_updates,
            rejections_delta=new_rejections_delta,
            resource_updates=new_resource_updates,
            entities_add=new_entities_add,
            entity_spawn_sources=_merged_spawn_sources(self, valid_others),
            entities_remove=list(new_entities_remove),
            nodes_add=new_nodes_add,
            **group_fields,
            ground_items_add_or_update=new_ground_items_add_or_update,
            ground_items_remove=list(new_ground_items_remove),
            corpses_add_or_update=new_corpses_add_or_update,
            corpses_remove=list(new_corpses_remove),
            owed_add_or_update=new_owed_add_or_update,
            owed_remove=sorted(new_owed_remove),
            chest_add_or_update=new_chest_add_or_update,
            scars_add_or_update=new_scars_add_or_update,
            scars_remove=list(new_scars_remove),
            transaction_trace=new_trace,
            rejection_events=new_rejection_events,
            processed_transaction_ids=list(new_processed_ids),
            maturity_set=maturity,
            last_calamity_tick_set=calamity,
            grief_drained_tick_set=grief_drained,
            next_node_id_set=node_id,
            next_entity_id_set=ent_id,
            rng_checkpoint=rng,
            pressure_signals_set=pressure,
            current_mode_set=mode,
            current_policy_set=policy,
            dirty_set=dirty,
            sub_phase_costs=sub_costs,
            metric_counters=new_metric_counters,
            world_events_add=new_world_events_add,
            quest_registry_add=new_quest_registry_add,
            quest_registry_remove=new_quest_registry_remove,
            quest_status_updates=new_quest_status_updates,
            quest_opportunity_reward_intents=new_quest_opportunity_reward_intents,
            information_providers_update=new_information_providers_update,
            faction_updates=new_faction_updates,
            clan_updates=new_clan_updates,
            item_instances_add_or_update=new_item_instances_add_or_update,
            item_instance_updates=new_item_instance_updates,
            next_item_instance_id_set=item_inst_id,
        )

    def compact(self) -> StateUpdate:
        """Remove no-op entity updates to reduce processing overhead."""
        compacted_entity_updates = {
            e_id: upd for e_id, upd in self.entity_updates.items()
            if not upd.is_noop()
        }
        if len(compacted_entity_updates) == len(self.entity_updates):
            return self
        return replace(self, entity_updates=compacted_entity_updates)
    
    def replace(self, **kwargs) -> StateUpdate:
        return replace(self, **kwargs)

# Logic ID: CORE-PERF-018 (Singleton for no-op entity updates)
EMPTY_ENTITY_UPDATE = EntityUpdate(entity_id=-1)
