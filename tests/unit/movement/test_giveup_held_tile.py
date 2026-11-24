"""Other bodies at the place are waiting, not failure (owner #715 7126061322 for the held tile, then #715 7130838054 (1)+(2) and 7130979190, ruling 476631fe): when the bounded way-round gives up and ANOTHER body stands on the
stored target tile or on any tile within Chebyshev 1 of it (the existing `LegalityServiceV2.get_occupant`, ignoring the subject), the target is dropped as before and an OCCUPIED record is filed with BODIES evidence, due after the
short `occupied_review_delay`. A place with nobody within one tile files OSCILLATION / RING_BLOCKED as before. Every test pairs the occupied scene with the free one (the failing control: the other answer), and the turn-taking
scene runs the whole path: the give-up, the consume step, the destination gate and the walk."""
from dataclasses import replace

from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

from src.content.navigation_experience_settings import navigation_experience_settings
from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.navigation_experience import NavCause, RingEvidence, apply_experience_update
from src.core.navigation_purpose import TargetPurpose
from src.core.state import AuthoritativeState
from src.core.updates import StrategicUpdate
from src.engine.movement import MovementSystem, _place_occupied
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


def test_a_held_target_tile_drops_the_target_and_files_an_occupied_record():
    for scene in (_osc_scene, _ring_scene):
        upd = scene(True)
        nav = upd.navigation
        assert upd.new_position is None and nav.clear_target is True and nav.clear_path is True  # the target is dropped, as before
        assert nav.failure_reason == ReasonCode.WAYROUND_GIVE_UP and nav.wayround_clear is True  # the same typed give-up as before
        rec = nav.giveup_record_add
        assert rec is not None and rec.cause == NavCause.OCCUPIED and rec.ring_evidence == (RingEvidence.BODIES,) and rec.anchor == T and rec.target_tile == T  # waiting, filed: the memory follows


def test_a_free_target_tile_files_the_record_as_before_the_failing_control():
    osc = _osc_scene(False).navigation
    assert osc.clear_target is True and osc.giveup_record_add is not None and osc.giveup_record_add.cause == NavCause.OSCILLATION and osc.giveup_record_add.anchor == T
    ring = _ring_scene(False).navigation
    assert ring.clear_target is True and ring.giveup_record_add is not None and ring.giveup_record_add.cause == NavCause.RING_BLOCKED


def _ring_hero():
    h = _hero(target=T, last_position=(6, 5), oscillation_count=3)
    return replace(h, navigation=replace(h.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=T, wayround_last_tick=0))


def test_a_body_next_to_a_free_target_tile_files_occupied_and_not_ring_blocked():
    """Crowding AROUND a free tile is the queue: a body on a ring tile of the target (none on it) makes the give-up OCCUPIED (the retired accepted limit)."""
    h = _ring_hero()
    walls = {10: _wall(10, 5, 4), 11: _wall(11, 5, 6), 12: _wall(12, 4, 5)}
    for x, y in ((10, 5), (8, 4), (10, 6), (9, 6)):  # every ring tile shape: beside, diagonal, below
        rec = _give_up({1: h, **walls, 20: _body(x, y, 20)}, h).navigation.giveup_record_add
        assert rec is not None and rec.cause == NavCause.OCCUPIED and rec.ring_evidence == (RingEvidence.BODIES,)
    osc = _oscillation_hero()
    assert _give_up({1: osc, 20: _body(10, 5, 20)}, osc).navigation.giveup_record_add.cause == NavCause.OCCUPIED  # the way-round-spent branch too


def test_a_body_two_tiles_from_the_target_does_not_make_it_occupied_the_failing_control():
    h = _ring_hero()
    walls = {10: _wall(10, 5, 4), 11: _wall(11, 5, 6), 12: _wall(12, 4, 5)}
    assert _give_up({1: h, **walls, 20: _body(11, 5, 20)}, h).navigation.giveup_record_add.cause == NavCause.RING_BLOCKED
    osc = _oscillation_hero()
    assert _give_up({1: osc, 20: _body(11, 5, 20)}, osc).navigation.giveup_record_add.cause == NavCause.OSCILLATION


def test_the_subject_itself_on_the_places_ring_is_not_counted():
    """The subject stands on a ring tile of the target (Chebyshev 1) with nobody else near: nothing makes the place occupied (ignore self)."""
    h = _hero(target=T, last_position=(8, 5), oscillation_count=3)
    h = replace(h, navigation=replace(h.navigation, position=(8.0, 6.0), wayround_count=2, wayround_best_distance=4, wayround_anchor=T, wayround_last_tick=0, target_purpose=P))
    assert not _place_occupied(T, h, AuthoritativeState(entities={1: h}, tick=7, seed=1))
    assert _place_occupied(T, h, AuthoritativeState(entities={1: h, 20: _body(10, 4, 20)}, tick=7, seed=1))  # the failing control: another body on the ring


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


def test_turn_taking_the_outside_body_waits_the_occupied_delay_then_gets_in_after_the_inside_one_leaves_within_a_bounded_number_of_ticks():
    """Two bodies, one tile. B (the subject) gives up while A holds T and files OCCUPIED; B is refused until `occupied_review_delay`, then the place is open; A has left, so B walks in within delay + 8 ticks. The control: the
    same give-up on a FREE tile files OSCILLATION and the place stays refused for the whole oscillation delay."""
    settings = navigation_experience_settings()
    delay, osc_delay = settings.occupied_review_delay, settings.oscillation_review_delay
    tick = 7
    held = _after_give_up(True, tick)
    recs = held.cognition.memory.navigation.records
    assert [(r.experience_id, r.cause, r.project_giveups) for r in recs] == [("nx_9_5_none_WANDER", NavCause.OCCUPIED, 0)] and held.navigation.giveup_records == ()  # remembered, and not counted as a failure
    assert propose_target(held, (9.0, 5.0), tick + 1, P) is None and propose_target(held, (9.0, 5.0), tick + delay - 1, P) is None  # refused until it is due
    assert propose_target(held, (9.0, 5.0), tick + delay, P) == (9.0, 5.0)  # open when the short delay has run
    # A has left (the state holds only B): B re-targets T once the place is open and steps in
    b = replace(held, navigation=replace(held.navigation, target=T, oscillation_count=0, wait_count=0))
    arrived = None
    for k in range(1, 9):
        upd = MovementSystem.resolve_move(AuthoritativeState(entities={1: b}, tick=tick + delay + k, seed=1), b, T)[1]
        if upd.new_position is not None:
            b = replace(b, navigation=replace(b.navigation, position=upd.new_position, last_position=b.navigation.position, step_ready_tick=upd.navigation.step_ready_tick_set or 0))
        if (int(b.navigation.position[0]), int(b.navigation.position[1])) == T:
            arrived = k
            break
    assert arrived is not None and delay + arrived <= delay + 8  # bounded: the delay, then a walk of 4 tiles takes 4 ticks
    # the failing control: the same give-up on a free tile files OSCILLATION, and the gate refuses the place for the whole oscillation delay
    free = _after_give_up(False, tick)
    assert [(r.experience_id, r.cause) for r in free.cognition.memory.navigation.records] == [("nx_9_5_none_WANDER", NavCause.OSCILLATION)]
    assert propose_target(free, (9.0, 5.0), tick + 1, P) is None and propose_target(free, (9.0, 5.0), tick + osc_delay - 1, P) is None
    assert propose_target(free, (9.0, 5.0), tick + osc_delay, P) == (9.0, 5.0)  # refused for the whole delay, open when it is due


def test_a_place_still_taken_when_the_new_try_runs_out_files_a_fresh_occupied_cycle():
    """Repeat while occupied: after the wait the body may choose the place again; when its count runs out with the place still taken, the same short delay follows (cycle 2)."""
    delay = navigation_experience_settings().occupied_review_delay
    first = _after_give_up(True, 7)
    h = replace(first, navigation=replace(first.navigation, target=T, last_position=(6, 5), oscillation_count=3, wayround_count=2, wayround_best_distance=4, wayround_anchor=T, wayround_last_tick=0, target_purpose=P))
    tick = 7 + delay
    upd = _give_up({1: h, 20: _body(*T)}, h, tick)
    assert upd.navigation.giveup_record_add.cause == NavCause.OCCUPIED
    b = _apply_nav(h, upd.navigation)
    _strat, eu = consume_giveup_records(b, StrategicUpdate(), None, tick)
    rec = eu.navigation_experience.upserts[0]
    assert (rec.cycle, rec.cause, rec.next_review_tick, rec.project_giveups) == (2, NavCause.OCCUPIED, tick + delay, 0)


def test_the_give_up_is_deterministic_held_and_free_alike():
    for held in (True, False):
        first, second = _osc_scene(held), _osc_scene(held)
        assert repr(first.navigation) == repr(second.navigation) and first.new_position == second.new_position
        a, b = _after_give_up(held), _after_give_up(held)
        assert a.cognition.memory.navigation.to_canonical_dict() == b.cognition.memory.navigation.to_canonical_dict() and a.navigation.to_canonical_dict() == b.navigation.to_canonical_dict()
