"""The #996 rework (architecture review of the item 2 shape): the producer reads what the place of a give-up serves, AT the give-up, and carries it on the record; the consume step no longer looks a building up.

`need_services_at` is a pure read through main's building-kind table. The worker path and the serial path must give the SAME answer: a worker's read-only packet carries `buildings` and `building_map` but no `building_tiles` (service_reach.py), and `SpatialQueryService.get_building_at` reads the map either way."""
from types import SimpleNamespace

import src.engine.movement as movement
from src.core.giveup_records import GiveUpRecord
from src.core.navigation_experience import NavCause, NeedService, RingEvidence
from src.core.navigation_purpose import TargetPurpose
from src.core.state import AuthoritativeState, BuildingState
from src.engine.movement import need_services_at

EAT, REST = NeedService.EAT, NeedService.REST


def _reach_of(kind):
    """A `service_tile` stand-in: a building of ``kind`` is in reach of every tile, so a service is served exactly when ``kind`` is among the building kinds the real table declares for it."""
    return lambda state, tile, kinds=None: tile if kind in kinds else None


def test_the_producer_names_the_needs_the_building_in_reach_serves_through_the_existing_table(monkeypatch):
    monkeypatch.setattr(movement, "service_tile", _reach_of("inn"))
    assert need_services_at(object(), (9, 5)) == frozenset({EAT, REST})  # an inn serves both
    monkeypatch.setattr(movement, "service_tile", _reach_of("home"))
    assert need_services_at(object(), (9, 5)) == frozenset({REST})  # a home gives a bed and no food
    monkeypatch.setattr(movement, "service_tile", _reach_of("shop"))
    assert need_services_at(object(), (9, 5)) == frozenset()  # a place that is neither a food nor a bed tile
    monkeypatch.setattr(movement, "service_tile", lambda state, tile, kinds=None: None)
    assert need_services_at(object(), (9, 5)) == frozenset()


def _packet_like(state):
    """What a worker sees: the buildings and the building map, no `building_tiles`, no occupancy snapshot (WorkerPacket, core/worker_protocol.py)."""
    return SimpleNamespace(buildings=dict(state.buildings), building_map={b.position: b for b in state.buildings.values()}, tick=state.tick, entities={})


def test_the_worker_packet_and_the_serial_state_give_the_same_needs():
    inn, home = BuildingState(id=1, kind="inn", position=(10, 5)), BuildingState(id=2, kind="home", position=(30, 5))
    state = AuthoritativeState(tick=3, seed=1, buildings={inn.id: inn, home.id: home})
    packet = _packet_like(state)
    assert getattr(packet, "building_tiles", None) is None
    for anchor, want in (((10, 5), {EAT, REST}), ((11, 5), {EAT, REST}), ((30, 5), {REST}), ((31, 5), {REST}), ((20, 20), set())):
        assert need_services_at(state, anchor) == need_services_at(packet, anchor) == frozenset(want), anchor


def test_the_record_canonical_form_carries_the_needs_sorted_and_a_bare_record_the_empty_list():
    r = GiveUpRecord((9, 5), 7, NavCause.RING_BLOCKED, (RingEvidence.BODIES,), (5, 5), (9, 5), TargetPurpose("none", "WANDER"), frozenset({REST, EAT}))
    assert r.to_canonical()["need_services"] == ["EAT", "REST"]  # sorted values, not a set
    assert GiveUpRecord((9, 5), 7).to_canonical()["need_services"] == []  # a bare record: the default, still hashed (the digest hashes every field)
