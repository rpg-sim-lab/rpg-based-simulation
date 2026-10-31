"""F3 (divergence 2.155): a lodger leaves when its rest is over and its next decision is not to keep resting; where it steps out; and a lodger is in no spatial index."""
from dataclasses import replace

from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate, TaskUpdate
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.lodging import keeps_lodging, leave_tile, place_leavers
from src.engine.occupancy_snapshot import OccupancySnapshot
from src.engine.pipeline_phases.occupancy import OccupancyPhase
from src.engine.spatial import SpatialGrid
from src.engine.spatial_query import SpatialQueryService
from src.engine.world_index import WorldIndexService
from tests.unit.engine.lodging_kernel import INN_AT, INN_ID, REACH, hero, kernel, run

LEAVE_ORDER = ((10, 9), (11, 10), (10, 11), (9, 10))     # the reach offsets beside (10, 10) without the building tile: north, east, south, west


def _lodged(eid, action=None, debt=15.0, **kw):
    h = hero(eid, INN_AT, debt=debt, action=action, project=False, **kw)
    return replace(h, navigation=replace(h.navigation, lodged_in=INN_ID))


def _state(entities, beds=10, functional=True):
    k = kernel(entities, beds=beds)
    if not functional:
        st = k._state
        object.__setattr__(st, "buildings", {**st.buildings, INN_ID: replace(st.buildings[INN_ID], functional=False)})
    return k


def _leave_update(eids):
    return StateUpdate(entity_updates={e: EntityUpdate(entity_id=e, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "WORK"})) for e in eids})


def test_keeps_lodging_only_while_resting_or_eating():
    assert keeps_lodging("ENTITY_ACT", {"action": "REST"}) and keeps_lodging("ENTITY_ACT", {"action": "SLEEP"}) and keeps_lodging("ENTITY_ACT", {"action": "EAT"})
    assert not keeps_lodging("ENTITY_ACT", {}) and not keeps_lodging("ENTITY_BRAIN", {})      # the held rest ended this tick: the bed is free, nobody waits awake indoors
    assert not keeps_lodging("ENTITY_ACT", {"action": "WORK"}) and not keeps_lodging("ENTITY_ACT", {"action": "SELL"})   # only EAT was ruled; a seller leaves
    assert not keeps_lodging("ENTITY_MOVE", {"target_position": (1, 1)})


def test_leavers_take_the_reach_tiles_in_the_fixed_order_lowest_id_first():
    k = _state([_lodged(3), _lodged(1), _lodged(2)])
    try:
        out = place_leavers(k._state, _leave_update([1, 2, 3]))
        tiles = {e: (int(u.new_position[0]), int(u.new_position[1])) for e, u in out.entity_updates.items()}
        assert [tiles[1], tiles[2], tiles[3]] == list(LEAVE_ORDER[:3])
        assert all(u.navigation.lodged_in_clear and u.moved_this_tick for u in out.entity_updates.values())
    finally:
        k.shutdown()


def test_a_leaver_takes_the_nearest_free_tile_by_the_ring_when_the_reach_tiles_are_taken_and_stays_lodged_when_none_is_free():
    k = _state([_lodged(1)])
    try:
        st = k._state
        taken = {(10, 9), (11, 10), (10, 11), (9, 10)}
        assert leave_tile(st, (10, 10), taken) == (10, 8)                                  # distance 2: row first (north), then column
        every_near = {(10 + dx, 10 + dy) for dx in range(-3, 4) for dy in range(-3, 4) if abs(dx) + abs(dy) <= 3}
        assert leave_tile(st, (10, 10), every_near) is None
    finally:
        k.shutdown()


def test_a_leaver_with_no_free_tile_stays_lodged_awake_and_is_counted(monkeypatch):
    import src.engine.lodging as lodging
    k = _state([_lodged(1)])
    try:
        monkeypatch.setattr(lodging, "leave_tile", lambda *a, **kw: None)
        out = lodging.place_leavers(k._state, _leave_update([1]))
        assert out.rejections_delta.get("LODGE_EXIT_BLOCKED") == 1
        assert out.entity_updates[1].new_position is None and not (out.entity_updates[1].navigation and out.entity_updates[1].navigation.lodged_in_clear)
    finally:
        k.shutdown()


def test_a_lodger_that_keeps_resting_does_not_leave_and_a_walk_target_makes_it_leave():
    k = _state([_lodged(1, action="REST"), _lodged(2, action="REST")])
    try:
        rest = StateUpdate(entity_updates={})
        assert place_leavers(k._state, rest) is rest
        walk = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, navigation=NavigationUpdate(target_set=(20.0, 20.0)))})
        out = place_leavers(k._state, walk)
        assert out.entity_updates[2].navigation.lodged_in_clear and 1 not in out.entity_updates
    finally:
        k.shutdown()


def test_a_building_that_stops_being_functional_ejects_its_lodgers():
    k = _state([_lodged(1, action="REST"), _lodged(2, action="REST")], functional=False)
    try:
        out = place_leavers(k._state, StateUpdate(entity_updates={}))
        assert {e for e, u in out.entity_updates.items() if u.navigation.lodged_in_clear} == {1, 2}
    finally:
        k.shutdown()


def test_two_leavers_through_the_occupancy_phase_end_on_different_tiles_and_are_no_longer_lodged():
    k = _state([_lodged(1), _lodged(2)])
    try:
        out = OccupancyPhase.resolve(k._state, _leave_update([1, 2]))
        a, b = out.entity_updates[1], out.entity_updates[2]
        assert a.new_position != b.new_position and a.navigation.lodged_in_clear and b.navigation.lodged_in_clear
    finally:
        k.shutdown()


def test_a_lodger_is_in_no_occupancy_map_spatial_index_or_candidate_index():
    k = _state([_lodged(1, action="REST"), hero(2, REACH[0], action=None, project=False)])
    try:
        st = k._state
        lodger_tile = (int(INN_AT[0]), int(INN_AT[1]))
        assert lodger_tile not in SpatialQueryService.get_occupancy_map(st)
        assert lodger_tile not in OccupancySnapshot.from_state(st).occupancy_by_tile
        assert 1 not in {e for ids in WorldIndexService.get_indexes(st).entities_by_tile.values() for e in ids}
        assert 1 not in SpatialQueryService.nearby_entities(st, INN_AT, 5.0)
        assert 1 not in {e for ids in MovementCandidateSelector.position_index(st.entities).values() for e in ids}
        grid = SpatialGrid(st.entities, 10)
        assert 1 not in {e for ids in grid.grid.values() for e in ids} and 2 in {e for ids in grid.grid.values() for e in ids}
    finally:
        k.shutdown()


def test_an_inn_lodger_is_served_a_meal_from_the_building_tile():
    eater = _lodged(1, action="EAT", debt=10.0)
    eater = replace(eater, biological=replace(eater.biological, hunger=80.0))
    k = _state([eater])
    try:
        run(k, 2)
        e = k._state.entities[1]
        assert e.biological.hunger < 80.0 and e.inventory.gold < 50       # the meal was served and paid for from the building tile (the subject started lodged there)
        assert e.navigation.lodged_in is None and (int(e.navigation.position[0]), int(e.navigation.position[1])) in LEAVE_ORDER   # the meal is one tick; its task ended, so it stepped out
    finally:
        k.shutdown()


def test_through_a_real_tick_a_lodger_whose_task_is_no_longer_resting_steps_out_onto_a_reach_tile():
    leaver = replace(_lodged(1, action="HOLD"), task=_lodged(1).task)
    leaver = replace(leaver, task=replace(leaver.task, payload={"action": "HOLD"}))
    k = _state([leaver])
    try:
        run(k, 2)
        e = k._state.entities[1]
        assert e.navigation.lodged_in is None and (int(e.navigation.position[0]), int(e.navigation.position[1])) in LEAVE_ORDER
    finally:
        k.shutdown()
