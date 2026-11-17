# Compliance IDs: WORLD-122
# src/world/births.py
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from src.core.builder import build_parent_bond_updates_for_birth
from src.core.enums import Domain
from src.core.species import species_of
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.state import EntityState, LifeStage
from src.core.updates import BiologicalUpdate, EntityUpdate, LifecycleUpdate, StateUpdate, WorldUpdate
from src.content.resolver import EntityArchetypeResolver
from src.engine.behavior_consumers import get_catalog
from src.engine.spatial_query import SpatialQueryService
from src.entities.archetype_factory import ArchetypeEntityFactory, NewbornBirth
from src.entities.contract_builder import resolved_archetype_to_contract
from src.systems.lifecycle_systems.genetics import GeneticsSystem

if TYPE_CHECKING:
    from src.content.schema import ReproductionProfileDefinition
    from src.core.state import AuthoritativeState
    from src.entities.runtime_contract import ResolvedEntityRuntimeContract
    from src.systems.world_systems.generator import EntityGenerator

# Below 65536 so it XORs only the low bits of the RNG key and cannot alias an `id << 16` term (see DeterministicRNG.get_float).
BIRTH_DRAW_SUB_ID = 7


class BirthService:
    """
    One births system for every kind that declares a reproduction profile (owner B2: only kinds that eat). A fed ADULT
    mother with an eligible same-species ADULT mate in range bears a newborn with a seeded chance per check. It reads
    only the two parents' own state and the profile: no region, no pair bond, no sex. Read-only on state; ApplyPath writes.
    """

    @staticmethod
    def process_births(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """The births of this check, one merged update per birth, mothers visited in id order."""
        catalog = get_catalog()
        profiles: Dict[str, Optional[ReproductionProfileDefinition]] = {}

        def profile_of(species_id: str) -> Optional[ReproductionProfileDefinition]:
            if species_id not in profiles:
                species = catalog.get_species(species_id)
                profiles[species_id] = catalog.get_reproduction_profile(species.reproduction_profile) if species and species.reproduction_profile else None
            return profiles[species_id]

        candidates: Dict[int, EntityState] = {
            e.id: e for e in sorted(state.entities.values(), key=lambda e: e.id)
            if e.identity.life_stage == LifeStage.ADULT and e.combat.alive and e.lifecycle.active and profile_of(species_of(e)) is not None
        }
        contracts: Dict[str, ResolvedEntityRuntimeContract] = {}
        used: Set[int] = set()
        result = StateUpdate()

        for mother in candidates.values():
            profile = profile_of(species_of(mother))
            if mother.id in used or profile is None or mother.biological.hunger > profile.fed_line or not _past_interval(mother, state.tick):
                continue
            mate = _find_mate(state, mother, candidates, used, profile.mate_radius_tiles)
            if mate is None:
                continue
            if generator.rng.get_float(Domain.SPAWN, state.tick, mother.id, sub_id=BIRTH_DRAW_SUB_ID) >= profile.birth_chance_per_check:
                continue
            used.update((mother.id, mate.id))
            result = result.merge(_birth(state, generator, catalog, contracts, mother, mate, profile))
        return result


def _past_interval(entity: EntityState, tick: int) -> bool:
    """Eligible when every partner entry has expired: the latest expiry is the end of the birth interval."""
    return max(entity.lifecycle.reproduction_cooldowns.values(), default=0) <= tick


def _find_mate(
    state: AuthoritativeState, mother: EntityState, candidates: Dict[int, EntityState], used: Set[int], radius: float,
) -> Optional[EntityState]:
    """The lowest-id other same-species candidate within `radius` tiles (Chebyshev) that is past its interval and not yet a parent this check."""
    px, py = mother.navigation.position
    # nearby_entities is Euclidean: the circle that contains the Chebyshev square, then filtered back to it.
    for mate_id in sorted(SpatialQueryService.nearby_entities(state, mother.navigation.position, math.ceil(radius * math.sqrt(2)))):
        mate = candidates.get(mate_id)
        if mate is None or mate_id == mother.id or mate_id in used or species_of(mate) != species_of(mother):
            continue
        mx, my = mate.navigation.position
        if max(abs(mx - px), abs(my - py)) <= radius and _past_interval(mate, state.tick):
            return mate
    return None


def _birth(
    state: AuthoritativeState, generator: EntityGenerator, catalog: object, contracts: Dict[str, ResolvedEntityRuntimeContract],
    mother: EntityState, mate: EntityState, profile: ReproductionProfileDefinition,
) -> StateUpdate:
    species_id = species_of(mother)
    species = catalog.get_species(species_id)  # type: ignore[attr-defined]
    if species_id not in contracts:
        contracts[species_id] = resolved_archetype_to_contract(EntityArchetypeResolver(catalog).resolve(species.newborn_archetype))  # type: ignore[arg-type]
    region = SpatialQueryService.get_region_at(state, mother.navigation.position)
    home_region_id = mother.strategic.home_region_id or (region.id if region is not None else None)

    newborns: List[EntityState] = []
    for _ in range(profile.litter_size):
        birth = NewbornBirth(
            mother, mate, generator.free_spawn_position(mother.navigation.position, state), state.tick, state.seed,
            mother.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(mother.id),
            mate.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(mate.id), home_region_id,
        )
        newborns.append(ArchetypeEntityFactory().build_newborn(generator.get_next_id(), contracts[species_id], birth))

    expiry = state.tick + profile.min_birth_interval_ticks
    cost = min(profile.birth_hunger_cost, 100.0 - mother.biological.hunger)
    update = StateUpdate(
        entities_add=newborns,
        entity_spawn_sources={n.id: SpawnSource(SpawnKind.BIRTH, parent_ids=(mother.id, mate.id)) for n in newborns},
        entity_updates={
            mother.id: EntityUpdate(
                entity_id=mother.id, biological=BiologicalUpdate(hunger_delta=cost),
                lifecycle=_cooldown_update(mother, mate.id, expiry, state.tick),
            ),
            mate.id: EntityUpdate(entity_id=mate.id, lifecycle=_cooldown_update(mate, mother.id, expiry, state.tick)),
        },
        world_updates={region.id: WorldUpdate(region_id=region.id, population_young_births_delta=1)} if region is not None else {},
    )
    for newborn in newborns:
        bonds = build_parent_bond_updates_for_birth([mother.id, mate.id], newborn.id, state.tick)
        update = update.merge(StateUpdate(entity_updates={u.entity_id: u for u in bonds}))
    return update


def _cooldown_update(parent: EntityState, partner_id: int, expiry: int, tick: int) -> LifecycleUpdate:
    """Record the new interval and prune the entries that have already expired, so the map stays bounded."""
    expired = tuple(sorted(k for k, v in parent.lifecycle.reproduction_cooldowns.items() if v <= tick))
    return LifecycleUpdate(reproduction_cooldowns_add={partner_id: expiry}, reproduction_cooldowns_remove=expired)
