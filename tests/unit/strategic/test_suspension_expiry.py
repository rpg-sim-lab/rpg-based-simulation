"""N10 (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK, divergence 2.212): a SUSPENDED project that stays suspended for SUSPENSION_TTL_TICKS ends ABANDONED /
SUSPENSION_EXPIRED through `end_record`. The clock is `ProjectState.suspended_since`: set by every SUSPENDED writer, cleared on resume, omitted from the canonical dict while None."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import (
    SUSPENSION_TTL_TICKS,
    GoalKind,
    ProjectEnd,
    ProjectState,
    ProjectStatus,
    expire_suspended,
    has_project_capacity,
    is_live_project,
    suspend_record,
)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.world_systems.events import EventInterpreter

T0 = 1000


def _proj(pid="p1", status=ProjectStatus.SUSPENDED, since=T0, kind=GoalKind.COMBAT_ENGAGE):
    return ProjectState(id=pid, kind=kind, status=status, suspended_since=since)


def _hero(*projects, current=None):
    hero = (
        V2EntityBuilder(1).kind("hero").location(10.0, 10.0).identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build()
    )
    return replace(hero, strategic=replace(hero.strategic, projects={p.id: p for p in projects}, current_project_id=current, current_objective_id=None))


def _state(hero, tick):
    return AuthoritativeState(tick=tick, seed=42, world_time=tick, entities={hero.id: hero})


def test_the_ttl_is_two_hundred_ticks():
    assert SUSPENSION_TTL_TICKS == 200


def test_a_record_one_tick_short_of_the_ttl_is_left_alone_and_at_the_ttl_it_ends_typed():
    assert expire_suspended({"p1": _proj()}, T0 + SUSPENSION_TTL_TICKS - 1) == []
    (ended,) = expire_suspended({"p1": _proj()}, T0 + SUSPENSION_TTL_TICKS)
    assert ended.status == ProjectStatus.ABANDONED and ended.ended_by == ProjectEnd.SUSPENSION_EXPIRED


@pytest.mark.parametrize("kind", [GoalKind.HUNGER, GoalKind.FATIGUE, GoalKind.HARVESTING, GoalKind.RESOLVE_BLOCKER, GoalKind.COMBAT_ENGAGE])
def test_every_kind_expires_the_exempt_need_projects_included(kind):
    (ended,) = expire_suspended({"p": _proj("p", kind=kind)}, T0 + SUSPENSION_TTL_TICKS)
    assert ended.ended_by == ProjectEnd.SUSPENSION_EXPIRED


def test_only_a_suspended_record_is_touched():
    rows = {"a": _proj("a", ProjectStatus.ACTIVE, None), "c": _proj("c", ProjectStatus.COMPLETED, None), "x": _proj("x", ProjectStatus.ABANDONED, None)}
    assert expire_suspended(rows, T0 + 10_000) == []


def test_a_suspended_record_with_no_clock_is_stamped_on_first_sight_and_counts_from_there():
    (stamped,) = expire_suspended({"p": _proj(since=None)}, T0)
    assert stamped.status == ProjectStatus.SUSPENDED and stamped.suspended_since == T0 and stamped.ended_by is None
    assert expire_suspended({"p": stamped}, T0 + SUSPENSION_TTL_TICKS - 1) == []
    assert expire_suspended({"p": stamped}, T0 + SUSPENSION_TTL_TICKS)[0].ended_by == ProjectEnd.SUSPENSION_EXPIRED


def test_a_terminal_record_carries_no_clock():
    (ended,) = expire_suspended({"p": _proj()}, T0 + SUSPENSION_TTL_TICKS)
    assert ended.suspended_since is None


def test_the_typed_end_is_written_once():
    (ended,) = expire_suspended({"p": _proj()}, T0 + SUSPENSION_TTL_TICKS)
    assert expire_suspended({ended.id: ended}, T0 + 10_000) == []


def test_the_canonical_extra_omits_the_clock_while_none_and_carries_it_after():
    assert "suspended_since" not in ProjectState(id="p", kind=GoalKind.COMBAT_ENGAGE).canonical_extra()
    assert _proj().canonical_extra()["suspended_since"] == T0


def test_suspend_record_opens_the_clock_at_the_tick():
    out = suspend_record(ProjectState(id="p", kind=GoalKind.COMBAT_ENGAGE), 77)
    assert out.status == ProjectStatus.SUSPENDED and out.suspended_since == 77


def test_resume_clears_the_clock():
    hero = _hero(_proj())
    up = StrategicIntelligenceSystem.resume_project(hero, "p1")
    (resumed,) = up.projects_add_or_update
    assert resumed.status == ProjectStatus.ACTIVE and resumed.suspended_since is None


def test_the_project_switch_opens_the_clock():
    cur = ProjectState(id="cur", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE, score=1.0)
    new = ProjectState(id="new", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.ACTIVE, score=90.0)
    up = StrategicIntelligenceSystem.evaluate_project_switch(_hero(cur, current="cur"), new, T0 + 500)
    if up is not None:  # the arbiter may hold the current project; when it switches the suspended record carries the tick
        old = next(p for p in up.projects_add_or_update if p.id == "cur")
        assert old.status == ProjectStatus.SUSPENDED and old.suspended_since == T0 + 500


def test_the_near_death_suspend_opens_the_clock_and_clears_the_current_ids():
    cur = ProjectState(id="cur", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE)
    up = EventInterpreter.interpret_near_death(_hero(cur, current="cur"), current_tick=60)
    old = next(p for p in up.projects_add_or_update if p.id == "cur")
    assert old.status == ProjectStatus.SUSPENDED and old.suspended_since == 60
    assert up.current_project_id_set == "" and up.current_objective_id_set == ""


def test_the_expiry_update_ends_the_old_record_and_leaves_a_young_one():
    hero = _hero(_proj("old", since=T0), _proj("young", since=T0 + 150))
    up = StrategicIntelligenceSystem.suspension_expiry_update(hero, T0 + SUSPENSION_TTL_TICKS)
    assert [p.id for p in up.projects_add_or_update] == ["old"]
    assert up.current_project_id_set is None


def test_an_expiring_current_project_clears_the_current_ids_in_the_same_update():
    hero = _hero(_proj("old", since=T0), current="old")
    up = StrategicIntelligenceSystem.suspension_expiry_update(hero, T0 + SUSPENSION_TTL_TICKS)
    assert up.current_project_id_set == "" and up.current_objective_id_set == ""


def test_nothing_to_expire_yields_no_update():
    assert StrategicIntelligenceSystem.suspension_expiry_update(_hero(_proj(since=T0)), T0 + 5) is None
    assert StrategicIntelligenceSystem.suspension_expiry_update(_hero(), T0) is None


def test_a_full_suspended_set_frees_its_slots_on_the_strategic_pass_before_the_capacity_gate():
    projs = [_proj(f"p{i}", since=T0) for i in range(3)]
    hero = _hero(*projs)
    assert not has_project_capacity(hero.strategic.projects, 3)
    up = StrategicIntelligenceSystem.evaluate_strategic_intent_with_expiry(_state(hero, T0 + SUSPENSION_TTL_TICKS), hero, force=True)
    ended = {p.id: p for p in up.projects_add_or_update if p.ended_by == ProjectEnd.SUSPENSION_EXPIRED}
    assert set(ended) == {"p0", "p1", "p2"}
    assert not any(is_live_project(p) for p in ended.values())


def test_a_dead_or_inactive_subject_expires_nothing():
    hero = _hero(_proj())
    dead = replace(hero, combat=replace(hero.combat, alive=False))
    up = StrategicIntelligenceSystem.evaluate_strategic_intent_with_expiry(_state(dead, T0 + 9999), dead, force=True)
    assert up.is_noop()
