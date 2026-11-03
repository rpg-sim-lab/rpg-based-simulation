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
