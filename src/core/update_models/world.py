"""World-side update records: resource nodes, regions, chests, camps, factions and clans, and the owner-clear sentinel."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from src.core.enums import DiplomaticState

if TYPE_CHECKING:
    from src.core.state import ItemStack


@dataclass(frozen=True, slots=True)
class ResourceNodeUpdate:
    """Updates to a harvestable node."""
    node_id: int
    charges_delta: int = 0
    cooldown_set: Optional[int] = None

    def merge(self, other: ResourceNodeUpdate) -> ResourceNodeUpdate:
        """Fold `other` (same node) in: charges add, a staged cooldown from `other` wins; a different node raises ValueError."""
        if self.node_id != other.node_id:
            raise ValueError("Cannot merge ResourceNodeUpdates for different nodes")
        return replace(self,
            charges_delta=self.charges_delta + other.charges_delta,
            cooldown_set=other.cooldown_set if other.cooldown_set is not None else self.cooldown_set
        )


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    """Updates to regional world state."""
    region_id: str
    hazard_level_set: Optional[float] = None
    suppression_set: Optional[bool] = None
    calamity_intensity_set: Optional[float] = None
    trauma_delta: float = 0.0
    trauma_score_set: Optional[float] = None
    retaliation_pressure_delta: float = 0.0
    retaliation_pressure_set: Optional[float] = None
    influence_delta: float = 0.0
    owner_faction_id_set: Optional[int] = None
    kind_set: Optional[str] = None
    weather_set: Optional[str] = None
    modifiers_add: List[str] = field(default_factory=list)
    modifiers_remove: List[str] = field(default_factory=list)
    price_modifiers_set: Optional[Dict[str, float]] = None
    # E52A: Per-region demographic cohort state (Dict[bracket, PopulationCohort])
    population_cohorts_set: Optional[Dict[str, Any]] = None
    # TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE: coarse, additive-only nudge
    # applied on top of population_cohorts_set (never a resync) — see apply_plan.py.
    population_young_births_delta: int = 0
    # E53Cb: Siege mechanics
    service_availability_delta: float = 0.0
    siege_state_set: Optional[Any] = None   # Optional[SiegeState] — Any to avoid circular import
    siege_state_clear: bool = False          # True = remove existing siege_state (None is no-op sentinel)
    siege_progress_delta: float = 0.0

    def merge(self, other: WorldUpdate) -> WorldUpdate:
        """Merges another WorldUpdate into this one, summing deltas and preferring non-None sets."""
        if self.region_id != other.region_id:
            raise ValueError("Cannot merge WorldUpdates for different regions")

        return replace(self,
            hazard_level_set=other.hazard_level_set if other.hazard_level_set is not None else self.hazard_level_set,
            suppression_set=other.suppression_set if other.suppression_set is not None else self.suppression_set,
            calamity_intensity_set=other.calamity_intensity_set if other.calamity_intensity_set is not None else self.calamity_intensity_set,
            trauma_delta=self.trauma_delta + other.trauma_delta,
            trauma_score_set=other.trauma_score_set if other.trauma_score_set is not None else self.trauma_score_set,
            retaliation_pressure_delta=self.retaliation_pressure_delta + other.retaliation_pressure_delta,
            retaliation_pressure_set=other.retaliation_pressure_set if other.retaliation_pressure_set is not None else self.retaliation_pressure_set,
            influence_delta=self.influence_delta + other.influence_delta,
            owner_faction_id_set=other.owner_faction_id_set if other.owner_faction_id_set is not None else self.owner_faction_id_set,
            kind_set=other.kind_set if other.kind_set is not None else self.kind_set,
            weather_set=other.weather_set if other.weather_set is not None else self.weather_set,
            modifiers_add=sorted(set(self.modifiers_add + other.modifiers_add)),
            modifiers_remove=sorted(set(self.modifiers_remove + other.modifiers_remove)),
            price_modifiers_set=other.price_modifiers_set if other.price_modifiers_set is not None else self.price_modifiers_set,
            population_cohorts_set=other.population_cohorts_set if other.population_cohorts_set is not None else self.population_cohorts_set,
            population_young_births_delta=self.population_young_births_delta + other.population_young_births_delta,
            service_availability_delta=self.service_availability_delta + other.service_availability_delta,
            siege_state_set=other.siege_state_set if other.siege_state_set is not None else self.siege_state_set,
            siege_state_clear=self.siege_state_clear or other.siege_state_clear,
            siege_progress_delta=self.siege_progress_delta + other.siege_progress_delta,
        )


#: In-band sentinel meaning "set the region's owner to None (unowned)".
#: `owner_faction_id_set=None` already means "no change", so an explicit
#: clear-to-unowned cannot be expressed with None and needs its own value.
#: Always decode with `decode_owner_faction_id_set()` before the value reaches
#: durable state, an event payload, or a `Faction`-keyed lookup -- `-1` is not a
#: `Faction` member, so indexing by it raises KeyError
#: (TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW).
NO_OWNER_SENTINEL: int = -1


def decode_owner_faction_id_set(value: Optional[int]) -> Optional[int]:
    """Decode a staged `WorldUpdate.owner_faction_id_set` into a durable owner.

    Returns None both for "no change" and for the explicit unowned sentinel; callers
    distinguish the two by testing `value is None` first. Mirrors the established
    `group_id_set` idiom in `src/engine/patches.py`.
    """
    if value == NO_OWNER_SENTINEL:
        return None
    return value


@dataclass(frozen=True, slots=True)
class ChestUpdate:
    """Updates to a world chest."""
    chest_id: int
    cooldown_set: Optional[int] = None
    items_set: Optional[List[ItemStack]] = None

    def merge(self, other: ChestUpdate) -> ChestUpdate:
        """Fold `other` (same chest) in: a staged cooldown or item set from `other` wins; a different chest raises ValueError."""
        if self.chest_id != other.chest_id:
            raise ValueError("Cannot merge ChestUpdates for different chests")
        return replace(self,
            cooldown_set=other.cooldown_set if other.cooldown_set is not None else self.cooldown_set,
            items_set=other.items_set if other.items_set is not None else self.items_set
        )


@dataclass(frozen=True, slots=True)
class CampUpdate:
    """Updates to a persistent encampment."""
    id: str
    maturity_delta: float = 0.0
    active_set: Optional[bool] = None
    last_raid_tick_set: Optional[int] = None
    totem_tier_set: Optional[int] = None
    stockpile_delta: float = 0.0
    palisade_integrity_set: Optional[float] = None

    def merge(self, other: CampUpdate) -> CampUpdate:
        """Fold `other` (same camp) in: maturity and stockpile deltas add, staged `*_set` values from `other` win; a different camp raises ValueError."""
        if self.id != other.id:
            raise ValueError("Cannot merge CampUpdates for different camps")
        return replace(self,
            maturity_delta=self.maturity_delta + other.maturity_delta,
            active_set=other.active_set if other.active_set is not None else self.active_set,
            last_raid_tick_set=other.last_raid_tick_set if other.last_raid_tick_set is not None else self.last_raid_tick_set,
            stockpile_delta=self.stockpile_delta + other.stockpile_delta,
            totem_tier_set=other.totem_tier_set if other.totem_tier_set is not None else self.totem_tier_set,
            palisade_integrity_set=other.palisade_integrity_set if other.palisade_integrity_set is not None else self.palisade_integrity_set,
        )


@dataclass(frozen=True, slots=True)
class QuestOpportunityRewardIntent:
    """
    Signal that the named entity should receive the reward for the named
    QuestOpportunity.  The actual reward amounts are read from
    state.quest_registry[quest_id].reward_spec inside the enforce stage.
    """
    entity_id: int
    quest_id: str


@dataclass(frozen=True, slots=True)
class FactionUpdate:
    """Typed mutation record for a single faction's durable state (E53Aa)."""
    faction_id: str
    tension_delta: float = 0.0
    military_strength_set: Optional[float] = None
    territory_add: Tuple[str, ...] = ()
    territory_remove: Tuple[str, ...] = ()
    resources_delta: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations_set: Dict[str, DiplomaticState] = field(default_factory=dict)
    active_doctrines_set: Optional[Tuple[str, ...]] = None
    faction_sentiment_delta: Dict[str, float] = field(default_factory=dict)  # target_faction_id -> sentiment delta, from a real interaction (bumps last_interaction_tick)
    faction_familiarity_delta: Dict[str, float] = field(default_factory=dict)  # target_faction_id -> familiarity delta, from a real interaction (bumps last_interaction_tick)
    faction_sentiment_decay_set: Dict[str, float] = field(default_factory=dict)  # target_faction_id -> absolute post-decay sentiment value; does NOT bump last_interaction_tick (not a real interaction)
    pairwise_tension_delta: Dict[str, float] = field(default_factory=dict)  # target_faction_id -> tension delta scoped to THIS rival only (unlike tension_delta, which is ambient and applies broadly -- see FactionState.pairwise_tension)

    def is_noop(self) -> bool:
        """True when no tension, strength, territory, resource, diplomacy or doctrine change is staged."""
        return (
            self.tension_delta == 0.0
            and self.military_strength_set is None
            and not self.territory_add
            and not self.territory_remove
            and not self.resources_delta
            and not self.diplomatic_relations_set
            and self.active_doctrines_set is None
            and not self.faction_sentiment_delta
            and not self.faction_familiarity_delta
            and not self.faction_sentiment_decay_set
            and not self.pairwise_tension_delta
        )


@dataclass(frozen=True, slots=True)
class ClanUpdate:
    """Typed mutation record for a single clan's durable state (idea 40/M4)."""
    clan_id: str
    member_entity_ids_add: Tuple[int, ...] = ()
    member_entity_ids_remove: Tuple[int, ...] = ()
    leader_entity_id_set: Optional[int] = None
    dissolved_tick_set: Optional[int] = None
    clan_reputation_delta: float = 0.0

    def is_noop(self) -> bool:
        """True when no member change, leader, dissolution or reputation change is staged."""
        return (
            not self.member_entity_ids_add
            and not self.member_entity_ids_remove
            and self.leader_entity_id_set is None
            and self.dissolved_tick_set is None
            and self.clan_reputation_delta == 0.0
        )
