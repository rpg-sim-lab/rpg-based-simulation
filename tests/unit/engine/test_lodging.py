"""F3 (divergence 2.155): a subject served a bed at a building lodges inside it. Real-Kernel tests: who lodges, the bed contest (grant before delivery), no bed free, beds 0."""
from dataclasses import replace

from src.core.state import TaskComponent
from src.engine.building_arrival import building_arrival_update
from src.engine.lodging import has_free_bed, is_lodged, lodgers_of
from src.engine.service_admission import admits, admits_at
from src.engine.sleep_debt import COLLAPSE_FLAG
from tests.unit.engine.lodging_kernel import INN_AT, INN_ID, REACH, hero, kernel, run


def _final(k, ticks=4):
    try:
        run(k, ticks)
        return {i: e for i, e in k._state.entities.items()}, k._state.buildings[INN_ID]
    finally:
        k.shutdown()


def _main_gold_per_hold():
    """What one hold of a bed costs a subject on main: a beds=0 inn serving the same REST (the worker result and the actions phase both merge the bed today, a defect with its own ticket;
    F3 reproduces the per-hold total exactly so its paired runs measure where the subject sleeps, not a cheaper inn)."""
    ents, _ = _final(kernel([hero(1, REACH[0])], beds=0))
    return 50 - ents[1].inventory.gold


def test_a_served_bed_lodges_the_subject_on_the_building_tile():
    ents, inn = _final(kernel([hero(1, REACH[0])], beds=2))
    assert ents[1].navigation.lodged_in == INN_ID and ents[1].navigation.position == INN_AT and is_lodged(ents[1])
    assert ents[1].inventory.gold == 50 - _main_gold_per_hold()   # the bed costs what it costs on main
    assert ents[1].task.payload.get("action") == "REST"


def test_an_eat_a_collapse_and_a_rest_with_no_inn_in_reach_do_not_lodge():
    eat = hero(1, REACH[0], action="EAT", debt=10.0, project=False)
    collapse = replace(hero(2, REACH[1], action="SLEEP", project=False), task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "SLEEP", COLLAPSE_FLAG: True}))
    rough = hero(3, (20.0, 20.0))                                   # a REST far from any building: sleeps where it stands
    ents, _ = _final(kernel([eat, collapse, rough], beds=5))
    assert not any(is_lodged(e) for e in ents.values())
    assert ents[3].navigation.position == (20.0, 20.0)


def test_a_lodger_s_gold_readiness_and_heal_per_hold_equal_main_s_beds_zero_hold():
    lodged, _ = _final(kernel([hero(1, REACH[0], debt=90.0)], beds=2))
    rough, _ = _final(kernel([hero(1, REACH[0], debt=90.0)], beds=0))
    assert is_lodged(lodged[1]) and not is_lodged(rough[1])
    assert lodged[1].inventory.gold == rough[1].inventory.gold
    assert lodged[1].combat.hp == rough[1].combat.hp and lodged[1].combat.readiness == rough[1].combat.readiness


def test_beds_zero_keeps_main_s_behaviour_the_rest_is_served_on_the_reach_tile():
    ents, inn = _final(kernel([hero(1, REACH[0])], beds=0))
    assert not is_lodged(ents[1]) and ents[1].navigation.position == REACH[0]
    assert ents[1].inventory.gold < 50                                # served on the reach tile, as before


def test_the_last_bed_goes_to_the_lowest_id_and_a_loser_is_never_charged_or_healed():
    claimants = [hero(3, REACH[2]), hero(1, REACH[0]), hero(2, REACH[1])]
    ents, inn = _final(kernel(claimants, beds=2, inn_gold=0))
    assert [i for i in (1, 2, 3) if is_lodged(ents[i])] == [1, 2]
    loser = ents[3]
    assert loser.inventory.gold == 50 and loser.combat.hp == 100                   # no charge, no heal ever applied to a refused claim
    assert loser.navigation.position == REACH[2] and not loser.task.payload        # it did not move and its REST ended
    project = loser.strategic.projects["p1"]
    assert project.status.value == "ABANDONED" and project.ended_by.value == "WAY_CLOSED" and not loser.strategic.current_project_id
    assert inn.inventory.gold == 2 * _main_gold_per_hold()                           # only the two granted beds were paid into the building, at main's price per hold


def test_a_full_building_does_not_admit_a_rest_and_beds_zero_gives_main_s_answer():
    k = kernel([hero(1, REACH[0]), hero(2, REACH[1]), hero(4, REACH[3], action=None)], beds=2)
    try:
        run(k, 3)
        st, inn = k._state, k._state.buildings[INN_ID]
        newcomer = st.entities[4]
        assert lodgers_of(st, INN_ID) == (1, 2)
        assert not has_free_bed(st, inn, newcomer) and not admits_at(newcomer, inn, "REST", st)
        assert has_free_bed(st, inn, st.entities[1]) and admits_at(st.entities[1], inn, "REST", st)   # a subject that holds a bed keeps it
        assert admits_at(newcomer, inn, "EAT", st) == admits(newcomer, "EAT")                          # only a REST is gated by beds
        no_beds = replace(inn, beds=0)
        for entity in st.entities.values():
            for action in ("EAT", "REST"):
                assert admits_at(entity, no_beds, action, st) == admits(entity, action)               # beds 0: main's answer on the whole grid
        # arrival with no bed: no REST is dispatched, the fatigue project ends with the typed way-closed end
        project = newcomer.strategic.projects.get("p1")
    finally:
        k.shutdown()


def test_an_arrival_with_no_bed_dispatches_no_rest_and_ends_the_project_way_closed():
    k = kernel([hero(1, REACH[0]), hero(2, REACH[1]), hero(4, REACH[3], action=None)], beds=2)
    try:
        run(k, 3)
        st = k._state
        newcomer = st.entities[4]
        project = newcomer.strategic.projects["p1"]
        update = building_arrival_update(st, newcomer, project, INN_ID)
        assert update.task is None                                        # no REST dispatched
        ended = update.strategic.projects_add_or_update[0]
        assert ended.status.value == "ABANDONED" and ended.ended_by.value == "WAY_CLOSED"
        # with a bed free it dispatches the REST as before
        free = building_arrival_update(st, st.entities[1], st.entities[1].strategic.projects["p1"], INN_ID)
        assert free.task is not None and free.task.payload_set["action"] == "REST"
    finally:
        k.shutdown()
