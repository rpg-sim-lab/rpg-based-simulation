"""Combat-side update records: combat intents, damage, equipment, wounds, stamina and status effects."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.update_models.resources import ResourceTransferIntent
from src.core.update_models.social import SocialUpdate
from src.core.update_models.strategic import StrategicUpdate

if TYPE_CHECKING:
    from src.core.state import EquipSlot, ScarState, StatusEffectState, WoundState


@dataclass(frozen=True, slots=True)
class CombatIntent:
    """A single combat interaction intent within a tick."""
    attacker_id: int
    damage: int
    is_opportunity_attack: bool = False
    is_lethal: bool = True
    splash_radius: int = 0
    splash_damage: int = 0
    impact_pos: Optional[tuple[float, float]] = None


@dataclass(frozen=True, slots=True)
class EquipmentUpdate:
    """Updates to equipped items."""
    slot_updates: Dict[EquipSlot, str | None] = field(default_factory=dict)
    durability_delta: Dict[EquipSlot, float] = field(default_factory=dict)
    durability_set: Dict[EquipSlot, float] = field(default_factory=dict)

    def is_noop(self) -> bool:
        """True when no slot change and no durability change is staged."""
        return not self.slot_updates and not self.durability_delta and not self.durability_set

    def merge(self, other: EquipmentUpdate) -> EquipmentUpdate:
        """Merge another EquipmentUpdate into this one."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.slot_updates:
            changes["slot_updates"] = {**self.slot_updates, **other.slot_updates}
        if other.durability_delta:
            new_deltas = dict(self.durability_delta)
            for s, d in other.durability_delta.items():
                new_deltas[s] = new_deltas.get(s, 0.0) + d
            changes["durability_delta"] = new_deltas
        if other.durability_set:
            changes["durability_set"] = {**self.durability_set, **other.durability_set}
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class CombatUpdate:
    """Authoritative combat interaction results."""
    damage_taken: int = 0
    hp_delta: int = 0
    attacker_id: Optional[int] = None
    hit_tick_set: Optional[int] = None  # the tick a damaging hit took hp; CombatPatch writes it to CombatComponent.last_hit_tick with attacker_id
    hit_damage_set: Optional[int] = None  # the damage of that same hit; CombatPatch writes it to CombatComponent.last_hit_damage with attacker_id
    is_opportunity_attack: bool = False
    alive_set: Optional[bool] = None
    # Regional hazard drain applied this tick, carried independently of `outcome_kind` so a hazard that lands on an entity combat already resolved stays
    # observable (hazard_drain_applied) without overwriting the combat outcome. Not a death cause; see Mechanics Bible 01 §4.
    hazard_damage: int = 0
    outcome_kind: str = "SURVIVE" # SURVIVE, DEFEAT, KILL, REJECTED
    is_lethal: bool = False
    failure_reason: Optional[str] = None
    max_hp_delta: int = 0
    permanent_max_hp_bonus_delta: int = 0 # Durable grant accumulator (CombatComponent.permanent_max_hp_bonus)
    atk_delta: int = 0
    def_delta: int = 0
    speed_delta: int = 0
    simultaneous_intents: List[CombatIntent] = field(default_factory=list)
    resource_transfers: List[ResourceTransferIntent] = field(default_factory=list)
    equipment_upd: Optional[EquipmentUpdate] = None # For defender
    attacker_equipment_upd: Optional[EquipmentUpdate] = None
    wound_update: Optional[WoundUpdate] = None
    social_upd: Optional[SocialUpdate] = None
    strategic_upd: Optional[StrategicUpdate] = None
    trace: Dict[str, float] = field(default_factory=dict) # Breakdown of modifiers

    def is_noop(self) -> bool:
        """True when no damage, hp, stat, hazard, intent or resource-transfer change is staged."""
        return (self.damage_taken == 0 and self.hp_delta == 0 and self.attacker_id is None and 
                self.alive_set is None and self.hazard_damage == 0 and self.max_hp_delta == 0 and self.permanent_max_hp_bonus_delta == 0 and self.atk_delta == 0 and 
                self.def_delta == 0 and self.speed_delta == 0 and 
                not self.simultaneous_intents and not self.resource_transfers)

    def merge(self, other: CombatUpdate) -> CombatUpdate:
        """Merges another CombatUpdate into this one, aggregating results."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.damage_taken != 0: changes["damage_taken"] = self.damage_taken + other.damage_taken
        if other.hp_delta != 0: changes["hp_delta"] = self.hp_delta + other.hp_delta
        if other.attacker_id is not None: changes.update(attacker_id=other.attacker_id, hit_tick_set=self.hit_tick_set if other.hit_tick_set is None else other.hit_tick_set, hit_damage_set=self.hit_damage_set if other.hit_damage_set is None else other.hit_damage_set)
        if other.is_opportunity_attack: changes["is_opportunity_attack"] = True
        if other.alive_set is not None: changes["alive_set"] = other.alive_set
        if other.hazard_damage != 0: changes["hazard_damage"] = self.hazard_damage + other.hazard_damage
        if other.outcome_kind != "SURVIVE":
             changes["outcome_kind"] = other.outcome_kind if (self.outcome_kind == "SURVIVE" or other.outcome_kind == "KILL") else self.outcome_kind
        if other.is_lethal: changes["is_lethal"] = True
        if other.max_hp_delta != 0: changes["max_hp_delta"] = self.max_hp_delta + other.max_hp_delta
        if other.permanent_max_hp_bonus_delta != 0: changes["permanent_max_hp_bonus_delta"] = self.permanent_max_hp_bonus_delta + other.permanent_max_hp_bonus_delta
        if other.atk_delta != 0: changes["atk_delta"] = self.atk_delta + other.atk_delta
        if other.def_delta != 0: changes["def_delta"] = self.def_delta + other.def_delta
        if other.speed_delta != 0: changes["speed_delta"] = self.speed_delta + other.speed_delta
        if other.simultaneous_intents: changes["simultaneous_intents"] = self.simultaneous_intents + other.simultaneous_intents
        if other.resource_transfers: changes["resource_transfers"] = self.resource_transfers + other.resource_transfers
        if other.equipment_upd: changes["equipment_upd"] = other.equipment_upd
        if other.attacker_equipment_upd: changes["attacker_equipment_upd"] = other.attacker_equipment_upd
        if other.wound_update: changes["wound_update"] = other.wound_update
        if other.social_upd: changes["social_upd"] = self.social_upd.merge(other.social_upd) if self.social_upd else other.social_upd
        if other.strategic_upd: changes["strategic_upd"] = self.strategic_upd.merge(other.strategic_upd) if self.strategic_upd else other.strategic_upd
        if other.trace: changes["trace"] = {**self.trace, **other.trace}
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class WoundUpdate:
    """New wounds and scar transitions."""
    wounds_add: List[WoundState] = field(default_factory=list)
    wounds_heal: List[str] = field(default_factory=list)  # wound IDs to heal
    scars_add: List[ScarState] = field(default_factory=list)

    def is_noop(self) -> bool:
        """True when no wound is added or healed and no scar is added."""
        return not self.wounds_add and not self.wounds_heal and not self.scars_add

    def merge(self, other: WoundUpdate) -> WoundUpdate:
        """Fold `other` in: the wound and scar lists concatenate."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.wounds_add: changes["wounds_add"] = self.wounds_add + other.wounds_add
        if other.wounds_heal: changes["wounds_heal"] = self.wounds_heal + other.wounds_heal
        if other.scars_add: changes["scars_add"] = self.scars_add + other.scars_add
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class StaminaUpdate:
    """Updates to stamina resource."""
    current_delta: float = 0.0
    current_set: Optional[float] = None
    max_stamina_set: Optional[float] = None

    def is_noop(self) -> bool:
        """True when no stamina delta, current value or maximum is staged."""
        return self.current_delta == 0.0 and self.current_set is None and self.max_stamina_set is None

    def merge(self, other: StaminaUpdate) -> StaminaUpdate:
        """Fold `other` in: the current delta adds, a staged current or maximum from `other` wins."""
        if not other or other.is_noop():
            return self
        changes: Dict[str, Any] = {}
        if other.current_delta != 0.0: changes["current_delta"] = self.current_delta + other.current_delta
        if other.current_set is not None: changes["current_set"] = other.current_set
        if other.max_stamina_set is not None: changes["max_stamina_set"] = other.max_stamina_set
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
