"""The project-switch decision of `StrategicIntelligenceSystem.evaluate_project_switch`, as two pure functions (TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH).

`escalated_need_takes_switch` is the SURV-07 rule (2.228, STRAT-359); `ordinary_switch_allows` is the lock-and-margin decision (STRAT-005/006/186), moved out of `evaluate_project_switch` unchanged. They read the
scale helpers and constants of `intelligence` at call time (that module imports these names, so a top-level import here would be circular).
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Optional

from src.ai.goals.escalation import escalated_need_wins, is_need_kind
from src.ai.goals.present_threat import present_threat_to

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.strategic import ProjectState


def escalated_need_takes_switch(entity: "EntityState", candidate: "ProjectState", current: "ProjectState", state: Optional["AuthoritativeState"]) -> bool:
    """SURV-07 (Standing Needs Escalate): an escalated hunger or fatigue candidate takes the project switch past the lock and the retention margin, unless a present threat exists.

    Pure read. False when no `state` is supplied (the pre-existing direct call sites), when the candidate is not an escalated need (`escalated_need_wins`, the tree's own
    pressing test), when the CURRENT project is itself a need project (need against need stays with scoring, by kind identity, escalated or not), or while `present_threat_to`
    (SURV-07's tier-1 test) holds. TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH."""
    if state is None or not escalated_need_wins(entity, candidate.kind) or is_need_kind(current.kind):
        return False
    return not present_threat_to(entity, state)


def ordinary_switch_allows(entity: "EntityState", candidate_project: "ProjectState", current: "ProjectState", current_tick: int, state: Optional["AuthoritativeState"]) -> bool:
    """The lock-and-margin decision of `evaluate_project_switch` (STRAT-005/006/186), moved out unchanged: True when the candidate may replace the live, ACTIVE current project."""
    _i = import_module("src.systems.strategic_systems.intelligence")      # call-time: `intelligence` imports this module at its top (a top-level import here is circular)

    profile = entity.strategic.profile
    # Logic ID: STRAT-005 (Project switching uses interruption resistance)
    retention_margin = profile.interruption_resistance * profile.resistance_multiplier
    # Logic ID: STRAT-006 (Current project gets retention priority)
    effective_current_score = current.score + retention_margin

    if current.lock_until_tick > current_tick:
        # STRAT-236 (generalized): when a real world `state` is supplied and the triggering
        # threat has resolved (HP > 80%, no hostile within radius 10.0), the lock is treated
        # as already expired. `state is None` (the default for the 27 pre-existing direct
        # test call sites that predate this check) short-circuits `and` before
        # `_threat_resolved` is ever called, preserving today's behavior exactly. Computed
        # here, inside the lock-active gate, rather than above it, so the O(radius^2) spatial
        # scan in SpatialQueryService.nearby_entities() only runs when the current project is
        # actually locked — not on every evaluate_project_switch() call for an unlocked,
        # healthy entity (the common case across all 3 real production call sites).
        threat_resolved = state is not None and _i._threat_resolved(entity, state)

        if not threat_resolved:
            # STRAT-186 (generalized): the lock may be bypassed only for the unconditional "detour"
            # structural override, or when the candidate's score — expressed as a percentage of its own
            # system's declared max — both exceeds the current project's own normalized effective score
            # AND clears the urgency floor. This comparison is intentionally normalized and kept separate
            # from the raw `effective_current_score` comparison below: the raw formula and the unlocked
            # path must stay byte-identical (test_interruption_resistance_margin depends on this).
            if candidate_project.kind == "detour":
                pass
            else:
                candidate_max = _i._score_scale_max(candidate_project.kind)
                current_max = _i._score_scale_max(current.kind)
                candidate_pct = candidate_project.score / candidate_max
                # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG: the margin term is
                # deliberately normalized against the universal baseline scale (_GOAL_UTILITY_SCORE_MAX),
                # not current_max — current_max can be as small as _ADVENTURE_ROUTE_SCORE_MAX (2.9),
                # which made retention_margin/current_max structurally dominate the comparison.
                normalized_effective_current_pct = (current.score / current_max) + (retention_margin / _i._GOAL_UTILITY_SCORE_MAX)
                if not (candidate_pct > normalized_effective_current_pct
                        and candidate_pct > _i._INTERRUPTION_URGENCY_FLOOR_PCT):
                    return False

    return candidate_project.score > effective_current_score
