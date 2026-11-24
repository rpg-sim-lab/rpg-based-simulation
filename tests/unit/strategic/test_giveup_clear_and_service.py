"""F2 v2.2a A'' + C (divergence 2.220; rpg-designer ruling on the F2 v10.1 smoke): a give-up's clear beats a same-update target set near ITS OWN anchor, and a subject holding a pending give-up record is served by
the slow pass (no fast path) and by a work-queue tier (inside the G4 window). Each rule has a failing control: the same scene with the rule removed gives the other answer."""
from dataclasses import replace


from src.core.navigation_purpose import TargetPurpose
from src.core.builder import V2EntityBuilder
from src.core.dirty import DirtySet
from src.core.giveup_records import GIVEUP_NEAR_RADIUS, GiveUpRecord, anchored_target, near_anchor
from src.core.inventory import ItemStack
from src.core.state import AuthoritativeState
from src.core.updates import NavigationUpdate, StateUpdate
from src.engine import patches
from src.engine.cadence import SystemCadence
from src.engine.patches import NavigationPatch
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue
from tests.unit.strategic.experience_fixture import WANDER, an_experience, refuse

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
    assert anchored_target((60.0, 61.0), False, None, GiveUpRecord(P, 10), ())[0] == (60.0, 61.0) and anchored_target((60.0, 61.0), False, None, GiveUpRecord(Q, 10), ())[0] is None


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
    monkeypatch.setattr(patches, "anchored_target", lambda target_set, explicit, stored, record, anchor: (target_set if target_set is not None else (None if explicit else stored), False))
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
    return NavigationUpdate(target_clear=True, target_clear_anchors=(P,), **kw)


def test_the_pass_clear_for_anchor_p_beats_a_same_tick_walk_set_near_p():
    t, nav = _applied_target(_suppression_clear(target_set=(20.0, 20.0), path_set=[(6.0, 6.0)]))
    assert t is None and nav.path is None
    assert _applied_target(_suppression_clear(target_set=(21.0, 19.0)))[0] is None  # an adjacent tile too


def test_a_set_far_from_the_clear_anchor_stands():
    assert _applied_target(_suppression_clear(target_set=(35.0, 20.0)))[0] == (35.0, 20.0)
    assert _applied_target(_suppression_clear(target_set=(22.0, 20.0)))[0] == (22.0, 20.0)  # exactly Chebyshev 2


def test_a_give_up_record_and_a_suppression_clear_in_one_update_are_both_honoured_each_for_its_own_anchor():
    both = dict(giveup_record_add=GiveUpRecord(P, 10), clear_target=True, target_clear=True, target_clear_anchors=(Q,))
    assert _applied_target(NavigationUpdate(target_set=(20.0, 21.0), **both))[0] is None  # near the record's anchor P
    assert _applied_target(NavigationUpdate(target_set=(60.0, 59.0), **both))[0] is None  # near the clear's anchor Q
    assert _applied_target(NavigationUpdate(target_set=(40.0, 40.0), **both))[0] == (40.0, 40.0)  # near neither


def test_no_anchor_means_todays_precedence_the_set_beats_a_plain_clear():
    assert _applied_target(NavigationUpdate(target_clear=True, target_set=(20.0, 20.0)))[0] == (20.0, 20.0)
    assert anchored_target((20.0, 20.0), True, None, None, ()) == ((20.0, 20.0), False) and anchored_target((20.0, 20.0), True, None, None, (P,)) == (None, True)


def test_the_clear_anchor_is_a_typed_update_field_that_merges_and_counts_as_a_change():
    assert NavigationUpdate().is_noop() and not NavigationUpdate(target_clear_anchors=(P,)).is_noop()
    merged = NavigationUpdate(target_set=(20.0, 20.0)).merge(_suppression_clear())
    assert merged.target_clear_anchors == (P,) and merged.target_set == (20.0, 20.0) and merged.target_clear is True
    assert _applied_target(merged)[0] is None  # the merged update (walk first, the pass's clear after) loses its set


def test_control_the_same_scene_without_the_rule_keeps_the_walk_set(monkeypatch):
    monkeypatch.setattr(patches, "anchored_target", lambda target_set, explicit, stored, record, anchor: (target_set if target_set is not None else (None if explicit else stored), False))
    assert _applied_target(_suppression_clear(target_set=(20.0, 20.0)))[0] == (20.0, 20.0)


def _holding(e, target, purpose=WANDER):
    """``e`` holding ``target`` as its stored target, accepted with ``purpose`` (and not through the gate: no latch)."""
    return replace(e, navigation=replace(e.navigation, target=target, target_purpose=purpose, target_gated=False))


def test_the_fused_pass_clears_a_stored_target_near_an_active_experience_of_its_purpose_and_names_the_anchor_that_refused_it():
    from src.strategy.destination_suppression import suppression_anchors
    anchor = (20, 20)
    e = refuse(_holding(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build(), (20.0, 20.0)), anchor)
    assert suppression_anchors(e, (21.0, 20.0), 5, WANDER) == (anchor,) and suppression_anchors(e, (40.0, 40.0), 5, WANDER) == ()
    upd = _pass(e).entity_updates.get(1)
    assert upd is not None and upd.navigation is not None and upd.navigation.target_clear is True and upd.navigation.target_clear_anchors == (anchor,)


def test_a_stored_target_of_another_purpose_at_the_anchor_is_not_cleared():
    """Design section 7, the purpose-scoped source: the experience is of PURSUE, the stored target walks for WANDER, so the gate for the stored purpose does not refuse it and the pass clears nothing."""
    anchor = (20, 20)
    e = refuse(_holding(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build(), (20.0, 20.0)), anchor, purpose=TargetPurpose("none", "PURSUE"))
    upd = _pass(e).entity_updates.get(1)
    assert upd is None or upd.navigation is None or (upd.navigation.target_clear is False and not upd.navigation.target_clear_anchors)


# --- the filing anchor: the pass that files a suppression for P says so (target_clear_anchors WITHOUT target_clear) --------------------------------------------
def _filing(**kw):
    return NavigationUpdate(target_clear_anchors=(P,), **kw)


def _applied_with_stored(nav_update, stored):
    return _applied_target(nav_update, target=stored)


def test_filing_1_a_walk_sets_p_on_a_tick_with_no_stored_target_and_p_is_filed_the_set_is_dropped():
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).build()
    assert e.navigation.target is None
    changes = {}
    NavigationPatch(entity_id=1, navigation=_filing(target_set=(20.0, 20.0), path_set=[(6.0, 6.0)])).apply(e, changes)
    nav = changes["navigation"]
    assert nav.target is None and nav.path is None


def test_filing_2_the_same_with_a_walk_to_a_far_tile_stands():
    assert _applied_with_stored(_filing(target_set=(40.0, 40.0)), None)[0] == (40.0, 40.0)


def test_filing_3_a_stored_far_target_and_a_filing_for_p_is_unchanged():
    assert _applied_with_stored(_filing(), (40.0, 40.0))[0] == (40.0, 40.0)
    assert _applied_with_stored(_filing(path_set=[(1.0, 1.0)]), (40.0, 40.0))[0] == (40.0, 40.0)


def test_filing_4_a_stored_target_near_p_and_a_filing_for_p_with_no_set_is_cleared():
    t, nav = _applied_with_stored(_filing(), (21.0, 20.0))
    assert t is None and nav.path is None


def test_filing_5_the_record_the_refusal_clear_and_the_filing_anchor_in_one_update_give_one_consistent_result():
    upd = dict(giveup_record_add=GiveUpRecord(P, 10), clear_target=True, target_clear=True, target_clear_anchors=(P,))
    assert _applied_with_stored(NavigationUpdate(target_set=(20.0, 21.0), **upd), (40.0, 40.0))[0] is None  # a set near P loses to all three at once
    assert _applied_with_stored(NavigationUpdate(target_set=(40.0, 41.0), **upd), (21.0, 20.0))[0] == (40.0, 41.0)  # a far set stands even over a near stored target
    assert _applied_with_stored(NavigationUpdate(**upd), (21.0, 20.0))[0] is None


def test_filing_a_set_dropped_by_a_filing_leaves_a_far_stored_target_alone_and_clears_the_stored_path():
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).navigation(target=(40.0, 40.0), path=[(6.0, 6.0), (7.0, 7.0)]).build()
    assert e.navigation.path
    changes = {}
    NavigationPatch(entity_id=1, navigation=_filing(target_set=(20.0, 20.0))).apply(e, changes)
    nav = changes["navigation"]
    assert nav.target == (40.0, 40.0) and nav.path is None  # the target stays, the stored path is cleared so movement re-plans


def test_filing_control_without_the_rule_the_near_set_stands_and_the_near_stored_target_stays(monkeypatch):
    monkeypatch.setattr(patches, "anchored_target", lambda target_set, explicit, stored, record, anchor: (target_set if target_set is not None else (None if explicit else stored), False))
    assert _applied_with_stored(_filing(target_set=(20.0, 20.0)), None)[0] == (20.0, 20.0)
    assert _applied_with_stored(_filing(), (21.0, 20.0))[0] == (21.0, 20.0)


def test_the_pass_that_files_an_experience_carries_its_anchors_and_nothing_else_clears():
    from src.core.navigation_experience import NavigationExperienceUpdate
    from src.strategy.destination_suppression import filed_suppression_anchors, navigation_with_filing_anchor
    e = _holding(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build(), (40.0, 40.0))  # a stored target for WANDER, far from P
    filed = NavigationExperienceUpdate(upserts=(an_experience(P, from_position=(10, 10)),))
    assert filed_suppression_anchors(e, filed) == (P,)
    nav = navigation_with_filing_anchor(e, None, filed)
    assert nav.target_clear_anchors == (P,) and nav.target_clear is False and nav.clear_target is False  # a bare clear would clear a far stored target: it is not emitted
    assert filed_suppression_anchors(e, NavigationExperienceUpdate()) == () and navigation_with_filing_anchor(e, None, NavigationExperienceUpdate()) is None and filed_suppression_anchors(e, None) == ()
    other = replace(e, navigation=replace(e.navigation, target_purpose=TargetPurpose("none", "PURSUE")))
    assert filed_suppression_anchors(other, filed) == ()  # a stored target moving for ANOTHER purpose stays: the filing source is purpose-scoped
    assert filed_suppression_anchors(replace(e, navigation=replace(e.navigation, target=None, target_purpose=None)), filed) == ()  # no stored purpose, no filing anchor
    own = NavigationUpdate(target_clear=True, target_clear_anchors=(Q,))
    assert navigation_with_filing_anchor(e, own, filed).target_clear_anchors == tuple(sorted({P, Q})) and navigation_with_filing_anchor(e, own, filed).target_clear is True  # united with the refusal clear's, the clear kept


# --- the filing source end to end through the fused pass, and the several-anchors cases (architecture review) ------------------------------------------------
def _with_records(e, records):
    return replace(e, navigation=replace(e.navigation, giveup_records=tuple(records)))


def test_the_fused_pass_that_files_an_experience_returns_its_anchor_without_a_clear():
    """End to end: a pending record for P (with a purpose) is consumed by the pass, which files the experience; the subject's stored target is a far one of the same purpose; the update the pass returns carries P and NO clear. Removing the final-update wiring in intelligence.py fails this."""
    e = _with_records(_holding(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build(), (60.0, 60.0)), [GiveUpRecord(P, 3, purpose=WANDER)])
    upd = _pass(e).entity_updates.get(1)
    assert upd is not None and upd.navigation is not None
    assert upd.navigation.target_clear_anchors == (P,) and upd.navigation.target_clear is False and upd.navigation.clear_target is False


def test_control_a_pass_that_files_nothing_carries_no_anchor():
    upd = _pass(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build()).entity_updates.get(1)
    assert upd is None or upd.navigation is None or not upd.navigation.target_clear_anchors


def test_a_refusal_anchor_a_and_a_filing_anchor_b_in_one_tick_a_same_tick_set_near_b_is_dropped():
    assert _applied_target(NavigationUpdate(target_set=(60.0, 61.0), target_clear=True, target_clear_anchors=(P, Q)))[0] is None  # near Q
    assert _applied_target(NavigationUpdate(target_set=(20.0, 21.0), target_clear=True, target_clear_anchors=(P, Q)))[0] is None  # near P


def test_two_filings_b_and_c_a_set_near_c_is_dropped_and_a_set_far_from_all_stands():
    three = (P, Q, (100, 100))
    assert _applied_with_stored(NavigationUpdate(target_set=(100.0, 99.0), target_clear_anchors=three), None)[0] is None  # near the third anchor C
    assert _applied_with_stored(NavigationUpdate(target_set=(60.0, 60.0), target_clear_anchors=three), None)[0] is None
    assert _applied_with_stored(NavigationUpdate(target_set=(40.0, 40.0), target_clear_anchors=three), None)[0] == (40.0, 40.0)  # far from all of them


def test_merging_two_updates_with_different_anchors_gives_the_sorted_deduplicated_union_whatever_the_order():
    a = NavigationUpdate(target_clear_anchors=(Q, P))
    b = NavigationUpdate(target_clear_anchors=(P, (100, 100)))
    expected = tuple(sorted({P, Q, (100, 100)}))
    assert a.merge(b).target_clear_anchors == expected and b.merge(a).target_clear_anchors == expected
    assert a.merge(NavigationUpdate(target_set=(1.0, 1.0))).target_clear_anchors == tuple(sorted({P, Q}))  # an update with none leaves them


def test_control_a_rule_that_checks_only_the_first_anchor_leaves_the_set_near_the_second(monkeypatch):
    """A REAL control: production apply with anchored_target replaced by a version that looks at clear_anchors[0] only. The set near the second anchor then stands, so the test above would fail on that build."""
    real = anchored_target
    monkeypatch.setattr(patches, "anchored_target", lambda target_set, explicit, stored, record, anchors: real(target_set, explicit, stored, record, tuple(anchors[:1])))
    assert _applied_with_stored(NavigationUpdate(target_set=(60.0, 61.0), target_clear_anchors=(P, Q)), None)[0] == (60.0, 61.0)  # near Q (the second): stands under the broken rule
    assert _applied_with_stored(NavigationUpdate(target_set=(20.0, 21.0), target_clear_anchors=(P, Q)), None)[0] is None  # near P (the first): still dropped


def test_the_anchors_are_normalised_at_construction_so_a_no_op_merge_returns_the_sorted_pair():
    a = NavigationUpdate(target_clear_anchors=(Q, P, P))
    assert a.target_clear_anchors == tuple(sorted({P, Q}))
    assert a.merge(NavigationUpdate()).target_clear_anchors == tuple(sorted({P, Q}))  # `other` is a no-op: self comes back, already normalised
    assert a.merge(NavigationUpdate(target_set=(1.0, 1.0))).target_clear_anchors == tuple(sorted({P, Q}))


def test_the_lowest_anchor_selection_is_gone_every_filing_is_carried():
    from src.core.navigation_experience import NavigationExperienceUpdate
    from src.strategy.destination_suppression import filed_suppression_anchors
    e = _holding(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build(), (60.0, 60.0))
    a, b = (20, 20), (30, 30)
    filed = [an_experience(t, from_position=(10, 10)) for t in (b, a)]
    assert filed_suppression_anchors(e, NavigationExperienceUpdate(upserts=tuple(filed))) == (a, b) == filed_suppression_anchors(e, NavigationExperienceUpdate(upserts=tuple(filed[::-1])))


def test_an_experience_the_same_update_evicts_is_not_a_filing():
    from src.core.navigation_experience import NavigationExperienceUpdate
    from src.strategy.destination_suppression import filed_suppression_anchors
    e = _holding(V2EntityBuilder(1).kind("worker").location(10.0, 10.0).build(), (60.0, 60.0))
    record = an_experience(P, from_position=(10, 10))
    assert filed_suppression_anchors(e, NavigationExperienceUpdate(upserts=(record,), evictions=(record.experience_id,))) == ()
