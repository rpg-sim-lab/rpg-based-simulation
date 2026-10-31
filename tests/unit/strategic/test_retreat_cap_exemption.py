"""TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, designer ruling: a retreat under a present threat is never refused for project capacity.

1. GATE: a NEW COMBAT_RETREAT candidate while `present_threat_to` holds passes the capacity gate exactly as an escalated need does (`exempt_from_the_project_cap`); the capacity trim
   still chooses which record yields the slot.
2. NO REMOVAL: an ACTIVE COMBAT_RETREAT under a present threat is never the record the capacity trim removes; once the threat is absent it is an ordinary project.
3. SCOPE: retreat only. RECOVER and COMBAT_ENGAGE get no exemption.

Trace: urban_political s42 entity 18 (probe9, fix arm): live set 3/3 (two SUSPENDED STABILIZE never resumed + one ACTIVE STABILIZE), hp 0.07, retreat_u 124-137 vs recover_u 89-110, threat True:
no retreat was adopted from tick 122 and the subject was killed at tick 195. The grid is standalone; the precedence grid adopts it when ENGAGEMENT-OVERRIDES lands.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.escalation import exempt_from_the_project_cap
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import (
    GoalKind,
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
    ProjectKind,
    ProjectState,
    ProjectStatus,
    has_project_capacity,
    retreat_held_under_threat,
)
from src.core.updates import EntityUpdate, StateUpdate, StrategicUpdate
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

TICK = 200


def _project(pid, kind=ProjectKind.TRAVEL, status=ProjectStatus.SUSPENDED, score=40.0):
    obj = ObjectiveState(id=f"o_{pid}", kind=ObjectiveKind.REACH_LOCATION, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id=pid, kind=kind, status=status, objectives=[obj], active_objective_id=obj.id, score=score)


def _hero(projects, hp=20, hunger=0.0, current=None):
    hero = V2EntityBuilder(1).kind("hero").location(10.0, 10.0).identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD).combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0).cognition(max_active_projects=3).build()
    hero = replace(hero, biological=replace(hero.biological, hunger=hunger))
    return replace(hero, strategic=replace(hero.strategic, projects={p.id: p for p in projects}, current_project_id=current or "", current_objective_id=""))


def _foe(pos=(10.0, 11.0)):
    return (V2EntityBuilder(2).kind("monster").location(*pos).identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0).lifecycle(active=True).build())


def _state(*entities):
    return AuthoritativeState(tick=TICK, seed=42, world_time=TICK, entities={e.id: e for e in entities})


FULL = [_project("stab_t2"), _project("stab_t22"), _project("stab_t102", status=ProjectStatus.ACTIVE)]


def test_e18_at_a_full_cap_with_an_adjacent_hostile_adopts_a_retreat():
    hero = _hero(FULL, current="stab_t102")
    assert not has_project_capacity(hero.strategic.projects, 3)
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero, _foe()), hero, force=True)
    assert [p for p in update.projects_add_or_update if p.kind == GoalKind.COMBAT_RETREAT and p.status == ProjectStatus.ACTIVE]


def test_at_a_full_cap_with_no_threat_nothing_new_is_adopted():
    hero = _hero(FULL, current="stab_t102")
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero), hero, force=True)
    assert not [p for p in update.projects_add_or_update if p.id not in hero.strategic.projects and p.status == ProjectStatus.ACTIVE]


@pytest.mark.parametrize("cap_full", [True, False])
@pytest.mark.parametrize("threat", [True, False])
@pytest.mark.parametrize("kind, hunger", [(GoalKind.COMBAT_RETREAT, 0.0), (GoalKind.HUNGER, 95.0), (GoalKind.RECOVER, 0.0), (GoalKind.COMBAT_ENGAGE, 0.0)])
def test_grid_a_new_project_passes_a_full_cap_only_as_an_escalated_need_or_a_retreat_under_threat(cap_full, threat, kind, hunger):
    projects = FULL if cap_full else FULL[:1]
    hero = _hero(projects, hunger=hunger, current="stab_t102")
    state = _state(hero, _foe()) if threat else _state(hero)
    admitted = has_project_capacity(hero.strategic.projects, 3) or exempt_from_the_project_cap(hero, state, kind)
    exempt_expected = (kind == GoalKind.COMBAT_RETREAT and threat) or (kind == GoalKind.HUNGER)  # HUNGER at 95 is past its onset whatever the threat (escalated_need_wins reads the need only)
    assert admitted == ((not cap_full) or exempt_expected)
    assert exempt_from_the_project_cap(hero, state, kind) == exempt_expected


def _trim(hero):
    new = _project("new", score=60.0, status=ProjectStatus.ACTIVE)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, strategic=StrategicUpdate(projects_add_or_update=[new]))})
    return CapacityEnforcementPhase.enforce(_state(hero), update).entity_updates[1].strategic.projects_remove


def _hero_with_retreat(cleared_since=None, ret_score=1.0):
    ret = replace(_project("ret", kind=GoalKind.COMBAT_RETREAT, status=ProjectStatus.ACTIVE, score=ret_score), cleared_since=cleared_since)
    return _hero([ret, _project("a", score=40.0), _project("b", score=45.0)], current="ret")


def test_a_retreat_held_under_a_present_threat_is_never_the_record_the_trim_removes():
    assert _trim(_hero_with_retreat()) == []  # outside the count like an escalated need: the other three fit the cap of 3, nothing is evicted for it (the cap plus one, as with a need)


def test_once_the_threat_is_absent_the_same_retreat_is_an_ordinary_project_and_the_trim_may_remove_it():
    assert _trim(_hero_with_retreat(cleared_since=TICK - 5)) == ["ret"]  # a clear window is open: the lowest score yields the slot


def test_retreat_held_under_threat_needs_the_current_active_retreat_with_no_clear_window():
    hero = _hero_with_retreat()
    ret = hero.strategic.projects["ret"]
    assert retreat_held_under_threat(ret, "ret")
    assert not retreat_held_under_threat(ret, "a")  # not the current project
    assert not retreat_held_under_threat(replace(ret, cleared_since=TICK), "ret")  # window open
    assert not retreat_held_under_threat(replace(ret, status=ProjectStatus.SUSPENDED), "ret")
    assert not retreat_held_under_threat(hero.strategic.projects["a"], "a")  # another kind
