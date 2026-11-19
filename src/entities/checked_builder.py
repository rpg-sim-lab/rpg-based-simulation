"""The one checked start of a body build for the campaign rebuild and the scenario runner (PERC-02a, STRAT-352).

``species_builder`` refuses a body whose species is in content but has no usable sense profile (``SenseProfileError`` naming the site), then returns the generic ``V2EntityBuilder`` with the species set.
``V2EntityBuilder`` itself is not hooked (rpg-designer): test fixtures that deliberately build unprofiled kinds keep using it directly."""
from __future__ import annotations

from src.content.species_senses import refuse_unprofiled_known_species
from src.core.builder import V2EntityBuilder


def species_builder(entity_id: int, species_id: str, where: str) -> V2EntityBuilder:
    """A ``V2EntityBuilder`` of `entity_id` with its species set, after refusing a species in content with no usable sense profile (``SenseProfileError`` naming `where`)."""
    refuse_unprofiled_known_species(species_id, where)
    return V2EntityBuilder(entity_id).kind(species_id)
