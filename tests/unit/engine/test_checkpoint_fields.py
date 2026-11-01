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


def test_every_rule_field_is_the_last_field_of_its_record_or_the_pickle_shift_is_invisible():
    """beds was inserted before `_canonical_cache`: an old pickle then put the old cache value in `beds` and nothing looked missing. Each F3 field is last."""
    assert [f.name for f in dataclasses.fields(NavigationComponent)][-1] == "lodged_in"
    assert [f.name for f in dataclasses.fields(BuildingState)][-1] == "beds"
    assert {r.field for r in FIELD_RULES} >= {"lodged_in", "beds"}


def test_a_navigation_without_lodged_in_restores_to_none_keeps_every_other_field_and_the_state_ticks():
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        nav = st.entities[1].navigation
        old = _old_shape(nav, ["lodged_in"])
        with pytest.raises(AttributeError):
            old.lodged_in
        object.__setattr__(st.entities[1], "navigation", old)
        fill_missing_fields(st, [r for r in FIELD_RULES if r.field == "lodged_in"])
        restored = st.entities[1].navigation
        assert restored.lodged_in is None
        assert _values(restored, skip=("lodged_in",)) == _values(nav, skip=("lodged_in",))      # nothing shifted
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
