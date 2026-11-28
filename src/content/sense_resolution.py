"""The pure part of the species sense-profile resolver (PERC-02), kept apart from ``species_senses`` so the content repository can use it at load without the import cycle
(``species_senses`` imports the warmed catalog, which imports the repository). ``species_senses`` re-exports ``species_sense_profile``, so every caller keeps its import."""
from __future__ import annotations

from typing import Any, Optional

from src.core.species import SenseProfileError


def species_sense_profile(catalog: Any, species_id: str) -> Optional[Any]:
    """The ``SenseProfileDefinition`` of `species_id`: None when the species is not in content (a test fixture body); ``SenseProfileError`` when it is but its profile does not resolve."""
    species = catalog.get_species(species_id)
    if species is None:
        return None
    defn = catalog.get_sense_profile(species.sense_profile) if species.sense_profile else None
    if defn is None:
        raise SenseProfileError(f"species {species_id!r} has no usable sense profile (declared {species.sense_profile!r})")
    return defn
