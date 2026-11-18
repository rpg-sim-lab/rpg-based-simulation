"""The single restore step for fields a checkpoint predates (F3, divergence 2.155; `src/engine/checkpoint_fields.py`).

A slotted dataclass unpickles POSITIONALLY (`dataclasses._dataclass_setstate` zips ``fields()`` with the state tuple), so the old-shape records here are built the way an old pickle
loads: the state tuple of the OLD field list, set through the dataclass's own ``__setstate__`` (a record from before the field existed is one value short)."""
import dataclasses
import pickle

import pytest

from src.core.state import BuildingState, NavigationComponent
from src.engine.checkpoint_fields import CheckpointFieldMissingError, FIELD_RULES, fill_missing_fields
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel, profile


def _old_shape(obj, missing):
    """The record as an older checkpoint loads it: the state tuple lacks the trailing field(s) ``missing``."""
    names = [f.name for f in dataclasses.fields(obj)]
    assert names[-len(missing):] == missing or all(m in names for m in missing)
    old = [n for n in names if n not in missing]
    new = type(obj).__new__(type(obj))
    type(obj).__setstate__(new, tuple(getattr(obj, n) for n in old))
    return new


def _values(obj, skip=()):
    return {f.name: getattr(obj, f.name) for f in dataclasses.fields(obj) if f.name not in skip and f.name != "_canonical_cache"}


def test_lodged_in_and_beds_have_field_rules_naming_their_record():
    """Replaces the append-last position assert (TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION): an insert is now refused by the schema fingerprint whatever the position
    (tests/unit/engine/test_checkpoint_schema.py); what stays pinned is that the appended fields have rows, and which record each row belongs to."""
    by_field = {r.field: r.record for r in FIELD_RULES}
    assert by_field["lodged_in"] == "NavigationComponent" and by_field["beds"] == "BuildingState"
    assert {r.field for r in FIELD_RULES} >= {"lodged_in", "beds"}


def test_a_navigation_without_lodged_in_restores_to_none_keeps_every_other_field_and_the_state_ticks():
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        nav = st.entities[1].navigation
        old = _old_shape(nav, ["lodged_in", "last_moved_tick"])      # PERC-02 appended last_moved_tick after it: a pre-F3 checkpoint lacks both
        with pytest.raises(AttributeError):
            old.lodged_in
        object.__setattr__(st.entities[1], "navigation", old)
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field in ("lodged_in", "last_moved_tick")])
        restored = st.entities[1].navigation
        assert restored.lodged_in is None and restored.last_moved_tick is None
        assert _values(restored, skip=("lodged_in", "last_moved_tick")) == _values(nav, skip=("lodged_in", "last_moved_tick"))      # nothing shifted
        r = Kernel(profile(), pickle.loads(pickle.dumps(st, protocol=pickle.HIGHEST_PROTOCOL)), DeterministicRNG(1))
        try:
            r.tick_once()
            assert r._state.entities[1].navigation.lodged_in is None or r._state.entities[1].navigation.lodged_in == INN_ID
        finally:
            r.shutdown()
    finally:
        k.shutdown()


def test_a_building_without_beds_is_refused_with_a_typed_error_naming_the_field_and_the_building():
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        b = st.buildings[INN_ID]
        old = _old_shape(b, ["beds"])
        assert _values(old, skip=("beds",)) == _values(b, skip=("beds",))                  # beds was last: the other fields did not shift
        object.__setattr__(st, "buildings", {**st.buildings, INN_ID: old})
        with pytest.raises(CheckpointFieldMissingError, match=r"'beds'.*building %d" % INN_ID):
            fill_missing_fields(st)
        assert issubclass(CheckpointFieldMissingError, ValueError)                              # the API route answers 400
    finally:
        object.__setattr__(k._state, "buildings", {**k._state.buildings, INN_ID: b})        # the refused state is not a state to hash: put the real building back before shutdown
        k.shutdown()


def test_a_current_shape_state_is_untouched():
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        before = {i: e.navigation for i, e in k._state.entities.items()}
        fill_missing_fields(k._state)
        assert all(k._state.entities[i].navigation is n for i, n in before.items())
    finally:
        k.shutdown()


def test_a_project_without_cleared_since_restores_to_no_window_and_keeps_every_other_field():
    """2.156: `cleared_since` was appended to ProjectState; a pickle from before it loads one value short and the slot is unset until the restore step fills None."""
    from dataclasses import replace
    from src.core.strategic import GoalKind, ProjectState
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        proj = ProjectState(id="proj_combat_retreat_9", kind=GoalKind.COMBAT_RETREAT, created_tick=3, score=7.5)
        old = _old_shape(proj, ["cleared_since", "suspended_since", "ended_tick"])  # N10 appended suspended_since after it, 2.214 ended_tick after that: a pre-2.156 checkpoint lacks all three
        with pytest.raises(AttributeError):
            old.cleared_since
        e = st.entities[1]
        object.__setattr__(e, "strategic", replace(e.strategic, projects={old.id: old}))
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field in ("cleared_since", "suspended_since", "ended_tick")])
        restored = st.entities[1].strategic.projects[old.id]
        assert restored.cleared_since is None
        assert restored.suspended_since is None
        assert _values(restored, skip=("cleared_since", "suspended_since")) == _values(proj, skip=("cleared_since", "suspended_since"))      # nothing shifted
    finally:
        k.shutdown()


def test_a_project_without_suspended_since_restores_to_no_clock_and_keeps_every_other_field():
    """2.212 (N10): `suspended_since` was appended to ProjectState; a pickle from before it loads one value short and the slot is unset until the restore step fills None."""
    from dataclasses import replace
    from src.core.strategic import GoalKind, ProjectState, ProjectStatus
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        proj = ProjectState(id="proj_combat_engage_9", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.SUSPENDED, created_tick=3, score=7.5)
        old = _old_shape(proj, ["suspended_since", "ended_tick"])  # 2.214 appended ended_tick after it: an older pickle lacks both
        with pytest.raises(AttributeError):
            old.suspended_since
        e = st.entities[1]
        object.__setattr__(e, "strategic", replace(e.strategic, projects={old.id: old}))
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field in ("suspended_since", "ended_tick")])
        restored = st.entities[1].strategic.projects[old.id]
        assert restored.suspended_since is None
        assert _values(restored, skip=("suspended_since",)) == _values(proj, skip=("suspended_since",))
    finally:
        k.shutdown()


def test_a_navigation_without_last_moved_tick_restores_to_never_stepped_and_keeps_every_other_field():
    """PERC-02 (2.210): `last_moved_tick` was appended to NavigationComponent; a pickle from before it loads one value short and the slot is unset until the restore step fills None."""
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        nav = st.entities[1].navigation
        old = _old_shape(nav, ["last_moved_tick"])
        with pytest.raises(AttributeError):
            old.last_moved_tick
        object.__setattr__(st.entities[1], "navigation", old)
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field == "last_moved_tick"])
        restored = st.entities[1].navigation
        assert restored.last_moved_tick is None
        assert _values(restored, skip=("last_moved_tick",)) == _values(nav, skip=("last_moved_tick",))      # nothing shifted
        assert {r.field: r.record for r in FIELD_RULES}["last_moved_tick"] == "NavigationComponent"
    finally:
        k.shutdown()


def test_last_moved_tick_survives_a_checkpoint_round_trip_and_the_hash_includes_it():
    from dataclasses import replace
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        e = st.entities[1]
        stepped = replace(e, navigation=replace(e.navigation, last_moved_tick=41))
        assert e.navigation.to_canonical_dict() != stepped.navigation.to_canonical_dict()      # the canonical form (hence the state hash) carries the step tick
        assert "last_moved_tick" not in e.navigation.to_canonical_dict()                       # and a body that never stepped keeps its old form
        assert stepped.navigation.to_canonical_dict()["last_moved_tick"] == 41
        loaded = pickle.loads(pickle.dumps(stepped.navigation, protocol=pickle.HIGHEST_PROTOCOL))
        assert loaded.last_moved_tick == 41
    finally:
        k.shutdown()


def test_a_blocker_without_the_lifecycle_fields_restores_to_none_and_no_failures_and_keeps_every_other_field():
    """2.214: `failure_count`, `last_seen_tick` and `last_project_end_tick` were appended to BlockerState; a pickle from before them loads three values short until the restore step fills them."""
    from dataclasses import replace
    from src.core.strategic import BlockerState
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        blk = BlockerState(id="blocker_congestion", kind="access", subject="congestion", severity=0.5, suppression_until_tick=40)
        old = _old_shape(blk, ["failure_count", "last_seen_tick", "last_project_end_tick"])
        with pytest.raises(AttributeError):
            old.failure_count
        e = st.entities[1]
        object.__setattr__(e, "strategic", replace(e.strategic, blockers={old.id: old}))
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field in ("failure_count", "last_seen_tick", "last_project_end_tick")])
        restored = st.entities[1].strategic.blockers[old.id]
        assert restored.failure_count == 0 and restored.last_seen_tick is None and restored.last_project_end_tick is None
        assert _values(restored, skip=("failure_count", "last_seen_tick", "last_project_end_tick")) == _values(blk, skip=("failure_count", "last_seen_tick", "last_project_end_tick"))
    finally:
        k.shutdown()


def test_a_project_without_ended_tick_restores_to_no_end_tick_and_keeps_every_other_field():
    """2.214 (churn): `ended_tick` was appended to ProjectState; a pickle from before it loads one value short and the slot is unset until the restore step fills None."""
    from dataclasses import replace
    from src.core.strategic import GoalKind, ProjectEnd, ProjectState, ProjectStatus, end_record
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        proj = end_record(ProjectState(id="proj_combat_engage_9", kind=GoalKind.COMBAT_ENGAGE, created_tick=3, score=7.5), ProjectStatus.ABANDONED, ProjectEnd.SUPERSEDED_BY_TARGET, 41)
        assert proj.ended_tick == 41 and proj.canonical_extra()["ended_tick"] == 41
        old = _old_shape(proj, ["ended_tick"])
        with pytest.raises(AttributeError):
            old.ended_tick
        e = st.entities[1]
        object.__setattr__(e, "strategic", replace(e.strategic, projects={old.id: old}))
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field == "ended_tick"])
        restored = st.entities[1].strategic.projects[old.id]
        assert restored.ended_tick is None and "ended_tick" not in restored.canonical_extra()
        assert _values(restored, skip=("ended_tick",)) == _values(proj, skip=("ended_tick",))
    finally:
        k.shutdown()


def test_a_blocker_without_last_project_end_tick_restores_to_none_and_a_set_one_round_trips():
    """2.214 (churn): `last_project_end_tick` was appended after `last_seen_tick`; a pickle from before it loads one value short and the slot is unset until the restore step fills None. A set value survives the canonical dict."""
    from dataclasses import replace
    from src.core.strategic import BlockerState
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        blk = BlockerState(id="blocker_congestion", kind="access", subject="congestion", failure_count=2, last_seen_tick=30, last_project_end_tick=55)
        assert blk.canonical_dict()["last_project_end_tick"] == 55 and "last_project_end_tick" not in replace(blk, last_project_end_tick=None).canonical_dict()
        old = _old_shape(blk, ["last_project_end_tick"])
        with pytest.raises(AttributeError):
            old.last_project_end_tick
        e = st.entities[1]
        object.__setattr__(e, "strategic", replace(e.strategic, blockers={old.id: old}))
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field == "last_project_end_tick"])
        restored = st.entities[1].strategic.blockers[old.id]
        assert restored.last_project_end_tick is None
        assert _values(restored, skip=("last_project_end_tick",)) == _values(blk, skip=("last_project_end_tick",))
    finally:
        k.shutdown()
