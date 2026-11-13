"""Body-side update records: interaction, task, biological, attribute, lifecycle and reward updates."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional

from src.core.death_cause import DeathRecord
from src.systems.lifecycle_systems.genetics import GeneticProfile


@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False
    kind: Optional[str] = None

    def is_noop(self) -> bool:
        """True when no interaction target, progress, reset or kind is staged."""
        return self.target_node_id is None and self.progress_delta == 0.0 and not self.reset and self.kind is None

    def merge(self, other: InteractionUpdate) -> InteractionUpdate:
        """Fold `other` in: its target and kind replace this one's, progress adds, a reset sticks."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.target_node_id is not None: changes["target_node_id"] = other.target_node_id
        if other.progress_delta != 0.0: changes["progress_delta"] = self.progress_delta + other.progress_delta
        if other.reset: changes["reset"] = True
        if other.kind is not None: changes["kind"] = other.kind
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class TaskUpdate:
    """Updates to next-tick work intent."""
    work_kind_set: Optional[str] = None
    payload_set: Optional[Dict[str, Any]] = None

    def is_noop(self) -> bool:
        """True when neither a work kind nor a payload is staged."""
        return self.work_kind_set is None and not self.payload_set

    def merge(self, other: TaskUpdate) -> TaskUpdate:
        """Fold `other` in: its work kind replaces this one's, its payload entries overlay this payload."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.work_kind_set is not None: changes["work_kind_set"] = other.work_kind_set
        if other.payload_set:
            new_payload = dict(self.payload_set or {})
            new_payload.update(other.payload_set)
            changes["payload_set"] = new_payload
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class BiologicalUpdate:
    """Updates to sleep, hunger, and biological pressures."""
    sleep_debt_delta: float = 0.0
    sleep_debt_set: Optional[float] = None
    hunger_delta: float = 0.0
    hunger_set: Optional[float] = None
    rest_pressure_delta: float = 0.0
    last_meal_tick_set: Optional[int] = None
    last_sleep_tick_set: Optional[int] = None
    well_rested_until_set: Optional[int] = None
    
    def is_noop(self) -> bool:
        """True when no hunger, sleep, rest or meal/sleep-tick change is staged."""
        return (self.sleep_debt_delta == 0.0 and self.sleep_debt_set is None and 
                self.hunger_delta == 0.0 and self.hunger_set is None and 
                self.rest_pressure_delta == 0.0 and self.last_meal_tick_set is None and 
                self.last_sleep_tick_set is None and self.well_rested_until_set is None)

    def merge(self, other: BiologicalUpdate) -> BiologicalUpdate:
        """Fold `other` in: deltas add, a staged `*_set` value from `other` wins over this one's."""
        if not other or other.is_noop():
            return self
        return BiologicalUpdate(
            sleep_debt_delta=self.sleep_debt_delta + other.sleep_debt_delta,
            sleep_debt_set=other.sleep_debt_set if other.sleep_debt_set is not None else self.sleep_debt_set,
            hunger_delta=self.hunger_delta + other.hunger_delta,
            hunger_set=other.hunger_set if other.hunger_set is not None else self.hunger_set,
            rest_pressure_delta=self.rest_pressure_delta + other.rest_pressure_delta,
            last_meal_tick_set=other.last_meal_tick_set if other.last_meal_tick_set is not None else self.last_meal_tick_set,
            last_sleep_tick_set=other.last_sleep_tick_set if other.last_sleep_tick_set is not None else self.last_sleep_tick_set,
            well_rested_until_set=other.well_rested_until_set if other.well_rested_until_set is not None else self.well_rested_until_set
        )


@dataclass(frozen=True, slots=True)
class AttributeUpdate:
    """Updates to base attributes."""
    strength_delta: int = 0
    agility_delta: int = 0
    vitality_delta: int = 0
    endurance_delta: int = 0
    intelligence_delta: int = 0
    spirit_delta: int = 0
    wisdom_delta: int = 0
    perception_delta: int = 0
    charisma_delta: int = 0
    
    def is_noop(self) -> bool:
        """True when every attribute delta is zero."""
        return (self.strength_delta == 0 and self.agility_delta == 0 and self.vitality_delta == 0 and 
                self.endurance_delta == 0 and self.intelligence_delta == 0 and 
                self.spirit_delta == 0 and self.wisdom_delta == 0 and 
                self.perception_delta == 0 and self.charisma_delta == 0)

    def merge(self, other: AttributeUpdate) -> AttributeUpdate:
        """Fold `other` in: each attribute delta adds."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.strength_delta != 0: changes["strength_delta"] = self.strength_delta + other.strength_delta
        if other.agility_delta != 0: changes["agility_delta"] = self.agility_delta + other.agility_delta
        if other.vitality_delta != 0: changes["vitality_delta"] = self.vitality_delta + other.vitality_delta
        if other.endurance_delta != 0: changes["endurance_delta"] = self.endurance_delta + other.endurance_delta
        if other.intelligence_delta != 0: changes["intelligence_delta"] = self.intelligence_delta + other.intelligence_delta
        if other.spirit_delta != 0: changes["spirit_delta"] = self.spirit_delta + other.spirit_delta
        if other.wisdom_delta != 0: changes["wisdom_delta"] = self.wisdom_delta + other.wisdom_delta
        if other.perception_delta != 0: changes["perception_delta"] = self.perception_delta + other.perception_delta
        if other.charisma_delta != 0: changes["charisma_delta"] = self.charisma_delta + other.charisma_delta
        return replace(self, **changes)


# The scalar fields a later update overwrites (a None leaves the earlier value); the list and dict fields accumulate.
_LIFECYCLE_SET_FIELDS = ("is_permadeath_set", "death_tick_set", "death_reason_set", "death_record_set", "heir_entity_id_set", "parent_a_entity_id_set",
                         "parent_b_entity_id_set", "birth_tick_set", "birth_city_id_set", "genetic_profile_set")


@dataclass(frozen=True, slots=True)
class LifecycleUpdate:
    """Updates to aging and death mechanics."""
    age_delta: int = 0
    is_permadeath_set: Optional[bool] = None
    death_tick_set: Optional[int] = None
    death_reason_set: Optional[str] = None
    death_record_set: Optional[DeathRecord] = None
    heir_entity_id_set: Optional[int] = None
    heirlooms_add: list[str] = field(default_factory=list)
    parent_a_entity_id_set: Optional[int] = None
    parent_b_entity_id_set: Optional[int] = None
    dependent_entity_ids_add: list[int] = field(default_factory=list)
    birth_tick_set: Optional[int] = None
    birth_city_id_set: Optional[int] = None
    reproduction_cooldowns_add: Dict[int, int] = field(default_factory=dict)  # per-key upsert, NOT wholesale replace
    genetic_profile_set: Optional[GeneticProfile] = None

    def is_noop(self) -> bool:
        """True when no age, death, heir, parent, birth, heirloom, dependent, cooldown or genetics change is staged."""
        return (self.age_delta == 0 and
                self.is_permadeath_set is None and self.death_tick_set is None and
                self.death_reason_set is None and self.death_record_set is None and self.heir_entity_id_set is None and
                not self.heirlooms_add and self.parent_a_entity_id_set is None and
                self.parent_b_entity_id_set is None and not self.dependent_entity_ids_add and
                self.birth_tick_set is None and
                self.birth_city_id_set is None and not self.reproduction_cooldowns_add and
                self.genetic_profile_set is None)

    def merge(self, other: LifecycleUpdate) -> LifecycleUpdate:
        """Fold `other` in: age adds, `*_add` lists concatenate, a staged `*_set` value from `other` wins."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.age_delta != 0: changes["age_delta"] = self.age_delta + other.age_delta
        changes.update({name: getattr(other, name) for name in _LIFECYCLE_SET_FIELDS if getattr(other, name) is not None})
        if other.heirlooms_add: changes["heirlooms_add"] = self.heirlooms_add + other.heirlooms_add
        if other.dependent_entity_ids_add: changes["dependent_entity_ids_add"] = self.dependent_entity_ids_add + other.dependent_entity_ids_add
        if other.reproduction_cooldowns_add:
            changes["reproduction_cooldowns_add"] = {**self.reproduction_cooldowns_add, **other.reproduction_cooldowns_add}
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class RewardUpdate:
    """
    Non-inventory progression rewards (XP, evolution points).
    Authority: Allowed from workers for pure progression, but verified by ApplyGate.
    Law: Gold and Items must use ResourceTransferIntent for authoritative conservation.
    """
    xp_gain: int = 0
    evolution_points_delta: int = 0
    
    def is_noop(self) -> bool:
        """True when neither XP nor evolution points are staged."""
        return self.xp_gain == 0 and self.evolution_points_delta == 0

    def merge(self, other: RewardUpdate) -> RewardUpdate:
        """Fold `other` in: XP and evolution-point deltas add."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.xp_gain != 0: changes["xp_gain"] = self.xp_gain + other.xp_gain
        if other.evolution_points_delta != 0: changes["evolution_points_delta"] = self.evolution_points_delta + other.evolution_points_delta
        return replace(self, **changes)
