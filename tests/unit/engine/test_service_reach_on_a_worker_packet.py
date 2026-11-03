"""Service reach must work on the read-only state a concurrent worker sees (a ``WorkerPacket``).

``service_reach.building_kind_at`` falls through to ``state.building_tiles.get(tile)`` whenever no building stood on the tile (most of the five reach
offsets). The packet once carried no ``building_tiles``: the lookup raised ``AttributeError`` (a worker crash, logged as "Internal worker crash"), and then
read a missing map as "no kind" while the state answered from its own map, so the two executors disagreed in any world with building tiles
(TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS). The packet now carries the state's ``building_tiles`` (empty when the state has none).
"""
from __future__ import annotations

from types import SimpleNamespace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import BuildingState
from src.core.worker_protocol import WorkerPacket
from src.core.work import WorkClass
from src.engine.service_reach import building_kind_at, service_at, service_tile


def _packet(buildings):
    """A packet as the executor builds it: ``buildings`` and the position map ``building_map``, no ``building_tiles``."""
    subject = V2EntityBuilder(1).kind("hero").identity(role=EntityRole.HERO).location(10.0, 10.0).lifecycle(active=True).build()
    return WorkerPacket(
        packet_id="p", work_id="w", tick=1, world_time=1, seed=42, work_class=WorkClass.CRITICAL, subject=subject,
        neighbor_view=[], work_kind="ENTITY_ACT", payload={}, buildings=buildings,
        building_map={b.position: b for b in buildings.values()},
    )


def _inn(tile=(12, 10)):
    return BuildingState(id=7, kind="inn", position=tile)


def test_the_packet_carries_a_building_tiles_map_empty_when_the_state_has_none():
    assert dict(_packet({}).building_tiles) == {}


def test_a_packet_that_carries_building_tiles_answers_from_them():
    packet = _packet({})
    carried = WorkerPacket(**{**{f: getattr(packet, f) for f in packet.__slots__}, "building_tiles": {(5, 5): "smithy"}})
    assert building_kind_at(carried, (5, 5)) == "smithy"


def test_a_lookup_on_a_worker_packet_returns_the_kind_on_a_building_tile_and_none_elsewhere_without_raising():
    packet = _packet({7: _inn()})
    assert building_kind_at(packet, (12, 10)) == "inn"
    assert building_kind_at(packet, (12, 11)) is None   # no building: this is the path that raised
    assert building_kind_at(packet, (0, 0)) is None


def test_service_reach_beside_a_building_on_a_worker_packet_finds_it_and_elsewhere_finds_nothing():
    packet = _packet({7: _inn()})
    assert service_tile(packet, (11, 10)) == (12, 10)            # orthogonally adjacent: in reach
    assert service_tile(packet, (11, 10), kinds=("inn",)) == (12, 10)
    assert service_tile(packet, (30, 30)) is None                 # every offset misses: all five fall through
    assert service_at(packet, (11, 10)) == ((12, 10), "inn")
    assert service_at(packet, (30, 30)) == ((30, 30), None)


def test_a_state_that_fills_building_tiles_is_still_honoured():
    state = SimpleNamespace(buildings={}, building_tiles={(5, 5): "smithy"}, entities={})
    assert building_kind_at(state, (5, 5)) == "smithy"
    assert building_kind_at(state, (5, 6)) is None
