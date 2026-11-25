"""TCK-20261119-A-WORKER-BRAIN-THAT-WEIGHS-PAID-WORK-READS-THE-WORLD-INDEX-A-PACKET-DOES-NOT-CARRY: ``work_shift.shift_takeable`` is read from a tactical ENTITY_BRAIN worker
(``building_arrival._hunger_arrival``), where the state is a ``WorkerPacket``. It must find the inn the wage is spent at without the ``world_indexes`` a packet does not carry
(an undeclared state read stops the run: docs/engine/contracts/bounded_concurrency_contract.md section 4), and give the same answer it gives on the state."""
from dataclasses import replace

from src.core.state import BuildingState
from src.engine.work_shift import meal_position_after, shift_takeable
from tests.unit.kernel.test_executor_context_parity import _packet, _state


def _inn(bid, pos):
    return BuildingState(id=bid, kind="inn", position=pos, functional=True)


def _world(inns):
    state = _state()
    return replace(state, buildings={b.id: b for b in inns})


def test_shift_takeable_on_a_real_worker_packet_does_not_read_the_world_index():
    """The regression: before the fix this raised PacketFieldMissingError (executor-side read of AuthoritativeState.world_indexes)."""
    state = _world([_inn(1, (20.0, 10.0))])
    packet = _packet(state)
    entity = packet.subject
    assert shift_takeable(entity, packet, (15.0, 10.0)) == shift_takeable(state.entities[1], state, (15.0, 10.0))


def test_meal_position_after_is_the_same_on_the_packet_and_on_the_state():
    state = _world([_inn(1, (40.0, 10.0)), _inn(2, (20.0, 10.0)), _inn(3, (30.0, 30.0))])
    packet = _packet(state)
    assert meal_position_after(packet, (18.0, 10.0)) == meal_position_after(state, (18.0, 10.0)) == (20.0, 10.0)


def test_two_equidistant_inns_resolve_to_the_first_in_state_order_on_both():
    """Manhattan tie: the first strictly smaller wins, in ``state.buildings`` order (the order the world index is built in), on the state and on the frozen packet copy."""
    state = _world([_inn(7, (10.0, 20.0)), _inn(3, (20.0, 10.0))])
    packet = _packet(state)
    assert meal_position_after(state, (15.0, 15.0)) == meal_position_after(packet, (15.0, 15.0)) == (10.0, 20.0)


def test_no_inn_gives_none_on_both():
    state = _world([BuildingState(id=1, kind="shop", position=(20.0, 10.0), functional=True)])
    packet = _packet(state)
    assert meal_position_after(state, (15.0, 10.0)) is None and meal_position_after(packet, (15.0, 10.0)) is None


def test_the_scan_agrees_with_the_world_index_it_replaces():
    """Same answer as `SpatialQueryService.nearest_building` on the state, which stays the reader for every strategic-phase caller."""
    from src.engine.spatial_query import SpatialQueryService
    state = _world([_inn(1, (40.0, 10.0)), _inn(2, (20.0, 10.0)), _inn(3, (20.0, 30.0))])
    for pos in ((0.0, 0.0), (18.0, 10.0), (30.0, 30.0), (20.0, 20.0)):
        near = SpatialQueryService.nearest_building(state, pos, "inn")
        assert meal_position_after(state, pos) == (near.position[0], near.position[1])
