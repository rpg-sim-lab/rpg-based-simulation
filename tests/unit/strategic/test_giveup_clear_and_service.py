"""F2 v2.2a A'' + C (divergence 2.220; rpg-designer ruling on the F2 v10.1 smoke): a give-up's clear beats a same-update target set near ITS OWN anchor, and a subject holding a pending give-up record is served by
the slow pass (no fast path) and by a work-queue tier (inside the G4 window). Each rule has a failing control: the same scene with the rule removed gives the other answer."""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.dirty import DirtySet
from src.core.giveup_records import GIVEUP_NEAR_RADIUS, GiveUpRecord, giveup_clear_beats_target, near_anchor
from src.core.inventory import ItemStack
from src.core.state import AuthoritativeState
from src.core.updates import NavigationUpdate, StateUpdate
from src.engine import patches
from src.engine.cadence import SystemCadence
from src.engine.patches import NavigationPatch
from src.strategy import destination_suppression
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue

P = (20, 20)  # the anchor of the give-up in the update
Q = (60, 60)  # another anchor


def _applied_target(nav_update, target=(40.0, 40.0)):
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).navigation(target=target).build()
    changes = {}
    NavigationPatch(entity_id=1, navigation=nav_update).apply(e, changes)
    return changes["navigation"].target, changes["navigation"]


def _giveup(**kw):
    return NavigationUpdate(giveup_record_add=GiveUpRecord(P, 10), clear_target=True, clear_path=True, **kw)


# --- A'': the apply rule ------------------------------------------------------------------------------------------------------------------------
def test_a_set_on_the_anchor_loses_to_the_give_ups_clear():
    t, nav = _applied_target(_giveup(target_set=(20.0, 20.0), path_set=[(6.0, 6.0)]))
    assert t is None and nav.path is None and nav.giveup_records == (GiveUpRecord(P, 10),)


def test_a_set_on_an_adjacent_tile_loses_too():
    assert _applied_target(_giveup(target_set=(21.4, 19.2)))[0] is None


def test_a_far_set_stands_a_flee_keeps_its_tile():
    from src.core.movement_modes import MovementMode
    t, nav = _applied_target(_giveup(target_set=(35.0, 20.0), movement_mode_set=MovementMode.RETREAT))
    assert t == (35.0, 20.0) and nav.movement_mode == MovementMode.RETREAT


def test_no_record_in_the_update_the_set_wins_as_today():
    assert _applied_target(NavigationUpdate(target_set=(20.0, 20.0), clear_target=True))[0] == (20.0, 20.0)


def test_the_rule_reads_the_records_own_anchor_not_another():
    """A record for P with a set near a DIFFERENT anchor Q: the set stands (decided by P only; no world read, no stored blocker)."""
    upd = NavigationUpdate(giveup_record_add=GiveUpRecord(P, 10), clear_target=True, target_set=(60.0, 61.0))
    assert _applied_target(upd)[0] == (60.0, 61.0)
    assert not giveup_clear_beats_target((60.0, 61.0), GiveUpRecord(P, 10)) and giveup_clear_beats_target((60.0, 61.0), GiveUpRecord(Q, 10))


def test_the_near_radius_is_one_constant_shared_by_the_suppression_and_the_rule():
    assert GIVEUP_NEAR_RADIUS == 1 and near_anchor((21, 21), (20, 20)) and not near_anchor((22, 20), (20, 20))
    import inspect
    src = inspect.getsource(destination_suppression)
    assert "near_anchor" in src and "<= 1" not in src  # the radius is not written a second time in the suppression module


def test_control_the_same_scene_without_the_rule_keeps_the_set(monkeypatch):
    """Failing control: with the rule switched off the same-tile set stands, so the test above fails on a build without it."""
    monkeypatch.setattr(patches, "giveup_clear_beats_target", lambda *a, **k: False)
    assert _applied_target(_giveup(target_set=(20.0, 20.0)))[0] == (20.0, 20.0)


# --- C(a): the fast path ------------------------------------------------------------------------------------------------------------------------
OFF = SystemCadence(strategic_intelligence=1000, concern_evaluation=1000)


def _loaded(records=()):
    e = V2EntityBuilder(1).kind("worker").location(10.0, 10.0).inventory(items=[ItemStack(item_id="wood", quantity=1)]).build()
    return replace(e, navigation=replace(e.navigation, giveup_records=tuple(records)))


def _pass(entity):
    state = AuthoritativeState(tick=5, seed=1, entities={1: entity}, town_center=(50.0, 50.0), town_tiles=set())
    return StrategicIntelligenceSystem.fused_strategic_pass(state, StateUpdate(), cadence=OFF)


def _clears_records(result):
    upd = result.entity_updates.get(1)
    return bool(upd is not None and upd.navigation is not None and upd.navigation.giveup_records_clear)


def test_a_subject_with_a_pending_record_takes_the_slow_pass_and_consumes_it_off_cadence():
    assert _clears_records(_pass(_loaded([GiveUpRecord((90, 90), 3)])))


def test_control_without_a_record_the_off_cadence_subject_takes_the_fast_path():
    assert not _clears_records(_pass(_loaded()))


# --- C(b): the work queue ------------------------------------------------------------------------------------------------------------------------
def _queue(entities, budget, sweep):
    state = replace(AuthoritativeState(tick=10, seed=1), entities=entities)
    return StrategicWorkQueue.build(state, StateUpdate(), DirtySet(), budget=budget, sweep_interval=sweep)


def test_a_pending_record_is_served_next_pass_under_a_full_queue_and_a_long_sweep():
    failed = {i: V2EntityBuilder(i).navigation(oscillation_count=4).build() for i in range(1, 6)}  # five tier-1 subjects fill a budget of 1
    holder = replace(V2EntityBuilder(9).build(), navigation=replace(V2EntityBuilder(9).build().navigation, giveup_records=(GiveUpRecord((90, 90), 3),)))
    plain = V2EntityBuilder(10).build()
    q = _queue({**failed, 9: holder, 10: plain}, budget=1, sweep=1000)
    assert 9 in q and tuple(q[:5]) == (1, 2, 3, 4, 5)  # served, and after (not instead of) the higher tiers, none of which lost its place
    assert 10 not in q  # control: the same subject without a record is left to the sweep


def test_a_blocker_holder_keeps_its_own_tier_and_the_record_tier_is_the_last_urgent_one():
    from src.core.strategic import BlockerKind, BlockerState
    blocker = BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="gold", resolved=False)
    both = V2EntityBuilder(2).strategic(blockers={"b1": blocker}).build()
    both = replace(both, navigation=replace(both.navigation, giveup_records=(GiveUpRecord((90, 90), 3),)))
    rec = replace(V2EntityBuilder(1).build(), navigation=replace(V2EntityBuilder(1).build().navigation, giveup_records=(GiveUpRecord((90, 90), 3),)))
    assert _queue({1: rec, 2: both}, budget=1, sweep=1000) == (2, 1)
