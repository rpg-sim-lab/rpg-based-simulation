"""The species of a hero spawn (M1 step 4): read from the named archetype `adventurer_hero` (key `species`), never chosen by code.

Lives in src.content so that both the generator (src.systems) and the campaign runner (src.domains) can import it under the registry layer order.
"""
from __future__ import annotations

from src.content.common_knowledge_seed import warmed_catalog
from src.core.species import SpeciesNotDeclaredError


def hero_species_id() -> str:
    """The species of a hero spawn, read from the named archetype `adventurer_hero` (key `species`); never chosen by code (M1 step 4)."""
    archetype = warmed_catalog().get_entity_archetype("adventurer_hero")
    species = archetype.species if archetype is not None else None
    if not isinstance(species, str) or not species:
        raise SpeciesNotDeclaredError("the archetype 'adventurer_hero' declares no species, so a hero spawn has none to write")
    return species
