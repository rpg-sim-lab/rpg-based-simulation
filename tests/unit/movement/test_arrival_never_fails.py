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
    # the control: two tiles away the held tile still drops the target and files nothing (the held-tile rule), as a give-up
    held_far = _replan(_hero_at(7, 5, (6, 5), _spent(), 2), (9.0, 5.0), _body(9, 5))
    assert held_far.arrived is False and held_far.gave_up is True and held_far.giveup_record is None


def test_an_arrived_walk_whose_count_is_not_exhausted_is_unchanged():
    fresh = _replan(_hero_at(9, 5, (8, 5), 0, None, anchor=None), (9.5, 5.0))  # no count open: the way-round step is taken, as today
    assert fresh.arrived is False and fresh.gave_up is False and fresh.effective_target is not None and fresh.wayround_set is not None
    # the control of the control: the same body with the count spent is the arrived outcome
    assert _replan(_hero_at(9, 5, (8, 5), _spent(), 0), (9.5, 5.0)).arrived is True


def test_arrival_beats_a_boxed_in_ring_too_arrived_never_fails():
    walls = [V2EntityBuilder(10).kind("OBSTACLE").location(9, 4).build(), V2EntityBuilder(11).kind("OBSTACLE").location(9, 6).build(), V2EntityBuilder(12).kind("OBSTACLE").location(10, 5).build()]
    boxed_arrived = _replan(_hero_at(9, 5, (8, 5), 0, None, anchor=None), (9.5, 5.0), *walls)  # the ring has no legal tile (a ring-blocked give-up today)
    assert boxed_arrived.arrived is True and boxed_arrived.giveup_record is None
    boxed_away = _replan(_hero_at(7, 5, (6, 5), 0, None, anchor=None), (9.5, 5.0), *[V2EntityBuilder(10 + i).kind("OBSTACLE").location(x, y).build() for i, (x, y) in enumerate([(7, 4), (7, 6), (8, 5)])])
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
