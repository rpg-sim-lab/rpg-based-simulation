"""The births system: one pass per check over every kind that declares a reproduction profile (M1)."""
# Compliance IDs: WORLD-122
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from src.content.resolver import EntityArchetypeResolver
from src.core.builder import build_parent_bond_updates_for_birth
from src.core.enums import Domain
from src.core.pregnancy import PregnancyState
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.species import species_of
from src.core.state import EntityState, GeneticProfile, LifeStage
from src.core.updates import (
    BiologicalUpdate,
    EntityUpdate,
    LifecycleUpdate,
    StateUpdate,
    WorldUpdate,
)
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
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
LITTER_DRAW_SUB_ID = 11


class BirthService:
    """
    One births system for every kind that declares a reproduction profile (owner B2: only kinds that eat). At each check a
    mother who is due bears her litter, and a fed ADULT mother with an eligible same-species ADULT mate in range conceives with a
    seeded chance; the pregnancy is recorded on her (PregnancyState) and ends at its due tick. It reads only the parents' own
    state and the profile: no region, no pair bond, no sex. Read-only on state; ApplyPath writes.
    """

    @staticmethod
    def process_births(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """The births at term and the conceptions of this check, mothers visited in id order."""
        catalog = get_catalog()
        profiles = _Profiles(catalog)
        check = _Check(state, generator, catalog)
        result = StateUpdate()
        for mother in _mothers_at_term(state, profiles):
            result = result.merge(_birth_at_term(check, mother, profiles.of(species_of(mother))))
        candidates = _candidates(state, profiles)
        used: Set[int] = set()
        for mother in candidates.values():
            profile = profiles.of(species_of(mother))
            if mother.id in used or profile is None or mother.biological.hunger > profile.fed_line or not _past_interval(mother, state.tick):
                continue
            # Draw first: it is stateless and independent of any mate, so a failed draw skips the spatial query.
            if generator.rng.get_float(Domain.SPAWN, state.tick, mother.id, sub_id=BIRTH_DRAW_SUB_ID) >= profile.birth_chance_per_check:
                continue
            mate = _find_mate(state, mother, candidates, used, profile.mate_radius_tiles)
            if mate is None:
                continue
            used.update((mother.id, mate.id))
            result = result.merge(_conceive(check, mother, mate, profile))
        return result


class _Profiles:
    """The reproduction profile of each species, read from the catalog once per check (None for a species that declares none)."""

    def __init__(self, catalog: Any) -> None:
        self._catalog = catalog
        self._by_species: Dict[str, Optional[ReproductionProfileDefinition]] = {}

    def of(self, species_id: str) -> Optional[ReproductionProfileDefinition]:
        """The species' profile, or None."""
        if species_id not in self._by_species:
            species = self._catalog.get_species(species_id)
            declared = species.reproduction_profile if species else None
            self._by_species[species_id] = self._catalog.get_reproduction_profile(declared) if declared else None
        return self._by_species[species_id]


def _candidates(state: AuthoritativeState, profiles: _Profiles) -> Dict[int, EntityState]:
    """Alive, active, not-pregnant ADULT bodies of a species that declares a profile, in id order."""
    return {
        e.id: e for e in sorted(state.entities.values(), key=lambda e: e.id)
        if e.identity.life_stage == LifeStage.ADULT and e.combat.alive and e.lifecycle.active and e.lifecycle.pregnancy is None
        and profiles.of(species_of(e)) is not None
    }


def _mothers_at_term(state: AuthoritativeState, profiles: _Profiles) -> List[EntityState]:
    """Alive, active mothers whose pregnancy has reached its due tick, in id order. Fed, mate and range are not asked again; the father may be dead."""
    return [
        e for e in sorted(state.entities.values(), key=lambda e: e.id)
        if e.lifecycle.pregnancy is not None and e.lifecycle.pregnancy.due_tick <= state.tick and e.combat.alive and e.lifecycle.active
        and profiles.of(species_of(e)) is not None
    ]


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


@dataclass
class _Check:
    """What one births check shares across its births: the state, the tick's generator, the catalog and the newborn contracts resolved so far."""

    state: AuthoritativeState
    generator: EntityGenerator
    catalog: Any
    contracts: Dict[str, ResolvedEntityRuntimeContract] = field(default_factory=dict)

    def contract(self, species_id: str) -> ResolvedEntityRuntimeContract:
        """The contract of the species' newborn archetype, resolved once per check."""
        if species_id not in self.contracts:
            archetype_id = self.catalog.get_species(species_id).newborn_archetype
            self.contracts[species_id] = resolved_archetype_to_contract(EntityArchetypeResolver(self.catalog).resolve(archetype_id))
        return self.contracts[species_id]


def _draw_litter(weights: Dict[int, float], draw: float) -> int:
    """The litter size at `draw` in [0, 1), over the table in ascending size order."""
    sizes = sorted(weights)
    point, running = draw * sum(weights.values()), 0.0
    for size in sizes:
        running += weights[size]
        if point < running:
            return size
    return sizes[-1]


def _conceive(check: _Check, mother: EntityState, mate: EntityState, profile: ReproductionProfileDefinition) -> StateUpdate:
    """The conception: the pregnancy is recorded on the mother (litter drawn now, father's genes snapshotted) and the father's interval starts."""
    state = check.state
    litter = _draw_litter(profile.litter_weights, check.generator.rng.get_float(Domain.SPAWN, state.tick, mother.id, sub_id=LITTER_DRAW_SUB_ID))
    pregnancy = PregnancyState(
        father_entity_id=mate.id, conceived_tick=state.tick, due_tick=state.tick + profile.gestation_ticks, litter_size=litter,
        father_genetic_profile=mate.lifecycle.genetic_profile or _fallback_genetics(state, mate),
    )
    expiry = state.tick + profile.min_birth_interval_ticks
    return StateUpdate(entity_updates={
        mother.id: EntityUpdate(entity_id=mother.id, lifecycle=LifecycleUpdate(pregnancy_set=pregnancy)),
        mate.id: EntityUpdate(entity_id=mate.id, lifecycle=_cooldown_update(mate, mother.id, expiry, state.tick)),
    })


def _birth_at_term(check: _Check, mother: EntityState, profile: ReproductionProfileDefinition) -> StateUpdate:
    """The litter at term. A newborn with no free tile is not born (a NEWBORN_UNPLACED event); the pregnancy is cleared either way; the mother's cost, her interval,
    the parents' bonds and the region's birth count are written only when at least one newborn is born."""
    state, generator = check.state, check.generator
    pregnancy = mother.lifecycle.pregnancy
    father = state.entities[pregnancy.father_entity_id]
    species_id = species_of(mother)
    region = SpatialQueryService.get_region_at(state, mother.navigation.position)
    home_region_id = mother.strategic.home_region_id or (region.id if region is not None else None)
    newborns: List[EntityState] = []
    unplaced: List[Any] = []
    for slot in range(pregnancy.litter_size):
        try:
            position = generator.free_spawn_position(mother.navigation.position, state)
        except RuntimeError:
            unplaced.append(WorldEvent(category=WorldEventCategory.NEWBORN_UNPLACED, tick=state.tick, subject=str(mother.id), payload={"litter_slot": slot}))
            continue
        birth = NewbornBirth(
            mother, father, position, state.tick, state.seed, mother.lifecycle.genetic_profile or _fallback_genetics(state, mother),
            pregnancy.father_genetic_profile, home_region_id,
        )
        newborns.append(ArchetypeEntityFactory().build_newborn(generator.get_next_id(), check.contract(species_id), birth))

    ended = LifecycleUpdate(pregnancy_clear=True)
    if not newborns:
        return StateUpdate(entity_updates={mother.id: EntityUpdate(entity_id=mother.id, lifecycle=ended)}, world_events_add=unplaced)
    expiry = state.tick + profile.min_birth_interval_ticks
    cost = min(profile.birth_hunger_cost, 100.0 - mother.biological.hunger)
    update = StateUpdate(
        entities_add=newborns,
        entity_spawn_sources={n.id: SpawnSource(SpawnKind.BIRTH, parent_ids=(mother.id, father.id)) for n in newborns},
        entity_updates={mother.id: EntityUpdate(
            entity_id=mother.id, biological=BiologicalUpdate(hunger_delta=cost),
            lifecycle=_cooldown_update(mother, father.id, expiry, state.tick).merge(ended),
        )},
        world_updates={region.id: WorldUpdate(region_id=region.id, population_young_births_delta=len(newborns))} if region is not None else {},
        world_events_add=unplaced,
    )
    living = [p.id for p in (mother, father) if p.combat.alive]
    for newborn in newborns:
        bonds = build_parent_bond_updates_for_birth(living, newborn.id, state.tick)
        update = update.merge(StateUpdate(entity_updates={u.entity_id: u for u in bonds}))
    return update


def _fallback_genetics(state: AuthoritativeState, parent: EntityState) -> GeneticProfile:
    """A parent with no genetic profile (every t0 body) gets one derived from (world seed, id), so the same id does not breed the same genes in every seed."""
    return GeneticsSystem.generate_profile_from_seed(state.seed * 1_000_003 + parent.id)


def _cooldown_update(parent: EntityState, partner_id: int, expiry: int, tick: int) -> LifecycleUpdate:
    """Record the new interval and prune the entries that have already expired, so the map stays bounded."""
    expired = tuple(sorted(k for k, v in parent.lifecycle.reproduction_cooldowns.items() if v <= tick))
    return LifecycleUpdate(reproduction_cooldowns_add={partner_id: expiry}, reproduction_cooldowns_remove=expired)
