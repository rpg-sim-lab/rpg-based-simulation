"""TCK-20261031-DEATH-CLOSES-NO-PROJECT (divergence 2.226): death ends every live project of the dead body, typed, through the authoritative apply path; records kept; the current project cleared.

Staged in `LifecycleSystem.resolve_lifecycle`'s death block (the sole death authority, so an OLD_AGE death, whose body keeps ``combat.alive`` True, is covered too). The end is ABANDONED / `ProjectEnd.DEATH`
via `end_record`; the quest domain's own `quest_status` is untouched (out of scope, a limit line in Bible ch04).
"""
from __future__ import annotations

import pickle
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import (
    BlockerKind, BlockerState, GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectEnd, ProjectState, ProjectStatus, end_live_on_death, end_record,
)
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate, StrategicUpdate
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
from src.systems.lifecycle import LifecycleSystem
from src.systems.strategic_systems.redirection import StrategicRedirectionSystem

TICK = 100


def project(pid: str, status=ProjectStatus.ACTIVE, kind=GoalKind.HUNGER, target_position=None) -> ProjectState:
    objective = ObjectiveState(id=f"{pid}_o", kind=ObjectiveKind.REACH_LOCATION, target="town_center", status=ObjectiveStatus.ACTIVE, target_position=target_position)
    return ProjectState(id=pid, kind=kind, status=status, objectives=[objective], active_objective_id=objective.id, suspended_since=50 if status == ProjectStatus.SUSPENDED else None)


def body(projects, current=None, age=0, max_age=100000, eid=1):
    entity = V2EntityBuilder(eid).kind("hero").location(0.0, 0.0).lifecycle(age_ticks=age, max_age_ticks=max_age).build()
    strategic = replace(entity.strategic, projects={p.id: p for p in projects}, current_project_id=current, current_objective_id=(f"{current}_o" if current else None))
    return replace(entity, strategic=strategic)


def state_of(*entities, tick=TICK) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=1, entities={e.id: e for e in entities})


def kill_update(eid=1) -> StateUpdate:
    from src.core.updates import CombatUpdate
    return StateUpdate(entity_updates={eid: EntityUpdate(entity_id=eid, combat=CombatUpdate(outcome_kind="KILL", alive_set=False))})


def die(entity, update=None, old_age=False):
    state = state_of(entity)
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate() if old_age else (update or kill_update(entity.id)))
    return state, refined, ApplyPath.apply_generation(state, refined, TICK + 1, TICK + 1)


def test_active_and_suspended_both_end_abandoned_by_death_and_the_records_are_kept():
    entity = body([project("a"), project("s", ProjectStatus.SUSPENDED), project("done", ProjectStatus.COMPLETED)], current="a")
    _, _, after = die(entity)
    projects = after.entities[1].strategic.projects
    assert set(projects) == {"a", "s", "done"}                                                    # nothing deleted
    for pid in ("a", "s"):
        assert (projects[pid].status, projects[pid].ended_by, projects[pid].ended_tick) == (ProjectStatus.ABANDONED, ProjectEnd.DEATH, TICK)
        assert projects[pid].suspended_since is None
    assert (projects["done"].status, projects["done"].ended_by) == (ProjectStatus.COMPLETED, None)  # a terminal record is left as it was


def test_the_current_project_and_objective_are_cleared():
    _, _, after = die(body([project("a")], current="a"))
    assert after.entities[1].strategic.current_project_id in ("", None) and after.entities[1].strategic.current_objective_id in ("", None)


def test_the_update_is_a_typed_strategic_update_not_a_mutation():
    entity = body([project("a")], current="a")
    state, refined, _ = die(entity)
    staged = refined.entity_updates[1].strategic
    assert [p.ended_by for p in staged.projects_add_or_update] == [ProjectEnd.DEATH] and staged.current_project_id_set == ""
    assert state.entities[1].strategic.projects["a"].status == ProjectStatus.ACTIVE                 # the prior state is untouched


def test_an_old_age_body_that_stays_alive_still_ends_its_projects():
    entity = body([project("a"), project("s", ProjectStatus.SUSPENDED)], current="a", age=1000, max_age=1000)
    _, _, after = die(entity, old_age=True)
    assert after.entities[1].combat.alive is True and after.entities[1].lifecycle.active is False   # the old-age caveat (vacancy.py): alive is never written
    assert {p.ended_by for p in after.entities[1].strategic.projects.values()} == {ProjectEnd.DEATH}


def test_a_project_this_tick_already_staged_or_removed_is_not_ended_twice():
    entity = body([project("a"), project("gone")], current="a")
    already = end_record(project("a"), ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED, TICK)
    update = kill_update()
    update = StateUpdate(entity_updates={1: replace(update.entity_updates[1], strategic=StrategicUpdate(projects_add_or_update=[already], projects_remove=["gone"]))})
    _, refined, after = die(entity, update)
    written = {p.id: p for p in refined.entity_updates[1].strategic.projects_add_or_update}
    assert written["a"].ended_by == ProjectEnd.THREAT_CLEARED and "gone" not in {p.id for p in refined.entity_updates[1].strategic.projects_add_or_update if p.ended_by == ProjectEnd.DEATH}
    assert "gone" not in after.entities[1].strategic.projects


def test_a_staged_new_live_project_of_the_dying_body_is_ended_in_the_same_update():
    entity = body([], current=None)
    update = kill_update()
    update = StateUpdate(entity_updates={1: replace(update.entity_updates[1], strategic=StrategicUpdate(projects_add_or_update=[project("new")], current_project_id_set="new"))})
    _, _, after = die(entity, update)
    assert after.entities[1].strategic.projects["new"].ended_by == ProjectEnd.DEATH and after.entities[1].strategic.current_project_id in ("", None)


def test_a_body_with_no_live_and_no_current_project_gets_no_strategic_update():
    entity = body([project("done", ProjectStatus.COMPLETED)], current=None)
    _, refined, _ = die(entity)
    assert refined.entity_updates[1].strategic is None


def test_a_resolve_blocker_end_stamps_its_blocker_like_any_other_end():
    blocker = BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="iron_ore")
    rb = replace(project("rb", kind="resolve_blocker"), objectives=[ObjectiveState(id="rb_o", kind=ObjectiveKind.REACH_LOCATION, target="b1", status=ObjectiveStatus.ACTIVE)])
    entity = body([rb], current="rb")
    entity = replace(entity, strategic=replace(entity.strategic, blockers={"b1": blocker}))
    _, _, after = die(entity)
    assert after.entities[1].strategic.blockers["b1"].last_project_end_tick == TICK


def test_end_live_on_death_is_pure_and_only_live_records():
    projects = {"a": project("a"), "s": project("s", ProjectStatus.SUSPENDED), "x": project("x", ProjectStatus.ABANDONED)}
    out = end_live_on_death(projects, [], [], 7)
    assert sorted(p.id for p in out) == ["a", "s"] and all(p.ended_tick == 7 for p in out)
    assert projects["a"].status == ProjectStatus.ACTIVE


def test_death_is_typed_round_trip_through_the_checkpoint_and_the_hash_moves_only_with_it():
    entity = body([project("a")], current="a")
    state, _, after = die(entity)
    restored = pickle.loads(pickle.dumps(after, protocol=pickle.HIGHEST_PROTOCOL))
    assert restored.entities[1].strategic.projects["a"].ended_by == ProjectEnd.DEATH
    assert CanonicalStateHasher.get_hash(restored) == CanonicalStateHasher.get_hash(after)
    assert after.entities[1].to_canonical_dict()["strategic"]["projects"]["a"]["ended_by"] == "DEATH"
    assert "ended_by" not in state.entities[1].to_canonical_dict()["strategic"]["projects"]["a"]


def test_a_body_that_does_not_die_keeps_its_projects():
    entity = body([project("a")], current="a")
    state = state_of(entity)
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    assert 1 not in refined.entity_updates or refined.entity_updates[1].strategic is None


def test_capacity_enforcement_does_not_trim_a_corpses_records_on_the_death_tick():
    """The :83 check counts every stored record plus the adds; with more than max_active_projects records the death update must trim nothing (ended records are not live, so the trim set is empty)."""
    cap = body([project("a")], current="a").strategic.profile.max_active_projects
    many = [project(f"p{i}", ProjectStatus.SUSPENDED if i % 2 else ProjectStatus.ACTIVE) for i in range(cap + 3)]
    entity = body(many, current="p0")
    state, refined, _ = die(entity)
    enforced = CapacityEnforcementPhase.enforce(state, refined)
    staged = enforced.entity_updates[1].strategic
    assert staged.projects_remove == []
    assert {p.id for p in staged.projects_add_or_update} == {p.id for p in many}


def test_redirection_reissues_no_navigation_for_the_dying_body_on_the_death_tick():
    entity = body([project("a", target_position=(5.0, 5.0))], current="a")
    state, refined, _ = die(entity)
    redirected = StrategicRedirectionSystem.enforce(state, refined)
    nav = redirected.entity_updates[1].navigation
    assert nav is None or nav.target_set is None
