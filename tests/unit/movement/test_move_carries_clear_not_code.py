"""TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE (divergence 2.214): a MOVE carries the clear and no failure code.

A move is any position change by the movement apply path: the subject's own step, a swap, or a yield displacement (lodge entry and exit excluded). Before, a yielded
occupant was left holding ``YIELDING`` and both swapped bodies ``POSITION_SWAP`` after really moving, so ``last_failure_reason`` named a failure the body had just walked past."""
from dataclasses import replace

from src.core.enums import ReasonCode
from src.engine.movement import MovementSystem
from src.core.updates import EntityUpdate, NavigationUpdate
from src.engine.patches import NavigationPatch
from src.engine.pipeline_phases.movement import _merge_move_update
from tests.unit.engine.test_swaps_and_yields_pay_step_time import _swap, _swap_state, _yield_state

_PLAIN = {(x, y): "plain" for x in range(-1, 5) for y in range(-1, 4)}


def _with_reason(entity, reason):
    return replace(entity, navigation=replace(entity.navigation, last_failure_reason=reason))


def test_a_yield_displacement_moves_the_occupant_with_the_clear_and_no_code():
    state, hero = _yield_state(_PLAIN)
    upd = MovementSystem.resolve_move(state, hero, (2.0, 1.0))[2]
    assert upd.new_position is not None and upd.moved_this_tick is True
    assert upd.navigation.failure_reason is None
    assert upd.navigation.failure_reason_clear is True


def test_a_yielded_occupant_ends_the_tick_with_no_last_failure_reason():
    state, hero = _yield_state(_PLAIN)
    occupant = _with_reason(state.entities[2], "STUCK")
    upd = MovementSystem.resolve_move(state, hero, (2.0, 1.0))[2]
    changes = {}
    NavigationPatch(entity_id=2, navigation=upd.navigation).apply(occupant, changes)
    assert changes["navigation"].last_failure_reason is None


def test_both_swapped_bodies_end_the_tick_with_no_last_failure_reason():
    state = _swap_state("plain")
    state = replace(state, entities={1: _with_reason(state.entities[1], "PATH_NOT_FOUND"), 2: _with_reason(state.entities[2], "STUCK")})
    _, after = _swap(state)
    assert after.entities[1].navigation.position == (1.0, 0.0) and after.entities[2].navigation.position == (0.0, 0.0)
    assert after.entities[1].navigation.last_failure_reason is None
    assert after.entities[2].navigation.last_failure_reason is None


def test_occupancy_conflict_is_a_reason_code_member_with_the_same_value_as_the_old_literal():
    assert ReasonCode.OCCUPANCY_CONFLICT.value == "OCCUPANCY_CONFLICT"
    assert ReasonCode.OCCUPANCY_CONFLICT == "OCCUPANCY_CONFLICT"


def _step_failed(eid, code):
    return EntityUpdate(entity_id=eid, navigation=NavigationUpdate(failure_reason=code))


def _yielded(eid):
    return EntityUpdate(entity_id=eid, new_position=(3.0, 1.0), moved_this_tick=True, navigation=NavigationUpdate(moved_recently_set=True, failure_reason_clear=True))


def test_an_own_failed_step_then_a_yield_displacement_ends_the_phase_as_moved():
    codes = {}
    failed = _merge_move_update(None, _step_failed(2, ReasonCode.OCCUPANCY_VIOLATION), codes)
    assert failed.navigation.failure_reason == ReasonCode.OCCUPANCY_VIOLATION
    moved = _merge_move_update(failed, _yielded(2), codes)
    assert moved.new_position == (3.0, 1.0)
    assert moved.navigation.failure_reason is None and moved.navigation.failure_reason_clear is True


def test_a_code_from_an_earlier_phase_survives_a_later_move_of_the_same_body():
    codes = {}
    action = _step_failed(2, "SOURCE_DEPLETED")  # staged by action routing, which runs before movement routing
    moved = _merge_move_update(action, _yielded(2), codes)
    assert moved.new_position == (3.0, 1.0)
    assert moved.navigation.failure_reason == "SOURCE_DEPLETED"


def test_an_action_code_written_after_the_move_still_wins_at_the_patch():
    upd = _merge_move_update(None, _yielded(2), {})
    later = upd.navigation.merge(NavigationUpdate(failure_reason="TARGET_NOT_FOUND"))
    state, _ = _yield_state(_PLAIN)
    changes = {}
    NavigationPatch(entity_id=2, navigation=later).apply(state.entities[2], changes)
    assert changes["navigation"].last_failure_reason == "TARGET_NOT_FOUND"
