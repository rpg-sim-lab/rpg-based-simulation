"""F3 (divergence 2.155): `navigation.lodged_in` is set and cleared by the apply path, survives a move, and leaves the canonical form of a subject that never lodged unchanged."""
from __future__ import annotations

from src.core.updates import NavigationUpdate
from src.engine.apply import ApplyPath
from src.engine.patches import NavigationPatch
from tests.helpers.entities import make_entity


def _apply(entity, patch):
    changes = {}
    patch.apply(entity, changes)
    return changes.get("navigation", entity.navigation)


def test_a_subject_that_never_lodged_keeps_its_canonical_form():
    nav = make_entity(1, pos=(3.0, 4.0)).navigation
    assert nav.lodged_in is None
    assert "lodged_in" not in nav.to_canonical_dict()


def test_lodged_in_is_set_by_the_navigation_patch_and_appears_in_the_canonical_form():
    entity = make_entity(1, pos=(3.0, 4.0))
    nav = _apply(entity, NavigationPatch(entity_id=1, navigation=NavigationUpdate(lodged_in_set=20000), new_position=(5.0, 6.0)))
    assert nav.lodged_in == 20000 and nav.position == (5.0, 6.0)
    assert nav.to_canonical_dict()["lodged_in"] == 20000


def test_a_move_carries_lodged_in_and_a_clear_removes_it():
    entity = make_entity(1, pos=(5.0, 6.0))
    lodged = _apply(entity, NavigationPatch(entity_id=1, navigation=NavigationUpdate(lodged_in_set=7)))
    moved = ApplyPath._fast_replace_navigation(lodged, (9.0, 9.0), None)
    assert moved.lodged_in == 7  # the hand-copied field list in _fast_replace_navigation must carry it
    entity2 = make_entity(1, pos=(5.0, 6.0))
    object.__setattr__(entity2, "navigation", lodged)
    cleared = _apply(entity2, NavigationPatch(entity_id=1, navigation=NavigationUpdate(lodged_in_clear=True), new_position=(5.0, 7.0)))
    assert cleared.lodged_in is None and cleared.position == (5.0, 7.0)


def test_the_navigation_update_merge_and_noop_know_the_lodging_fields():
    assert NavigationUpdate().is_noop()
    assert not NavigationUpdate(lodged_in_set=1).is_noop() and not NavigationUpdate(lodged_in_clear=True).is_noop()
    merged = NavigationUpdate(lodged_in_set=3).merge(NavigationUpdate(lodged_in_clear=True))
    assert merged.lodged_in_set == 3 and merged.lodged_in_clear
