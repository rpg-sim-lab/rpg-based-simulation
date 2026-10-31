"""
src/ai/goals/escalation.py
TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (SURV-07)

A hunger or sleep goal that wins scoring at or past its escalation onset is never refused for project capacity. Pure read of the subject's needs.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.ai.goals.present_threat import present_threat_to
from src.core.strategic import GoalKind
from src.engine.need_pull import need_is_pressing

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def escalated_need_wins(entity: "EntityState", goal_kind: object) -> bool:
    """True for a HUNGER or FATIGUE goal while that need is at or past its onset.

    The onset is the pull's own and the scheduler wake's (`need_is_pressing`: ESCALATION_ONSET of the consequence line), no new constant. The
    caller's `not existing` keeps it to one project per need, so a full cap is exceeded by at most one hunger and one sleep project; nothing is
    evicted, abandoned or resumed (a live need project is outside the capacity trims, `live_projects_in_the_trim`). Below the onset the cap applies."""
    kind = getattr(goal_kind, "value", goal_kind)
    if kind == GoalKind.HUNGER.value:
        return need_is_pressing(entity.biological.hunger, 0.0)
    if kind == GoalKind.FATIGUE.value:
        return need_is_pressing(0.0, entity.biological.sleep_debt)
    return False


def retreat_under_threat_wins(entity: "EntityState", state: "AuthoritativeState", goal_kind: object) -> bool:
    """True for a COMBAT_RETREAT goal while a present threat holds (`present_threat_to`, the test the retreat is adopted and ended on): admitted past a full project cap exactly as an
    escalated need is (the caller's `not existing` and the capacity trim keep the choice of which record yields the slot unchanged). Retreat only: RECOVER and COMBAT_ENGAGE get none."""
    return getattr(goal_kind, "value", goal_kind) == GoalKind.COMBAT_RETREAT.value and present_threat_to(entity, state)


def exempt_from_the_project_cap(entity: "EntityState", state: "AuthoritativeState", goal_kind: object) -> bool:
    """The one capacity-gate exemption: a NEW project of this kind is admitted past a full cap when it is an escalated need (`escalated_need_wins`) or a retreat under a present threat
    (`retreat_under_threat_wins`). RECOVER, COMBAT_ENGAGE and every other kind get none."""
    return escalated_need_wins(entity, goal_kind) or retreat_under_threat_wins(entity, state, goal_kind)
