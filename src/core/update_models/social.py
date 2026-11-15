"""Social update records: the rejection event, bond update and per-tick SocialUpdate."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.enums import ReasonCode
from src.core.models.social import RelationshipRole
from src.core.social_counts import add_rejection_counts

if TYPE_CHECKING:
    from src.core.strategic import ContractState


@dataclass(frozen=True, slots=True)
class RejectionEvent:
    """
    Structured record of an authoritative rejection.
    Logic ID: RPG-AUTH-009
    """
    tick: int
    actor_id: int
    action_kind: str
    reason: ReasonCode
    target_id: Optional[int | str] = None


@dataclass(frozen=True, slots=True)
class SocialBondUpdate:
    """Updates to a first-class directed relationship record."""
    target_id: int
    familiarity_delta: float = 0.0
    sentiment_delta: float = 0.0
    last_interaction_tick_set: Optional[int] = None
    role_set: Optional[RelationshipRole] = None


@dataclass(frozen=True, slots=True)
class SocialUpdate:
    # PH15 Recovery: Bond updates
    """One tick's social changes for an entity: trust, familiarity, grudge, reputation and rejection increments."""
    bond_updates: List[SocialBondUpdate] = field(default_factory=list)
    trust_delta: Dict[int, float] = field(default_factory=dict)
    familiarity_delta: Dict[int, float] = field(default_factory=dict)
    debt_delta: Dict[int, float] = field(default_factory=dict)
    fear_delta: Dict[int, float] = field(default_factory=dict)
    grudge_delta: Dict[int, float] = field(default_factory=dict)
    salience_delta: Dict[int, float] = field(default_factory=dict)
    
    betrayal_increment: int = 0
    betrayal_records_add: List[Any] = field(default_factory=list) # List[BetrayalRecord]
    reputation_set: Optional[float] = None
    heroism_delta: float = 0.0
    notoriety_delta: float = 0.0
    
    # Domain 7 Hardening: Social Fatigue
    last_offer_tick_set: Optional[int] = None
    rejection_increment: Dict[int, int] = field(default_factory=dict) # SourceID -> Increment
    
    # Domain 4 Hardening
    nemesis_promotion: List[int] = field(default_factory=list) # EntityIDs to add to nemesis_ids
    place_attachment_delta: Dict[str, float] = field(default_factory=dict) # RegionID -> Delta
    regional_reputation_delta: Dict[str, float] = field(default_factory=dict) # RegionID -> Delta
    combat_loss_delta: Dict[int, int] = field(default_factory=dict) # EntityID -> +1 per defeat by that entity
    
    contracts_add: List[ContractState] = field(default_factory=list)
    contracts_remove: List[str] = field(default_factory=list) # IDs
    
    def is_noop(self) -> bool:
        """True when no social field (bond, trust, grudge, reputation, rejection and so on) is staged."""
        return (not self.bond_updates and not self.trust_delta and not self.familiarity_delta and 
                not self.debt_delta and not self.fear_delta and not self.grudge_delta and 
                not self.salience_delta and self.betrayal_increment == 0 and 
                not self.betrayal_records_add and self.reputation_set is None and 
                self.heroism_delta == 0.0 and self.notoriety_delta == 0.0 and 
                self.last_offer_tick_set is None and not self.rejection_increment and
                not self.nemesis_promotion and not self.place_attachment_delta and
                not self.regional_reputation_delta and
                not self.combat_loss_delta and not self.contracts_add and not self.contracts_remove)

    def merge(self, other: SocialUpdate) -> SocialUpdate:
        """Merges another SocialUpdate into this one."""
        if not other or other.is_noop():
            return self
        
        # Merge dictionaries by summing values
        new_trust = dict(self.trust_delta)
        for k, v in other.trust_delta.items():
            new_trust[k] = new_trust.get(k, 0.0) + v
            
        new_grudge = dict(self.grudge_delta)
        for k, v in other.grudge_delta.items():
            new_grudge[k] = new_grudge.get(k, 0.0) + v
            
        new_places = dict(self.place_attachment_delta)
        for region_id, v in other.place_attachment_delta.items():
            new_places[region_id] = new_places.get(region_id, 0.0) + v

        new_regional_rep = dict(self.regional_reputation_delta)
        for region_id, v in other.regional_reputation_delta.items():
            new_regional_rep[region_id] = new_regional_rep.get(region_id, 0.0) + v

        new_combat_loss = dict(self.combat_loss_delta)
        for k, v in other.combat_loss_delta.items():
            new_combat_loss[k] = new_combat_loss.get(k, 0) + v

        return SocialUpdate(
            bond_updates=self.bond_updates + other.bond_updates,
            trust_delta=new_trust,
            familiarity_delta={**self.familiarity_delta, **other.familiarity_delta},
            debt_delta={**self.debt_delta, **other.debt_delta},
            fear_delta={**self.fear_delta, **other.fear_delta},
            grudge_delta=new_grudge,
            salience_delta={**self.salience_delta, **other.salience_delta},
            betrayal_increment=self.betrayal_increment + other.betrayal_increment,
            betrayal_records_add=self.betrayal_records_add + other.betrayal_records_add,
            reputation_set=other.reputation_set if other.reputation_set is not None else self.reputation_set,
            heroism_delta=self.heroism_delta + other.heroism_delta,
            notoriety_delta=self.notoriety_delta + other.notoriety_delta,
            last_offer_tick_set=other.last_offer_tick_set if other.last_offer_tick_set is not None else self.last_offer_tick_set,
            rejection_increment=add_rejection_counts(self.rejection_increment, other.rejection_increment),
            nemesis_promotion=self.nemesis_promotion + other.nemesis_promotion,
            place_attachment_delta=new_places,
            regional_reputation_delta=new_regional_rep,
            combat_loss_delta=new_combat_loss,
            contracts_add=self.contracts_add + other.contracts_add,
            contracts_remove=self.contracts_remove + other.contracts_remove
        )
