"""The purpose of a navigation target (the #996 rework, TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON; design: docs/plans/systemic_world/experience_memory_design.md section 2.1 and 4).

A target is chosen FOR something: the project the subject is on and the movement mode its writer sets. That pair travels with the target (``NavigationComponent.target_purpose``, written by the navigation patch with every NEW
target) so a later refusal of the place can be scoped to what the subject was doing, not to the tile alone. The three functions here are PURE reads of the entity and the update staged so far: no state is written,
no kind, role, faction or name is read (the project kind is the project's own typed kind value).

* ``purpose_of``: the purpose a writer's NEW target will carry. A writer calls it once, binds the result to one name and passes that same name to the gate and to ``target_purpose_set``.
* ``stored_purpose``: a re-emission site carries the purpose already stored.
* ``ungated_purpose``: the by-value own-tile writes that skip the gate (a hold, a flight step); their target is stored with ``target_gated`` False.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.core.hold_mode import effective_movement_mode, hold_reset_kwargs
from src.core.movement_modes import MovementMode

NO_PROJECT_KIND = "none"  # the project kind of a purpose when the subject has no current project


@dataclass(frozen=True, slots=True)
class TargetPurpose:
    """What a target was chosen for: ``project_kind`` is the VALUE of the subject's current project's kind ("hunger" / "fatigue" are the need-project kinds; ``NO_PROJECT_KIND`` when none) and ``movement_mode`` the VALUE of
    the `MovementMode` the target is stored with."""
    project_kind: str
    movement_mode: str

    def to_canonical(self) -> dict:
        """The canonical-dict form."""
        return {"project_kind": self.project_kind, "movement_mode": self.movement_mode}


def purpose_canonical(purpose: Optional[TargetPurpose], gated: bool) -> dict:
    """The canonical-dict entries of a navigation's target purpose and gate flag: each present only while set, so the form of a subject whose target carries neither is unchanged."""
    return {**({"target_purpose": purpose.to_canonical()} if purpose is not None else {}), **({"target_gated": True} if gated else {})}


def _value(enum_or_str: Any) -> str:
    return str(getattr(enum_or_str, "value", enum_or_str))


def _project_kind_value(entity: Any, staged: Optional[Any]) -> str:
    """The kind value of the subject's current project AFTER the staged strategic update (its current project id, its added or updated and removed projects)."""
    strat = entity.strategic
    upd = getattr(staged, "strategic", None) if staged is not None else None
    current_id = strat.current_project_id
    projects = strat.projects
    if upd is not None:
        if upd.current_project_id_set is not None:
            current_id = upd.current_project_id_set
        projects = {**projects, **{p.id: p for p in upd.projects_add_or_update}}
        for removed in upd.projects_remove:
            projects = {k: v for k, v in projects.items() if k != removed}
    project = projects.get(current_id) if current_id else None
    return NO_PROJECT_KIND if project is None else _value(project.kind)


def _effective_mode(entity: Any, staged: Optional[Any], mode_set: Optional[MovementMode]) -> MovementMode:
    """The mode a target written now is stored with: ``mode_set`` when the writer's update sets one, else the mode a walk decision leaves (a HOLD becomes WANDER when the writer resets it, `hold_reset_kwargs`), else the mode in force."""
    if mode_set is not None:
        return mode_set
    reset = hold_reset_kwargs(entity, staged).get("movement_mode_set")
    return reset if reset is not None else effective_movement_mode(entity, staged)


def purpose_of(entity: Any, staged: Optional[Any] = None, mode_set: Optional[MovementMode] = None) -> TargetPurpose:
    """The purpose of a NEW target written now: (the project kind current after ``staged``, the effective mode the update leaves stored). Pure."""
    return TargetPurpose(_project_kind_value(entity, staged), _value(_effective_mode(entity, staged, mode_set)))


def ungated_purpose(entity: Any, mode_set: Optional[MovementMode] = None, staged: Optional[Any] = None) -> TargetPurpose:
    """The purpose of a by-value own-tile target that skips the gate: the same pair as `purpose_of`; a separate name so the static check can tell a gated write from an ungated one (neither may mix)."""
    return purpose_of(entity, staged, mode_set)


def stored_purpose(entity: Any) -> Optional[TargetPurpose]:
    """The purpose stored with the entity's target (None for a target restored from an old checkpoint, or when no target is held). A re-emission carries it unchanged."""
    return entity.navigation.target_purpose
