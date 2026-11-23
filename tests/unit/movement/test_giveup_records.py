"""TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON, commit 1 (rpg-designer FINAL v2.1): the typed give-up record. Movement appends one at a give-up, the navigation patch applies it
(newest last, at most GIVEUP_RECORDS_CAP, a drop is counted), the strategic pass clears them; the record is omitted from the canonical form and the fingerprint while empty."""
from dataclasses import replace

import pytest

from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GIVEUP_RECORDS_CAP, GiveUpDropCounts, GiveUpRecord
from src.core.state import AuthoritativeState
from src.core.updates import NavigationUpdate
from src.engine.movement import MovementSystem
from src.engine.patches import NavigationPatch
from src.core.navigation_experience import NavCause, RingEvidence
from src.replay.fingerprint import StateFingerprinter


@pytest.fixture(autouse=True)
def _reset_drops():
    GiveUpDropCounts.reset()
    yield
    GiveUpDropCounts.reset()


def _hero(**nav):
    return V2EntityBuilder(1).kind("human").location(5, 5).combat(readiness=100.0).navigation(**nav).build()


def _wall(eid, x, y):
    return V2EntityBuilder(eid).kind("OBSTACLE").location(x, y).build()


def _apply(entity, update):
    changes = {}
    NavigationPatch(entity_id=entity.id, navigation=update).apply(entity, changes)
    return changes["navigation"]


def _give_up_update(hero, tick=7, anchor=(9, 5)):
    """The oscillation give-up on a boxed-in hero with a spent way-round count: returns resolve_move's navigation update."""
    hero = replace(hero, navigation=replace(hero.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=anchor, wayround_last_tick=0))
    state = AuthoritativeState(entities={1: hero, 10: _wall(10, 5, 4), 11: _wall(11, 5, 6), 12: _wall(12, 4, 5)}, tick=tick, seed=1)
    return MovementSystem.resolve_move(state, hero, (9, 5))[1].navigation


def _ring_blocked_record(anchor, tick):
    """The widened record (design section 3) of the boxed-in hero: obstacle bodies (entities) on three ring tiles, the fourth is the tile just left, so the ring check finds no legal tile (RING_BLOCKED, the refusals are bodies), the subject's tile (5, 5), the target tile (9, 5), no stored purpose."""
    return GiveUpRecord(anchor=anchor, tick=tick, cause=NavCause.RING_BLOCKED, ring_evidence=(RingEvidence.BODIES,), from_position=(5, 5), target_tile=(9, 5), purpose=None)


def test_a_give_up_carries_one_typed_record_of_the_pursuit_anchor_and_the_tick():
    nav = _give_up_update(_hero(target=(9, 5), last_position=(6, 5), oscillation_count=3), tick=7, anchor=(9, 4))
    assert nav.wayround_clear is True
    assert nav.giveup_record_add == _ring_blocked_record(anchor=(9, 4), tick=7)  # the tile the count opened on, not this tick's target tile


def test_a_give_up_with_no_open_anchor_records_the_target_tile():
    hero = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    hero = replace(hero, navigation=replace(hero.navigation, wayround_count=0, wayround_anchor=None))
    state = AuthoritativeState(entities={1: hero, 10: _wall(10, 5, 4), 11: _wall(11, 5, 6), 12: _wall(12, 4, 5)}, tick=3, seed=1)
    nav = MovementSystem.resolve_move(state, hero, (9, 5))[1].navigation
    assert nav.wayround_clear is True and nav.giveup_record_add == _ring_blocked_record(anchor=(9, 5), tick=3)


def test_a_way_round_step_writes_no_record():
    hero = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    nav = MovementSystem.resolve_move(AuthoritativeState(entities={1: hero}, tick=0, seed=1), hero, (9, 5))[1].navigation
    assert nav.wayround_clear is False and nav.giveup_record_add is None


def test_the_patch_appends_newest_last_and_clears_through_the_typed_flag():
    hero = _hero()
    one, two = GiveUpRecord((1, 1), 5), GiveUpRecord((2, 2), 9)
    nav = _apply(hero, NavigationUpdate(giveup_record_add=one))
    assert nav.giveup_records == (one,)
    hero = replace(hero, navigation=nav)
    nav = _apply(hero, NavigationUpdate(giveup_record_add=two))
    assert nav.giveup_records == (one, two)
    assert _apply(replace(hero, navigation=nav), NavigationUpdate(giveup_records_clear=True)).giveup_records == ()
    assert _apply(replace(hero, navigation=nav), NavigationUpdate(target_set=(3, 3))).giveup_records == (one, two)  # nothing else touches them


def test_a_clear_and_an_add_in_one_update_keeps_the_new_record():
    old, new = GiveUpRecord((1, 1), 5), GiveUpRecord((4, 4), 20)
    hero = replace(_hero(), navigation=replace(_hero().navigation, giveup_records=(old,)))
    assert _apply(hero, NavigationUpdate(giveup_records_clear=True, giveup_record_add=new)).giveup_records == (new,)


def test_a_record_past_the_cap_drops_the_oldest_and_is_counted():
    hero = _hero()
    records = [GiveUpRecord((i, i), 10 * i) for i in range(GIVEUP_RECORDS_CAP + 2)]
    for r in records:
        hero = replace(hero, navigation=_apply(hero, NavigationUpdate(giveup_record_add=r)))
    assert hero.navigation.giveup_records == tuple(records[-GIVEUP_RECORDS_CAP:])
    assert GiveUpDropCounts.dropped() == 2


def test_update_merge_and_noop_carry_the_record_fields():
    r = GiveUpRecord((3, 3), 1)
    assert NavigationUpdate().is_noop() and not NavigationUpdate(giveup_record_add=r).is_noop() and not NavigationUpdate(giveup_records_clear=True).is_noop()
    merged = NavigationUpdate(target_set=(1, 1)).merge(NavigationUpdate(giveup_record_add=r)).merge(NavigationUpdate(giveup_records_clear=True))
    assert merged.giveup_record_add == r and merged.giveup_records_clear is True and merged.target_set == (1, 1)


def test_the_canonical_form_and_the_fingerprint_omit_the_field_while_empty_and_show_it_while_held():
    hero = _hero()
    state = AuthoritativeState(entities={1: hero}, tick=0, seed=1)
    assert "giveup_records" not in hero.navigation.to_canonical_dict()
    held = replace(hero, navigation=replace(hero.navigation, giveup_records=(GiveUpRecord((9, 5), 7),)))
    assert held.navigation.to_canonical_dict()["giveup_records"] == [{"anchor": [9, 5], "tick": 7}]
    empty_fp = StateFingerprinter.get_fingerprint(state)["state_hash"]
    held_fp = StateFingerprinter.get_fingerprint(AuthoritativeState(entities={1: held}, tick=0, seed=1))["state_hash"]
    assert empty_fp != held_fp
    cleared = replace(held, navigation=replace(held.navigation, giveup_records=()))
    assert StateFingerprinter.get_fingerprint(AuthoritativeState(entities={1: cleared}, tick=0, seed=1))["state_hash"] == empty_fp  # a subject that never gave up (or consumed them) is unchanged


def test_held_records_round_trip_through_the_real_checkpoint_writer(tmp_path):
    from types import SimpleNamespace
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.scenario_checkpoint import ScenarioCheckpointer
    from src.scenarios.schema import SimulationScenarioDefinition

    spec = SimulationScenarioDefinition(id="f2_roundtrip", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    hero = _hero()
    hero = replace(hero, navigation=replace(hero.navigation, giveup_records=(GiveUpRecord((9, 5), 7), GiveUpRecord((2, 8), 11))))
    state = AuthoritativeState(entities={1: hero}, tick=0, seed=123)
    svc = SimpleNamespace(_kernel=SimpleNamespace(state=state), tick=0, _spec=spec)
    path = tmp_path / "ckpt.bin"
    ScenarioCheckpointer.save(svc, path)
    restored = ScenarioCheckpointer.restore(path, spec)
    try:
        r_state = restored._kernel.state
        assert r_state.entities[1].navigation.giveup_records == (GiveUpRecord((9, 5), 7), GiveUpRecord((2, 8), 11))
        assert CanonicalStateHasher.get_hash(r_state) == CanonicalStateHasher.get_hash(state)
    finally:
        restored.abort()
