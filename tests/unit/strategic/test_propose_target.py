"""F2 v2.2 / v2.2a (divergence 2.220; rpg-designer): the one proposal point of a place target, its same-pass staged read (D1), the per-class fallbacks (D2) and the give-up counter's state rule (D4).

D3 (filing with no project) is in test_giveup_filing.py. The source test that forbids an unguarded writer is tests/unit/engine/test_propose_target_single_path.py."""
from dataclasses import replace

from src.core.navigation_purpose import TargetPurpose
from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.state import AuthoritativeState, RegionState
from src.core.navigation_experience import ExperienceReview, NavigationExperienceUpdate, ReviewReason
from src.core.updates import EntityUpdate, NavigationUpdate
from src.engine.executor import _entity_move_updates
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.engine.tactical_destinations import RETREAT_STEP, retreat_destination
from tests.unit.strategic.experience_fixture import an_experience, refuse
from src.strategy.destination_suppression import (
    DestinationSuppressedEnd,
    ObjectiveDestinationSuppressed,
    destination_open,
    propose_target,
    regroup_to_town_update,
)

ANCHOR = (9, 5)


def _subject(refused=(), records=(), pos=(5.0, 5.0), home=None, until=500):
    """A subject at ``pos`` that remembers a failed WANDER approach to each anchor in ``refused`` (until the tick ``until``) and holds ``records`` as pending give-ups."""
    e = V2EntityBuilder(1).kind("HERO").location(*pos).build()
    e = replace(e, strategic=replace(e.strategic, home_region_id=home), navigation=replace(e.navigation, giveup_records=tuple(records)))
    return refuse(e, *refused, until=until) if refused else e


# --- the proposal point ---------------------------------------------------------------------------------------------------------------------------
def test_propose_target_returns_the_position_when_open_and_none_when_suppressed_or_pending():
    assert propose_target(_subject(), (9.0, 5.0), 10, TargetPurpose("none", "WANDER")) == (9.0, 5.0)
    assert propose_target(_subject(refused=(ANCHOR,)), (10.0, 6.0), 10, TargetPurpose("none", "WANDER")) is None  # Chebyshev 1 of the anchor
    assert propose_target(_subject(refused=(ANCHOR,)), (11.0, 5.0), 10, TargetPurpose("none", "WANDER")) == (11.0, 5.0)  # two tiles away is open
    assert propose_target(_subject(refused=(ANCHOR,), until=10), (9.0, 5.0), 10, TargetPurpose("none", "WANDER")) == (9.0, 5.0)  # the refusal has passed (due at tick 10)
    assert propose_target(_subject(records=(GiveUpRecord(ANCHOR, 9),)), (9.0, 5.0), 10, TargetPurpose("none", "WANDER")) is None  # a stored pending record


# --- D1: the staged update of the same pass --------------------------------------------------------------------------------------------------------
def test_the_staged_give_up_record_forbids_the_tile_in_the_pass_that_learns_of_it_and_a_staged_experience_does_not_refuse_until_the_next_read():
    e = _subject()
    assert destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER")) and destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER"), EntityUpdate(entity_id=1))
    staged_record = EntityUpdate(entity_id=1, navigation=NavigationUpdate(giveup_record_add=GiveUpRecord(ANCHOR, 10)))
    assert not destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER"), staged_record)
    assert destination_open(e, (20.0, 5.0), 10, TargetPurpose("none", "WANDER"), staged_record) and destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER")) is True  # the staged arg changes nothing stored
    staged_experience = EntityUpdate(entity_id=1, navigation_experience=NavigationExperienceUpdate(upserts=(an_experience(ANCHOR),)))
    assert destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER"), staged_experience)  # the filing pass does not refuse by its own upsert: it applies from the next read


def test_a_staged_review_lifts_a_stored_experiences_refusal_for_the_pass():
    e = _subject(refused=(ANCHOR,))
    record = e.cognition.memory.navigation.records[0]
    staged = EntityUpdate(entity_id=1, navigation_experience=NavigationExperienceUpdate(reviews=(ExperienceReview(record.experience_id, record.cycle, 10, ReviewReason.DUE_TICK),)))
    assert not destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER")) and destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER"), staged)
    stale = EntityUpdate(entity_id=1, navigation_experience=NavigationExperienceUpdate(reviews=(ExperienceReview(record.experience_id, record.cycle + 1, 10, ReviewReason.DUE_TICK),)))
    assert not destination_open(e, (9.0, 5.0), 10, TargetPurpose("none", "WANDER"), stale)  # a review of another cycle lifts nothing (failing control)


# --- D2 class F: flight candidates ---------------------------------------------------------------------------------------------------------------
def _flight_state(e, threat_pos, home_center=(40.0, 40.0)):
    threat = V2EntityBuilder(2).kind("monster").location(*threat_pos).build()
    regions = {"field": RegionState(id="field", name="Field", bounds=(0, 0, 100, 100)), "home": RegionState(id="home", name="Home", bounds=(35, 35, 45, 45))}
    return AuthoritativeState(entities={1: e, 2: threat}, tick=10, seed=1, regions=regions), [threat]


def test_a_flight_tries_the_computed_point_then_half_the_distance_then_home_and_then_has_no_destination():
    e = _subject(pos=(20.0, 20.0), home="home")
    state, threats = _flight_state(e, (15.0, 20.0))  # the threat is west: away is east
    full = (20.0 + RETREAT_STEP, 20.0)
    half = (20.0 + RETREAT_STEP / 2.0, 20.0)
    assert retreat_destination(state, e, threats, TargetPurpose("none", "WANDER")) == full
    e_full = refuse(e, (30, 20))
    assert retreat_destination(state, e_full, threats, TargetPurpose("none", "WANDER")) == half  # (2)
    e_both = refuse(e, (30, 20), (25, 20))
    assert retreat_destination(state, e_both, threats, TargetPurpose("none", "WANDER")) == (40.0, 40.0)  # (3) home.center
    assert retreat_destination(state, refuse(e, (30, 20), (25, 20), (40, 40)), threats, TargetPurpose("none", "WANDER")) is None  # the caller's existing no-destination hold


def test_an_unsuppressed_flight_is_the_old_derivation():
    e = _subject(pos=(20.0, 20.0), home="home")
    state, threats = _flight_state(e, (15.0, 20.0))
    assert retreat_destination(state, e, threats, TargetPurpose("none", "WANDER")) == (30.0, 20.0)


# --- D2 class X: the executor's re-emission -------------------------------------------------------------------------------------------------------
def test_the_executor_ends_a_held_move_whose_target_is_suppressed_typed_and_does_not_re_emit_it():
    e = _subject(refused=(ANCHOR,))
    e = replace(e, navigation=replace(e.navigation, target_purpose=TargetPurpose("none", "WANDER")))  # the #996 rework: a re-emission carries the STORED purpose, so the fixture's held move has one
    out = _entity_move_updates(e, {"target_position": (9.0, 5.0)}, {1: e}, [], 10)[1]
    assert isinstance(out, DestinationSuppressedEnd) and out.navigation.target_clear is True and out.navigation.target_set is None
    assert out.task.work_kind_set == "ENTITY_ACT" and out.task.payload_set == {}
    free = _entity_move_updates(e, {"target_position": (30.0, 5.0)}, {1: e}, [], 10)[1]
    assert not isinstance(free, DestinationSuppressedEnd) and free.navigation.target_set == (30.0, 5.0)


def test_a_held_move_with_no_stored_purpose_ends_typed_even_toward_an_open_tile_and_with_one_it_carries_it():
    """The #996 rework (design section 4, v2.4): a re-emission carries the stored purpose and gate flag; a subject with none (a target restored from an old checkpoint) ends the move typed and re-decides."""
    e = _subject()
    assert e.navigation.target_purpose is None
    ended = _entity_move_updates(e, {"target_position": (30.0, 5.0)}, {1: e}, [], 10)[1]
    assert isinstance(ended, DestinationSuppressedEnd) and ended.navigation.target_set is None  # failing control: with the purpose below, the same open tile is re-emitted
    held = replace(e, navigation=replace(e.navigation, target_purpose=TargetPurpose("hunger", "WANDER"), target_gated=True))
    kept = _entity_move_updates(held, {"target_position": (30.0, 5.0)}, {1: held}, [], 10)[1]
    assert kept.navigation.target_set == (30.0, 5.0) and kept.navigation.target_purpose_set == TargetPurpose("hunger", "WANDER") and kept.navigation.target_gated_set is True


# --- D2 class O: the investigate path -----------------------------------------------------------------------------------------------------------
def test_a_move_to_intent_at_a_suppressed_position_is_the_typed_idle_and_sets_no_target():
    e = _subject(refused=(ANCHOR,))
    intent = ActionIntent(kind="MOVE_TO", actor_id=1, payload={"position": (9.0, 5.0)}, reason="investigate")
    out = ActionIntentAdapter.execute(e, intent, current_tick=10)[1]
    assert isinstance(out, ObjectiveDestinationSuppressed) and out.navigation is None
    ok = ActionIntentAdapter.execute(e, ActionIntent(kind="MOVE_TO", actor_id=1, payload={"position": (30.0, 5.0)}, reason="investigate"), current_tick=10)[1]
    assert ok.navigation.target_set == (30.0, 5.0)


# --- the town regroup builder ----------------------------------------------------------------------------------------------------------------------
def test_the_regroup_builder_matches_both_forms_the_fused_pass_wrote_by_hand():
    from src.core.movement_modes import MovementMode
    town = (3.0, 4.0)
    fresh = regroup_to_town_update(1, None, town, TargetPurpose("none", "WANDER"))
    assert fresh.entity_id == 1 and fresh.navigation.target_set == town and fresh.navigation.movement_mode_set == MovementMode.REGROUP and fresh.interaction.reset is True
    staged = EntityUpdate(entity_id=1, navigation=NavigationUpdate(path_set=[(1.0, 1.0)]))
    built = regroup_to_town_update(1, staged, town, TargetPurpose("none", "WANDER"))
    assert built.navigation.path_set == [(1.0, 1.0)] and built.navigation.target_set == town and built.interaction.reset is True


# --- D4: the blocker fingerprint is the pre-F2 string (the give-up counter on a blocker is gone) ------------------------------------------------------
def test_the_fingerprint_of_a_blocker_is_the_pre_f2_string():
    """The blockers' fragment is the pre-F2 format: the give-up counter lives on the navigation experience (`project_giveups`), not on a blocker."""
    from src.core.strategic import BlockerState
    from src.replay.fingerprint import _blocker_ident

    plain = BlockerState(id="b1", kind="access", subject="(9.0, 5.0)", severity=0.8)
    pre_f2 = f"{plain.id}:{plain.kind}:{plain.subject}:{plain.severity:.3f}:{plain.resolved}"
    assert _blocker_ident({"b1": plain}) == pre_f2
