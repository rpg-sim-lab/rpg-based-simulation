# Compliance IDs: WORLD-118, WORLD-119
# src/world/creature_territory.py
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate
from src.core.enums import EntityRole

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.world_systems.generator import EntityGenerator


class CreatureTerritoryService:
    """
    Manages territory maturity for monster-kind entities anchored (by proximity) to a camp.

    Mirrors CampService's trauma-scaled maturity shape (src/world/camp.py) for a per-entity
    concept instead of a per-camp one -- a parallel service, not a shared refactor, per this
    ticket's explicit Out of Scope.
    """

    TERRITORY_MATURITY_RATES: Dict[str, float] = {
        "goblin_warrior": 0.04,
        "orc_warrior": 0.03,
    }
    DEFAULT_TERRITORY_MATURITY_RATE: float = 0.03
    TERRITORY_MATURITY_THRESHOLD: float = 100.0

    @staticmethod
    def maturity_rate(occupation: Optional[str]) -> float:
        """The maturity rate of a creature by its occupation label (M1 step 3: the table is keyed by label); the default for a label with no row or none."""
        if occupation is None:
            return CreatureTerritoryService.DEFAULT_TERRITORY_MATURITY_RATE
        return CreatureTerritoryService.TERRITORY_MATURITY_RATES.get(occupation, CreatureTerritoryService.DEFAULT_TERRITORY_MATURITY_RATE)

    @staticmethod
    def process_territories(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        entity_updates: Dict[int, EntityUpdate] = {}
        entities_add = []

        from src.engine.legality import LegalityServiceV2

        for camp in state.camps.values():
            if not camp.active:
                continue

            region = LegalityServiceV2.get_region_for_position(camp.position, state)
            trauma_multiplier = 1.5 if region and region.trauma_score > 50.0 else 1.0

            anchored_monsters = [
                e for e in state.entities.values()
                if e.identity.role == EntityRole.MONSTER and e.combat.alive
                and abs(e.navigation.position[0] - camp.position[0]) < 10
                and abs(e.navigation.position[1] - camp.position[1]) < 10
            ]

            for entity in anchored_monsters:
                base_rate = CreatureTerritoryService.maturity_rate(entity.identity.occupation)
                delta = base_rate * trauma_multiplier
                current_maturity = entity.identity.territory_maturity
                new_maturity = current_maturity + delta

                if (new_maturity >= CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD
                        and current_maturity < CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD):
                    mob = generator.spawn_monster(
                        entity.navigation.position,
                        state=state,
                        species=entity.kind,
                        occupation=entity.identity.occupation,
                        difficulty_tier=1,
                    )
                    entities_add.append(mob)
                    # Reset overrides growth on the crossing tick -- brings post-apply
                    # maturity to exactly 0.0, not merely capped at the threshold.
                    delta = -current_maturity

                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    identity=IdentityUpdate(territory_maturity_delta=delta),
                )

        return StateUpdate(entity_updates=entity_updates, entities_add=entities_add)
