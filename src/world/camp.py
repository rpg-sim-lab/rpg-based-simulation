# Compliance IDs: WORLD-030, WORLD-031
# src/world/camp.py
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict
from src.core.updates import StateUpdate, CampUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.world_systems.generator import EntityGenerator

class CampService:
    """
    Manages persistent world encampments and their maturity.
    """

    MATURITY_PER_TICK = 0.05
    RAID_MATURITY_THRESHOLD = 80.0
    EXPAND_TERRITORY_MATURITY_BOOST = 1.0

    @staticmethod
    def process_camps(state: AuthoritativeState, generator: EntityGenerator, faction_directives: list | None = None) -> StateUpdate:
        """
        Evolve camps: maturity only. A camp spawns nothing (D70); its kind's population grows through BirthService, which reads no camp.
        """
        camp_updates: Dict[str, CampUpdate] = {}

        # 1. Maturity Evolution
        for c_id, camp in state.camps.items():
            if not camp.active:
                continue
                
            m_delta = CampService.MATURITY_PER_TICK
            
            # Rule: High regional trauma increases maturity faster
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(camp.position, state)
            if region and region.trauma_score > 50.0:
                m_delta *= 1.5
                
            camp_updates[c_id] = CampUpdate(id=c_id, maturity_delta=m_delta)

            # 1b. Faction EXPAND_TERRITORY consumption: a matching directive boosts maturity growth.
            if faction_directives and region is not None:
                from src.engine.faction_constants import EXPAND_TERRITORY
                for directive in faction_directives:
                    if getattr(directive, "directive_kind", None) == EXPAND_TERRITORY and directive.target_region == region.id:
                        existing = camp_updates[c_id]
                        camp_updates[c_id] = replace(
                            existing,
                            maturity_delta=existing.maturity_delta + CampService.EXPAND_TERRITORY_MATURITY_BOOST,
                        )
                        break

        return StateUpdate(camp_updates=camp_updates)

    @staticmethod
    def resolve_camp_clearing(state: AuthoritativeState, camp_id: str) -> StateUpdate:
        """
        Rule: Clearing a camp provides rewards and reduces threat.
        """
        camp = state.camps.get(camp_id)
        if not camp or not camp.active:
            return StateUpdate()
            
        camp_updates = {camp_id: CampUpdate(id=camp_id, active_set=False)}
        
        from src.engine.legality import LegalityServiceV2
        region = LegalityServiceV2.get_region_for_position(camp.position, state)
        if not region:
            return StateUpdate(camp_updates=camp_updates)
            
        from src.core.updates import WorldUpdate
        w_upd = WorldUpdate(
            region_id=region.id,
            trauma_delta=-10.0 # Reward for clearing
        )
        
        return StateUpdate(camp_updates=camp_updates, world_updates={region.id: w_upd})
