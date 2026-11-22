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


def _chebyshev_literals(path):
    """Every comparison of a `max(abs(..), abs(..))` against the literal 1 (`<= 1`, `< 2`) in a module: a second copy of the radius."""
    import ast
    tree = ast.parse(open(path).read())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Call) and getattr(node.left.func, "id", None) == "max" and len(node.ops) == 1:
            op, comp = node.ops[0], node.comparators[0]
            if isinstance(comp, ast.Constant) and ((isinstance(op, ast.LtE) and comp.value == 1) or (isinstance(op, ast.Lt) and comp.value == 2)):
                found.append(node.lineno)
    return found


def test_the_near_radius_is_one_constant_shared_by_the_suppression_and_the_rule():
    assert GIVEUP_NEAR_RADIUS == 1 and near_anchor((21, 21), (20, 20)) and not near_anchor((22, 20), (20, 20))
    for path in ("src/strategy/destination_suppression.py", "src/systems/strategic_systems/blocker_lifecycle.py"):
        assert _chebyshev_literals(path) == [], path  # the radius is not written a second time


def test_control_the_literal_check_finds_a_planted_second_copy(tmp_path):
    p = tmp_path / "m.py"
    p.write_text("def f(a, b):\n    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1\n\ndef g(a, b):\n    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) < 2\n")
    assert _chebyshev_literals(str(p)) == [2, 5]


def test_a_set_at_exactly_chebyshev_two_stands_and_at_one_loses():
    assert _applied_target(_giveup(target_set=(22.0, 20.0)))[0] == (22.0, 20.0)
    assert _applied_target(_giveup(target_set=(22.0, 22.0)))[0] == (22.0, 22.0)
    assert _applied_target(_giveup(target_set=(21.0, 21.0)))[0] is None


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


# --- A'' generalised: the strategic pass's suppression clear carries its anchor (rpg-designer, F2 pairing re-run) ---------------------------------------------
def _suppression_clear(**kw):
    return NavigationUpdate(target_clear=True, target_clear_anchor=P, **kw)


def test_the_pass_clear_for_anchor_p_beats_a_same_tick_walk_set_near_p():
    t, nav = _applied_target(_suppression_clear(target_set=(20.0, 20.0), path_set=[(6.0, 6.0)]))
    assert t is None and nav.path is None
    assert _applied_target(_suppression_clear(target_set=(21.0, 19.0)))[0] is None  # an adjacent tile too


def test_a_set_far_from_the_clear_anchor_stands():
    assert _applied_target(_suppression_clear(target_set=(35.0, 20.0)))[0] == (35.0, 20.0)
    assert _applied_target(_suppression_clear(target_set=(22.0, 20.0)))[0] == (22.0, 20.0)  # exactly Chebyshev 2


def test_a_give_up_record_and_a_suppression_clear_in_one_update_are_both_honoured_each_for_its_own_anchor():
    both = dict(giveup_record_add=GiveUpRecord(P, 10), clear_target=True, target_clear=True, target_clear_anchor=Q)
    assert _applied_target(NavigationUpdate(target_set=(20.0, 21.0), **both))[0] is None  # near the record's anchor P
    assert _applied_target(NavigationUpdate(target_set=(60.0, 59.0), **both))[0] is None  # near the clear's anchor Q
    assert _applied_target(NavigationUpdate(target_set=(40.0, 40.0), **both))[0] == (40.0, 40.0)  # near neither


def test_no_anchor_means_todays_precedence_the_set_beats_a_plain_clear():
    assert _applied_target(NavigationUpdate(target_clear=True, target_set=(20.0, 20.0)))[0] == (20.0, 20.0)
    assert not giveup_clear_beats_target((20.0, 20.0), None, None) and giveup_clear_beats_target((20.0, 20.0), None, P)


def test_the_clear_anchor_is_a_typed_update_field_that_merges_and_counts_as_a_change():
    assert NavigationUpdate().is_noop() and not NavigationUpdate(target_clear_anchor=P).is_noop()
    merged = NavigationUpdate(target_set=(20.0, 20.0)).merge(_suppression_clear())
    assert merged.target_clear_anchor == P and merged.target_set == (20.0, 20.0) and merged.target_clear is True
    assert _applied_target(merged)[0] is None  # the merged update (walk first, the pass's clear after) loses its set


def test_control_the_same_scene_without_the_rule_keeps_the_walk_set(monkeypatch):
    monkeypatch.setattr(patches, "giveup_clear_beats_target", lambda *a, **k: False)
    assert _applied_target(_suppression_clear(target_set=(20.0, 20.0)))[0] == (20.0, 20.0)


def test_the_fused_pass_clears_a_suppressed_stored_target_and_names_the_anchor_that_refused_it():
    from src.core.strategic import BlockerState
    from src.strategy.destination_suppression import access_blocker_id, suppression_anchor
    anchor = (20, 20)
    e = V2EntityBuilder(1).kind("worker").location(10.0, 10.0).navigation(target=(20.0, 20.0)).build()
    blocker = BlockerState(id=access_blocker_id(anchor), kind="access", subject=f"{anchor}", suppression_until_tick=500, giveup_count=1)
    e = replace(e, strategic=replace(e.strategic, blockers={blocker.id: blocker}))
    assert suppression_anchor(e, (21.0, 20.0), 5) == anchor and suppression_anchor(e, (40.0, 40.0), 5) is None
    upd = _pass(e).entity_updates.get(1)
    assert upd is not None and upd.navigation is not None and upd.navigation.target_clear is True and upd.navigation.target_clear_anchor == anchor
