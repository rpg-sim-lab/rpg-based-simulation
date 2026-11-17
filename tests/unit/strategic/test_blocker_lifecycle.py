"""Divergence 2.214 (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION): a blocker has a lifecycle that a re-inference does not erase.
`failure_count` and the suppression double with each resolve_blocker timeout (100, 200, 400, 800, capped); a re-inference MERGES into the stored blocker; a congestion blocker is removed after
a quiet spell (suppression over and not re-inferred for 200 ticks), ending a resolve_blocker project that names it COMPLETED / BLOCKER_CLEARED; the timeout ends ABANDONED / BLOCKER_TIMEOUT."""
from __future__ import annotations

import dataclasses
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import (
    BLOCKER_QUIET_SPELL_TICKS,
    CONGESTION_BLOCKER_ID,
    BlockerRemoval,
    BlockerState,
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
    ProjectEnd,
    ProjectState,
    ProjectStatus,
    blocker_timeout_suppression,
    merge_inferred_blocker,
    quiet_blockers,
)
from src.core.update_models.strategic import StrategicUpdate
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

T0 = 1000


def _blocker(bid=CONGESTION_BLOCKER_ID, supp=0, failures=0, seen=None, severity=0.5, resolved=False):
    return BlockerState(id=bid, kind="access", subject="congestion", severity=severity, resolved=resolved, suppression_until_tick=supp, failure_count=failures, last_seen_tick=seen)


def _project(created, status=ProjectStatus.ACTIVE, target=CONGESTION_BLOCKER_ID, pid="proj_resolve_blocker_1"):
    obj = ObjectiveState(id=f"obj_{pid}", kind=ObjectiveKind.REACH_LOCATION, target=target, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id=pid, kind="resolve_blocker", status=status, objectives=[obj], active_objective_id=obj.id, created_tick=created)


def _hero(blockers=(), projects=(), current=None):
    hero = (
        V2EntityBuilder(1).kind("hero").location(10.0, 10.0).identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build()
    )
    strat = replace(hero.strategic, blockers={b.id: b for b in blockers}, projects={p.id: p for p in projects}, current_project_id=current,
                    current_objective_id=projects[0].active_objective_id if current and projects else None)
    return replace(hero, strategic=strat)


def test_the_backoff_doubles_from_100_and_is_capped_at_800():
    assert [blocker_timeout_suppression(n) for n in (1, 2, 3, 4, 5, 6)] == [100, 200, 400, 800, 800, 800]


def test_a_new_inference_is_stamped_with_the_tick():
    assert merge_inferred_blocker(None, _blocker(), T0).last_seen_tick == T0


def test_a_re_inference_keeps_the_suppression_and_failure_count_and_refreshes_what_is_observed():
    stored = _blocker(supp=T0 + 300, failures=2, seen=T0 - 5, severity=0.5)
    merged = merge_inferred_blocker(stored, _blocker(severity=0.9), T0)
    assert merged.suppression_until_tick == T0 + 300 and merged.failure_count == 2
    assert merged.last_seen_tick == T0 and merged.severity == 0.9


def test_the_canonical_dict_omits_the_lifecycle_fields_while_default_and_carries_them_after():
    plain = _blocker()
    assert plain.canonical_dict() == {k: v for k, v in dataclasses.asdict(plain).items() if k not in ("failure_count", "last_seen_tick")}
    assert _blocker(failures=1, seen=7).canonical_dict()["failure_count"] == 1
    assert _blocker(seen=7).canonical_dict()["last_seen_tick"] == 7


def test_a_congestion_blocker_is_quiet_at_exactly_the_quiet_spell_and_not_before():
    b = _blocker(seen=T0)
    assert quiet_blockers({b.id: b}, T0 + BLOCKER_QUIET_SPELL_TICKS - 1) == []
    assert quiet_blockers({b.id: b}, T0 + BLOCKER_QUIET_SPELL_TICKS) == [b.id]


def test_a_suppression_still_in_force_keeps_the_blocker():
    b = _blocker(seen=T0, supp=T0 + 500)
    assert quiet_blockers({b.id: b}, T0 + BLOCKER_QUIET_SPELL_TICKS) == []
    assert quiet_blockers({b.id: b}, T0 + 500) == [b.id]


def test_only_the_congestion_blocker_is_ever_quiet_and_one_with_no_last_seen_is_not():
    other = _blocker(bid="blocker_node_1", seen=T0)
    old = _blocker(seen=None)
    assert quiet_blockers({other.id: other, old.id: old}, T0 + 10_000) == []


def test_the_quiet_spell_removes_the_blocker_with_its_reason_and_ends_the_project_that_names_it():
    b = _blocker(seen=T0)
    proj = _project(created=T0 + 20)
    hero = _hero([b], [proj], current=proj.id)
    up = StrategicIntelligenceSystem.quiet_spell_update(hero, StrategicUpdate(), T0 + BLOCKER_QUIET_SPELL_TICKS)
    assert up.blockers_remove == [b.id] and up.blockers_removed_for == {b.id: BlockerRemoval.QUIET_SPELL}
    (ended,) = up.projects_add_or_update
    assert ended.status == ProjectStatus.COMPLETED and ended.ended_by == ProjectEnd.BLOCKER_CLEARED
    assert up.current_project_id_set == "" and up.current_objective_id_set == ""


def test_a_blocker_inferred_this_pass_is_not_removed():
    b = _blocker(seen=T0)
    staged = StrategicUpdate(blockers_add_or_update=[merge_inferred_blocker(b, b, T0 + BLOCKER_QUIET_SPELL_TICKS)])
    assert StrategicIntelligenceSystem.quiet_spell_update(_hero([b]), staged, T0 + BLOCKER_QUIET_SPELL_TICKS) is None


def test_a_congestion_blocker_with_no_last_seen_is_stamped_on_first_sight():
    up = StrategicIntelligenceSystem.quiet_spell_update(_hero([_blocker(seen=None)]), StrategicUpdate(), T0)
    assert [b.last_seen_tick for b in up.blockers_add_or_update] == [T0] and up.blockers_remove == []


def test_an_unrelated_resolve_blocker_project_is_left_alone():
    b = _blocker(seen=T0)
    other = _project(created=T0, target="blocker_node_9", pid="proj_resolve_blocker_9")
    up = StrategicIntelligenceSystem.quiet_spell_update(_hero([b], [other]), StrategicUpdate(), T0 + BLOCKER_QUIET_SPELL_TICKS)
    assert up.projects_add_or_update == [] and up.current_project_id_set is None


def _timeout_update(failures, tick):
    b = _blocker(failures=failures, seen=tick - 5)
    proj = _project(created=tick - 60)
    hero = _hero([b], [proj], current=proj.id)
    state = AuthoritativeState(tick=tick, seed=1, world_time=tick, entities={hero.id: hero})
    return StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)


@pytest.mark.parametrize("failures,expected", [(0, 100), (1, 200), (2, 400), (3, 800), (4, 800)])
def test_the_timeout_ends_typed_counts_the_failure_and_doubles_the_suppression(failures, expected):
    tick = T0 + 60
    up = _timeout_update(failures, tick)
    (ended,) = [p for p in up.projects_add_or_update if p.kind == "resolve_blocker"]
    assert ended.status == ProjectStatus.ABANDONED and ended.ended_by == ProjectEnd.BLOCKER_TIMEOUT
    (blocker,) = up.blockers_add_or_update
    assert blocker.failure_count == failures + 1 and blocker.suppression_until_tick == tick + expected


def test_applying_a_removal_with_its_reason_changes_only_the_removal_and_stores_nothing_about_the_reason():
    """Divergence 2.214 (B): `blockers_removed_for` is observability only. Through the real apply path (StrategicPatch.apply) the stored blockers lose exactly the removed id and the canonical dict
    of the others is unchanged; nothing of the reason is stored."""
    from src.engine.patches import StrategicPatch

    gone, kept = _blocker(seen=T0), _blocker(bid="blocker_node_9", failures=1, supp=T0 + 300, seen=T0 + 5)
    hero = _hero([gone, kept])
    plain = StrategicUpdate(blockers_remove=[gone.id])
    with_reason = StrategicUpdate(blockers_remove=[gone.id], blockers_removed_for={gone.id: BlockerRemoval.QUIET_SPELL})
    out = {}
    for name, upd in (("plain", plain), ("reason", with_reason)):
        changes: dict = {}
        StrategicPatch(entity_id=hero.id, strategic=upd).apply(hero, changes)
        out[name] = changes["strategic"]
    assert out["reason"].blockers == out["plain"].blockers
    assert set(out["reason"].blockers) == {kept.id}
    assert out["reason"].blockers[kept.id].canonical_dict() == kept.canonical_dict()
    assert not any(hasattr(out["reason"], f) for f in ("blockers_removed_for", "blocker_removal_reasons"))
