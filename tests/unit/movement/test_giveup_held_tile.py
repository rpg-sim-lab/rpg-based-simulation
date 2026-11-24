"""A full spot is not a failed spot (owner, #996, #715 7126061322): when the bounded way-round gives up and the stored target tile is HELD by another body at that moment (the existing
`LegalityServiceV2.get_occupant`, no new occupancy rule), the target is still dropped as before but NO give-up record is filed, so no navigation experience follows. A free target tile files as
before. Every test pairs the held scene with the same scene on a free tile (the failing control: the other answer), and the turn-taking scene runs the whole path: the give-up, the consume step, the
destination gate and the walk."""
from dataclasses import replace

from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

from src.content.navigation_experience_settings import navigation_experience_settings
from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.navigation_experience import NavCause, apply_experience_update
from src.core.navigation_purpose import TargetPurpose
from src.core.state import AuthoritativeState
from src.core.updates import StrategicUpdate
from src.engine.movement import MovementSystem
from src.engine.patches import NavigationPatch
from src.strategy.destination_suppression import propose_target
from src.systems.strategic_systems.blocker_lifecycle import consume_giveup_records

T = (9, 5)
P = TargetPurpose("none", "WANDER")


def _hero(**nav):
    return V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(**nav).build()


def _body(x, y, eid=20):
    return V2EntityBuilder(eid).kind("HERO").location(x, y).build()


def _wall(eid, x, y):
    return V2EntityBuilder(eid).kind("OBSTACLE").location(x, y).build()


def _spent_count(h):
    """The way-round count already spent on this target (the bounded give-up of 2.213), the stored purpose set: the next oscillation gives up."""
    return replace(h, navigation=replace(h.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=T, wayround_last_tick=0, target_purpose=P))


def _oscillation_hero():
    return _spent_count(_hero(target=T, last_position=(6, 5), oscillation_count=3))


def _give_up(entities, hero, tick=7):
    """resolve_move's result for ``hero`` toward T in a state holding ``entities`` (the hero among them)."""
    return MovementSystem.resolve_move(AuthoritativeState(entities=entities, tick=tick, seed=1), hero, T)[1]


def _apply_nav(entity, nav):
    changes = {}
    NavigationPatch(entity_id=entity.id, navigation=nav).apply(entity, changes)
    return replace(entity, navigation=changes["navigation"])


def _ring_scene(held):
    """A boxed-in hero (a body on three ring tiles, the fourth is the tile just left): the one-ring check finds no legal tile. ``held`` puts another body on the target tile."""
    h = _hero(target=T, last_position=(6, 5), oscillation_count=3)
    h = replace(h, navigation=replace(h.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=T, wayround_last_tick=0))
    ents = {1: h, 10: _wall(10, 5, 4), 11: _wall(11, 5, 6), 12: _wall(12, 4, 5)}
    if held:
        ents[20] = _body(*T)
    return _give_up(ents, h)


def _osc_scene(held):
    h = _oscillation_hero()
    ents = {1: h, **({20: _body(*T)} if held else {})}
    return _give_up(ents, h)


def test_a_held_target_tile_drops_the_target_and_files_no_record():
    for scene in (_osc_scene, _ring_scene):
        upd = scene(True)
        nav = upd.navigation
        assert upd.new_position is None and nav.clear_target is True and nav.clear_path is True  # the target is dropped, as before
        assert nav.failure_reason == ReasonCode.WAYROUND_GIVE_UP and nav.wayround_clear is True  # the same typed give-up as before
        assert nav.giveup_record_add is None  # a full spot is not a failed spot: no record, so no memory follows


def test_a_free_target_tile_files_the_record_as_before_the_failing_control():
    osc = _osc_scene(False).navigation
    assert osc.clear_target is True and osc.giveup_record_add is not None and osc.giveup_record_add.cause == NavCause.OSCILLATION and osc.giveup_record_add.anchor == T
    ring = _ring_scene(False).navigation
    assert ring.clear_target is True and ring.giveup_record_add is not None and ring.giveup_record_add.cause == NavCause.RING_BLOCKED


def test_the_target_tile_is_the_one_tested_not_a_body_elsewhere_in_the_ring():
    """Crowding AROUND a free tile still files (a known limit): bodies on the ring tiles, none on the target."""
    ring = _ring_scene(False).navigation
    assert ring.giveup_record_add is not None and ring.giveup_record_add.ring_evidence  # the ring was crowded and the record says so
    other = _hero(target=T, last_position=(6, 5), oscillation_count=3)
    other = replace(other, navigation=replace(other.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=T, wayround_last_tick=0))
    ents = {1: other, 10: _wall(10, 5, 4), 11: _wall(11, 5, 6), 12: _wall(12, 4, 5), 20: _body(10, 5, 20)}  # a body NEXT to the target tile, not on it
    assert _give_up(ents, other).navigation.giveup_record_add is not None


def _after_give_up(held, tick=7):
    """The subject after the give-up, the patch and the strategic consume step (the experience applied), as a whole pass would leave it."""
    h = _oscillation_hero()
    ents = {1: h, **({20: _body(*T)} if held else {})}
    upd = _give_up(ents, h, tick)
    b = _apply_nav(h, upd.navigation)
    _strat, eu = consume_giveup_records(b, StrategicUpdate(), None, tick)
    if eu.navigation_experience is not None:
        b = replace(b, cognition=replace(b.cognition, memory=replace(b.cognition.memory, navigation=apply_experience_update(b.cognition.memory.navigation, eu.navigation_experience))))
    return _apply_nav(b, eu.navigation) if eu.navigation is not None else b


def test_turn_taking_the_outside_body_gets_in_after_the_inside_one_leaves_within_a_bounded_number_of_ticks():
    """Two bodies, one tile. B (the subject) gives up while A holds T; A leaves; B re-targets T at once and walks in. The control: the same give-up on a FREE tile leaves the place refused for the review delay."""
    delay = navigation_experience_settings().oscillation_review_delay
    tick = 7
    held = _after_give_up(True, tick)
    assert held.navigation.giveup_records == () and held.cognition.memory.navigation.records == ()  # no memory of the place
    assert all(propose_target(held, (9.0, 5.0), tick + dt, P) == (9.0, 5.0) for dt in (1, 5, delay - 1, delay))  # open at once and throughout
    # A has left (the state holds only B): B re-targets T and steps in
    b = replace(held, navigation=replace(held.navigation, target=T, oscillation_count=0, wait_count=0))
    arrived = None
    for k in range(1, 9):
        upd = MovementSystem.resolve_move(AuthoritativeState(entities={1: b}, tick=tick + k, seed=1), b, T)[1]
        if upd.new_position is not None:
            b = replace(b, navigation=replace(b.navigation, position=upd.new_position, last_position=b.navigation.position, step_ready_tick=upd.navigation.step_ready_tick_set or 0))
        if (int(b.navigation.position[0]), int(b.navigation.position[1])) == T:
            arrived = k
            break
    assert arrived is not None and arrived <= 8  # bounded: the walk of 4 tiles takes 4 ticks
    # the failing control: the same give-up on a free tile files the record, and the gate refuses the place until it is due
    free = _after_give_up(False, tick)
    assert [r.experience_id for r in free.cognition.memory.navigation.records] == ["nx_9_5_none_WANDER"]
    assert propose_target(free, (9.0, 5.0), tick + 1, P) is None and propose_target(free, (9.0, 5.0), tick + delay - 1, P) is None
    assert propose_target(free, (9.0, 5.0), tick + delay, P) == (9.0, 5.0)  # refused for the whole delay, open when it is due


def test_the_give_up_is_deterministic_held_and_free_alike():
    for held in (True, False):
        first, second = _osc_scene(held), _osc_scene(held)
        assert repr(first.navigation) == repr(second.navigation) and first.new_position == second.new_position
        a, b = _after_give_up(held), _after_give_up(held)
        assert a.cognition.memory.navigation.to_canonical_dict() == b.cognition.memory.navigation.to_canonical_dict() and a.navigation.to_canonical_dict() == b.navigation.to_canonical_dict()
