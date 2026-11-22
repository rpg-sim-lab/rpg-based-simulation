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
    assert update.strategic.projects_add_or_update[0].status == ProjectStatus.COMPLETED


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
