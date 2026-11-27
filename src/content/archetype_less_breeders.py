"""The refusal of a population that has no archetype but spawns MONSTERs of a breeding species (M1 births).

A population with no archetype carries no `newborn_role` declaration, so its children are born with the no-archetype default (CITIZEN). One that spawns MONSTERs of a breeding species would
change that outcome silently, so it is refused at assembly, before tick 0. Both build paths call this one function with the role THEY derived for the body: the spawner path
(`WorldEntitySpawner._spawn_legacy_guard`, the profile's `legacy_role`) and the classic compile (`WorldCompiler.compile`, its `role_enum`)."""
from __future__ import annotations

from typing import Any, Optional

from src.content.repository import ReproductionProfileError
from src.core.enums import EntityRole


def refuse_archetype_less_monster_breeder(population_id: Optional[str], species_id: Optional[str], role: int, catalog: Any) -> None:
    """Raise `ReproductionProfileError` when `species_id` breeds and `role` is MONSTER; call it only for a population with no archetype."""
    species = catalog.species.get(species_id) if species_id else None
    if species is not None and species.reproduction_profile is not None and role == EntityRole.MONSTER:
        raise ReproductionProfileError(
            f"population {population_id!r} names no archetype and spawns MONSTERs of species {species_id!r}, which breeds: declare an archetype with a newborn_role, since a child of an archetype-less mother is born CITIZEN")
