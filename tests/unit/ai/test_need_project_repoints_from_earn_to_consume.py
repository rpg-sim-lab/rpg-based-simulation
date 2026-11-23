"""#995 case (c) (trace v6, designer ruling; TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1): a need project made while the subject could not pay keeps its EARN objective after the coin is in hand
(the objective is frozen at the way it was made with, and the switch check refuses a same-need candidate), so the subject started NEW shifts with the meal affordable.

`live_record_route.repoint_earn_to_consume`: when the existing record is the CURRENT project of a need kind, its active objective is an EARN step (a building that offers a shift, a shop, or the
seek-work town centre), the candidate is the direct consume way open now AND admitted to the subject (`work_shift.meal_in_reach` for hunger; the bed the scorer targets for fatigue) and no
shift is HELD in progress (`work_shift.shift_held`), the route returns an update that re-points the SAME project's active objective (old objective RESOLVED, a new REACH_LOCATION objective
at the candidate's target, no new project, no switch check). The arrival never starts a NEW shift while the same predicate holds (`building_arrival`), so the guarantee does not wait for the next strategic pass."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals import live_record_route
from src.ai.goals.base import GoalScore, NeedAccess
from src.ai.goals.live_record_route import route_live_record
from src.core.strategic import SEEK_WORK_TARGET_ID, GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.building_arrival import building_arrival_update
from src.engine.work_shift import SHIFT_TICKS, shift_held
from tests.unit.engine.test_earn_shift import _consumers, _hall, _inn, _state, _worker  # noqa: F401  (_consumers: the module's autouse content fixture)

HALL, INN = 10, 11
TICK = 500


def _project(kind=GoalKind.HUNGER, target=str(HALL), pos=(20.0, 10.0), pid="proj_need_1"):
    obj = ObjectiveState(id=f"{kind.value}_{target}", kind=ObjectiveKind.REACH_LOCATION, target=target, target_position=pos, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id=pid, kind=kind, status=ProjectStatus.ACTIVE, score=90.0, objectives=[obj], active_objective_id=obj.id)


def _with(ent, project, task_payload=None):
    ent = replace(ent, strategic=replace(ent.strategic, projects={project.id: project}, current_project_id=project.id))
    return ent if task_payload is None else replace(ent, task=replace(ent.task, payload=task_payload))


def _candidate(kind=GoalKind.HUNGER, target=INN, access=NeedAccess.WAY_WITHIN_REACH):
    return GoalScore(kind=kind, utility=80.0, target_id=str(target), target_pos=(30.0, 10.0), need_access=access if kind == GoalKind.HUNGER else None)


def _route(ent, state, candidate):
    return route_live_record(ent, candidate, lambda e, i: None, state)


def _case1_assertions(route, project):
    """The expectation of case 1, kept as a function so the mutant test can show it FAILS without the re-point."""
    upd = route.update
    assert upd is not None
    assert [p.id for p in upd.projects_add_or_update] == [project.id]  # the SAME project, no new one
    moved = upd.projects_add_or_update[0]
    active = next(o for o in moved.objectives if o.id == moved.active_objective_id)
    assert active.target == str(INN) and active.status == ObjectiveStatus.ACTIVE and upd.current_objective_id_set == active.id
    old = next(o for o in moved.objectives if o.id != active.id)
    assert old.target == str(HALL) and old.status == ObjectiveStatus.RESOLVED  # the earn step's purpose, having the coin, is met


def _world(gold, kind="human", hunger=60.0, task_payload=None, tick=TICK):
    ent = _worker(hunger=hunger, gold=gold)
    if kind != "human":
        from src.core.builder import V2EntityBuilder
        e = V2EntityBuilder(1).kind(kind).properties({"species_id": kind}).location(10.0, 10.0).inventory(gold=gold).build()
        ent = replace(e, biological=replace(e.biological, hunger=hunger))
    project = _project()
    ent = _with(ent, project, task_payload)
    return ent, project, _state(ent, _hall(), _inn(), tick=tick)


def test_a_hunger_project_on_a_work_objective_is_repointed_to_the_inn_once_the_price_is_in_hand():
    ent, project, state = _world(gold=6)
    _case1_assertions(_route(ent, state, _candidate()), project)


def test_the_work_objective_is_kept_while_gold_is_below_the_price():
    ent, project, state = _world(gold=3)
    assert _route(ent, state, _candidate()).update is None  # the meal is not admitted: no re-point, the earn objective stays


def test_a_non_coin_body_is_not_repointed():
    ent, project, state = _world(gold=50, kind="troll")
    assert _route(ent, state, _candidate()).update is None  # admission carries the coin trait (2.224): a body the inn refuses is never re-pointed to it


def test_a_held_shift_is_not_cut_and_the_project_is_repointed_after_it_ends():
    held = {"action": "WORK", "target_id": HALL, "shift_start": TICK - 50}
    ent, project, state = _world(gold=6, task_payload=held)
    assert shift_held(ent, state) and _route(ent, state, _candidate()).update is None
    ended = {"action": "WORK", "target_id": HALL, "shift_start": TICK - (SHIFT_TICKS - 1)}  # the wage tick: elapsed ticks = SHIFT_TICKS, no longer held
    ent2, project2, state2 = _world(gold=6, task_payload=ended)
    assert not shift_held(ent2, state2)
    _case1_assertions(_route(ent2, state2, _candidate()), project2)  # a lingering WORK action alone is not a held shift


def test_a_rest_project_on_a_work_objective_is_repointed_to_the_paid_bed():
    ent, project, state = _world(gold=12)
    project = _project(kind=GoalKind.FATIGUE)
    ent = _with(ent, project)
    state = _state(ent, _hall(), _inn())
    route = _route(ent, state, _candidate(kind=GoalKind.FATIGUE))
    assert route.update is not None and route.update.projects_add_or_update[0].id == project.id
    moved = route.update.projects_add_or_update[0]
    assert next(o for o in moved.objectives if o.id == moved.active_objective_id).target == str(INN)


def test_a_seek_work_objective_is_repointed_too():
    ent, _p, _s = _world(gold=6)
    project = _project(target=SEEK_WORK_TARGET_ID, pos=(0.0, 0.0))
    ent = _with(ent, project)
    state = _state(ent, _hall(), _inn())
    route = _route(ent, state, _candidate())
    assert route.update is not None and route.update.projects_add_or_update[0].id == project.id


def test_a_sell_objective_at_a_shop_is_repointed_too():
    from src.core.state import BuildingState, InventoryComponent
    ent, _p, _s = _world(gold=6)
    shop = BuildingState(id=12, kind="shop", position=(11.0, 10.0), functional=True, inventory=InventoryComponent(gold=100))
    project = _project(target="12", pos=(11.0, 10.0))
    ent = _with(ent, project)
    state = _state(ent, shop, _inn())
    assert _route(ent, state, _candidate()).update is not None


def test_an_objective_that_is_not_an_earn_step_is_untouched():
    ent, _p, _s = _world(gold=6)
    project = _project(target="9999", pos=(12.0, 10.0))  # not a building at all (a food node id): no earn step, no re-point, so no thrash between consume ways
    ent = _with(ent, project)
    state = _state(ent, _hall(), _inn())
    assert _route(ent, state, _candidate()).update is None


def test_a_non_current_record_is_not_repointed():
    ent, project, state = _world(gold=6)
    ent = replace(ent, strategic=replace(ent.strategic, current_project_id=""))
    assert _route(ent, state, _candidate()).update is None  # the contest goes to the switch check as before


def test_the_removed_repoint_mutant_fails_case_1(monkeypatch):
    ent, project, state = _world(gold=6)
    monkeypatch.setattr(live_record_route, "repoint_earn_to_consume", lambda *a, **k: None)
    with pytest.raises(AssertionError):
        _case1_assertions(_route(ent, state, _candidate()), project)


def _arrival_assertions(out, project):
    """Case a (the arrival re-point): at a work building with gold >= price and an admitting inn, the arrival re-points the SAME project to the inn: no WORK, no project end."""
    assert out.task is None and out.strategic is not None
    assert out.strategic.current_project_id_set is None  # the project is NOT ended (an end writes current_project_id_set == "" and COMPLETED while the subject is still hungry)
    (moved,) = out.strategic.projects_add_or_update
    assert moved.id == project.id and moved.status == ProjectStatus.ACTIVE
    active = next(o for o in moved.objectives if o.id == moved.active_objective_id)
    assert active.target == str(INN) and active.status == ObjectiveStatus.ACTIVE and out.strategic.current_objective_id_set == active.id
    old = next(o for o in moved.objectives if o.id != active.id)
    assert old.target == str(HALL) and old.status == ObjectiveStatus.RESOLVED


def test_the_arrival_at_a_work_building_repoints_the_same_project_to_the_meal_when_it_is_affordable_and_admitted():
    """The same predicate at the shift start (`work_shift.meal_in_reach`) and the same helper as the route (`work_shift.repoint_to_consume`): the shift ends with gold >= price and the inn admitting and NO
    strategic pass runs before the next tactical decision (the arrival is called directly): no new shift starts and the project is re-pointed, not ended. With the price not in hand the shift is still given."""
    rich, project, state = _world(gold=6, hunger=70.0)
    _arrival_assertions(building_arrival_update(state, rich, project, HALL), project)
    poor, project2, state2 = _world(gold=0, hunger=70.0)
    out2 = building_arrival_update(state2, poor, project2, HALL)
    assert out2.task is not None and out2.task.payload_set["action"] == "WORK"


def test_the_arrival_and_the_route_build_the_same_repoint():
    """One helper at both sites: the same project and the same inn give the identical update."""
    ent, project, state = _world(gold=6, hunger=70.0)
    from_route = _route(ent, state, _candidate()).update
    from_arrival = building_arrival_update(state, ent, project, HALL).strategic
    assert from_route.projects_add_or_update == from_arrival.projects_add_or_update and from_route.current_objective_id_set == from_arrival.current_objective_id_set


def test_a_subject_with_no_affordable_meal_and_no_startable_shift_still_ends_the_project_at_the_work_building():
    """_end_project stays for a building that truly cannot serve: no meal in reach and no shift the subject can start (here the hall cannot pay a wage)."""
    ent, project, state = _world(gold=0, hunger=70.0)
    broke_hall = replace(state.buildings[HALL], inventory=replace(state.buildings[HALL].inventory, gold=0), maintenance_shifts_needed=0, maintenance_shifts_done=0)
    state = replace(state, buildings={**state.buildings, HALL: broke_hall})
    out = building_arrival_update(state, ent, project, HALL)
    assert out.task is None and out.strategic.current_project_id_set == "" and out.strategic.projects_add_or_update[0].status == ProjectStatus.COMPLETED


def test_the_arrival_mutant_that_ends_instead_of_repointing_fails_the_arrival_case(monkeypatch):
    from src.core.updates import StrategicUpdate
    from src.engine import building_arrival
    rich, project, state = _world(gold=6, hunger=70.0)
    ends = lambda p, *a, **k: StrategicUpdate(projects_add_or_update=[replace(p, status=ProjectStatus.COMPLETED)], current_project_id_set="", current_objective_id_set="")
    monkeypatch.setattr(building_arrival, "repoint_to_consume", ends)
    with pytest.raises(AssertionError):
        _arrival_assertions(building_arrival_update(state, rich, project, HALL), project)
