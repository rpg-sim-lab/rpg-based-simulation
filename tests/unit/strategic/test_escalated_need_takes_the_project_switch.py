"""TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH (SURV-07, Bible ch04 "Standing Needs Escalate", divergence 2.228).

An escalated hunger or fatigue candidate with no present threat takes the project switch past the lock and the retention margin; the current project is suspended in the same update.
Need against need, a non-escalated winner, a present threat and `detour` keep the ordinary decision. The two helpers split the old body: with the rule off the result is the pre-refactor
function's on every case of a table (the oracle below is its code, copied).
"""
from dataclasses import replace

import pytest

from src.core.enums import Faction
from src.core.strategic import GoalKind, ProjectState, ProjectStatus
from src.systems.strategic_systems import intelligence as intel
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem as SIS
from tests.unit.combat.test_tactical_destinations import _entity, _state

ESCALATED_HUNGER, FED = 80.0, 10.0


def subject(current: ProjectState, hunger=ESCALATED_HUNGER, sleep_debt=0.0, resistance=None):
    entity = _entity(1, Faction.HERO_GUILD, pos=(20.0, 20.0))
    strategic = replace(entity.strategic, projects={current.id: current}, current_project_id=current.id)
    if resistance is not None:
        strategic = replace(strategic, profile=replace(strategic.profile, interruption_resistance=resistance))
    return replace(entity, strategic=strategic, biological=replace(entity.biological, hunger=hunger, sleep_debt=sleep_debt))


def project(pid, kind, score, lock=0, status=ProjectStatus.ACTIVE):
    return ProjectState(id=pid, kind=kind, status=status, score=score, lock_until_tick=lock)


def with_hostile(entity, adjacent=True):
    return _state(entity, _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0 if adjacent else 40.0)), tick=50)


def switch(entity, candidate, state=None):
    return SIS.evaluate_project_switch(entity, candidate, 50, state if state is not None else _state(entity, tick=50))


def test_an_escalated_hunger_winner_takes_the_switch_from_a_locked_town_return_and_suspends_it():
    entity = subject(project("tr", "town_return", 90.0, lock=60))
    candidate = project("h", GoalKind.HUNGER, 70.0)                                 # utility <= 80: the 0.8 floor holds a locked current
    assert switch(entity, candidate) is not None
    update = switch(entity, candidate)
    assert update.current_project_id_set == "h"
    by_id = {p.id: p for p in update.projects_add_or_update}
    assert by_id["tr"].status == ProjectStatus.SUSPENDED and by_id["tr"].suspended_since == 50 and by_id["h"].status == ProjectStatus.ACTIVE


def test_an_escalated_hunger_winner_takes_the_switch_from_a_resolve_blocker_current_above_the_floor():
    entity = subject(project("rb", "resolve_blocker", 95.0, lock=60), resistance=1.0)
    assert switch(entity, project("h", GoalKind.HUNGER, 88.0)).current_project_id_set == "h"


def test_a_present_threat_leaves_the_ordinary_decision():
    entity = subject(project("tr", "town_return", 90.0, lock=60))
    candidate = project("h", GoalKind.HUNGER, 70.0)
    assert switch(entity, candidate, with_hostile(entity)) is None                    # the ordinary path refuses; the threat withholds the bypass
    assert intel._escalated_need_takes_switch(entity, candidate, entity.strategic.projects["tr"], with_hostile(entity)) is False
    assert intel._escalated_need_takes_switch(entity, candidate, entity.strategic.projects["tr"], with_hostile(entity, adjacent=False)) is True


def test_a_non_escalated_hunger_winner_keeps_the_ordinary_lock_and_margin():
    entity = subject(project("tr", "town_return", 90.0, lock=60), hunger=40.0)
    assert switch(entity, project("h", GoalKind.HUNGER, 70.0)) is None


@pytest.mark.parametrize("current_kind, candidate_kind, hunger, sleep", [(GoalKind.FATIGUE, GoalKind.HUNGER, 80.0, 0.0), (GoalKind.HUNGER, GoalKind.FATIGUE, 0.0, 90.0), (GoalKind.HUNGER, GoalKind.HUNGER, 80.0, 0.0), (GoalKind.FATIGUE, GoalKind.HUNGER, 40.0, 0.0)])
def test_need_against_need_stays_with_the_ordinary_path_by_kind_identity(current_kind, candidate_kind, hunger, sleep):
    entity = subject(project("cur", current_kind, 90.0, lock=60), hunger=hunger, sleep_debt=sleep)
    assert intel._escalated_need_takes_switch(entity, project("c", candidate_kind, 70.0), entity.strategic.projects["cur"], _state(entity, tick=50)) is False
    assert switch(entity, project("c", candidate_kind, 70.0)) is None


def test_an_escalated_fatigue_winner_takes_the_switch_from_an_ordinary_current():
    entity = subject(project("q", "quest", 90.0, lock=60), hunger=0.0, sleep_debt=90.0)
    assert switch(entity, project("f", GoalKind.FATIGUE, 70.0)).current_project_id_set == "f"


def test_a_detour_and_a_non_need_candidate_are_unchanged():
    entity = subject(project("tr", "town_return", 90.0, lock=60))
    assert switch(entity, project("d", "detour", 140.0)).current_project_id_set == "d"                       # detour: its own bypass
    assert switch(entity, project("w", "quest", 70.0)) is None                                                # a non-need candidate: the lock holds


def test_no_state_never_takes_the_bypass_and_no_current_project_is_created_as_before():
    entity = subject(project("tr", "town_return", 90.0, lock=60))
    assert SIS.evaluate_project_switch(entity, project("h", GoalKind.HUNGER, 70.0), 50) is None
    empty = replace(entity, strategic=replace(entity.strategic, current_project_id=""))
    assert SIS.evaluate_project_switch(empty, project("h", GoalKind.HUNGER, 70.0), 50, _state(empty, tick=50)).current_project_id_set == "h"


def test_a_taken_case_the_ordinary_path_also_allows_gives_the_same_update_as_the_ordinary_path(monkeypatch):
    entity = subject(project("tr", "town_return", 20.0), resistance=0.0)                                         # unlocked, low score: both allow
    candidate = project("h", GoalKind.HUNGER, 70.0)
    taken = switch(entity, candidate)
    monkeypatch.setattr(intel, "_escalated_need_takes_switch", lambda *a: False)
    assert intel._ordinary_switch_allows(entity, candidate, entity.strategic.projects["tr"], 50, _state(entity, tick=50)) is True
    assert switch(entity, candidate) == taken


# ---- refactor neutrality: the pre-refactor body (copied) against the helpers with the rule off
def oracle(entity, candidate, tick, state):
    """evaluate_project_switch before the TCK: its code, copied (comments dropped)."""
    profile = entity.strategic.profile
    current_id = entity.strategic.current_project_id
    if not current_id:
        return candidate.id
    current = entity.strategic.projects.get(current_id)
    if not current or current.status != ProjectStatus.ACTIVE:
        return candidate.id
    retention_margin = profile.interruption_resistance * profile.resistance_multiplier
    effective_current_score = current.score + retention_margin
    if current.lock_until_tick > tick:
        threat_resolved = state is not None and intel._threat_resolved(entity, state)
        if not threat_resolved:
            if candidate.kind == "detour":
                pass
            else:
                candidate_max = intel._score_scale_max(candidate.kind)
                current_max = intel._score_scale_max(current.kind)
                candidate_pct = candidate.score / candidate_max
                normalized = (current.score / current_max) + (retention_margin / intel._GOAL_UTILITY_SCORE_MAX)
                if not (candidate_pct > normalized and candidate_pct > intel._INTERRUPTION_URGENCY_FLOOR_PCT):
                    return None
    return candidate.id if candidate.score > effective_current_score else None


@pytest.mark.parametrize("current_kind", ["town_return", "quest", GoalKind.HUNGER, "resolve_blocker"])
@pytest.mark.parametrize("candidate_kind", [GoalKind.HUNGER, GoalKind.FATIGUE, "quest", "detour", "danger"])
@pytest.mark.parametrize("cur_score, cand_score, lock, status", [(10.0, 70.0, 0, ProjectStatus.ACTIVE), (90.0, 70.0, 60, ProjectStatus.ACTIVE), (30.0, 95.0, 60, ProjectStatus.ACTIVE), (50.0, 55.0, 0, ProjectStatus.ACTIVE),
                                                                    (50.0, 95.0, 60, ProjectStatus.SUSPENDED), (2.0, 85.0, 60, ProjectStatus.ACTIVE)])
@pytest.mark.parametrize("resistance", [0.0, 0.5, 1.0])
def test_with_the_rule_off_the_helpers_give_the_pre_refactor_decision(monkeypatch, current_kind, candidate_kind, cur_score, cand_score, lock, status, resistance):
    monkeypatch.setattr(intel, "_escalated_need_takes_switch", lambda *a: False)
    entity = subject(project("cur", current_kind, cur_score, lock=lock, status=status), resistance=resistance)
    candidate = project("cand", candidate_kind, cand_score)
    state = _state(entity, tick=50)
    got = switch(entity, candidate, state)
    assert (got.current_project_id_set if got is not None else None) == oracle(entity, candidate, 50, state)
