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
    ended_blocker_stamps,
    merge_inferred_blocker,
    quiet_blockers,
)
from src.core.update_models.strategic import StrategicUpdate
from src.systems.strategic_systems.blocker_lifecycle import quiet_spell_update
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

T0 = 1000


def _blocker(bid=CONGESTION_BLOCKER_ID, supp=0, failures=0, seen=None, severity=0.5, resolved=False, end=None):
    return BlockerState(id=bid, kind="access", subject="congestion", severity=severity, resolved=resolved, suppression_until_tick=supp, failure_count=failures, last_seen_tick=seen,
                        last_project_end_tick=end)


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
    assert plain.canonical_dict() == {k: v for k, v in dataclasses.asdict(plain).items() if k not in ("failure_count", "last_seen_tick", "last_project_end_tick")}
    assert _blocker(failures=1, seen=7).canonical_dict()["failure_count"] == 1
    assert _blocker(seen=7).canonical_dict()["last_seen_tick"] == 7
    assert _blocker(end=9).canonical_dict()["last_project_end_tick"] == 9


def test_a_congestion_blocker_is_quiet_at_exactly_the_quiet_spell_and_not_before():
    b = _blocker(seen=T0)
    assert quiet_blockers({b.id: b}, {}, T0 + BLOCKER_QUIET_SPELL_TICKS - 1) == []
    assert quiet_blockers({b.id: b}, {}, T0 + BLOCKER_QUIET_SPELL_TICKS) == [b.id]


def test_the_quiet_spell_counts_from_the_end_of_a_suppression_not_from_its_start():
    """Divergence 2.214 (rpg-designer ruling, urban s42 eid 11): 200 ticks of OBSERVABLE quiet = tick >= max(last_seen, suppression_until) + 200."""
    b = _blocker(seen=T0, supp=T0 + 500)
    assert quiet_blockers({b.id: b}, {}, T0 + 500 + BLOCKER_QUIET_SPELL_TICKS - 1) == []
    assert quiet_blockers({b.id: b}, {}, T0 + 500) == []
    assert quiet_blockers({b.id: b}, {}, T0 + 500 + BLOCKER_QUIET_SPELL_TICKS) == [b.id]


def test_only_the_congestion_blocker_is_ever_quiet_and_one_with_no_last_seen_is_not():
    other = _blocker(bid="blocker_node_1", seen=T0)
    old = _blocker(seen=None)
    assert quiet_blockers({other.id: other, old.id: old}, {}, T0 + 10_000) == []


@pytest.mark.parametrize("status", [ProjectStatus.ACTIVE, ProjectStatus.SUSPENDED])
def test_a_live_resolve_blocker_project_naming_it_keeps_the_blocker_however_long_it_is_quiet(status):
    """eid 11's shape: a clear while a project is live must not remove the blocker (which would reset its backoff)."""
    b = _blocker(seen=T0, failures=1, end=T0 + 30)
    live = _project(created=T0 + 20, status=status)
    assert quiet_blockers({b.id: b}, {live.id: live}, T0 + 10 * BLOCKER_QUIET_SPELL_TICKS) == []
    done = replace(live, status=ProjectStatus.ABANDONED, ended_by=ProjectEnd.BLOCKER_TIMEOUT, ended_tick=T0 + 30)
    assert quiet_blockers({b.id: b}, {done.id: done}, T0 + 30 + BLOCKER_QUIET_SPELL_TICKS) == [b.id]


def test_the_eid_11_shape_a_timeout_then_a_quiet_clear_during_suppression_keeps_the_blocker_and_its_backoff():
    """Timeout at t=170 (failure 1, suppression to 270): last seen at 96 is far enough back for the old rule at t=297, but not for the new bound max(96, 270) + 200 = 470."""
    b = _blocker(seen=96, supp=270, failures=1, end=170)
    ended = replace(_project(created=109), status=ProjectStatus.ABANDONED, ended_by=ProjectEnd.BLOCKER_TIMEOUT, ended_tick=170)
    hero = _hero([b], [ended])
    assert quiet_spell_update(hero, StrategicUpdate(), 297) is None
    assert quiet_spell_update(hero, StrategicUpdate(), 469) is None
    up = quiet_spell_update(hero, StrategicUpdate(), 470)
    assert up.blockers_remove == [b.id] and up.blockers_removed_for == {b.id: BlockerRemoval.QUIET_SPELL}


def test_the_quiet_spell_removes_the_blocker_with_its_reason_after_a_real_observable_quiet():
    b = _blocker(seen=T0)
    up = quiet_spell_update(_hero([b]), StrategicUpdate(), T0 + BLOCKER_QUIET_SPELL_TICKS)
    assert up.blockers_remove == [b.id] and up.blockers_removed_for == {b.id: BlockerRemoval.QUIET_SPELL}
    assert up.projects_add_or_update == [] and up.current_project_id_set is None


def test_a_blocker_inferred_this_pass_is_not_removed():
    b = _blocker(seen=T0)
    staged = StrategicUpdate(blockers_add_or_update=[merge_inferred_blocker(b, b, T0 + BLOCKER_QUIET_SPELL_TICKS)])
    assert quiet_spell_update(_hero([b]), staged, T0 + BLOCKER_QUIET_SPELL_TICKS) is None


def test_a_congestion_blocker_with_no_last_seen_is_stamped_on_first_sight():
    up = quiet_spell_update(_hero([_blocker(seen=None)]), StrategicUpdate(), T0)
    assert [b.last_seen_tick for b in up.blockers_add_or_update] == [T0] and up.blockers_remove == []


def test_an_unrelated_resolve_blocker_project_is_left_alone():
    b = _blocker(seen=T0)
    other = _project(created=T0, target="blocker_node_9", pid="proj_resolve_blocker_9")
    up = quiet_spell_update(_hero([b], [other]), StrategicUpdate(), T0 + BLOCKER_QUIET_SPELL_TICKS)
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


def test_a_live_project_names_the_blocker_in_eid_11s_shape_so_nothing_is_removed_and_the_backoff_stays():
    """eid 11 (urban s42): the blocker was last seen at 96, a timeout set failure 1 and suppression to 270, the next project (built at 269) was live when the old rule removed it at 297."""
    b = _blocker(seen=96, supp=270, failures=1)
    live = _project(created=269, pid="proj_resolve_blocker_269")
    hero = _hero([b], [live], current=live.id)
    assert quiet_spell_update(hero, StrategicUpdate(), 297) is None
    assert quiet_spell_update(hero, StrategicUpdate(), 10_000) is None


@pytest.mark.parametrize("end", [ProjectEnd.SUSPENSION_EXPIRED, ProjectEnd.SUPERSEDED_BY_TARGET, ProjectEnd.BLOCKER_TIMEOUT])
def test_any_typed_end_of_a_project_naming_it_holds_the_blocker_until_the_end_tick_plus_the_quiet_spell(end):
    """A project that ended by SUSPENSION_EXPIRED (or any other typed end) at 600 holds the blocker, last seen at 100 with its suppression over, until 600 + 200."""
    b = _blocker(seen=100, supp=0, end=600)
    ended = replace(_project(created=300), status=ProjectStatus.ABANDONED, ended_by=end, ended_tick=600)
    hero = _hero([b], [ended])
    assert quiet_spell_update(hero, StrategicUpdate(), 600 + BLOCKER_QUIET_SPELL_TICKS - 1) is None
    up = quiet_spell_update(hero, StrategicUpdate(), 600 + BLOCKER_QUIET_SPELL_TICKS)
    assert up.blockers_remove == [b.id] and up.blockers_removed_for == {b.id: BlockerRemoval.QUIET_SPELL}


def test_the_blocker_stamps_follow_the_latest_end_of_the_projects_that_ended():
    b = _blocker(seen=100, end=300)
    early = replace(_project(created=110, pid="p_early"), status=ProjectStatus.ABANDONED, ended_by=ProjectEnd.BLOCKER_TIMEOUT, ended_tick=170)
    late = replace(_project(created=500, pid="p_late"), status=ProjectStatus.ABANDONED, ended_by=ProjectEnd.SUSPENSION_EXPIRED, ended_tick=700)
    other = replace(_project(created=500, target="blocker_node_9", pid="p_other"), status=ProjectStatus.ABANDONED, ended_by=ProjectEnd.BLOCKER_TIMEOUT, ended_tick=800)
    assert [x.last_project_end_tick for x in ended_blocker_stamps({b.id: b}, [early])] == []          # older than the stored 300: nothing to write
    assert [x.last_project_end_tick for x in ended_blocker_stamps({b.id: b}, [early, late, other])] == [700]
    assert ended_blocker_stamps({}, [late]) == []                                                       # a blocker no longer stored


def test_a_project_ended_and_trimmed_in_its_end_tick_still_holds_the_spell_until_end_plus_the_quiet_spell():
    """The capacity trim can list a record that ends this tick in projects_remove. The update that ends it also carries the blocker stamp, so applying it through the real apply path leaves
    the blocker field set with no project record at all, and the removal waits until end + 200."""
    from src.engine.patches import StrategicPatch

    b = _blocker(seen=100, supp=0, failures=1)
    live = _project(created=500)
    hero = _hero([b], [live], current=live.id)
    ended = replace(live, status=ProjectStatus.ABANDONED, ended_by=ProjectEnd.SUSPENSION_EXPIRED, ended_tick=600)
    upd = StrategicUpdate(projects_add_or_update=[ended], projects_remove=[ended.id], blockers_add_or_update=ended_blocker_stamps(hero.strategic.blockers, [ended]))
    changes: dict = {}
    StrategicPatch(entity_id=hero.id, strategic=upd).apply(hero, changes)
    after = replace(hero, strategic=changes["strategic"])
    assert after.strategic.projects == {} and after.strategic.blockers[b.id].last_project_end_tick == 600
    assert quiet_spell_update(after, StrategicUpdate(), 600 + BLOCKER_QUIET_SPELL_TICKS - 1) is None
    assert quiet_spell_update(after, StrategicUpdate(), 600 + BLOCKER_QUIET_SPELL_TICKS).blockers_remove == [b.id]


def test_a_later_trim_and_a_re_inference_leave_the_blocker_field_intact():
    b = _blocker(seen=100, end=600)
    assert merge_inferred_blocker(b, _blocker(), 650).last_project_end_tick == 600
    from src.engine.patches import StrategicPatch
    hero = _hero([b], [])
    changes: dict = {}
    StrategicPatch(entity_id=hero.id, strategic=StrategicUpdate(projects_remove=["gone"])).apply(hero, changes)
    assert (changes.get("strategic") or hero.strategic).blockers[b.id].last_project_end_tick == 600


def test_the_suspension_expiry_pass_stamps_the_blocker_in_the_same_update():
    from src.core.strategic import SUSPENSION_TTL_TICKS

    b = _blocker(seen=T0)
    parked = replace(_project(created=T0, status=ProjectStatus.SUSPENDED), suspended_since=T0)
    hero = _hero([b], [parked])
    up = StrategicIntelligenceSystem.suspension_expiry_update(hero, T0 + SUSPENSION_TTL_TICKS)
    (ended,) = up.projects_add_or_update
    assert ended.ended_by == ProjectEnd.SUSPENSION_EXPIRED and ended.ended_tick == T0 + SUSPENSION_TTL_TICKS
    (stamped,) = up.blockers_add_or_update
    assert stamped.id == b.id and stamped.last_project_end_tick == T0 + SUSPENSION_TTL_TICKS


def test_the_timeout_stamps_the_blocker_in_the_same_update():
    tick = T0 + 60
    up = _timeout_update(0, tick)
    (ended,) = [p for p in up.projects_add_or_update if p.kind == "resolve_blocker"]
    (blocker,) = up.blockers_add_or_update
    assert ended.ended_tick == tick and blocker.last_project_end_tick == tick


def test_superseding_a_resolve_blocker_stamps_its_blocker_in_the_same_update():
    from src.ai.goals.live_record_route import LiveRecordRoute, supersede_on_win

    b = _blocker(seen=T0)
    existing = _project(created=T0)
    candidate = _project(created=T0 + 5, pid="proj_other")
    route = LiveRecordRoute(existing=existing, target_matches=False)
    out = supersede_on_win(StrategicUpdate(projects_add_or_update=[candidate]), route, candidate, T0 + 7, {b.id: b})
    assert out is not None
    assert any(p.id == existing.id and p.ended_tick == T0 + 7 for p in out.projects_add_or_update)
    assert [x.last_project_end_tick for x in out.blockers_add_or_update] == [T0 + 7]


def test_the_timeout_update_applied_through_the_real_patch_keeps_the_count_the_backoff_and_the_end_tick_together():
    """One staged blocker carries failure_count + 1, the new suppression AND last_project_end_tick: the stamp never rebuilds the blocker from the stored record."""
    from src.engine.patches import StrategicPatch

    tick = T0 + 60
    up = _timeout_update(2, tick)
    hero = _hero([_blocker(failures=2, seen=tick - 5)], [_project(created=tick - 60)])
    changes: dict = {}
    StrategicPatch(entity_id=hero.id, strategic=up).apply(hero, changes)
    stored = changes["strategic"].blockers[CONGESTION_BLOCKER_ID]
    assert (stored.failure_count, stored.suppression_until_tick, stored.last_project_end_tick) == (3, tick + blocker_timeout_suppression(3), tick)


def test_a_supersede_stamp_is_built_on_the_blocker_the_same_update_already_rewrote():
    from src.ai.goals.live_record_route import LiveRecordRoute, supersede_on_win

    stored = _blocker(seen=T0, failures=1)
    rewritten = replace(stored, failure_count=2, suppression_until_tick=T0 + 400)
    candidate = _project(created=T0 + 5, pid="proj_other")
    route = LiveRecordRoute(existing=_project(created=T0), target_matches=False)
    out = supersede_on_win(StrategicUpdate(projects_add_or_update=[candidate], blockers_add_or_update=[rewritten]), route, candidate, T0 + 7, {stored.id: stored})
    last = [b for b in out.blockers_add_or_update if b.id == stored.id][-1]          # the later entry wins at apply
    assert (last.failure_count, last.suppression_until_tick, last.last_project_end_tick) == (2, T0 + 400, T0 + 7)


def test_the_expiry_stamp_survives_a_write_of_the_same_blocker_by_the_body_of_the_same_call():
    """suspension expiry + the 50-tick timeout of another project naming the same blocker, in one evaluate_strategic_intent_with_expiry call: after the real apply the blocker has the
    timeout's count and suppression and an end tick (the later of the two ends)."""
    from src.engine.patches import StrategicPatch

    tick = T0 + 300
    b = _blocker(seen=tick - 5)
    parked = replace(_project(created=T0, status=ProjectStatus.SUSPENDED, pid="proj_resolve_blocker_parked"), suspended_since=T0)
    running = _project(created=tick - 60, pid="proj_resolve_blocker_running")
    hero = _hero([b], [parked, running], current=running.id)
    state = AuthoritativeState(tick=tick, seed=1, world_time=tick, entities={hero.id: hero})
    up = StrategicIntelligenceSystem.evaluate_strategic_intent_with_expiry(state, hero, force=True)
    changes: dict = {}
    StrategicPatch(entity_id=hero.id, strategic=up).apply(hero, changes)
    stored = changes["strategic"].blockers[CONGESTION_BLOCKER_ID]
    assert stored.failure_count == 1 and stored.suppression_until_tick == tick + blocker_timeout_suppression(1) and stored.last_project_end_tick == tick
