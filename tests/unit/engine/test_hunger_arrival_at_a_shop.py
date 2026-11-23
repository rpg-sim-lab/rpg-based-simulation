"""Divergence 2.223 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1, trace v4 stage 2): at a shop with nothing left to sell, a hunger arrival is not ended by the
shop's kind alone. A subject that can pay for a meal in reach ends the visit and goes to eat; otherwise the normal order decides (a meal, a shift it can start, the end).
The open earn step and the arrival read the one predicate `work_shift.shift_startable`, so what the step opened is what the arrival dispatches."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.base import OpeningStepKind
from src.ai.goals.opening_steps import opening_steps, work_in_reach
from src.core.state import BuildingState, InventoryComponent
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.building_arrival import building_arrival_update
from tests.unit.engine.test_earn_shift import _consumers, _inn, _state, _worker  # noqa: F401  (_consumers: the module's autouse content fixture)

SHOP_ID = 12


def _shop(gold=100, hires=True, pos=(11.0, 10.0)):
    return BuildingState(id=SHOP_ID, kind="shop", position=pos, functional=True, hires_for_pay=hires, inventory=InventoryComponent(gold=gold))


def _project(target=SHOP_ID):
    objective = ObjectiveState(id="hunger_1", kind=ObjectiveKind.REACH_LOCATION, target=str(target), target_position=(11.0, 10.0), status=ObjectiveStatus.ACTIVE)
    return ProjectState(id="proj_hunger_1", kind=GoalKind.HUNGER, status=ProjectStatus.ACTIVE, score=100.0, objectives=[objective], active_objective_id=objective.id)


def _action(update):
    return None if update.task is None else update.task.payload_set.get("action")


def test_a_broke_subject_at_a_shop_with_nothing_to_sell_and_a_takeable_shift_is_given_the_shift():
    ent = _worker(hunger=60.0, gold=0, pos=(10.0, 10.0))
    state = _state(ent, _shop(), _inn(pos=(30.0, 10.0)))
    update = building_arrival_update(state, ent, _project(), SHOP_ID)
    assert _action(update) == "WORK" and update.strategic is None  # not ended as a finished sell visit (it was, on 89a37bb2)


def test_a_subject_that_can_pay_for_a_meal_in_reach_still_ends_the_shop_visit():
    ent = _worker(hunger=60.0, gold=5, pos=(10.0, 10.0))  # it has sold: it holds the price of a meal and an inn is in reach
    state = _state(ent, _shop(), _inn(pos=(30.0, 10.0)))
    update = building_arrival_update(state, ent, _project(), SHOP_ID)
    assert update.task is None and update.strategic.current_project_id_set == ""
    assert update.strategic.projects_add_or_update[0].status == ProjectStatus.COMPLETED  # this asserts today's COMPLETED for a hunger project ended at a shop that cannot serve the need; TCK-20261123-A-NEED-PROJECT-ENDED-AT-A-BUILDING-THAT-CANNOT-SERVE-IT-IS-RECORDED-AS-COMPLETED changes it


def test_a_fed_subject_at_a_shop_with_nothing_to_sell_ends_the_visit():
    ent = _worker(hunger=5.0, gold=0, pos=(10.0, 10.0))
    state = _state(ent, _shop(), _inn(pos=(30.0, 10.0)))
    update = building_arrival_update(state, ent, _project(), SHOP_ID)
    assert update.task is None and update.strategic.current_project_id_set == ""


@pytest.mark.parametrize("shop_gold,hires", [(100, True), (0, True), (100, False)])
def test_the_open_earn_step_and_the_shop_arrival_agree_on_the_same_state(shop_gold, hires):
    ent = _worker(hunger=60.0, gold=0, pos=(10.0, 10.0))
    state = _state(ent, _shop(gold=shop_gold, hires=hires), _inn(pos=(30.0, 10.0)))
    step_open = work_in_reach(ent, state) is not None
    earn = [s for s in opening_steps(ent, state) if s.kind is OpeningStepKind.EARN_THEN_BUY][0]
    assert earn.available is step_open
    dispatched = _action(building_arrival_update(state, ent, _project(), SHOP_ID)) == "WORK"
    assert dispatched is step_open  # a shop that cannot pay its wage (or hires no one) opens no step and dispatches no shift


def _leashed(ent, home, radius):
    return replace(ent, navigation=replace(ent.navigation, home_position=home, leash_radius=radius))


@pytest.mark.parametrize("gold", [0, 5])
@pytest.mark.parametrize("inns", [
    [],                                                       # no inn at all
    [(30.0, 10.0)],                                           # one inn, in range (no leash)
    [(25.0, 10.0), (8.0, 10.0)],                              # nearest inn OUT of the range, a farther one IN it (the loop by another door)
    [(8.0, 10.0), (25.0, 10.0)],                              # the same layout in the other building order (the nearest, at x=25, is still out of range)
    [(25.0, 10.0)],                                           # the only inn out of range
])
@pytest.mark.parametrize("leashed", [False, True])
def test_a_meal_in_reach_is_one_definition_for_the_way_set_and_the_arrival(inns, gold, leashed):
    """The arrival's "a meal in reach" is the INN_MEAL way's own test: the nearest inn in range and the admission rule. (On 4b10ece43 the arrival took ANY inn in range.)"""
    from src.ai.goals.ways import inn_in_reach
    from src.engine.building_arrival import _meal_in_reach
    from src.engine.service_admission import admits
    ent = _worker(hunger=60.0, gold=gold, pos=(20.0, 10.0))
    if leashed:
        ent = _leashed(ent, (10.0, 10.0), 12)
    state = _state(ent, *[_inn(pos=p, bid=20 + i) for i, p in enumerate(inns)])
    assert _meal_in_reach(state, ent) == (inn_in_reach(ent, state) is not None and admits(ent, "EAT"))
    if leashed and gold >= 5 and inns[:1] == [(25.0, 10.0)]:
        assert _meal_in_reach(state, ent) is False  # the nearest inn is out of range: a farther in-range inn does not stand in for it


def test_a_shop_arrival_gives_the_shift_when_the_nearest_inn_is_out_of_range_even_if_a_farther_one_is_in_it():
    ent = _leashed(_worker(hunger=60.0, gold=5, pos=(20.0, 10.0)), (10.0, 10.0), 12)
    state = _state(ent, _shop(pos=(21.0, 10.0)), _inn(pos=(25.0, 10.0), bid=20), _inn(pos=(8.0, 10.0), bid=21))
    assert work_in_reach(ent, state) is not None  # the shop is within the range; the step is open
    assert _action(building_arrival_update(state, ent, _project(), SHOP_ID)) == "WORK"  # so the arrival does not end the visit (it did on 4b10ece43)


def test_a_tie_between_two_inns_picks_the_first_in_state_buildings_order_as_the_index_does():
    """Two inns at equal Manhattan distance, the higher id listed first: the helper picks the FIRST in ``state.buildings`` order (not the lower id), the same building the index-based
    `SpatialQueryService.nearest_building` picks, so a silent switch to id order is caught here."""
    from src.engine.spatial_query import SpatialQueryService
    from src.engine.work_shift import nearest_inn
    ent = _worker(hunger=60.0, gold=5, pos=(20.0, 10.0))
    state = _state(ent, _inn(pos=(20.0, 14.0), bid=30), _inn(pos=(20.0, 6.0), bid=20))
    assert list(state.buildings) == [30, 20]  # building order and id order differ
    assert nearest_inn(state, ent.navigation.position).id == 30
    assert nearest_inn(state, ent.navigation.position).id == SpatialQueryService.nearest_building(state, ent.navigation.position, "inn").id


def test_a_nearer_inn_wins_whatever_the_building_order_and_matches_the_index():
    from src.engine.spatial_query import SpatialQueryService
    from src.engine.work_shift import nearest_inn
    ent = _worker(hunger=60.0, gold=5, pos=(20.0, 10.0))
    state = _state(ent, _inn(pos=(20.0, 16.0), bid=30), _inn(pos=(20.0, 12.0), bid=40), _inn(pos=(20.0, 6.0), bid=20))
    assert nearest_inn(state, ent.navigation.position).id == 40 == SpatialQueryService.nearest_building(state, ent.navigation.position, "inn").id
