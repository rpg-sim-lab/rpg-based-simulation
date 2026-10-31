"""TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, commit 2: a COMBAT_RETREAT project completes when its threat is gone.

The end is `objective_outcome`'s retreat branch (shared by the evaluator and the strategic work queue): COMPLETED with the typed end THREAT_CLEARED once no perceived hostile is
adjacent (decision 32) or acts on the subject. The retreat here is created through the real selection path (a wounded hero beside a hostile), never hand-built, so a
GoalKind-vs-ProjectKind or string-vs-enum mismatch cannot skip the branch unseen.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
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
    is_live_project,
)
from src.engine.need_wake import NEED_WAKE_CADENCE
from src.systems.strategic_systems.entity_target_objective import (
    ObjectiveOutcome,
    close_entity_target_project,
    entity_target_outcome,
    objective_outcome,
)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue

TICK = 60


def _entity(eid, faction, pos, hp=100):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos).identity(role=role, faction=faction)
        .combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0, alive=hp > 0).lifecycle(active=True).build()
    )


def _state(*entities, tick=TICK):
    return AuthoritativeState(tick=tick, seed=42, world_time=tick, entities={e.id: e for e in entities})


def _hero(foe_pos=(10.0, 11.0)):
    """A wounded hero with a retreat project the real selection path created beside a hostile, plus that hostile."""
    hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0), hp=10)
    foe = _entity(2, Faction.MONSTER_HORDE, foe_pos)
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero, foe), hero, force=True)
    retreats = [p for p in update.projects_add_or_update if p.kind == GoalKind.COMBAT_RETREAT]
    assert retreats, "a wounded hero beside a hostile must adopt a retreat (non-vacuous setup)"
    project = retreats[0]
    strategic = replace(hero.strategic, projects={project.id: project}, current_project_id=project.id, current_objective_id=project.active_objective_id)
    return replace(hero, strategic=strategic), foe, project


def _objective(project):
    return next(o for o in project.objectives if o.id == project.active_objective_id)


def test_the_retreat_the_selection_path_creates_is_a_combat_retreat_project_with_no_entity_target():
    _hero_with_project, _foe, project = _hero()
    assert project.kind == GoalKind.COMBAT_RETREAT and project.status == ProjectStatus.ACTIVE
    assert _objective(project).target_entity_id is None


def test_it_holds_while_a_hostile_is_adjacent():
    hero, foe, project = _hero(foe_pos=(10.0, 11.0))
    assert objective_outcome(hero, _state(hero, foe), project, _objective(project)) is None
    assert close_entity_target_project(hero, _state(hero, foe), project) is None


def test_it_holds_while_a_hostile_acts_on_the_subject_from_a_distance():
    hero, foe, project = _hero()
    hero = replace(hero, combat=replace(hero.combat, last_hit_tick=TICK - 1, last_attacker_id=2))
    far_foe = replace(foe, navigation=replace(foe.navigation, position=(10.0, 14.0)))
    assert objective_outcome(hero, _state(hero, far_foe), project, _objective(project)) is None


def test_it_completes_with_threat_cleared_when_the_hostile_is_gone():
    hero, _foe, project = _hero()
    outcome = objective_outcome(hero, _state(hero), project, _objective(project))
    assert outcome == ObjectiveOutcome(ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED)
    closed = close_entity_target_project(hero, _state(hero), project)
    assert (closed.status, closed.ended_by) == (ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED)
    assert _objective(closed).status == ObjectiveStatus.RESOLVED and not is_live_project(closed)


def test_it_completes_when_a_hostile_is_perceived_but_neither_adjacent_nor_acting():
    hero, foe, project = _hero()
    watching_foe = replace(foe, navigation=replace(foe.navigation, position=(10.0, 13.0)))
    assert objective_outcome(hero, _state(hero, watching_foe), project, _objective(project)).ended_by == ProjectEnd.THREAT_CLEARED


def test_an_old_hit_is_not_a_present_threat():
    hero, foe, project = _hero()
    hero = replace(hero, combat=replace(hero.combat, last_hit_tick=TICK - NEED_WAKE_CADENCE - 1, last_attacker_id=2))
    far_foe = replace(foe, navigation=replace(foe.navigation, position=(10.0, 14.0)))
    assert objective_outcome(hero, _state(hero, far_foe), project, _objective(project)).ended_by == ProjectEnd.THREAT_CLEARED


def test_a_returning_threat_gets_a_new_retreat_through_the_scorer_not_the_old_record():
    hero, foe, project = _hero()
    closed = close_entity_target_project(hero, _state(hero), project)
    strategic = replace(hero.strategic, projects={closed.id: closed}, current_project_id="", current_objective_id="")
    hero_after = replace(hero, strategic=strategic)
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero_after, foe, tick=TICK + 5), hero_after, force=True)
    new = [p for p in update.projects_add_or_update if p.kind == GoalKind.COMBAT_RETREAT and p.status == ProjectStatus.ACTIVE]
    assert new and all(p.ended_by is None for p in new)


def test_the_work_queue_schedules_the_evaluation_when_the_threat_leaves_and_not_while_it_holds():
    from src.core.dirty import DirtySet
    from src.core.updates import StateUpdate

    hero, foe, _project = _hero()

    def selected(state):
        # sweep_interval=10 and (tick + id) % 10 != 0 for entity 1 at tick 58: only an urgent tier selects it.
        return StrategicWorkQueue.build(state, StateUpdate(), DirtySet(), budget=10, sweep_interval=10)

    assert 1 not in selected(_state(hero, foe, tick=58))
    assert 1 in selected(_state(hero, tick=58))


def test_other_kinds_return_what_they_returned_before_with_no_end():
    hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
    foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0))
    obj = ObjectiveState(id="combat_engage_2", kind=ObjectiveKind.DEFEAT_ENEMY, target="2", status=ObjectiveStatus.ACTIVE, target_entity_id=2)
    proj = ProjectState(id="proj_combat_engage_1", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)
    assert objective_outcome(hero, _state(hero, foe), proj, obj) is None
    dead_foe = replace(foe, combat=replace(foe.combat, alive=False, hp=0))
    state = _state(hero, dead_foe)
    assert objective_outcome(hero, state, proj, obj) == ObjectiveOutcome(*entity_target_outcome(hero, state, obj))
    assert objective_outcome(hero, state, proj, obj).ended_by is None
    # a project that is neither a retreat, entity-targeted nor a contract has no outcome
    plain = ProjectState(id="proj_hunger_1", kind=GoalKind.HUNGER, status=ProjectStatus.ACTIVE, objectives=[replace(obj, target_entity_id=None)], active_objective_id=obj.id)
    assert objective_outcome(hero, state, plain, plain.objectives[0]) is None
