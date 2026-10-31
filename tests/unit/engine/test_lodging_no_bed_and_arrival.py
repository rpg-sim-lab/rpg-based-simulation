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
