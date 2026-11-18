"""The one place a species' sense profile is resolved (PERC-02): ``catalog.species[species_id].sense_profile``.

The perception gate reads it at every check and the compile, spawn and archetype build paths call it to refuse a body early, so a build can never pass while the gate would fall back
to a baseline. Content layer: it reads the catalog only, so every layer that builds a body may import it."""
from __future__ import annotations

from typing import Any, Optional

from src.content.common_knowledge_seed import warmed_catalog
from src.content.sense_resolution import species_sense_profile
from src.core.species import SenseProfileError

__all__ = ["require_species_sense_profile", "species_sense_profile"]


def require_species_sense_profile(species_id: Optional[str], where: str, catalog: Optional[Any] = None) -> Any:
    """Refuse a body built on the compile, spawn or archetype path whose species is missing from content or has no usable sense profile (``SenseProfileError``).

    `catalog` defaults to the warmed catalog, the one the gate reads."""
    cat = warmed_catalog() if catalog is None else catalog
    defn = species_sense_profile(cat, species_id) if species_id else None
    if defn is None:
        raise SenseProfileError(f"{where}: species {species_id!r} is not in content or has no usable sense profile")
    return defn
