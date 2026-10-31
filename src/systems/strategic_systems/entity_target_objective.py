"""Lifecycle of an objective whose subject is a specific moving entity (typed ``target_entity_id``), and of a project that
serves a social contract.

TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES (entity-targeted objectives) and
TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT (contract projects). Pure, read-only:
the caller (``StrategicIntelligenceSystem.evaluate_strategic_intent``) emits the ``StrategicUpdate`` and the strategic work
queue (``StrategicWorkQueue``) uses the same predicate (``objective_outcome``) to schedule the evaluation, so the two can
never disagree about when an objective has ended.
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import TYPE_CHECKING, NamedTuple, Optional

from src.ai.goals.present_threat import retreat_threat_present
from src.core.combat_constants import ENTITY_TARGET_PERCEPTION_RADIUS
from src.core.strategic import (
    ContractStatus,
    GoalKind,
    ObjectiveStatus,
    ProjectEnd,
    ProjectStatus,
    end_record,
)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.strategic import ObjectiveState, ProjectState



def entity_target_outcome(
    hero: "EntityState", state: "AuthoritativeState", objective: "ObjectiveState"
) -> Optional[tuple[ObjectiveStatus, ProjectStatus]]:
    """Terminal (objective, project) status for an entity-targeted objective, or None while it holds.

      - target dead            -> RESOLVED / COMPLETED
      - target gone from state -> FAILED / ABANDONED
      - target outside ENTITY_TARGET_PERCEPTION_RADIUS (Manhattan) -> FAILED / ABANDONED
    """
    if objective.target_entity_id is None:
        return None
    target = state.entities.get(objective.target_entity_id)
    if target is None:
        return ObjectiveStatus.FAILED, ProjectStatus.ABANDONED
    if not target.combat.alive:
        return ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED
    hx, hy = hero.navigation.position
    tx, ty = target.navigation.position
    if abs(tx - hx) + abs(ty - hy) > ENTITY_TARGET_PERCEPTION_RADIUS:
        return ObjectiveStatus.FAILED, ProjectStatus.ABANDONED
    return None


_CONTRACT_PROJECT_ID = re.compile(r"proj_contract_(.+)_t\d+")


def contract_project_id(contract_id: object, tick: int) -> str:
    """The id of the project that serves ``contract_id``, created at ``tick``. The inverse is ``contract_id_of_project``;
    the strategic evaluator builds the id here, so the two cannot drift. ``contract_id`` is typed ``object`` because the
    evaluator reads it from untyped goal metadata, exactly as the f-string it replaced did."""
    return f"proj_contract_{contract_id}_t{tick}"


def contract_id_of_project(project_id: str) -> Optional[str]:
    """The contract a project serves, read back from its id, or None for a project that serves no contract."""
    match = _CONTRACT_PROJECT_ID.fullmatch(project_id)
    return match.group(1) if match else None


def contract_objective_outcome(
    hero: "EntityState", project: "ProjectState"
) -> Optional[tuple[ObjectiveStatus, ProjectStatus]]:
    """Terminal (objective, project) status for a project that serves a contract, or None while the contract holds.

    A contract objective exists to serve its contract, so it ends when the contract is no longer ACTIVE:
      - contract FULFILLED -> RESOLVED / COMPLETED
      - any other status, or the contract gone from the entity (failed, betrayed, expired, cancelled, reaped,
        or never made ACTIVE) -> FAILED / ABANDONED
    """
    contract_id = contract_id_of_project(project.id)
    if contract_id is None:
        return None
    contract = hero.strategic.contracts.get(contract_id)
    if contract is not None and contract.status == ContractStatus.ACTIVE:
        return None
    if contract is not None and contract.status == ContractStatus.FULFILLED:
        return ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED
    return ObjectiveStatus.FAILED, ProjectStatus.ABANDONED


class ObjectiveOutcome(NamedTuple):
    """How an objective ended: the terminal (objective, project) status, and the typed ``ended_by`` when the end is one of the typed ones (None otherwise)."""

    objective: ObjectiveStatus
    project: ProjectStatus
    ended_by: Optional[ProjectEnd] = None


def retreat_outcome(hero: "EntityState", state: "AuthoritativeState") -> Optional[ObjectiveOutcome]:
    """Terminal outcome of a COMBAT_RETREAT project, or None while its threat holds: the retreat COMPLETES (RESOLVED / COMPLETED, THREAT_CLEARED) when no
    hostile the subject perceives is adjacent to it or acts on it (`retreat_threat_present`, read from ``state`` at its tick)."""
    if retreat_threat_present(hero, state):
        return None
    return ObjectiveOutcome(ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED)


def objective_outcome(
    hero: "EntityState", state: "AuthoritativeState", project: "ProjectState", objective: "ObjectiveState"
) -> Optional[ObjectiveOutcome]:
    """The one predicate for "has this project's active objective ended": a retreat by its threat, entity-targeted objectives by their target, contract projects
    by their contract. Shared by the evaluator and the work queue."""
    if project.kind == GoalKind.COMBAT_RETREAT:
        return retreat_outcome(hero, state)
    outcome = entity_target_outcome(hero, state, objective) if objective.target_entity_id is not None else contract_objective_outcome(hero, project)
    return None if outcome is None else ObjectiveOutcome(*outcome)


def close_entity_target_project(
    hero: "EntityState", state: "AuthoritativeState", project: "ProjectState"
) -> Optional["ProjectState"]:
    """The project with its active objective closed (entity-targeted, or serving a contract), or None while it holds.

    The name predates the contract case and is kept because the mechanism registry cites it. Kept out of
    ``evaluate_strategic_intent`` (already far over the complexity limits): the caller only wraps the returned
    project in its ``StrategicUpdate``.
    """
    objective = next((o for o in project.objectives if o.id == project.active_objective_id), None)
    if objective is None:
        return None
    outcome = objective_outcome(hero, state, project, objective)
    if outcome is None:
        return None
    closed = replace(objective, status=outcome.objective)
    ended = replace(project, objectives=[closed if o.id == closed.id else o for o in project.objectives])
    if outcome.ended_by is not None:
        return end_record(ended, outcome.project, outcome.ended_by)
    return replace(ended, status=outcome.project)
