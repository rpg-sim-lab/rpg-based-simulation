"""What the two executors hand to domain logic must be the same world (TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS).

``LocalSequentialExecutor`` passes the read-only ``AuthoritativeState``; ``ConcurrentExecutionAdapter`` passes a ``WorkerPacket``. Domain logic asks the same questions of
either (``context.seed``, ``context.feature_flags``, ``context.building_tiles`` ...). A question the packet answered differently, or silently with a default, gave a
different world on the same seed (law: docs/engine/contracts/bounded_concurrency_contract.md, "Fallback Equivalence"; certification matrix local-vs-concurrent).
"""
import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ClanState, RegionState
from src.core.work import WorkClass, WorkItem
from src.engine.executor import ConcurrentExecutionAdapter, LocalSequentialExecutor
from src.engine.tactical_destinations import wander_destination
from src.platform.rng import DeterministicRNG
from tests.unit.kernel.test_executor_parity import make_profile

REGION = RegionState(id="field", name="Field", bounds=(5, 5, 60, 60))


def _entity(eid, pos=(10.0, 10.0)):
    return V2EntityBuilder(eid).kind("worker").properties({"species_id": "human"}).location(*pos).combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True).build()


def _state(seed=45, tick=600, **extra):
    entities = {1: _entity(1), 2: _entity(2, (12.0, 10.0))}
    return AuthoritativeState(tick=tick, seed=seed, world_time=tick, entities=entities, regions={"field": REGION}, **extra)


class _Spy:
    """A worker manager that records the packets the adapter builds and runs nothing."""

    def __init__(self):
        self.packets = []

    def execute_batch(self, packets, worker_fn, concurrency_limit=1.0):
        self.packets = list(packets)
        return []


def _packet(state, eid=1):
    spy = _Spy()
    item = WorkItem(work_id=f"{state.tick}:{eid}", owner_id=eid, work_kind="ENTITY_ACT", work_class=WorkClass.CRITICAL, payload={}, priority=eid)
    ConcurrentExecutionAdapter(spy).execute([item], state.readonly_view(), DeterministicRNG(state.seed), make_profile())
    assert spy.packets, "the adapter built no packet"
    return spy.packets[0]


def test_the_packet_seed_is_the_world_seed():
    state = _state(seed=45)
    assert _packet(state).seed == 45


def test_a_seeded_draw_is_the_same_through_a_packet_and_through_the_state():
    """The row that split crowded s45: a STALEMATE_BREAK wander target drawn from ``DeterministicRNG(context.seed)``."""
    state = _state(seed=45)
    entity = state.entities[1]
    assert wander_destination(state, entity) is not None
    assert wander_destination(_packet(state), entity) == wander_destination(state.readonly_view(), entity)


def test_the_packet_carries_the_state_feature_flags_by_value():
    flags = {"ENABLE_COMBAT_ENGAGEMENT": "ON", "ENABLE_HABIT_BIAS_ACTION_STYLE": "OFF"}
    packet = _packet(_state(feature_flags=flags))
    assert dict(packet.feature_flags) == flags
    assert (getattr(packet, "feature_flags", None) or {}).get("ENABLE_COMBAT_ENGAGEMENT", "OFF") == "ON"


def test_the_packet_carries_building_tiles_and_the_town_center():
    state = _state(building_tiles={(5, 5): "inn", (6, 5): "inn"}, town_center=(7.0, 8.0))
    packet = _packet(state)
    assert dict(packet.building_tiles) == {(5, 5): "inn", (6, 5): "inn"}
    assert packet.town_center == (7.0, 8.0)


def test_service_reach_reads_the_same_kind_through_a_packet_and_through_the_state():
    from src.engine.service_reach import building_kind_at
    state = _state(building_tiles={(5, 5): "inn"})
    assert building_kind_at(_packet(state), (5, 5)) == building_kind_at(state.readonly_view(), (5, 5)) == "inn"


def _clan_state():
    clan = ClanState(clan_id="c1", name="Clan", member_entity_ids=(1,), leader_entity_id=2, founded_tick=1)
    return _state(clans={"c1": clan})


def _join(executor_kind):
    state = _clan_state()
    item = WorkItem(work_id="600:1", owner_id=1, work_kind="ENTITY_ACT", work_class=WorkClass.CRITICAL,
                    payload={"action": "JOIN_CLAN", "clan_id": "c1"}, priority=1)
    if executor_kind == "local":
        results = LocalSequentialExecutor().execute([item], state.readonly_view(), DeterministicRNG(45), make_profile())
    else:
        from src.engine.worker_manager import WorkerManager
        workers = WorkerManager(max_workers=1)
        try:
            results = ConcurrentExecutionAdapter(workers).execute([item], state.readonly_view(), DeterministicRNG(45), make_profile())
        finally:
            workers.shutdown()
    return {r.entity_id: r.update.navigation.failure_reason for r in results if r.entity_id == 1 and r.update.navigation is not None}


def test_join_clan_gives_the_same_answer_on_both_executors():
    """``execute_join_clan`` reads ``context.clans``; a packet without them answered TARGET_NOT_FOUND where the state said ALREADY_MEMBER."""
    local, concurrent = _join("local"), _join("concurrent")
    assert local == {1: "ALREADY_MEMBER"}
    assert concurrent == local


def test_an_undeclared_state_field_read_on_a_packet_fails_instead_of_defaulting():
    from src.core.worker_protocol import PacketFieldMissingError
    packet = _packet(_state())
    with pytest.raises(PacketFieldMissingError):
        getattr(packet, "quest_registry", None)  # a state field the packet does not carry: the default must not hide it
    with pytest.raises(PacketFieldMissingError):
        hasattr(packet, "factions")


def test_a_name_that_is_not_a_state_field_is_an_ordinary_attribute_error():
    packet = _packet(_state())
    assert getattr(packet, "not_a_state_field", "default") == "default"
    assert not hasattr(packet, "__deepcopy__")


def test_a_lazily_derived_cache_the_packet_lacks_is_an_ordinary_attribute_error():
    """Allow-listed: a helper rebuilds it from fields the packet carries (the reason is written beside the allow-list)."""
    packet = _packet(_state())
    for name in ("_spatial_grid_cache", "_region_list_cache", "_has_hostiles_or_dead_cache", "occupancy_snapshot", "movement_cache", "route_plans"):
        assert getattr(packet, name, "absent") == "absent", name


def test_the_packet_town_center_equals_the_states_and_a_state_without_tiles_gives_an_empty_map():
    assert _packet(_state(town_center=(33.0, 44.0))).town_center == _state(town_center=(33.0, 44.0)).town_center == (33.0, 44.0)
    assert dict(_packet(_state()).building_tiles) == {}  # empty only because the state has none; the next test pins the other direction


def test_a_state_with_building_tiles_never_gives_an_empty_packet_map():
    tiles = {(x, 5): "inn" for x in range(5, 9)}
    assert dict(_packet(_state(building_tiles=tiles)).building_tiles) == tiles


def test_the_executor_is_the_only_place_that_builds_a_worker_packet():
    """A packet built anywhere else could carry an empty map for a state that has tiles; the guard cannot see that, so the construction site is pinned to one."""
    import pathlib
    sites = [str(p) for p in pathlib.Path("src").rglob("*.py") if "WorkerPacket(" in p.read_text(encoding="utf-8")]
    assert sites == ["src/engine/executor.py"], sites


def test_a_move_resolved_in_the_executor_takes_the_same_far_town_branch_as_sequential(monkeypatch):
    """``MovementSystem._route_step`` (movement.py:112) skips the terrain route for a far target equal to ``town_center``. On a packet without town_center the default
    None made it take the route branch where the state did not. The route function is spied: it must not be called for the far-town target on either context."""
    import src.engine.movement as movement
    state = _state(town_center=(95.0, 95.0))
    entity = state.entities[1]  # at (10, 10): the town centre is more than 50 tiles away
    calls = []
    monkeypatch.setattr(movement, "route_next_step", lambda *a, **k: (calls.append(a), None)[1])
    for context in (state.readonly_view(), _packet(state)):
        calls.clear()
        movement.MovementSystem._route_step(entity, (95.0, 95.0), context)
        assert calls == [], type(context).__name__


# FIELD PARITY (rpg-planner conditions, TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS).
# Fields are discovered with dataclasses.fields(WorkerPacket), never listed by hand. Each is one of:
#   * the state's own value (same name, or the renamed pair in _RENAMED), compared BY CONTENT (frozen copies and views by value);
#   * set per work item by the executor (_PER_ITEM);
#   * a derived structure the executor builds from the state (_DERIVED), with a reason and an owner. An entry with no reason, or a field that shares a name with a
#     state field and is listed here, fails: a same-name field must be equal to the state's (what broke ``seed``; and ``blocked_tiles``, which a default left empty).
_RENAMED = {"all_entities": "entities"}
_PER_ITEM = {"packet_id", "work_id", "work_class", "subject", "neighbor_view", "work_kind", "payload", "class_priority", "local_priority"}
_DERIVED = {  # name: (reason, owner)
    "spatial_grid": ("the neighbour grid built from the state's entities; COMPARED by content with a fresh SpatialGrid in _DERIVED_CHECKS", "executor.py"),
    "occupancy_map": ("tile -> entity id built from the state's entities; COMPARED by content with a cache-free rebuild and with OccupancySnapshot.from_state in _DERIVED_CHECKS", "executor.py"),
    "region_list": ("the region list of the state; COMPARED by content with list(state.regions.values()) in _DERIVED_CHECKS", "executor.py"),
    "building_map": ("tile -> building built from state.buildings; COMPARED by content with a fresh rebuild in _DERIVED_CHECKS", "executor.py"),
    "_region_index_cache": ("identity of a memo cannot be compared (no public fresh rebuild that returns the same type); derived from state.regions", "executor.py"),
    "_regions_global_bounds": ("identity of a memo cannot be compared (no public fresh rebuild that returns the same type); derived from state.regions", "executor.py"),
    "_building_region_map_cache": ("identity of a memo cannot be compared (no public fresh rebuild that returns the same type); derived from state.buildings and regions", "executor.py"),
    "_node_map_cache": ("identity of a memo cannot be compared (no public fresh rebuild that returns the same type); derived from state.resource_nodes", "executor.py"),
    "_corpse_map_cache": ("identity of a memo cannot be compared (no public fresh rebuild that returns the same type); derived from state.corpses", "executor.py"),
    "_ground_item_map_cache": ("identity of a memo cannot be compared (no public fresh rebuild that returns the same type); derived from state.ground_items", "executor.py"),
    "transient_claims": ("the state's value is None outside a resolution pass (state.py:1369, reset at :1479); verify_occupancy reads `or []`, so [] and None read the same", "rpg-implementer"),
}


def _by_value(value):
    if isinstance(value, (set, frozenset)):
        return frozenset(value)
    if hasattr(value, "items"):
        return {k: _by_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)) and not (isinstance(value, tuple) and len(value) == 2 and all(isinstance(x, float) for x in value)):
        return [_by_value(v) for v in value]
    return value


def _packet_fields():
    import dataclasses
    from src.core.worker_protocol import WorkerPacket
    return dataclasses.fields(WorkerPacket)


def _fresh_occupancy(state) -> dict:
    """Tile -> entity id rebuilt from the entities with no cache (a lodger stands on no tile, F3)."""
    return {(int(e.navigation.position[0]), int(e.navigation.position[1])): eid for eid, e in state.entities.items()
            if e.lifecycle.active and e.combat.alive and e.navigation.lodged_in is None}


def _check_occupancy_map(packet, state):
    from src.engine.occupancy_snapshot import OccupancySnapshot
    fresh = _fresh_occupancy(state)
    out = []
    if dict(packet.occupancy_map) != fresh:
        out.append("occupancy_map differs from a cache-free rebuild")
    if OccupancySnapshot.from_state(state).occupancy_by_tile != fresh:
        out.append("OccupancySnapshot.from_state differs from the cache-free rebuild")
    snap = getattr(state, "occupancy_snapshot", None)
    if snap is not None and dict(snap.occupancy_by_tile) != fresh:
        out.append("the state's own occupancy_snapshot is stale against the entities")
    return out


def _check_spatial_grid(packet, state):
    from src.engine.spatial import SpatialGrid
    fresh = SpatialGrid(state.entities)
    return [f"spatial_grid neighbours of entity {eid} differ from a fresh grid" for eid, e in sorted(state.entities.items())
            if [t[0] for t in packet.spatial_grid.get_neighbor_tuples(e.navigation.position, 10.0, eid)] != [t[0] for t in fresh.get_neighbor_tuples(e.navigation.position, 10.0, eid)]]


def _check_region_list(packet, state):
    return [] if [r.id for r in packet.region_list] == [r.id for r in state.regions.values()] else ["region_list differs from list(state.regions.values())"]


def _check_building_map(packet, state):
    fresh = {b.position: b.id for b in state.buildings.values()}
    return [] if {k: v.id for k, v in packet.building_map.items()} == fresh else ["building_map differs from a rebuild of state.buildings"]


_DERIVED_CHECKS = {"occupancy_map": _check_occupancy_map, "spatial_grid": _check_spatial_grid, "region_list": _check_region_list, "building_map": _check_building_map}


def check_field_parity(state) -> list:
    """The list of packet fields whose value differs from the state's (empty when the packet is the state's world)."""
    import dataclasses
    state_names = {f.name for f in dataclasses.fields(AuthoritativeState)}
    packet = _packet(state)
    view = state.readonly_view()
    wrong = []
    for f in _packet_fields():
        name = f.name
        if name in _PER_ITEM or name in _DERIVED:
            continue
        source = _RENAMED.get(name, name)
        if source not in state_names and source != "entities":
            wrong.append(f"{name}: not a state field, not renamed, not per-item, not derived (no reason given)")
            continue
        if _by_value(getattr(packet, name)) != _by_value(getattr(view, source)):
            wrong.append(f"{name}: packet {str(getattr(packet, name))[:60]} != state {str(getattr(view, source))[:60]}")
    for name, check in _DERIVED_CHECKS.items():
        wrong.extend(check(packet, view))
    return wrong


def test_the_exclusions_have_reasons_and_no_same_name_field_is_excluded_but_the_two_written_kinds():
    """Rule: no field may be excluded if its name matches a state field (what broke ``seed``), except (a) the state's own derived caches (leading underscore: the same
    cache, built from fields the packet carries) and (b) ``transient_claims`` (reason in the table). Anything else must be compared."""
    import dataclasses
    state_names = {f.name for f in dataclasses.fields(AuthoritativeState)}
    for name, (reason, owner) in _DERIVED.items():
        assert reason.strip() and owner.strip(), f"{name}: an exclusion needs a reason and an owner"
    same_name_excluded = {n for n in _DERIVED if n in state_names}
    assert {n for n in same_name_excluded if not n.startswith("_")} == {"transient_claims"}, same_name_excluded
    assert (_PER_ITEM | set(_DERIVED) | set(_RENAMED)) <= {f.name for f in _packet_fields()}
    unchecked = {n for n in _DERIVED if not n.startswith("_") and n != "transient_claims"} - set(_DERIVED_CHECKS)
    assert unchecked == set(), f"derived structures excluded without a by-content check: {sorted(unchecked)}"


def test_a_stale_occupancy_map_is_caught():
    """Positive control: the memoised map that drifts (an entity moved after the map was built) must fail the parity check."""
    import dataclasses
    state = _rich_state()
    packet = _packet(state)
    stale = dataclasses.replace(packet, occupancy_map={**dict(packet.occupancy_map), (30, 30): 99})
    assert _check_occupancy_map(stale, state.readonly_view()) != []
    assert _check_occupancy_map(packet, state.readonly_view()) == []


def test_a_stale_snapshot_on_the_state_is_caught():
    import dataclasses
    from src.engine.occupancy_snapshot import OccupancySnapshot
    state = _rich_state()
    snap = OccupancySnapshot.from_state(state)
    moved = dataclasses.replace(state.entities[1], navigation=dataclasses.replace(state.entities[1].navigation, position=(15.0, 15.0)))
    drifted = dataclasses.replace(state, entities={**state.entities, 1: moved}, occupancy_snapshot=snap)
    assert any("stale" in m for m in _check_occupancy_map(_packet(drifted), drifted.readonly_view()))


def _after_lodging(state):
    """An entity lodged in a building: it stands on no tile (F3 2.155)."""
    import dataclasses
    e = state.entities[1]
    lodged = dataclasses.replace(e, navigation=dataclasses.replace(e.navigation, lodged_in=100))
    return dataclasses.replace(state, entities={**state.entities, 1: lodged})


def _after_building_change(state):
    """A building added after t0: its tile joins the blocked tiles and the building tiles."""
    import dataclasses
    from src.core.state import BuildingState
    return dataclasses.replace(state, buildings={**state.buildings, 100: BuildingState(id=100, kind="inn", position=(20.0, 20.0))},
                               blocked_tiles=frozenset(set(state.blocked_tiles) | {(20, 20)}), building_tiles={**state.building_tiles, (20, 20): "inn"})


@pytest.mark.parametrize("name", ["t0", "mid_run", "after_lodging", "after_building_change"])
def test_every_packet_field_equals_the_states_value_at_each_stage(name):
    """PR-lane fixture version of the gate-world check below (a small state, the stages the reviewer named)."""
    base = _rich_state()
    state = {"t0": lambda: _state(seed=7, tick=0, blocked_tiles={(5, 5)}, building_tiles={(5, 5): "inn"}),
             "mid_run": lambda: _rich_state(),
             "after_lodging": lambda: _after_lodging(base),
             "after_building_change": lambda: _after_building_change(base)}[name]()
    assert check_field_parity(state) == []


@pytest.mark.extra_slow
@pytest.mark.parametrize("ticks", [0, 150, 600])
def test_every_packet_field_equals_the_states_value_on_a_gate_world(ticks):
    """Slow-lane version: crowded_frontier s45 compiled and run sequentially to ``ticks``; the packet is built from the state at that tick (drift in a memoised
    structure shows here). Stage coverage: t0 and mid-run always; lodging and building changes only if the run produced one, which is recorded not assumed."""
    from src.config.profiles import PROD_SMALL
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository
    from tests.helpers.kernel_pinning import PinnedNormalGovernor
    spec, context = WorldRepository("data/worlds").load_world_with_context("crowded_frontier")
    state, _ = WorldCompiler.compile(spec, 45, context=context)
    kernel = Kernel(PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state, DeterministicRNG(45), governor=PinnedNormalGovernor(),
                    executor=LocalSequentialExecutor(), flags={"audit_mode": True, "no_frame_pacing": True}, run_id=f"fieldparity_{ticks}")
    try:
        for _ in range(ticks):
            kernel.tick_once()
        assert check_field_parity(kernel.state) == []
    finally:
        kernel.shutdown()


def test_a_defaulted_packet_field_is_shown_set_by_the_executor_or_listed():
    """A defaulted field the constructor does not set answers the state's question with the default (blocked_tiles: [] said walkable for the inn tile)."""
    import dataclasses
    import pathlib
    import re
    text = pathlib.Path("src/engine/executor.py").read_text(encoding="utf-8")
    block = text[text.index("packet = WorkerPacket("):text.index("packets.append(packet)")]
    set_names = set(re.findall(r"^\s*(\w+)=", block, re.M))
    unset = {f.name for f in _packet_fields() if (f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING) and f.name not in set_names}
    assert unset <= set(_DERIVED), f"defaulted packet fields the executor never sets and no reason lists: {sorted(unset - set(_DERIVED))}"


def test_a_walled_or_built_tile_is_blocked_on_the_packet_as_on_the_state():
    """The row that split crowded s42 at t1973: ``find_intercept_position`` asked ``verify_occupancy`` about the inn tile; the compiler puts each building tile into
    ``blocked_tiles``, the packet carried none, and the worker said walkable where the state said solid."""
    from src.engine.legality import LegalityServiceV2
    state = _rich_state()
    for tile in ((5, 5), (6, 5), (9, 9)):
        assert LegalityServiceV2.verify_occupancy(tile, state.readonly_view())[0] is False
        assert LegalityServiceV2.verify_occupancy(tile, _packet(state))[0] is False, tile


def _rich_state():
    clan = ClanState(clan_id="c1", name="Clan", member_entity_ids=(1,), leader_entity_id=2, founded_tick=1)
    return _state(seed=7, clans={"c1": clan}, feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"}, building_tiles={(5, 5): "inn"}, town_center=(7.0, 8.0),
                  blocked_tiles={(5, 5), (6, 5), (9, 9)}, terrain={(1, 1): "WALL"})
