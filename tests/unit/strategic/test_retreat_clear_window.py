"""TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, shape (d): a COMBAT_RETREAT ends THREAT_CLEARED when `present_threat_to` is false AND it has reached its destination OR no
present threat has held for CLEAR_TICKS consecutive ticks (`ProjectState.cleared_since`, written only by `note_threat_state`).

The window rules: a returning threat restarts it; a suspended retreat's window does not advance and restarts on resume; only a COMBAT_RETREAT ever gets one. The e18-shaped case is
urban_political s42 entity 18 (probe9 trace, hp 5/85 at tick 63-82, no hostile perceived for 15 ticks): the old rule ended its retreat at once, the subject was then killed within ~110 ticks.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.combat_constants import CLEAR_TICKS
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import (
    GoalKind,
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
    ProjectEnd,
    ProjectState,
    ProjectStatus,
    note_threat_state,
    restart_clear_window,
)
from src.core.updates import StateUpdate
from src.systems.strategic_systems.entity_target_objective import (
    close_entity_target_project,
    objective_outcome,
    retreat_window_update,
)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue

T0 = 1000
HERO_POS = (10.0, 10.0)
DESTINATION = (40.0, 40.0)


def _entity(eid, faction, pos, hp=100):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos).identity(role=role, faction=faction)
        .combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0, alive=hp > 0).lifecycle(active=True).build()
    )


def _state(*entities, tick):
    return AuthoritativeState(tick=tick, seed=42, world_time=tick, entities={e.id: e for e in entities})


def _retreat(since=None, status=ProjectStatus.ACTIVE):
    obj = ObjectiveState(id="obj_retreat", kind=ObjectiveKind.REACH_LOCATION, target="town_center", target_position=DESTINATION, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id="proj_combat_retreat_1", kind=GoalKind.COMBAT_RETREAT, status=status, objectives=[obj], active_objective_id=obj.id, cleared_since=since)


def _hero(project, pos=HERO_POS, hp=6):
    hero = _entity(1, Faction.HERO_GUILD, pos, hp=hp)
    strategic = replace(hero.strategic, projects={project.id: project}, current_project_id=project.id, current_objective_id=project.active_objective_id)
    return replace(hero, strategic=strategic)


def _obj(project):
    return project.objectives[0]


def _foe(pos):
    return _entity(2, Faction.MONSTER_HORDE, pos)


def _observe(hero, project, tick, foe=None):
    state = _state(hero, *( [foe] if foe else [] ), tick=tick)
    return retreat_window_update(hero, state, project) or project


def _outcome(hero, project, tick):
    return objective_outcome(hero, _state(hero, tick=tick), project, _obj(project))


def test_reaching_the_destination_ends_the_retreat_the_first_clear_tick():
    project = _retreat()
    hero = _hero(project, pos=DESTINATION)
    outcome = _outcome(hero, project, T0)
    assert outcome is not None and outcome.ended_by == ProjectEnd.THREAT_CLEARED


def test_a_present_threat_at_the_destination_does_not_end_it():
    project = _retreat()
    hero = _hero(project, pos=DESTINATION)
    foe = _foe((DESTINATION[0], DESTINATION[1] + 1))
    assert objective_outcome(hero, _state(hero, foe, tick=T0), project, _obj(project)) is None


def test_the_window_opens_on_the_first_clear_tick_and_ends_the_retreat_at_exactly_clear_ticks():
    project = _retreat()
    hero = _hero(project)
    opened = _observe(hero, project, T0)
    assert opened.cleared_since == T0 and _outcome(hero, opened, T0) is None
    assert _outcome(hero, opened, T0 + CLEAR_TICKS - 1) is None
    ended = _outcome(hero, opened, T0 + CLEAR_TICKS)
    assert ended is not None and ended.ended_by == ProjectEnd.THREAT_CLEARED


def test_later_clear_ticks_keep_the_window_where_it_opened():
    project = _retreat()
    hero = _hero(project)
    opened = _observe(hero, project, T0)
    assert _observe(hero, opened, T0 + 50) is opened


def test_a_threat_returning_at_150_restarts_the_window():
    project = _retreat()
    hero = _hero(project)
    opened = _observe(hero, project, T0)
    adjacent = _foe((HERO_POS[0], HERO_POS[1] + 1))
    dropped = _observe(hero, opened, T0 + 150, foe=adjacent)
    assert dropped.cleared_since is None
    reopened = _observe(hero, dropped, T0 + 151)
    assert reopened.cleared_since == T0 + 151
    assert _outcome(hero, reopened, T0 + CLEAR_TICKS) is None  # 200 ticks after the FIRST window would have ended it
    assert _outcome(hero, reopened, T0 + 151 + CLEAR_TICKS) is not None


def test_the_e18_shaped_subject_does_not_end_one_tick_after_the_hostile_leaves_view():
    """hp 0.06, the attacker 12 tiles away (outside the 10-tile perception): no present threat, but the window has only just opened."""
    project = _retreat()
    hero = _hero(project, hp=5)
    far = _foe((HERO_POS[0], HERO_POS[1] + 12))
    assert objective_outcome(hero, _state(hero, far, tick=T0), project, _obj(project)) is None  # window not open yet
    opened = _observe(hero, project, T0, foe=far)
    assert opened.cleared_since == T0
    assert objective_outcome(hero, _state(hero, far, tick=T0 + 1), opened, _obj(opened)) is None
    assert close_entity_target_project(hero, _state(hero, far, tick=T0 + 1), opened) is None


def test_a_suspended_window_does_not_advance_and_restarts_on_resume():
    project = _retreat()
    hero = _hero(project)
    window = _observe(hero, project, T0)
    assert window.cleared_since == T0
    suspended = replace(window, status=ProjectStatus.SUSPENDED)
    assert note_threat_state(suspended, False, T0 + 450) is suspended  # not observed while suspended
    entity = _hero(suspended)
    update = StrategicIntelligenceSystem.resume_project(entity, suspended.id)
    resumed = update.projects_add_or_update[0]
    assert resumed.status == ProjectStatus.ACTIVE and resumed.cleared_since is None
    hero2 = _hero(resumed)
    assert _outcome(hero2, resumed, T0 + 450) is None  # 450 ticks since T0 but not observed clear: no end at once
    reopened = _observe(hero2, resumed, T0 + 450)
    assert reopened.cleared_since == T0 + 450
    assert _outcome(hero2, reopened, T0 + 450 + CLEAR_TICKS - 1) is None
    assert _outcome(hero2, reopened, T0 + 450 + CLEAR_TICKS) is not None


def test_restart_clear_window_is_a_no_op_without_a_window():
    project = _retreat()
    assert restart_clear_window(project) is project


@pytest.mark.parametrize("kind", [GoalKind.COMBAT_ENGAGE, GoalKind.RECOVER, GoalKind.HUNGER])
def test_a_project_of_another_kind_never_gets_a_clear_window(kind):
    other = replace(_retreat(), kind=kind)
    hero = _hero(other)
    assert note_threat_state(other, False, T0) is other
    assert retreat_window_update(hero, _state(hero, tick=T0), other) is None
    assert other.cleared_since is None


def test_the_evaluator_opens_the_window_without_ending_or_switching_the_project():
    project = _retreat()
    hero = _hero(project)
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero, tick=T0), hero, force=True)
    kept = [p for p in update.projects_add_or_update if p.id == project.id]
    assert kept and kept[0].cleared_since == T0 and kept[0].status == ProjectStatus.ACTIVE and kept[0].ended_by is None
    assert update.current_project_id_set is None


def test_the_work_queue_schedules_the_tick_a_window_opens_or_drops_and_not_the_ticks_between():
    from src.core.dirty import DirtySet

    project = _retreat()
    hero = _hero(project)

    def selected(h, tick, *others):
        return StrategicWorkQueue.build(_state(h, *others, tick=tick), StateUpdate(), DirtySet(), budget=10, sweep_interval=10)

    assert 1 in selected(hero, 996)  # no window yet and no threat: the first clear tick opens it
    opened = _hero(_observe(hero, project, 996))
    assert 1 not in selected(opened, 997)  # window standing, nothing changes this tick
    adjacent = _foe((HERO_POS[0], HERO_POS[1] + 1))
    assert 1 in selected(opened, 997, adjacent)  # a threat returned: the window drops this tick


def test_cleared_since_is_absent_from_the_canonical_dict_until_set():
    project = _retreat()
    key = project.id
    assert "cleared_since" not in _hero(project).to_canonical_dict()["strategic"]["projects"][key]
    opened = replace(project, cleared_since=T0)
    assert _hero(opened).to_canonical_dict()["strategic"]["projects"][key]["cleared_since"] == T0


def test_cleared_since_advances_while_lodged():
    """F3 (2.155) hides a lodger from outside, so a lodged retreat holder sees no one: the window opens the first lodged tick, is kept, and ends the retreat after CLEAR_TICKS (the retreat is not held open by a hostile it cannot see)."""
    project = _retreat()
    hero = _hero(project)
    hero = replace(hero, navigation=replace(hero.navigation, lodged_in=7))
    foe = _foe((11.0, 10.0))                       # adjacent outside the building
    for tick in (T0, T0 + 1, T0 + 100):
        project = _observe(hero, project, tick, foe)
        assert project.cleared_since == T0
    hero = _hero(project)
    hero = replace(hero, navigation=replace(hero.navigation, lodged_in=7))
    outcome = _outcome(hero, project, T0 + CLEAR_TICKS)
    assert outcome is not None and outcome.project == ProjectStatus.COMPLETED and outcome.ended_by == ProjectEnd.THREAT_CLEARED
