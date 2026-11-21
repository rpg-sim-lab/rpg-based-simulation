"""F2 v2.2 / v2.2a (divergence 2.220; rpg-designer): the one proposal point of a place target, its same-pass staged read (D1), the per-class fallbacks (D2) and the give-up counter's state rule (D4).

D3 (filing with no project) is in test_giveup_filing.py. The source test that forbids an unguarded writer is tests/unit/engine/test_propose_target_single_path.py."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import BlockerState
from src.core.updates import EntityUpdate, NavigationUpdate, StrategicUpdate
from src.engine.executor import _entity_move_updates
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.engine.tactical_destinations import RETREAT_STEP, retreat_destination
from src.strategy.destination_suppression import (
    DestinationSuppressedEnd,
    ObjectiveDestinationSuppressed,
    access_blocker_id,
    destination_open,
    propose_target,
    regroup_to_town_update,
)

ANCHOR = (9, 5)


def _subject(blockers=(), records=(), pos=(5.0, 5.0), home=None):
    e = V2EntityBuilder(1).kind("HERO").location(*pos).build()
    strat = replace(e.strategic, blockers={b.id: b for b in blockers}, home_region_id=home)
    return replace(e, strategic=strat, navigation=replace(e.navigation, giveup_records=tuple(records)))


def _blocker(until=500, anchor=ANCHOR, giveups=1):
    return BlockerState(id=access_blocker_id(anchor), kind="access", subject=f"{anchor}", suppression_until_tick=until, giveup_count=giveups)


# --- the proposal point ---------------------------------------------------------------------------------------------------------------------------
def test_propose_target_returns_the_position_when_open_and_none_when_suppressed_or_pending():
    assert propose_target(_subject(), (9.0, 5.0), 10) == (9.0, 5.0)
    assert propose_target(_subject(blockers=(_blocker(),)), (10.0, 6.0), 10) is None  # Chebyshev 1 of the anchor
    assert propose_target(_subject(blockers=(_blocker(),)), (11.0, 5.0), 10) == (11.0, 5.0)  # two tiles away is open
    assert propose_target(_subject(blockers=(_blocker(until=10),)), (9.0, 5.0), 10) == (9.0, 5.0)  # the suppression has passed
    assert propose_target(_subject(records=(GiveUpRecord(ANCHOR, 9),)), (9.0, 5.0), 10) is None  # a stored pending record


# --- D1: the staged update of the same pass --------------------------------------------------------------------------------------------------------
def test_the_staged_give_up_record_and_the_staged_blocker_forbid_the_tile_in_the_pass_that_learns_of_them():
    e = _subject()
    assert destination_open(e, (9.0, 5.0), 10) and destination_open(e, (9.0, 5.0), 10, EntityUpdate(entity_id=1))
    staged_record = EntityUpdate(entity_id=1, navigation=NavigationUpdate(giveup_record_add=GiveUpRecord(ANCHOR, 10)))
    assert not destination_open(e, (9.0, 5.0), 10, staged_record)
    staged_blocker = EntityUpdate(entity_id=1, strategic=StrategicUpdate(blockers_add_or_update=[_blocker()]))
    assert not destination_open(e, (9.0, 5.0), 10, staged_blocker)
    assert destination_open(e, (20.0, 5.0), 10, staged_blocker) and destination_open(e, (9.0, 5.0), 10) is True  # the staged arg changes nothing stored


def test_a_staged_removal_lifts_a_stored_suppression_for_the_pass():
    e = _subject(blockers=(_blocker(),))
    staged = EntityUpdate(entity_id=1, strategic=StrategicUpdate(blockers_remove=[access_blocker_id(ANCHOR)]))
    assert not destination_open(e, (9.0, 5.0), 10) and destination_open(e, (9.0, 5.0), 10, staged)


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
    assert retreat_destination(state, e, threats) == full
    e_full = replace(e, strategic=replace(e.strategic, blockers={_blocker(anchor=(30, 20)).id: _blocker(anchor=(30, 20))}))
    assert retreat_destination(state, e_full, threats) == half  # (2)
    both = {b.id: b for b in (_blocker(anchor=(30, 20)), _blocker(anchor=(25, 20)))}
    e_both = replace(e, strategic=replace(e.strategic, blockers=both))
    assert retreat_destination(state, e_both, threats) == (40.0, 40.0)  # (3) home.center
    all_three = {b.id: b for b in (_blocker(anchor=(30, 20)), _blocker(anchor=(25, 20)), _blocker(anchor=(40, 40)))}
    assert retreat_destination(state, replace(e, strategic=replace(e.strategic, blockers=all_three)), threats) is None  # the caller's existing no-destination hold


def test_an_unsuppressed_flight_is_the_old_derivation():
    e = _subject(pos=(20.0, 20.0), home="home")
    state, threats = _flight_state(e, (15.0, 20.0))
    assert retreat_destination(state, e, threats) == (30.0, 20.0)


# --- D2 class X: the executor's re-emission -------------------------------------------------------------------------------------------------------
def test_the_executor_ends_a_held_move_whose_target_is_suppressed_typed_and_does_not_re_emit_it():
    e = _subject(blockers=(_blocker(),))
    out = _entity_move_updates(e, {"target_position": (9.0, 5.0)}, {1: e}, [], 10)[1]
    assert isinstance(out, DestinationSuppressedEnd) and out.navigation.target_clear is True and out.navigation.target_set is None
    assert out.task.work_kind_set == "ENTITY_ACT" and out.task.payload_set == {}
    free = _entity_move_updates(e, {"target_position": (30.0, 5.0)}, {1: e}, [], 10)[1]
    assert not isinstance(free, DestinationSuppressedEnd) and free.navigation.target_set == (30.0, 5.0)


# --- D2 class O: the investigate path -----------------------------------------------------------------------------------------------------------
def test_a_move_to_intent_at_a_suppressed_position_is_the_typed_idle_and_sets_no_target():
    e = _subject(blockers=(_blocker(),))
    intent = ActionIntent(kind="MOVE_TO", actor_id=1, payload={"position": (9.0, 5.0)}, reason="investigate")
    out = ActionIntentAdapter.execute(e, intent, current_tick=10)[1]
    assert isinstance(out, ObjectiveDestinationSuppressed) and out.navigation is None
    ok = ActionIntentAdapter.execute(e, ActionIntent(kind="MOVE_TO", actor_id=1, payload={"position": (30.0, 5.0)}, reason="investigate"), current_tick=10)[1]
    assert ok.navigation.target_set == (30.0, 5.0)


# --- the town regroup builder ----------------------------------------------------------------------------------------------------------------------
def test_the_regroup_builder_matches_both_forms_the_fused_pass_wrote_by_hand():
    from src.core.movement_modes import MovementMode
    town = (3.0, 4.0)
    fresh = regroup_to_town_update(1, None, town)
    assert fresh.entity_id == 1 and fresh.navigation.target_set == town and fresh.navigation.movement_mode_set == MovementMode.REGROUP and fresh.interaction.reset is True
    staged = EntityUpdate(entity_id=1, navigation=NavigationUpdate(path_set=[(1.0, 1.0)]))
    built = regroup_to_town_update(1, staged, town)
    assert built.navigation.path_set == [(1.0, 1.0)] and built.navigation.target_set == town and built.interaction.reset is True


# --- D4: the counter's state rule ------------------------------------------------------------------------------------------------------------------
def test_giveup_count_is_omitted_at_zero_carried_above():
    b0 = _blocker(giveups=0)
    assert "giveup_count" not in b0.canonical_dict()
    assert _blocker(giveups=2).canonical_dict()["giveup_count"] == 2


def test_an_older_checkpoint_blocker_fills_giveup_count_to_zero():
    from src.engine.checkpoint_fields import FIELD_RULES
    rule = next(r for r in FIELD_RULES if r.field == "giveup_count")
    assert rule.fill(None, None) == 0 and rule.ruling


def test_the_fingerprint_of_a_blocker_is_the_pre_f2_string_at_zero_and_adds_g_n_above():
    """D4, executed: the blockers' fragment is byte-identical to the pre-F2 format while giveup_count is 0, and carries ':g2' at 2."""
    from src.replay.fingerprint import _blocker_ident

    plain = BlockerState(id="b1", kind="access", subject="(9.0, 5.0)", severity=0.8)
    pre_f2 = f"{plain.id}:{plain.kind}:{plain.subject}:{plain.severity:.3f}:{plain.resolved}"
    assert _blocker_ident({"b1": plain}) == pre_f2
    assert _blocker_ident({"b1": replace(plain, giveup_count=2)}) == pre_f2 + ":g2"
