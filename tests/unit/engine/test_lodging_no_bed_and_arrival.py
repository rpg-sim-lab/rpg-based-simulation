"""F3 (divergence 2.155), Q-A and Q-B: a REST whose first execution is in reach of a full beds building does not run there; lodging IS arrival, so a lodger is never walked out by a redirect."""
from dataclasses import replace

from src.core.strategic import ObjectiveStatus, ProjectStatus
from src.core.updates import BiologicalUpdate, EntityUpdate
from src.engine.building_services import with_service
from src.engine.lodging import finds_no_bed, is_lodged, lodgers_of, no_bed_in_reach
from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel, run


def _full_inn_state(beds=2):
    """A kernel run until `beds` heroes lodge, plus a newcomer on the last reach tile with no task yet."""
    heroes = [hero(i + 1, REACH[i]) for i in range(beds)]
    k = kernel(heroes + [hero(9, REACH[3], action=None)], beds=beds)
    run(k, 3)
    assert lodgers_of(k._state, INN_ID) == tuple(range(1, beds + 1))
    return k


def _rest_update(entity_id):
    return {entity_id: EntityUpdate(entity_id=entity_id, biological=BiologicalUpdate(rest_pressure_delta=-30.0))}


def test_a_first_execution_rest_beside_a_full_inn_is_refused_with_a_typed_reason_and_a_fatigue_project_ends_way_closed():
    k = _full_inn_state()
    try:
        st = k._state
        newcomer = hero(9, REACH[3])                                                              # a REST at the inn with its fatigue project, first execution
        assert no_bed_in_reach(st, newcomer) is not None
        out = with_service(_rest_update(9), newcomer, "REST", st.tick, st)[9]
        assert out.navigation.failure_reason == "NO_BED_FREE" and not out.resource_transfers and out.biological is None   # no rest, no charge, no claim
        assert out.strategic.projects_add_or_update[0].ended_by.value == "WAY_CLOSED" and out.strategic.current_project_id_set == ""
    finally:
        k.shutdown()


def test_a_bare_rest_on_the_reach_tile_of_a_full_inn_is_refused_and_holds_nothing():
    k = _full_inn_state()
    try:
        st = k._state
        bare = hero(9, REACH[3], project=False)
        out = with_service(_rest_update(9), bare, "REST", st.tick, st)[9]
        assert out.navigation.failure_reason == "NO_BED_FREE" and out.biological is None and out.strategic is None   # typed refusal, no project to end
    finally:
        k.shutdown()


def test_a_non_coin_subject_a_held_rest_and_a_rest_far_from_the_inn_run_as_on_main():
    k = _full_inn_state()
    try:
        st = k._state
        non_coin = replace(hero(9, REACH[3]), identity=replace(hero(9, REACH[3]).identity, properties={}))
        assert not finds_no_bed(st, non_coin, st.buildings[INN_ID])
        base = _rest_update(9)
        assert with_service(base, non_coin, "REST", st.tick, st) == base                       # the service does not serve it: unchanged
        held = replace(hero(9, REACH[3]), task=replace(hero(9, REACH[3]).task, payload={"action": "REST", "target_id": INN_ID, "outcome": "SUCCESS"}))
        assert with_service(base, held, "REST", st.tick, st) == base                           # a held sleep repeats its action: not a first execution
        far = hero(9, (20.0, 20.0), project=False)
        assert no_bed_in_reach(st, far) is None and with_service(base, far, "REST", st.tick, st) == base
        no_beds = kernel([hero(9, REACH[3], action=None)], beds=0)
        try:
            assert no_bed_in_reach(no_beds._state, no_beds._state.entities[9]) is None             # a building that declares no beds is main's answer
        finally:
            no_beds.shutdown()
    finally:
        k.shutdown()


def test_two_subjects_dispatched_to_the_last_bed_in_one_tick_the_lowest_id_lodges_and_the_other_ends_way_closed_holding_no_tile():
    k = kernel([hero(1, REACH[0]), hero(2, REACH[1])], beds=1)
    try:
        run(k, 4)
        st = k._state
        assert is_lodged(st.entities[1]) and not is_lodged(st.entities[2])
        loser = st.entities[2]
        assert not loser.task.payload and loser.navigation.position == REACH[1]
        project = loser.strategic.projects["p1"]
        assert project.ended_by.value == "WAY_CLOSED" and project.status == ProjectStatus.ABANDONED and not loser.strategic.current_project_id
        assert loser.inventory.gold == 50 and loser.combat.hp == 100                            # no charge, no heal
    finally:
        k.shutdown()


def test_lodging_resolves_the_arrival_objective_keeps_the_project_active_and_the_lodger_stays_indoors_and_asleep_while_it_rests():
    k = kernel([hero(1, REACH[0], debt=95.0)], beds=1)
    try:
        run(k, 3)
        project = k._state.entities[1].strategic.projects["p1"]
        assert project.status == ProjectStatus.ACTIVE and [o.status for o in project.objectives] == [ObjectiveStatus.RESOLVED] and len(project.objectives) == 1
        positions = set()
        for _ in range(25):
            run(k, 1)
            e = k._state.entities[1]
            assert is_lodged(e) and (e.task.payload or {}).get("action") == "REST" and e.navigation.target is None
            positions.add(tuple(e.navigation.position))
            assert len(e.strategic.projects["p1"].objectives) == 1                                  # no new reach objective was created while lodged
        assert len(positions) == 1                                                                  # never carried off the building tile
    finally:
        k.shutdown()


def test_a_lodged_subjects_fatigue_project_with_a_resolved_objective_completes_through_its_own_debt_test():
    """Q-B (a)/(c): the project stays ACTIVE with its objective RESOLVED; the existing completion test (sleep debt below 20, `StrategicIntelligenceSystem.evaluate_strategic_intent`)
    still ends it, and while the need is not met it is left alone (not replanned, no new objective). The rest/leave/re-rest cycle at the wake line is main's, not F3's."""
    from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
    k = kernel([hero(1, REACH[0], debt=95.0)], beds=1)
    try:
        run(k, 3)
        st = k._state
        e = st.entities[1]
        assert e.strategic.projects["p1"].status == ProjectStatus.ACTIVE
        rested = replace(e, biological=replace(e.biological, sleep_debt=15.0))
        done = StrategicIntelligenceSystem.evaluate_strategic_intent(st, rested, force=True)
        assert [p.status for p in done.projects_add_or_update if p.id == "p1"] == [ProjectStatus.COMPLETED] and done.current_project_id_set == ""
        tired = StrategicIntelligenceSystem.evaluate_strategic_intent(st, e, force=True)
        assert not [p for p in tired.projects_add_or_update if p.id == "p1" and (p.status != ProjectStatus.ACTIVE or len(p.objectives) != 1)]
    finally:
        k.shutdown()


def test_the_lodger_indoors_hard_law_flags_a_lodged_entity_with_a_target_or_off_its_tile():
    from src.observability.hard_law_monitor import HardLawMonitor
    k = kernel([hero(1, REACH[0], debt=95.0)], beds=1)
    try:
        run(k, 3)
        st = k._state
        e = st.entities[1]
        assert is_lodged(e)
        ds = type("D", (), {"all_dirty_entities": {1}, "movement_entities": {1}})()
        assert not [v for v in HardLawMonitor.check_entities(st, ds) if v.law_id == "LAW-LODGER-INDOORS"]
        # the state is read-only here: the violating entity is checked through a shallow state view
        bad = replace(e, navigation=replace(e.navigation, target=(30.0, 30.0)))
        view = type("S", (), {"entities": {1: bad}, "buildings": st.buildings})()
        assert [v.law_id for v in HardLawMonitor.check_entities(view, ds) if v.law_id == "LAW-LODGER-INDOORS"] == ["LAW-LODGER-INDOORS"]
        off = replace(e, navigation=replace(e.navigation, position=(5.0, 5.0)))
        view = type("S", (), {"entities": {1: off}, "buildings": st.buildings})()
        assert [v.law_id for v in HardLawMonitor.check_entities(view, ds) if v.law_id == "LAW-LODGER-INDOORS"] == ["LAW-LODGER-INDOORS"]
    finally:
        k.shutdown()


def test_a_walk_target_in_the_same_update_as_a_granted_claim_does_not_survive_the_grant_and_is_counted():
    """The claim tick: another writer (the town-return fallback, the objective redirect) puts a walk target on the update that carries the claim. The subject is indoors from this tick, so the
    grant drops the target, mode and path (target_clear, clear_path) and counts it as LODGER_TARGET_DROPPED."""
    from src.core.movement_modes import MovementMode
    from src.core.updates import NavigationUpdate, StateUpdate
    from src.engine.lodging import grant_beds, lodge_claim
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        claim = lodge_claim(st.entities[1], st.buildings[INN_ID]).merge(
            EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(38.0, 23.0), movement_mode_set=MovementMode.REGROUP, path_set=[(38.0, 23.0)])))
        assert claim.navigation.target_set == (38.0, 23.0)                                          # the merge keeps the other writer's target beside the claim
        out = grant_beds(st, StateUpdate(entity_updates={1: claim}))
        nav = out.entity_updates[1].navigation
        assert nav.lodged_in_set == INN_ID and nav.target_set is None and nav.movement_mode_set is None and nav.path_set is None and nav.target_clear and nav.clear_path
        assert out.rejections_delta.get("LODGER_TARGET_DROPPED") == 1
        assert out.rejection_events[-1].actor_id == 1 and "REGROUP" in out.rejection_events[-1].target_id and "(38.0, 23.0)" in out.rejection_events[-1].target_id
    finally:
        k.shutdown()


def test_a_walk_target_written_after_the_grant_in_the_same_tick_is_dropped_at_the_leave_step():
    """The strategic phase runs after the grant and before the leave step: its fallback target for a subject granted a bed this tick (the update carries the claim) is dropped there, and the claim's own move
    onto the building tile is kept."""
    from src.core.movement_modes import MovementMode
    from src.core.updates import NavigationUpdate, StateUpdate
    from src.engine.lodging import lodge_claim, place_leavers
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        late = lodge_claim(st.entities[1], st.buildings[INN_ID]).merge(EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(38.0, 23.0), movement_mode_set=MovementMode.REGROUP)))
        out = place_leavers(st, StateUpdate(entity_updates={1: late}))
        u = out.entity_updates[1]
        assert u.navigation.lodged_in_set == INN_ID and u.navigation.target_set is None and u.navigation.target_clear and u.new_position is not None and u.moved_this_tick
        assert out.rejections_delta.get("LODGER_TARGET_DROPPED") == 1
    finally:
        k.shutdown()


def test_a_granted_claim_stands_on_the_building_tile_whatever_step_another_writer_merged_into_its_update():
    """A walk step onto the reach tile merged with the claim (the merge keeps the later position) must not decide where the lodger stands: a granted claim is placed on the building's tile."""
    from src.core.updates import StateUpdate
    from src.engine.lodging import grant_beds, lodge_claim
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        claim = lodge_claim(st.entities[1], st.buildings[INN_ID]).merge(EntityUpdate(entity_id=1, new_position=(9, 11), moved_this_tick=True))
        assert claim.new_position == (9, 11)
        out = grant_beds(st, StateUpdate(entity_updates={1: claim}))
        assert out.entity_updates[1].new_position == (10.0, 10.0) and out.entity_updates[1].moved_this_tick
    finally:
        k.shutdown()


def test_a_leaver_whose_step_is_refused_keeps_no_walk_target_so_it_is_never_lodged_holding_one():
    """A leaver is placed by `place_leavers`; a walk target another writer proposed for the same tick is dropped and counted, so a leave refused by the occupancy vet leaves a lodger with no target."""
    from src.core.movement_modes import MovementMode
    from src.core.updates import NavigationUpdate, StateUpdate, TaskUpdate
    from src.engine.lodging import place_leavers
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        e = st.entities[1]
        object.__setattr__(e, "navigation", replace(e.navigation, lodged_in=INN_ID, position=(10.0, 10.0)))
        upd = EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}),
                           navigation=NavigationUpdate(target_set=(10.0, 10.0), movement_mode_set=MovementMode.REGROUP))
        out = place_leavers(st, StateUpdate(entity_updates={1: upd}))
        u = out.entity_updates[1]
        assert u.navigation.lodged_in_clear and u.navigation.target_set is None and u.navigation.target_clear
        assert out.rejections_delta.get("LODGER_TARGET_DROPPED") == 1
    finally:
        k.shutdown()


def _lodged_stayer_kernel(items=True):
    """A hero lodged in the inn with a REST running, carrying an item (which makes the town-return fallback fire for anyone not lodged)."""
    from src.core.state import InventoryComponent  # noqa: F401
    k = kernel([hero(1, REACH[0], action="REST")], beds=1)
    st = k._state
    e = st.entities[1]
    inv = e.inventory
    if items:
        from src.core.inventory import ItemStack
        inv = replace(inv, items=[ItemStack(item_id="wood", quantity=1)])
    object.__setattr__(e, "navigation", replace(e.navigation, lodged_in=INN_ID, position=(10.0, 10.0)))
    object.__setattr__(e, "inventory", inv)
    return k


def test_the_claim_wins_the_merge_in_either_order_and_the_refused_step_is_counted():
    from src.core.updates import StateUpdate
    from src.engine.lodging import grant_beds, lodge_claim
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        claim = lodge_claim(st.entities[1], st.buildings[INN_ID])
        step = EntityUpdate(entity_id=1, new_position=(9, 11), moved_this_tick=True)
        for merged in (claim.merge(step), step.merge(claim)):
            out = grant_beds(st, StateUpdate(entity_updates={1: merged}))
            assert out.entity_updates[1].new_position == (10.0, 10.0) and out.entity_updates[1].navigation.lodged_in_set == INN_ID
        assert out.rejections_delta.get("LODGER_TARGET_DROPPED") in (1, None) and out.rejections_delta.get("LODGER_DROP_CLAIM_TICK") in (1, None)
        both = grant_beds(st, StateUpdate(entity_updates={1: claim.merge(step)}))
        assert both.rejections_delta["LODGER_DROP_CLAIM_TICK"] == 1 and both.rejections_delta["LODGER_TARGET_DROPPED"] == 1
    finally:
        k.shutdown()


def test_the_strategic_pass_writes_no_walk_target_for_a_lodged_stayer_but_does_for_the_same_subject_outdoors():
    from src.core.updates import StateUpdate
    from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
    k = _lodged_stayer_kernel()
    try:
        st = k._state
        out = StrategicIntelligenceSystem.fused_strategic_pass(st, StateUpdate(entity_updates={}))
        upd = out.entity_updates.get(1)
        assert upd is None or upd.navigation is None or upd.navigation.target_set is None
        e = st.entities[1]
        object.__setattr__(e, "navigation", replace(e.navigation, lodged_in=None, position=(30.0, 30.0)))
        outdoors = StrategicIntelligenceSystem.fused_strategic_pass(st, StateUpdate(entity_updates={}))
        u2 = outdoors.entity_updates.get(1)
        assert u2 is not None and u2.navigation is not None and u2.navigation.target_set is not None   # the check is not vacuous
    finally:
        k.shutdown()


def test_the_cognition_entry_strips_movement_from_a_stayers_decision_and_leaves_a_leavers_whole():
    from src.core.movement_modes import MovementMode
    from src.core.updates import NavigationUpdate, TaskUpdate
    from src.engine.lodging import suppress_stayer_movement
    k = _lodged_stayer_kernel(items=False)
    try:
        e = k._state.entities[1]
        walk = NavigationUpdate(target_set=(1.0, 1.0), movement_mode_set=MovementMode.REGROUP)
        stays = suppress_stayer_movement(e, EntityUpdate(entity_id=1, navigation=walk))
        assert stays.navigation.target_set is None and stays.navigation.movement_mode_set is None
        eats = suppress_stayer_movement(e, EntityUpdate(entity_id=1, navigation=walk, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT"})))
        assert eats.navigation.target_set is None
        leaves = EntityUpdate(entity_id=1, navigation=walk, task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={}))
        assert suppress_stayer_movement(e, leaves) is leaves
        outdoor = replace(e, navigation=replace(e.navigation, lodged_in=None))
        plain = EntityUpdate(entity_id=1, navigation=walk)
        assert suppress_stayer_movement(outdoor, plain) is plain
    finally:
        k.shutdown()


def test_a_starving_resting_lodger_gets_the_same_decisions_as_the_same_subject_resting_outdoors_on_main():
    """The skip must not pin a lodger in bed: the decision a hunger-woken sleeper makes is the decision it makes outdoors (beds=0 is main's behaviour). The action sequence over 60 ticks is equal."""
    from src.core.inventory import ItemStack

    def actions(beds):
        h = hero(1, REACH[0], debt=90.0, action="REST")
        h = replace(h, biological=replace(h.biological, hunger=97.0), inventory=replace(h.inventory, items=[ItemStack(item_id="bread", quantity=3)]))
        k = kernel([h], beds=beds)
        try:
            return [d[1][4] for _, d in run(k, 60)]
        finally:
            k.shutdown()
    assert actions(1) == actions(0)


def test_a_lodger_whose_held_rest_ends_on_tick_t_is_placed_outside_on_t_or_t_plus_1():
    """No tick is lost between the end of the held REST and the leave: the rest ends at the wake line, and the subject is off its bed the same tick or the next, never lodged and awake for longer."""
    k = kernel([hero(1, REACH[0], debt=59.95, action="REST")], beds=1)
    try:
        hist = run(k, 20)
        by_tick = {t: d[1] for t, d in hist}
        ended = next(t for t, s in sorted(by_tick.items()) if s[4] != "REST")
        assert by_tick[ended - 1][1] == INN_ID                       # it did lodge while the rest ran
        out = [t for t, s in sorted(by_tick.items()) if t >= ended and s[1] is None]
        assert out and out[0] <= ended + 1
        assert by_tick[out[0]][0] in REACH
    finally:
        k.shutdown()


def test_a_stayer_re_claiming_its_own_bed_is_not_a_counted_drop_but_a_real_step_is():
    """A REST executes every tick, so a lodger re-emits the claim's building-tile position while already standing on it. That is no move: it is not counted as a stayer drop.
    A step to any other tile is counted (the stayer count stays the finding the arm asserts is zero)."""
    from src.core.updates import StateUpdate
    from src.engine.lodging import drop_lodger_targets, lodge_claim
    k = _lodged_stayer_kernel(items=False)
    try:
        st = k._state
        claim = lodge_claim(st.entities[1], st.buildings[INN_ID])
        assert tuple(claim.new_position) == tuple(st.entities[1].navigation.position)
        out = drop_lodger_targets(st, StateUpdate(entity_updates={1: claim}), [])
        assert out.rejections_delta.get("LODGER_TARGET_DROPPED") is None
        step = EntityUpdate(entity_id=1, new_position=(9.0, 11.0), moved_this_tick=True)
        out = drop_lodger_targets(st, StateUpdate(entity_updates={1: step}), [])
        assert out.rejections_delta.get("LODGER_TARGET_DROPPED") == 1 and out.entity_updates[1].new_position is None
    finally:
        k.shutdown()
