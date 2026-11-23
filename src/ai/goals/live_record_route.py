# Compliance IDs: STRAT-289
"""Where a winning goal's live record of its kind goes: continue, resume, make current, or become a switch candidate.

TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED (divergence 2.143). Pure reads of the entity: nothing here writes state; the caller
carries the returned `StrategicUpdate` through the authoritative apply path.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Optional

from src.core.state import EntityState
from src.core.strategic import (
    BlockerState,
    ProjectState,
    ProjectStatus,
    ended_blocker_stamps,
    live_projects,
    project_target_matches,
    same_kind_record,
    supersede_record,
)
from src.core.updates import StrategicUpdate


@dataclass(frozen=True, slots=True)
class LiveRecordRoute:
    """The live record of the winning goal's kind, whether its target matches, and what to do with it.

    `update` is set when the record is dealt with here (continue, resume, make current): the caller returns it with its own bookkeeping deltas. `orphan` is set for an ACTIVE
    record at the matching target while ANOTHER live project is current: it goes through the switch check as the candidate."""
    existing: Optional[ProjectState]
    target_matches: bool
    update: Optional[StrategicUpdate] = None
    orphan: Optional[ProjectState] = None


def _earn_objective(state: Any, objective: Any, candidate_target_id: Any) -> bool:
    """True when the objective is an EARN step toward a way the candidate no longer needs: it targets the seek-work town centre (`SEEK_WORK_TARGET_ID`), or a building (not the candidate's own
    target) the subject earns at: one that buys goods (a kind in `SERVICE_KINDS["SELL"]`) or offers a shift (`building_services.offers_work`). No typed marker exists on an objective, so it is
    read from the building the target names, with the predicates the sale and shift steps use."""
    from src.core.strategic import SEEK_WORK_TARGET_ID
    from src.engine.building_services import SERVICE_KINDS, offers_work
    target = getattr(objective, "target", None)
    if target is None or str(target) == str(candidate_target_id):
        return False
    if target == SEEK_WORK_TARGET_ID:
        return True
    try:
        building = state.buildings.get(int(target))
    except (TypeError, ValueError):
        return False
    return building is not None and (building.kind in SERVICE_KINDS["SELL"] or offers_work(building))


def _consume_way_open(entity: EntityState, state: Any, best_candidate: Any) -> bool:
    """True when the candidate IS the direct way to meet the need, open now and ADMITTED to this subject (the one admission rule, which carries the coin trait): hunger: a candidate that
    names its target with no opening step while `work_shift.meal_in_reach` holds (the INN_MEAL way's own test, the one the arrival also reads); fatigue: a candidate that carries a target
    (SleepScorer targets only a bed `admits_at(entity, inn, "REST", state)` delivers to this subject: a paid bed, or a free home's, as the scorer reads it)."""
    from src.engine.work_shift import meal_in_reach
    if best_candidate.target_id is None:
        return False
    if str(getattr(best_candidate.kind, "value", best_candidate.kind)) == "hunger":
        return best_candidate.opening_step is None and meal_in_reach(state, entity)
    return True


def repoint_earn_to_consume(entity: EntityState, state: Any, existing: ProjectState, best_candidate: Any) -> Optional[StrategicUpdate]:
    """A need project made while the subject could not pay keeps its EARN objective after the coin is in hand (the objective is frozen at the way it was made with, and the switch check
    refuses a same-need candidate): the subject then starts NEW shifts with the meal affordable. When the existing record is the CURRENT project of a need kind (`NEED_PROJECT_KINDS`),
    its active objective is an EARN step (`_earn_objective`), the candidate is the direct consume way open now (`_consume_way_open`) and no shift is running, return an update that
    RE-POINTS the same project's active objective to the candidate's target (same project id, no new project, no switch check). A shift already held is not cut: the re-point comes at the
    next decision after it ends (`work_shift.shift_held`). Otherwise None (behaviour unchanged)."""
    from src.core.strategic import NEED_PROJECT_KINDS, ObjectiveKind, ObjectiveState, ObjectiveStatus
    from src.engine.work_shift import shift_held
    if existing.id != entity.strategic.current_project_id or str(getattr(existing.kind, "value", existing.kind)) not in NEED_PROJECT_KINDS:
        return None
    active = next((o for o in existing.objectives if o.id == existing.active_objective_id), None)
    if active is None or not _earn_objective(state, active, best_candidate.target_id) or not _consume_way_open(entity, state, best_candidate):
        return None
    if shift_held(entity, state):
        return None  # a shift held in progress runs to its end (the wage law is unchanged); the next decision after it re-points
    kind_str = getattr(best_candidate.kind, "value", best_candidate.kind)
    fresh = ObjectiveState(id=f"{kind_str}_{best_candidate.target_id}", kind=ObjectiveKind.REACH_LOCATION, target=best_candidate.target_id, target_position=best_candidate.target_pos,
                           target_entity_id=best_candidate.target_entity_id, status=ObjectiveStatus.ACTIVE)
    objectives = [replace(o, status=ObjectiveStatus.RESOLVED) if o.id == active.id else o for o in existing.objectives if o.id != fresh.id] + [fresh]
    return StrategicUpdate(projects_add_or_update=[replace(existing, objectives=objectives, active_objective_id=fresh.id)], current_objective_id_set=fresh.id)


def route_live_record(entity: EntityState, best_candidate: Any, resume: Callable[[EntityState, str], Optional[StrategicUpdate]], state: Any) -> LiveRecordRoute:
    """The live record a goal of `best_candidate.kind` continues, resumes, makes current or contests the current project with (see the module docstring).

    The record is the current project when it is of the kind, else the newest live one (`same_kind_record`); a COMPLETED or ABANDONED record and storage order take no part. A
    matching target never creates a same-target duplicate: the current project continues; a SUSPENDED record is resumed (`resume`, existing behaviour); an ACTIVE one that lost
    `current_project_id` (several writers clear it without ending the project) is made current again, or, beside another live current project, contests it through the switch check.
    A different target returns the record with `update` None: the caller's candidate may supersede it, except that a current NEED project on an earn objective is re-pointed to the
    open consume way (`repoint_earn_to_consume`; `state` is required: a default would silently disable the re-point)."""
    strat = entity.strategic
    existing = same_kind_record(strat.projects, best_candidate.kind, strat.current_project_id)
    matches = existing is not None and project_target_matches(existing, best_candidate.target_id, best_candidate.target_entity_id)
    if existing is not None and not matches:
        return LiveRecordRoute(existing, matches, repoint_earn_to_consume(entity, state, existing, best_candidate))
    if existing is None or not matches:
        return LiveRecordRoute(existing, matches)
    if existing.id == strat.current_project_id:
        return LiveRecordRoute(existing, matches, StrategicUpdate())
    if existing.status == ProjectStatus.SUSPENDED:
        return LiveRecordRoute(existing, matches, resume(entity, existing.id) or StrategicUpdate())
    if strat.current_project_id and strat.current_project_id in live_projects(strat.projects):
        return LiveRecordRoute(existing, matches, None, existing)
    return LiveRecordRoute(existing, matches, StrategicUpdate(current_project_id_set=existing.id, current_objective_id_set=existing.active_objective_id))


def orphan_switch_candidate(route: LiveRecordRoute, candidate: ProjectState, utility: float, current_tick: int) -> ProjectState:
    """The project the switch check weighs: the orphan as a fresh commitment at today's utility, locked like any freshly switched-in project (min(t+10, t+50)); the stored score
    and lock are written only on a win. `same_kind` is class-strict, so the orphan is never a ProjectKind record: its score is on the utility scale like a new candidate's.
    Without an orphan the generated `candidate` is returned unchanged."""
    if route.orphan is None:
        return candidate
    return replace(route.orphan, score=utility, lock_until_tick=min(current_tick + 10, current_tick + 50))


def supersede_on_win(switch_up: Optional[StrategicUpdate], route: LiveRecordRoute, candidate: ProjectState, tick: Optional[int] = None, blockers: Optional[Mapping[str, BlockerState]] = None) -> Optional[StrategicUpdate]:
    """A winning candidate at a DIFFERENT target ends the live record of its kind, cap-neutral (the gate was not consulted). Only that one record ends; older same-kind duplicates
    are left to the existing trims. The update that makes the candidate current also ends the record, with the typed reason. A loss, or a matching target, changes nothing."""
    existing = route.existing
    if not switch_up or existing is None or route.target_matches or existing.id == candidate.id:
        return switch_up
    ended = supersede_record(existing, tick)
    return replace(switch_up, projects_add_or_update=[
        ended,
        *[p for p in switch_up.projects_add_or_update if p.id != existing.id],
    ], blockers_add_or_update=[*switch_up.blockers_add_or_update, *ended_blocker_stamps({**(blockers or {}), **{b.id: b for b in switch_up.blockers_add_or_update}}, [ended])])  # 2.214: the same update stamps the blocker a resolve_blocker's end names
