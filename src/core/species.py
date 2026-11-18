"""The one way to read an entity's species (M1: `kind` always means species; occupation is its own field).

Step 2 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD. Every new reader of an entity's species (births included) calls `species_of`, so that
step 4, which makes `EntityState.kind` the species id on every build path, changes what this helper reads without touching any reader.

Step 4 (kind=species): `EntityState.kind` IS the species id on every build path, so the helper reads `kind`. `properties["species_id"]` stays as a mirror, written from the
same value at build, until step 5 moves its readers and removes it. A writer with no species to declare is refused with `SpeciesNotDeclaredError`, never defaulted.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from src.core.state import EntityState


class SpeciesNotDeclaredError(ValueError):
    """A build or spawn path was asked to write an entity with no declared species (kind=species, step 4): the typed refusal that replaced every code-chosen default
    species (`or "human"`, `or "entity"`, a default kind, a role label written as kind)."""


# The one kind value allowed that is NOT an id in data/content/living/species.yaml: a non-living or boss body with no declared species yet. Each entry names its owning
# ticket and reason; K6 of the step-4 measurement counts kinds against species.yaml plus this list only. Nothing is silently accepted.
NON_LIVING_KIND_ALLOWLIST: dict[str, str] = {
    "world_boss": "TCK-20261117-A-WORLD-BOSS-BODY-DECLARES-A-SPECIES (the boss feature is OFF by default, ENABLE_WORLD_BOSS_SPAWN)",
    "magical_demonic_entity": "TCK-20261117-A-MAGICAL-DEMONIC-ENTITY-BODY-DECLARES-A-SPECIES (behind the OFF flag ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH)",
}


def species_of(entity: "EntityState") -> str:
    """The species id of `entity`: its `kind` (M1 step 4: `kind` always means species; the label it replaced lives in `identity.occupation`)."""
    return entity.kind


def occupation_of(entity: Any) -> Optional[str]:
    """The role label of `entity` (`identity.occupation`), or None for a body with none or an object that carries no identity.

    M1 step 3: the readers that compared `kind` with a role label read this instead, with the same literal; in step 2 the field equals `kind` on every writer."""
    return getattr(getattr(entity, "identity", None), "occupation", None)


class SenseProfileError(Exception):
    """A body's species has no usable sense profile (PERC-02): a content error, never a silent baseline."""
