"""TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS.

On an off-cadence tick the fused strategic pass's fast path wrote REGROUP (home, with an interaction reset) for a loaded entity whose
active objective names an entity, because its "the objective owns the direction" guard read only `target_position`. The slow path
(and its tickets, 20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET...) treats `target_entity_id` as owning the direction.

This regression runs the wired path: `AuthoritativeApplyPipeline.refine`, the pipeline's own strategic_intelligence phase, not the bare
function the characterisation file calls.
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.inventory import ItemStack
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectKind, ProjectState, ProjectStatus
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.cadence import SystemCadence
from src.engine.pipeline import AuthoritativeApplyPipeline

pytestmark = [pytest.mark.domain("strategic_cognition"), pytest.mark.level("unit")]

TOWN = (50.0, 50.0)
OFF_CADENCE = SystemCadence(strategic_intelligence=1000, concern_evaluation=1000)


def _pursuer(objective):
    project = ProjectState(id="p1", kind=ProjectKind.TRAVEL, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id=objective.id)
    return (V2EntityBuilder(1).kind("worker").location(10.0, 10.0).inventory(items=[ItemStack(item_id="wood", quantity=1)])
            .strategic(projects={"p1": project}, current_project_id="p1").build())


def _refined_nav(objective, tick=5):
    target = V2EntityBuilder(2).kind("worker").location(30.0, 30.0).build()
    state = AuthoritativeState(tick=tick, seed=1, entities={1: _pursuer(objective), 2: target}, town_center=TOWN)
    raw = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)}, force_full_scan=True)
    upd = AuthoritativeApplyPipeline.refine(state, raw, cadence=OFF_CADENCE).entity_updates.get(1)
    nav = None if upd is None else upd.navigation
    reset = bool(upd is not None and upd.interaction is not None and upd.interaction.reset)
    return nav, reset


def test_a_loaded_entity_pursuing_an_entity_objective_is_not_sent_home_off_cadence():
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, status=ObjectiveStatus.ACTIVE, target_entity_id=2)
    nav, reset = _refined_nav(objective)
    assert nav is None or (nav.target_set is None and nav.movement_mode_set is None), nav     # no REGROUP, no home target
    assert not reset                                                                              # and its interaction is not reset


def test_control_the_same_loaded_entity_with_no_objective_still_regroups_home_off_cadence():
    """Control: this setup does reach the fast path's regroup. Without a project the entity is sent home, so the test above passes because of the guard, not because the setup is inert."""
    target = V2EntityBuilder(2).kind("worker").location(30.0, 30.0).build()
    plain = V2EntityBuilder(1).kind("worker").location(10.0, 10.0).inventory(items=[ItemStack(item_id="wood", quantity=1)]).build()
    state = AuthoritativeState(tick=5, seed=1, entities={1: plain, 2: target}, town_center=TOWN)
    raw = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)}, force_full_scan=True)
    nav = AuthoritativeApplyPipeline.refine(state, raw, cadence=OFF_CADENCE).entity_updates[1].navigation
    assert nav.movement_mode_set == MovementMode.REGROUP and nav.target_set == TOWN
