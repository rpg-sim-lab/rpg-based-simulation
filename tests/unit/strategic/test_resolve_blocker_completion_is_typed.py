"""Divergence 2.214 (D): a resolve_blocker project that completes at the generic objective-resolution site of `fused_strategic_pass` ends through `end_record` as COMPLETED with
`ProjectEnd.BLOCKER_CLEARED`, whatever made its blocker go (here: absent from the stored blockers). Before this a resolve_blocker project whose blocker had been removed completed with
`ended_by` None one pass later. A hand-built state through the fused pass itself."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectEnd, ProjectState, ProjectStatus
from src.core.updates import StateUpdate
from src.engine.cadence import SystemCadence
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

BLOCKER = "blocker_congestion"
PID = "proj_resolve_blocker_100"


def _scene(stored_blockers):
    obj = ObjectiveState(id="obj_rb", kind=ObjectiveKind.REACH_LOCATION, target=BLOCKER, blocker_ids=[BLOCKER], status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(id=PID, kind="resolve_blocker", status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id, created_tick=100)
    hero = (
        V2EntityBuilder(1).kind("hero").location(10.0, 10.0).identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build()
    )
    strat = replace(hero.strategic, projects={PID: proj}, current_project_id=PID, current_objective_id=obj.id, blockers=dict(stored_blockers))
    hero = replace(hero, strategic=replace(strat))
    return AuthoritativeState(tick=110, seed=1, world_time=110, entities={1: hero})


def _pass(state):
    return StrategicIntelligenceSystem.fused_strategic_pass(state, StateUpdate(entity_updates={}), cadence=SystemCadence(strategic_intelligence=1, concern_evaluation=1))


def test_a_resolve_blocker_project_whose_blocker_is_absent_ends_completed_with_blocker_cleared():
    out = _pass(_scene({}))
    writes = [p for p in out.entity_updates[1].strategic.projects_add_or_update if p.id == PID]
    assert writes, "the fused pass wrote nothing for the resolve_blocker project whose blocker is absent"
    completed = [p for p in writes if p.status == ProjectStatus.COMPLETED]
    assert completed, f"no COMPLETED write: {[(p.status, p.ended_by) for p in writes]}"
    assert all(p.ended_by == ProjectEnd.BLOCKER_CLEARED for p in completed)
    assert all(p.ended_tick == 110 for p in completed)  # the fused pass passes state.tick; a NameError or a missing tick here fails the test (it ran on a state at tick 110)
