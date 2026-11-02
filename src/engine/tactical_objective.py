"""
src/engine/tactical_objective.py
───────────────────────────────────────────────────────────────────────────────
The objective-pursuit step of the tactical pass (Pillar 5.1): walk to, or act at, the subject's current objective.

Moved out of `TacticalDecisionSystem.evaluate_entity_intent` (it sat inside the `if not hostiles:` block) unchanged in behaviour, so the pressing-need path
(SURV-07 LAW P, TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED) can run it with hostiles in sight and the no-hostile path runs it as before.
`resolve` is `TacticalDecisionSystem._resolve_target_position` (passed in: this module does not import the tactical system).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional, Sequence, Tuple

from src.core.movement_modes import MovementMode
from src.core.strategic import ObjectiveKind
from src.core.updates import (
    EntityUpdate,
    InteractionUpdate,
    NavigationUpdate,
    TaskUpdate,
)
from src.domains.adventure.resolver import ObjectiveIntentResolver
from src.engine.building_arrival import building_arrival_update
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.engine.lodging import rest_would_lodge
from src.engine.tactical_avoid import eat_at_hunger_corpse
from src.engine.tactical_rest import in_danger

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.strategic import ObjectiveState, ProjectState

Resolver = Callable[["AuthoritativeState", "ObjectiveState"], Tuple[Optional[Tuple[float, float]], Optional[int], Optional[int]]]


def _distance(entity: "EntityState", target_pos: Tuple[float, float]) -> float:
    return abs(target_pos[0] - entity.navigation.position[0]) + abs(target_pos[1] - entity.navigation.position[1])


def _walk_to(entity: "EntityState", target_pos: Tuple[float, float]) -> EntityUpdate:
    """Still en route: set the nav target and stay idle so the brain re-evaluates on each cadence tick."""
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.WANDER))


def _fatigue_arrival_waits(state: "AuthoritativeState", entity: "EntityState", obj: "ObjectiveState", resolve: Resolver, hostiles: Sequence["EntityState"]) -> bool:
    """With hostiles in sight, a fatigue arrival (the subject is within a step of the building) dispatches its REST only if the REST lodges (a bed is delivered) or the AGENCY-07 terms
    are clear; otherwise it waits (nothing is dispatched and the project stays current), because a rest on the reach tile beside a hostile is the widening memo row 88 leaves to the
    owner (SURV-06). Walking to the building is not an arrival and is never held here."""
    project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
    if not hostiles or project is None or str(getattr(project.kind, "value", project.kind)).lower() != "fatigue":
        return False
    target_pos, _, building_id = resolve(state, obj)
    if not target_pos or building_id is None or _distance(entity, target_pos) > 1.0:
        return False
    return not rest_would_lodge(state, entity, state.buildings.get(building_id)) and in_danger(entity, hostiles)


def _reach_location_step(state: "AuthoritativeState", entity: "EntityState", project: "ProjectState", obj: "ObjectiveState", resolve: Resolver) -> Optional[EntityUpdate]:
    target_pos, node_id, building_id = resolve(state, obj)
    if not target_pos:
        return None
    if _distance(entity, target_pos) > 1.0:
        return _walk_to(entity, target_pos)
    if node_id is not None:
        return EntityUpdate(
            entity_id=entity.id,
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "INTERACT", "target_id": node_id}),
            interaction=InteractionUpdate(target_node_id=node_id, progress_delta=1),
        )
    if building_id is not None:
        return building_arrival_update(state, entity, project, building_id)
    # Arrived at a carcass the hunger goal pointed at (decision 44): eat where it lies.
    return eat_at_hunger_corpse(entity, state, project, obj) or EntityUpdate(entity_id=entity.id)


def _harvest_at_node(state: "AuthoritativeState", entity: "EntityState", obj: "ObjectiveState", node_id: int, neighbors: Optional[List["EntityState"]]) -> EntityUpdate:
    """Arrived at the resource node: transition to a harvest action instead of falling through to ObjectiveIntentResolver's REACH_RESOURCE -> MOVE_TO mapping,
    which would re-issue navigation forever."""
    harvest_intent = ActionIntent(
        kind="HARVEST_RESOURCE",
        actor_id=entity.id,
        target_id=node_id,
        source_opportunity_id=obj.id,
        reason=f"Arrived at resource node {node_id} for objective {obj.id}",
    )
    updates = ActionIntentAdapter.execute(entity, harvest_intent, current_tick=state.tick, neighbor_view=neighbors, context=state)
    return updates.get(entity.id, EntityUpdate(entity_id=entity.id))


def _other_objective_step(state: "AuthoritativeState", entity: "EntityState", obj: "ObjectiveState", neighbors: Optional[List["EntityState"]], resolve: Resolver) -> EntityUpdate:
    """Every other ObjectiveKind System A/B can produce reaches real execution via ObjectiveIntentResolver + ActionIntentAdapter, not just REACH_LOCATION."""
    target_pos, node_id = None, None
    if obj.target:
        target_pos, node_id, _ = resolve(state, obj)
    if target_pos:
        if _distance(entity, target_pos) > 1.0:
            return _walk_to(entity, target_pos)
        if obj.kind == ObjectiveKind.REACH_RESOURCE and node_id is not None:
            return _harvest_at_node(state, entity, obj, node_id, neighbors)
    intent = ObjectiveIntentResolver.resolve(entity.id, obj, payload={"position": target_pos} if target_pos else {})
    updates = ActionIntentAdapter.execute(entity, intent, current_tick=state.tick, neighbor_view=neighbors, context=state)
    return updates.get(entity.id, EntityUpdate(entity_id=entity.id))


def pursue_objective(state: "AuthoritativeState", entity: "EntityState", neighbors: Optional[List["EntityState"]], resolve: Resolver,
                     hostiles: Sequence["EntityState"] = ()) -> Optional[EntityUpdate]:
    """The step toward the current objective, or None when the objective gives no step (DEFEAT_ENEMY is the hostile-engagement branch's). `hostiles` is passed only by the
    pressing-need path (hostiles in sight, none acting); the no-hostile path leaves it empty and is unchanged."""
    strat = entity.strategic
    if not strat.current_objective_id:
        return None
    project = strat.projects.get(strat.current_project_id or "")
    if not project:
        return None
    obj = next((o for o in project.objectives if o.id == strat.current_objective_id), None)
    if obj is None:
        return None
    if obj.kind == "reach_location":
        if not obj.target:
            return None
        if _fatigue_arrival_waits(state, entity, obj, resolve, hostiles):
            return EntityUpdate(entity_id=entity.id)
        return _reach_location_step(state, entity, project, obj, resolve)
    if obj.kind not in (ObjectiveKind.REACH_LOCATION, ObjectiveKind.DEFEAT_ENEMY):
        return _other_objective_step(state, entity, obj, neighbors, resolve)
    return None
