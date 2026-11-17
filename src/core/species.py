"""The one way to read an entity's species (M1: `kind` always means species; occupation is its own field).

Step 2 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD. Every new reader of an entity's species (births included) calls `species_of`, so that
step 4, which makes `EntityState.kind` the species id on every build path, changes what this helper reads without touching any reader.

Today the species id is written in two places: `identity.properties["species_id"]` (the classic world compiler and the archetype paths write it) and, on the archetype path
only, `kind` itself. So the helper reads `properties["species_id"]` and falls back to `kind` where there is none.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import EntityState


def species_of(entity: "EntityState") -> str:
    """The species id of `entity`: `identity.properties["species_id"]`, else `kind` (the archetype path, where `kind` already is the species)."""
    species_id = entity.identity.properties.get("species_id")
    if isinstance(species_id, str) and species_id:
        return species_id
    return entity.kind


class SenseProfileError(Exception):
    """A body's species has no usable sense profile (PERC-02): a content error, never a silent baseline."""
