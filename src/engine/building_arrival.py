"""What a subject does on arriving at a building its project walked to (SURV-06, EXCH-02), and the end of a shop visit made to sell.

A hunger project whose objective is a shop is the SELL opening step. The sale lands with its action (`building_services.py`); once the subject
stands in the shop's reach with nothing left the shop would buy, the visit is done, and the project ends so that the next hunger goal points at
the inn. Without this a sold worker stayed on the shop project, whose score the fresh inn goal did not clear the retention margin to replace.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from src.core.strategic import ObjectiveStatus, ProjectEnd, ProjectStatus, end_record
from src.core.updates import EntityUpdate, StrategicUpdate, TaskUpdate
from src.engine.building_services import SERVICE_KINDS, offers_work
from src.engine.lodging import finds_no_bed
from src.engine.service_admission import admits
from src.engine.shop_sale import plan_sale
from src.engine.work_shift import SHIFT_START, meal_in_reach, shift_startable
from src.engine.work_wake import held_work_is_threatened


def _end_project(entity: Any, project: Any) -> EntityUpdate:
    """The update that completes `project` (its active objective resolved) and clears the subject's current project."""
    objectives = [replace(o, status=ObjectiveStatus.RESOLVED) if o.id == project.active_objective_id else o for o in project.objectives]
    return EntityUpdate(entity_id=entity.id, strategic=StrategicUpdate(
        projects_add_or_update=[replace(project, objectives=objectives, status=ProjectStatus.COMPLETED)],
        current_project_id_set="", current_objective_id_set=""))


def finished_visit(state: Any, entity: Any, project: Any, shop: Any) -> Optional[EntityUpdate]:
    """The update that ends `project` when `entity`, in `shop`'s reach, has nothing left to sell it; None while a sale remains."""
    return None if plan_sale(state, entity, shop) is not None else _end_project(entity, project)


HUNGER_NEED_FLOOR = 20.0  # the hunger scorer's own floor (EatScorer): below it there is no hunger need to meet


def _act(entity: Any, action: str, building_id: int, **extra: Any) -> EntityUpdate:
    return EntityUpdate(entity_id=entity.id, task=TaskUpdate(work_kind_set="ENTITY_ACT",
                                                             payload_set={"action": action, "target_id": building_id, **extra}))


def _meal_in_reach(state: Any, entity: Any) -> bool:
    """True when the subject could buy a meal in reach now: `work_shift.meal_in_reach`, the one predicate (also read by the re-point of a need project from its earn step to the meal)."""
    return meal_in_reach(state, entity)


def _hunger_arrival(state: Any, entity: Any, project: Any, building_id: int) -> EntityUpdate:
    """The hunger project's action at the building it reached: a sale at a shop while one remains, else a meal, a shift or the end.

    At a shop with nothing left to sell the visit is not ended by kind alone (divergence 2.223): a subject that can now pay for a meal in reach ends the visit and goes to eat (the pull
    goes to the step that can meet the need, SURV-06/07); one that cannot falls through to the normal order below, so a broke subject at a shop that offers a shift is given the shift."""
    building = state.buildings.get(building_id)
    at_shop = getattr(building, "kind", None) == "shop"
    if at_shop:
        done = finished_visit(state, entity, project, building)
        if done is None:
            return _act(entity, "SELL", building_id)
        if _meal_in_reach(state, entity):
            return done
    if entity.biological.hunger < HUNGER_NEED_FLOOR:
        return _end_project(entity, project)  # fed: a meal is bought only for a hunger (no paying to eat when not hungry)
    # The action is derived from what this building can do for the subject, never stored on the project: a building that serves a meal and would
    # deliver it to this subject (the one admission rule) is a meal; otherwise a building that offers a shift the subject can start (`shift_startable`, the one predicate the open
    # earn step also reads; the EARN_THEN_BUY step, held for SHIFT_TICKS, paid on the last tick); otherwise there is nothing to do here.
    if getattr(building, "kind", None) in SERVICE_KINDS["EAT"] and admits(entity, "EAT"):
        return _act(entity, "EAT", building_id)
    if building is not None and offers_work(building):
        # No NEW shift while a meal is affordable and admitted in reach (the earn step has done its work: the coin is in hand): the same predicate the strategic re-point reads
        # (`work_shift.meal_in_reach`), so the guarantee does not depend on when the next strategic pass runs. The project then ends below and the next decision goes to eat.
        if not _meal_in_reach(state, entity) and shift_startable(state, entity, building):
            return _act(entity, "WORK", building_id, **{SHIFT_START: state.tick})
        if held_work_is_threatened(entity, state):
            # Not takeable NOW because of a present threat (designer ruling 2026-10-30): the hunger project stays current, nothing is dispatched, and the
            # tactical answer to the threat takes over through the normal switch; the next decision judges again. The project is not ended or abandoned.
            return EntityUpdate(entity_id=entity.id)
    return _end_project(entity, project)  # nothing this building can do for the subject now: the project ends


def building_arrival_update(state: Any, entity: Any, project: Any, building_id: int) -> EntityUpdate:
    """The survival action by project kind at the building the subject reached: a meal, a shift or a sale (hunger), a bed (fatigue); anything else is idle."""
    kind = getattr(project, "kind", "")
    if kind == "hunger":
        return _hunger_arrival(state, entity, project, building_id)
    if kind == "fatigue":
        building = state.buildings.get(building_id)
        if finds_no_bed(state, entity, building):
            # F3: the bed is taken (the way closed on the way): no REST on the reach tile, the project ends with the typed way-closed end and the subject re-decides.
            return EntityUpdate(entity_id=entity.id, strategic=StrategicUpdate(projects_add_or_update=[end_record(project, ProjectStatus.ABANDONED, ProjectEnd.WAY_CLOSED, state.tick)], current_project_id_set="", current_objective_id_set=""))
        return _act(entity, "REST", building_id)
    return EntityUpdate(entity_id=entity.id)
