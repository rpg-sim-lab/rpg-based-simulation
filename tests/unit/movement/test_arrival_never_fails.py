"""Arrived never fails (owner, #996, #715 7128509663 asked as 7127902957; the lead's record after it): a body ARRIVED at the walk's nav target (`src/core/arrival.py`, Manhattan distance <= 1) does not give up when the way-round
count runs out: the outcome is `arrived`, the walk ends (`target_clear`), no `WAYROUND_GIVE_UP` code, no record, and the pursuit's counters end. A body not arrived files as before, a walk whose count is not exhausted is unchanged, and
arrival beats the held-tile rule. Every test pairs the arrived scene with the same scene one tile further away (the control). The scenes are the dungeon-7 case: a body ON its target tile (target (x.5, y), distance 0.5) that has
shuffled between two in-band tiles until its count was spent."""
from dataclasses import replace

from src.core.arrival import ARRIVAL_DISTANCE, has_arrived
from src.core.builder import V2EntityBuilder
from src.core.navigation_experience import NavCause
from src.core.navigation_purpose import TargetPurpose
from src.core.state import AuthoritativeState
from src.engine.movement import MovementSystem, OscReplanOutcome, _wayround
from src.engine.patches import NavigationPatch
from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

P = TargetPurpose("none", "WANDER")
TICK = 7


def _hero_at(x, y, last, wayround_count, best, anchor=(9, 5)):
    h = V2EntityBuilder(1).kind("HERO").location(x, y).combat(readiness=100.0).navigation(target=(9.5, 5.0), last_position=last, oscillation_count=3).build()
    return replace(h, navigation=replace(h.navigation, wayround_count=wayround_count, wayround_best_distance=best, wayround_anchor=anchor, wayround_last_tick=0, target_purpose=P))


def _replan(hero, target_pos, *others):
    ents = {1: hero, **{o.id: o for o in others}}
    state = AuthoritativeState(entities=ents, tick=TICK, seed=1)
    return MovementSystem._oscillation_replan(hero, (float(hero.navigation.last_position[0]), float(hero.navigation.last_position[1])), target_pos, state, 1.0)


def _spent():
    """The count the next oscillation event pushes past the limit."""
    return _wayround().limit


def _body(x, y, eid=20):
    return V2EntityBuilder(eid).kind("HERO").location(x, y).build()


def test_the_arrival_rule_is_manhattan_at_most_one_tile_boundary_included():
    assert ARRIVAL_DISTANCE == 1.0
    assert has_arrived((9.0, 5.0), (9.5, 5.0)) and has_arrived((8.0, 5.0), (9.0, 5.0)) and has_arrived((9.0, 5.0), (9.0, 5.0))  # 0.5, 1.0 (the boundary), 0
    assert not has_arrived((7.0, 5.0), (9.0, 5.0)) and not has_arrived((8.0, 5.0), (9.5, 5.0)) and not has_arrived((8.0, 4.0), (9.0, 5.0))  # 2.0, 1.5, a diagonal step (2.0 Manhattan)
    assert not (1.0 < ARRIVAL_DISTANCE)  # the failing control of a strict rule: `<` would have said False at exactly 1.0


def test_the_dungeon_7_scene_arrived_and_shuffling_never_gives_up_and_files_nothing():
    arrived = _replan(_hero_at(9, 5, (8, 5), _spent(), 0), (9.5, 5.0))  # ON the target tile, distance 0.5, the count spent, no progress
    assert arrived.arrived is True and arrived.gave_up is False and arrived.giveup_record is None and arrived.effective_target is None
    assert arrived.osc_delta == -3  # the pursuit's counters are handed back to end
    # the control: the same walk one and a half tiles away is not arrived and gives up as today, with its record
    away = _replan(_hero_at(8, 5, (7, 5), _spent(), 1), (9.5, 5.0))
    assert away.arrived is False and away.gave_up is True and away.giveup_record is not None and away.giveup_record.cause == NavCause.OSCILLATION


def test_arrival_includes_the_boundary_exactly_one_tile_away():
    on_edge = _replan(_hero_at(8, 5, (7, 5), _spent(), 1), (9.0, 5.0))  # distance 1.0
    assert on_edge.arrived is True and on_edge.gave_up is False and on_edge.giveup_record is None
    past_edge = _replan(_hero_at(8, 5, (7, 5), _spent(), 1), (9.5, 5.0))  # distance 1.5
    assert past_edge.arrived is False and past_edge.gave_up is True and past_edge.giveup_record is not None


def test_held_tile_plus_arrived_arrival_wins_and_no_give_up_code_is_written():
    # another body HOLDS the target tile while the subject stands one tile away: arrived (the walk ends), not the held-tile give-up
    arrived_held = _replan(_hero_at(8, 5, (7, 5), _spent(), 1), (9.0, 5.0), _body(9, 5))
    assert arrived_held.arrived is True and arrived_held.gave_up is False and arrived_held.giveup_record is None
    # the control: two tiles away the held tile still drops the target, and the give-up now files OCCUPIED (a wait)
    held_far = _replan(_hero_at(7, 5, (6, 5), _spent(), 2), (9.0, 5.0), _body(9, 5))
    assert held_far.arrived is False and held_far.gave_up is True and held_far.giveup_record is not None and held_far.giveup_record.cause == NavCause.OCCUPIED  # waiting, filed (ruling 476631fe)


def test_an_arrived_walk_whose_count_is_not_exhausted_is_unchanged():
    fresh = _replan(_hero_at(9, 5, (8, 5), 0, None, anchor=None), (9.5, 5.0))  # no count open: the way-round step is taken, as today
    assert fresh.arrived is False and fresh.gave_up is False and fresh.effective_target is not None and fresh.wayround_set is not None
    # the control of the control: the same body with the count spent is the arrived outcome
    assert _replan(_hero_at(9, 5, (8, 5), _spent(), 0), (9.5, 5.0)).arrived is True


def test_arrival_beats_a_boxed_in_ring_too_arrived_never_fails():
    walls = [V2EntityBuilder(10).kind("OBSTACLE").location(9, 4).build(), V2EntityBuilder(11).kind("OBSTACLE").location(9, 6).build(), V2EntityBuilder(12).kind("OBSTACLE").location(10, 5).build()]
    boxed_arrived = _replan(_hero_at(9, 5, (8, 5), 0, None, anchor=None), (9.5, 5.0), *walls)  # the ring has no legal tile (a ring-blocked give-up today)
    assert boxed_arrived.arrived is True and boxed_arrived.giveup_record is None
    boxed_away = _replan(_hero_at(6, 5, (5, 5), 0, None, anchor=None), (9.5, 5.0), *[V2EntityBuilder(10 + i).kind("OBSTACLE").location(x, y).build() for i, (x, y) in enumerate([(6, 4), (6, 6), (7, 5)])])  # walls on the subject's own ring, none within one tile of the place (a wall there would be a body at the place: OCCUPIED)
    assert boxed_away.arrived is False and boxed_away.gave_up is True and boxed_away.giveup_record is not None and boxed_away.giveup_record.cause == NavCause.RING_BLOCKED


def _known_give_up_scene():
    """The scene the held-tile tests verified reaches the oscillation replan: (5,5) toward (9,5), the count spent, a free ring."""
    h = V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(target=(9, 5), last_position=(6, 5), oscillation_count=3).build()
    h = replace(h, navigation=replace(h.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=(9, 5), wayround_last_tick=0, target_purpose=P))
    return h, AuthoritativeState(entities={1: h}, tick=TICK, seed=1)


def test_resolve_move_ends_an_arrived_walk_with_target_clear_and_the_counters_and_no_give_up(monkeypatch):
    h, state = _known_give_up_scene()
    control = MovementSystem.resolve_move(state, h, (9, 5))[1].navigation  # not patched: the real give-up of this scene, with its code and record
    assert control.clear_target is True and control.failure_reason is not None and control.giveup_record_add is not None
    monkeypatch.setattr(MovementSystem, "_oscillation_replan", staticmethod(lambda *a, **k: OscReplanOutcome(None, -3, -1, None, False, None, True)))
    upd = MovementSystem.resolve_move(state, h, (9, 5))[1]
    nav = upd.navigation
    assert upd.new_position is None and nav.target_clear is True and nav.wayround_clear is True and nav.oscillation_count_delta == -3 and nav.wait_count_delta == -1
    assert nav.failure_reason is None and nav.giveup_record_add is None and nav.clear_target is False  # no WAYROUND_GIVE_UP code, no record
    changes = {}
    NavigationPatch(entity_id=1, navigation=nav).apply(h, changes)  # applied: the target is gone and the pursuit's counters are ended
    after = changes["navigation"]
    assert after.target is None and after.wayround_count == 0 and after.oscillation_count == 0 and after.giveup_records == ()


def test_the_arrived_outcome_is_deterministic():
    for hero, target in ((_hero_at(9, 5, (8, 5), _spent(), 0), (9.5, 5.0)), (_hero_at(8, 5, (7, 5), _spent(), 1), (9.5, 5.0))):
        assert _replan(hero, target) == _replan(hero, target)


# --- arrived THIS ATTEMPT (owner #715 7130852946, ruling 476631fe) ---------------------------------------------------------------------------------
def _nudged(flag):
    """The dungeon-8 scene: the body reached its place earlier in this attempt (``flag``), was nudged to a tile 1.5 away (Manhattan), and its count runs out."""
    h = _hero_at(8, 5, (7, 5), _spent(), 1)
    return replace(h, navigation=replace(h.navigation, arrived_this_attempt=flag))


def test_a_body_that_arrived_earlier_in_the_attempt_and_was_nudged_aside_files_nothing_and_a_body_that_never_arrived_files_as_before():
    out = _replan(_nudged(True), (9.5, 5.0))  # Manhattan 1.5 now: not arrived at the instant
    assert out.arrived is True and out.gave_up is False and out.giveup_record is None
    never = _replan(_nudged(False), (9.5, 5.0))  # the failing control: the same body that never reached the place
    assert never.arrived is False and never.gave_up is True and never.giveup_record is not None and never.giveup_record.cause == NavCause.OSCILLATION


def test_attempt_arrival_beats_occupied_and_a_never_arrived_body_in_a_crowd_files_occupied():
    crowd = (_body(9, 5), _body(10, 5, 21))
    assert _replan(_nudged(True), (9.5, 5.0), *crowd).arrived is True  # held target + arrived this attempt: nothing filed
    waiting = _replan(_nudged(False), (9.5, 5.0), *crowd)
    assert waiting.arrived is False and waiting.giveup_record is not None and waiting.giveup_record.cause == NavCause.OCCUPIED


def _applied(nav, entity=None):
    """The navigation component the patch leaves for ``nav`` applied to ``entity`` (default: the hero ON its target)."""
    h = entity or _hero_at(9, 5, (8, 5), 0, None, anchor=None)
    changes = {}
    NavigationPatch(entity_id=1, navigation=nav).apply(h, changes)
    return changes["navigation"]


def test_the_flag_is_set_by_movement_kept_on_a_same_value_target_and_cleared_by_a_change_or_a_clear():
    from src.core.updates import NavigationUpdate
    h = _hero_at(9, 5, (8, 5), 0, None, anchor=None)  # ON its target (9.5, 5.0)
    state = AuthoritativeState(entities={1: h}, tick=TICK, seed=1)
    upd = MovementSystem.resolve_move(state, h, (9.5, 5.0))[1]
    assert upd.navigation is not None and upd.navigation.arrived_this_attempt_set is True  # measured from the position BEFORE the step
    far = _hero_at(5, 5, (4, 5), 0, None, anchor=None)
    far_upd = MovementSystem.resolve_move(AuthoritativeState(entities={1: far}, tick=TICK, seed=1), far, (9.5, 5.0))[1]
    assert not (far_upd.navigation is not None and far_upd.navigation.arrived_this_attempt_set)  # the control: a body 4 tiles away measures nothing
    stored = _applied(NavigationUpdate(arrived_this_attempt_set=True), h)  # the patch stores the flag with the target it keeps
    assert stored.arrived_this_attempt is True and _applied(NavigationUpdate(), h).arrived_this_attempt is False  # the control: no flag named, none stored
    again = replace(h, navigation=stored)
    assert _applied(NavigationUpdate(target_set=(9.5, 5.0), target_purpose_set=P, target_gated_set=True), again).arrived_this_attempt is True  # the objective step re-sets the SAME value: kept
    assert _applied(NavigationUpdate(target_set=(12.5, 5.0), target_purpose_set=P, target_gated_set=True), again).arrived_this_attempt is False  # another value: cleared
    assert _applied(NavigationUpdate(target_clear=True), again).arrived_this_attempt is False and _applied(NavigationUpdate(clear_target=True), again).arrived_this_attempt is False
    assert _applied(NavigationUpdate(moved_recently_set=True), again).arrived_this_attempt is True  # an unrelated update keeps it


def test_a_true_measured_on_the_old_target_is_dropped_with_a_new_target_in_the_same_update():
    from src.core.updates import NavigationUpdate
    h = _hero_at(9, 5, (8, 5), 0, None, anchor=None)
    merged = NavigationUpdate(arrived_this_attempt_set=True).merge(NavigationUpdate(target_set=(12.5, 5.0), target_purpose_set=P, target_gated_set=True))
    assert merged.arrived_this_attempt_set is True and _applied(merged, h).arrived_this_attempt is False  # safe: the next resolve measures again


def test_the_flag_merges_true_wins_is_a_noop_only_while_false_and_is_canonical_only_while_true():
    from src.core.updates import NavigationUpdate
    assert NavigationUpdate().is_noop() and not NavigationUpdate(arrived_this_attempt_set=True).is_noop()
    assert NavigationUpdate(arrived_this_attempt_set=True).merge(NavigationUpdate(moved_recently_set=True)).arrived_this_attempt_set is True
    assert NavigationUpdate(moved_recently_set=True).merge(NavigationUpdate(arrived_this_attempt_set=True)).arrived_this_attempt_set is True
    h = _hero_at(9, 5, (8, 5), 0, None, anchor=None)
    assert "arrived_this_attempt" not in h.navigation.to_canonical_dict()
    assert replace(h.navigation, arrived_this_attempt=True).to_canonical_dict()["arrived_this_attempt"] is True


def test_each_outcome_is_byte_identical_on_a_repeat():
    from src.core.updates import NavigationUpdate
    for scene in (_nudged(True), _nudged(False)):
        assert repr(_replan(scene, (9.5, 5.0))) == repr(_replan(scene, (9.5, 5.0)))
    h = _hero_at(9, 5, (8, 5), 0, None, anchor=None)
    state = AuthoritativeState(entities={1: h}, tick=TICK, seed=1)
    assert repr(MovementSystem.resolve_move(state, h, (9.5, 5.0))) == repr(MovementSystem.resolve_move(state, h, (9.5, 5.0)))
    a, b = _applied(NavigationUpdate(arrived_this_attempt_set=True), h), _applied(NavigationUpdate(arrived_this_attempt_set=True), h)
    assert a.to_canonical_dict() == b.to_canonical_dict()
