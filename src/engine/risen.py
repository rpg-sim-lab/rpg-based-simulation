"""The risen origin (M1): a corpse the world holds may rise as a new subject of a kind that declares a risen profile (STR-02; the dead body stays dead)."""
# Compliance IDs: WORLD-122
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from src.content.resolver import EntityArchetypeResolver
from src.core.enums import Domain
from src.core.spawn_errors import NoFreeSpawnTileError
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.species import species_of
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.behavior_consumers import get_catalog
from src.engine.cadence import SystemCadence
from src.engine.corpse_goods import corpse_remains
from src.engine.rise_trigger import rise_triggers_phase
from src.entities.archetype_factory import ArchetypeEntityFactory
from src.entities.contract_builder import resolved_archetype_to_contract

if TYPE_CHECKING:
    from src.content.schema import RisenProfileDefinition
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

# Below 65536 so it XORs only the low bits of the RNG key and cannot alias an `id << 16` term (see DeterministicRNG.get_float).
RISE_DRAW_SUB_ID = 13


class RisenService:
    """
    Every `cadence.rises` ticks (absolute tick) each corpse not yet at its decay tick, whose body's species is a source species of a kind that declares a
    risen profile, gets one keyed stateless draw; below the profile's chance it rises. A corpse a loot or meal took or shrank this tick (the post-transfer
    outcome) does not rise this tick. The rise adds the new subject and sends the corpse's goods out through the shared remains rule; nothing else of the
    dead body passes on.
    """

    @staticmethod
    def process_rises(state: AuthoritativeState, update: StateUpdate, cadence: Optional[SystemCadence] = None, *, generator_for_state: Callable[..., Any]) -> StateUpdate:
        """`update` with this check's risings added (it is returned unchanged when none rise), run after the transfers resolved. `generator_for_state` is `EntityGenerator.for_state`, handed in by the engine's pipeline (the engine may not import the systems layer); it is called with the same (state, update) as before."""
        if not rise_triggers_phase("resource_transactions", state, cadence):
            return update
        catalog = get_catalog()
        by_source = _profiles_by_source(catalog)
        if not by_source:
            return update
        taken = set(update.corpses_remove) | {c.id for c in update.corpses_add_or_update}
        generator = generator_for_state(state, update)
        generator.claim_tiles_of(state, update.entities_add)
        entity_spawn_sources: Dict[int, SpawnSource] = {}
        risings = _Risings(next_item_id=max(state.next_item_instance_id, update.next_item_instance_id_set or 0))
        for corpse_id in sorted(state.corpses):
            corpse = state.corpses[corpse_id]
            original = state.entities.get(corpse.original_entity_id)
            match = by_source.get(species_of(original)) if original is not None else None
            if match is None or corpse_id in taken or state.tick + 1 >= corpse.decay_tick:
                continue
            species_id, profile = match
            if generator.rng.get_float(Domain.SPAWN, state.tick, corpse_id, sub_id=RISE_DRAW_SUB_ID) >= profile.rise_chance_per_check:
                continue
            try:
                position = generator.free_spawn_position(corpse.position, state)
            except NoFreeSpawnTileError:
                continue
            body = ArchetypeEntityFactory().build_risen(generator.get_next_id(), _contract(catalog, profile), position, state.tick, state.seed)
            entity_spawn_sources[body.id] = SpawnSource(SpawnKind.RISEN, source_corpse_id=corpse_id, original_entity_id=corpse.original_entity_id)
            risings.add(corpse, body, state.tick)
        return risings.into(update, entity_spawn_sources)


class _Risings:
    """The records of this check's risings, folded into the update once."""

    def __init__(self, next_item_id: int) -> None:
        self.next_item_id = next_item_id
        self.entities: List[Any] = []
        self.removed: List[int] = []
        self.ground: List[Any] = []
        self.events: List[WorldEvent] = []

    def add(self, corpse: Any, body: Any, tick: int) -> None:
        """Record one rising: the body, its source, the corpse's removal and its goods."""
        remains = corpse_remains(corpse, tick, self.next_item_id)
        self.next_item_id = remains.next_item_id
        self.entities.append(body)
        self.removed.append(corpse.id)
        self.ground.extend(([remains.purse] if remains.purse is not None else []) + list(remains.ground_items))
        if remains.meat_left > 0:
            self.events.append(WorldEvent(category=WorldEventCategory.MEAT_DECAYED, tick=tick, subject=str(corpse.id),
                                          payload={"quantity": remains.meat_left, "cause": "risen"}))

    def into(self, update: StateUpdate, entity_spawn_sources: Dict[int, SpawnSource]) -> StateUpdate:
        """`update` with the risings added; unchanged when there are none."""
        if not self.entities:
            return update
        return replace(
            update,
            entities_add=[*update.entities_add, *self.entities],
            entity_spawn_sources={**update.entity_spawn_sources, **entity_spawn_sources},
            corpses_remove=[*update.corpses_remove, *self.removed],
            ground_items_add_or_update=[*update.ground_items_add_or_update, *self.ground],
            world_events_add=[*update.world_events_add, *self.events],
            next_item_instance_id_set=self.next_item_id,
        )


def _profiles_by_source(catalog: Any) -> Dict[str, tuple]:
    """Source species -> (risen species, its profile); the lowest risen species id wins a species two profiles name."""
    by_source: Dict[str, tuple] = {}
    for species_id in sorted(catalog.species):
        profile_id = catalog.species[species_id].risen_profile
        profile = catalog.get_risen_profile(profile_id) if profile_id else None
        for source in (profile.source_species if profile else ()):
            by_source.setdefault(source, (species_id, profile))
    return by_source


def _contract(catalog: Any, profile: RisenProfileDefinition) -> Any:
    return resolved_archetype_to_contract(EntityArchetypeResolver(catalog).resolve(profile.risen_archetype))
