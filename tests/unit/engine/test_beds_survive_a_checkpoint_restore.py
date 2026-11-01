"""F3 (divergence 2.155): `BuildingState.beds` is behaviour-bearing durable state. A scenario checkpoint is a pickle of the whole `AuthoritativeState`
(`src/engine/scenario_checkpoint.py`), so the field, the canonical dict that carries it, and a lodger's `navigation.lodged_in` must all come back, and lodging must still work on the restored state."""
import pickle

from src.engine.checkpoint import CanonicalStateHasher
from src.engine.kernel import Kernel
from src.observability.hard_law_monitor import HardLawMonitor
from src.engine.lodging import has_free_bed, is_lodged, lodgers_of
from src.platform.rng import DeterministicRNG
from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel, profile


def _restored(k):
    state = pickle.loads(pickle.dumps(k._state, protocol=pickle.HIGHEST_PROTOCOL))
    return Kernel(profile(), state, DeterministicRNG(1))


def test_beds_and_a_lodger_round_trip_through_a_checkpoint_and_lodging_still_works():
    k = kernel([hero(1, REACH[0])], beds=1)
    try:
        for _ in range(3):
            k.tick_once()
        assert is_lodged(k._state.entities[1]) and k._state.buildings[INN_ID].beds == 1
        before = CanonicalStateHasher.get_hash(k._state)
        r = _restored(k)
        try:
            assert r._state.buildings[INN_ID].beds == 1
            assert r._state.buildings[INN_ID].to_canonical_dict()["beds"] == 1
            assert CanonicalStateHasher.get_hash(r._state) == before
            assert is_lodged(r._state.entities[1]) and tuple(lodgers_of(r._state, INN_ID)) == (1,)
            assert not has_free_bed(r._state, r._state.buildings[INN_ID], None)         # the one bed is still held after the restore
            assert not HardLawMonitor.check_initial_placement(r._state)               # a restored lodger on the building tile is not a placement collision
            r.tick_once()
            assert r._state.buildings[INN_ID].beds == 1
        finally:
            r.shutdown()
    finally:
        k.shutdown()


def test_the_lodger_exemption_does_not_widen_an_unlodged_entity_on_an_occupied_tile_is_still_flagged():
    from dataclasses import replace
    k = kernel([hero(1, (10.0, 10.0), action=None, project=False)], beds=1)         # standing on the inn's own tile with lodged_in unset
    try:
        assert k._state.entities[1].navigation.lodged_in is None
        violations = HardLawMonitor.check_initial_placement(k._state)
        assert any(v.law_id == "LAW-SPAWN-OCCUPANCY" and v.entity_id in (1, INN_ID) for v in violations)
    finally:
        k.shutdown()
    h = hero(1, (10.0, 10.0), action=None, project=False)
    k2 = kernel([replace(h, navigation=replace(h.navigation, lodged_in=INN_ID))], beds=1)   # the same entity, lodged: exempt
    try:
        assert not HardLawMonitor.check_initial_placement(k2._state)
    finally:
        k2.shutdown()
