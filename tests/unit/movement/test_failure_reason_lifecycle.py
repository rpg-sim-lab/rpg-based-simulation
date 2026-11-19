"""TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE: ``last_failure_reason`` is the outcome of the LAST step.

A step that carries a code sets it, a successful step clears it through the typed ``NavigationUpdate.failure_reason_clear``, and a bare None (a give-up, a held step) leaves it as it was.
Codes come from any action writer; ONLY a successful movement step clears it. Blocker inference therefore stops acting on a failure once the subject has moved on."""
from dataclasses import replace

from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import NavigationUpdate
from src.engine.movement import MovementSystem
from src.engine.patches import NavigationPatch
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


def _hero(**nav):
    return V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(**nav).build()


def _state(hero, *others):
    return AuthoritativeState(entities={1: hero, **{o.id: o for o in others}}, tick=0, seed=123)


def _wall(eid, x, y):
    return V2EntityBuilder(eid).kind("OBSTACLE").location(x, y).build()


def _apply(entity, nav_update):
    changes = {}
    NavigationPatch(entity_id=entity.id, navigation=nav_update).apply(entity, changes)
    return changes["navigation"]


def test_a_successful_step_emits_the_typed_clear_and_no_code():
    hero = _hero(target=(9, 5), last_failure_reason="PATH_NOT_FOUND")
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]
    assert upd.new_position is not None
    assert upd.navigation.failure_reason is None and upd.navigation.failure_reason_clear is True


def test_a_successful_step_clears_the_stored_reason_through_the_patch():
    hero = _hero(target=(9, 5), last_failure_reason="PATH_NOT_FOUND")
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]
    assert _apply(hero, upd.navigation).last_failure_reason is None


def test_a_failed_step_sets_its_code_and_does_not_clear():
    ring = [_wall(10 + i, 5 + dx, 5 + dy) for i, (dx, dy) in enumerate((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0))]
    hero = _hero(target=(9, 5))
    upd = MovementSystem.resolve_move(_state(hero, *ring), hero, (9, 5))[1]
    assert upd.new_position is None
    assert upd.navigation.failure_reason is not None and upd.navigation.failure_reason_clear is False
    assert _apply(hero, upd.navigation).last_failure_reason == upd.navigation.failure_reason


def test_a_bare_none_update_keeps_the_old_reason_where_no_step_succeeded():
    hero = _hero(target=(9, 5), last_failure_reason="STUCK")
    assert _apply(hero, NavigationUpdate(moved_recently_set=True)).last_failure_reason == "STUCK"


def test_a_code_in_the_same_update_wins_over_the_clear():
    hero = _hero(last_failure_reason="STUCK")
    assert _apply(hero, NavigationUpdate(failure_reason="PATH_NOT_FOUND", failure_reason_clear=True)).last_failure_reason == "PATH_NOT_FOUND"


def test_the_clear_alone_is_not_a_noop_and_survives_a_merge():
    clear = NavigationUpdate(failure_reason_clear=True)
    assert clear.is_noop() is False
    assert NavigationUpdate(moved_recently_set=True).merge(clear).failure_reason_clear is True
    assert NavigationUpdate(failure_reason_clear=True).merge(NavigationUpdate(moved_recently_set=True)).failure_reason_clear is True
    assert NavigationUpdate().is_noop() is True


def test_a_stale_failure_no_longer_files_an_access_blocker_against_a_new_target():
    """The before-picture: with a step that did not clear (main's behaviour) a stale PATH_NOT_FOUND files ACCESS for the NEW target; with the clear it does not."""
    hero = _hero(target=(9, 5), last_failure_reason="PATH_NOT_FOUND")
    new_payload = {"target_position": (30.0, 30.0)}
    stale = _apply(hero, NavigationUpdate(moved_recently_set=True))  # no clear: the old value is carried forward
    fixed = _apply(hero, NavigationUpdate(moved_recently_set=True, failure_reason_clear=True))
    filed_stale = StrategicIntelligenceSystem.infer_blockers(replace(hero, navigation=stale), "ENTITY_MOVE", new_payload, navigation_failure=stale.last_failure_reason)
    filed_fixed = StrategicIntelligenceSystem.infer_blockers(replace(hero, navigation=fixed), "ENTITY_MOVE", new_payload, navigation_failure=fixed.last_failure_reason)
    assert [b.id for b in filed_stale.blockers_add_or_update] == ["blocker_access_30_30"]
    assert not any(b.kind == "access" and b.id.startswith("blocker_access_") for b in filed_fixed.blockers_add_or_update)


def test_no_new_state_field_is_added_to_the_checkpoint_or_the_fingerprint():
    """The clear is a field of the UPDATE, not of the state: the navigation component's fields are the same as before."""
    from dataclasses import fields

    from src.core.state import NavigationComponent
    assert not any("failure_reason_clear" in f.name for f in fields(NavigationComponent))
