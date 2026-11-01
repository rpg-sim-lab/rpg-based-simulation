"""TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS: restoring a checkpoint written before the group-contract binding.

A frozen slotted dataclass unpickles positionally and without running __init__/__post_init__, so an older checkpoint leaves the new slots absent
(AttributeError on first read). fill_missing_fields is the one post-unpickle step: it fills a field only when its value is a pure function of the
loaded state, otherwise it refuses with CheckpointFieldMissingError. The old shape is produced here by pickling with the new fields left out.
"""
from __future__ import annotations

import dataclasses
import json
import pickle
import struct

import pytest

from src.core.state import AuthoritativeState, GroupRecord, seeded_next_group_id
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.checkpoint_fields import FIELD_RULES, CheckpointFieldMissingError, check_group_counter, fill_missing_fields
from src.engine.scenario_checkpoint import ScenarioCheckpointer
from src.systems.world_systems.groups import GroupSystem

NEW_GROUP_FIELDS = {"contract_holder_id", "dissolution_reason", "dissolution_contract_status"}


def _old_shape_dumps(state, monkeypatch, *, group_fields=True, counter=True):
    """Pickle `state` the way a build before the binding did: the new fields are not in the saved tuple."""
    def group_state(self):
        return [getattr(self, f.name) for f in dataclasses.fields(self) if f.name not in NEW_GROUP_FIELDS]

    def auth_state(self):
        return [getattr(self, f.name) for f in dataclasses.fields(self) if f.name != "next_group_id"]

    if group_fields:
        monkeypatch.setattr(GroupRecord, "__getstate__", group_state, raising=False)
    if counter:
        monkeypatch.setattr(AuthoritativeState, "__getstate__", auth_state, raising=False)
    try:
        return pickle.dumps(state)
    finally:
        monkeypatch.undo()


def _state(groups):
    return AuthoritativeState(tick=7, seed=1, groups=groups, next_item_instance_id=77)


def _unbound(gid=10003):
    return GroupRecord(id=gid, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0), last_updated_tick=4)


def _bound(gid=10004, **kw):
    return GroupRecord(id=gid, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0), contract_id="r1", contract_holder_id=1, **kw)


def test_an_old_shape_checkpoint_leaves_the_new_slots_absent_and_keeps_every_other_field_aligned(monkeypatch):
    blob = _old_shape_dumps(_state({10003: _unbound()}), monkeypatch)
    old = pickle.loads(blob)
    g = old.groups[10003]
    assert not hasattr(g, "contract_holder_id") and not hasattr(old, "next_group_id")  # absent, not a neighbour's value
    assert old.next_item_instance_id == 77 and g.last_updated_tick == 4 and g.contract_id is None


def test_an_old_checkpoint_with_an_unbound_group_restores_with_holder_none_and_the_counter_seeded(monkeypatch):
    old = pickle.loads(_old_shape_dumps(_state({10003: _unbound(), 10009: _unbound(10009)}), monkeypatch))
    fill_missing_fields(old)
    g = old.groups[10003]
    assert (g.contract_holder_id, g.dissolution_reason, g.dissolution_contract_status) == (None, None, None)
    assert old.next_group_id == seeded_next_group_id(old.groups) == 10010
    assert g.to_canonical_dict() == _unbound().to_canonical_dict()


def test_an_old_checkpoint_with_a_bound_group_is_refused_naming_the_group(monkeypatch):
    old = pickle.loads(_old_shape_dumps(_state({10003: _unbound(), 10004: _bound()}), monkeypatch))
    with pytest.raises(CheckpointFieldMissingError, match=r"predates the group-contract binding: group 10004"):
        fill_missing_fields(old)


def test_a_retained_dissolved_record_with_a_contract_counts_as_bound(monkeypatch):
    old = pickle.loads(_old_shape_dumps(_state({10004: _bound(dissolution_tick=9)}), monkeypatch))
    with pytest.raises(CheckpointFieldMissingError, match="retained dissolved record"):
        fill_missing_fields(old)


def test_a_current_shape_round_trip_is_byte_equal_and_untouched_by_the_step():
    state = _state({10003: _unbound(), 10004: _bound()})
    blob = pickle.dumps(state)
    back = pickle.loads(blob)
    fill_missing_fields(back)
    assert pickle.dumps(back) == blob
    assert CanonicalStateHasher.to_canonical_data(back) == CanonicalStateHasher.to_canonical_data(state)
    assert back.groups[10004].contract_holder_id == 1


def test_with_only_the_counter_slot_missing_it_is_seeded_and_the_readers_work(monkeypatch):
    old = pickle.loads(_old_shape_dumps(_state({10003: _bound(), 10012: _unbound(10012)}), monkeypatch, group_fields=False))
    assert not hasattr(old, "next_group_id")
    fill_missing_fields(old)
    assert old.next_group_id == 10013
    GroupSystem.update_groups(old)  # groups.py reads state.next_group_id without error
    new = ApplyPath.apply_generation(old, GroupSystem.update_groups(old))  # apply.py reads it too
    assert new.next_group_id >= 10013


def test_every_rule_names_its_ruling_and_the_step_is_the_only_caller():
    assert {r.field for r in FIELD_RULES} == {"next_group_id", *NEW_GROUP_FIELDS, "lodged_in", "beds"}  # the group rows and F3 (2.155) rows share the one table
    assert all(r.ruling for r in FIELD_RULES)
    import pathlib
    src = pathlib.Path("src")
    users = [str(p) for p in src.rglob("*.py") if "fill_missing_fields(state)" in p.read_text() and p.name != "checkpoint_fields.py"]
    assert users == ["src/engine/scenario_checkpoint.py"]


def test_restore_refuses_a_bound_group_checkpoint_before_building_a_kernel(tmp_path, monkeypatch):
    from src.scenarios.schema import SimulationScenarioDefinition
    blob = _old_shape_dumps(_state({10004: _bound()}), monkeypatch)
    header = json.dumps({"tick": 7, "spec_id": "s", "rng_checkpoint": None}).encode()
    path = tmp_path / "old.bin"
    path.write_bytes(struct.pack("<I", len(header)) + header + blob)
    spec = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    with pytest.raises(CheckpointFieldMissingError) as err:
        ScenarioCheckpointer.restore(path, spec)
    assert isinstance(err.value, ValueError)  # the restore route answers ValueError as a client error


def test_a_group_pickled_under_the_old_module_path_still_loads_through_the_re_export(monkeypatch):
    """GroupRecord lives in src.core.group_record; pickles name the module, so checkpoints written when it lived in src.core.state must still load."""
    import sys

    import src.core.state as state_module
    assert state_module.GroupRecord is GroupRecord
    monkeypatch.setattr(GroupRecord, "__module__", "src.core.state")
    blob = pickle.dumps(_bound())
    monkeypatch.undo()
    assert b"src.core.state" in blob and b"src.core.group_record" not in blob
    back = pickle.loads(blob)
    assert type(back) is GroupRecord and back.contract_holder_id == 1
    assert "src.core.group_record" in sys.modules


def test_restore_fills_an_old_shape_checkpoint_before_the_kernel_is_built_and_reads_it(tmp_path, monkeypatch):
    """The ordering the restore step relies on: on an old-shape checkpoint the new slots are ABSENT after unpickling, `fill_missing_fields` runs inside `restore`,
    and only then is the Kernel built. The Kernel is replaced by a recorder that captures the state it is given, so this proves the order without running a tick."""
    import src.engine.kernel as kernel_module
    from src.scenarios.schema import SimulationScenarioDefinition
    seen = {}

    class RecordingKernel:
        def __init__(self, profile, state, rng, *a, **k):
            seen["next_group_id"] = state.next_group_id
            seen["holder"] = state.groups[10003].contract_holder_id
            seen["reason"] = state.groups[10003].dissolution_reason

    blob = _old_shape_dumps(_state({10003: _unbound(), 10009: _unbound(10009)}), monkeypatch)  # first: the helper undoes the monkeypatch it made
    monkeypatch.setattr(kernel_module, "Kernel", RecordingKernel)
    assert not hasattr(pickle.loads(blob), "next_group_id")  # absent as unpickled: nothing reads it before the fill
    header = json.dumps({"tick": 7, "spec_id": "s", "rng_checkpoint": None}).encode()
    path = tmp_path / "old.bin"
    path.write_bytes(struct.pack("<I", len(header)) + header + blob)
    spec = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    ScenarioCheckpointer.restore(path, spec)
    assert seen == {"next_group_id": 10010, "holder": None, "reason": None}


def test_after_restore_the_counter_is_an_int_and_never_none(monkeypatch):
    old = pickle.loads(_old_shape_dumps(_state({10003: _unbound()}), monkeypatch))
    fill_missing_fields(old)
    check_group_counter(old)
    assert type(old.next_group_id) is int and old.next_group_id == 10004
    assert type(_state({}).next_group_id) is int and _state({}).next_group_id == 10000  # a fresh state starts at 10000, nothing seeds it


def test_a_counter_not_above_every_stored_non_squad_id_raises_at_restore_and_one_above_it_passes():
    from src.engine.checkpoint_fields import GroupCounterBehindStoreError
    groups = {10003: _unbound(), 10009: _unbound(10009)}
    behind = _state(groups)
    object.__setattr__(behind, "next_group_id", 10009)  # equal to a stored id: the next formation would reuse it
    with pytest.raises(GroupCounterBehindStoreError, match="needs >= 10010"):
        check_group_counter(behind)
    ok = _state(groups)
    object.__setattr__(ok, "next_group_id", 10010)
    check_group_counter(ok)  # passes
    assert issubclass(GroupCounterBehindStoreError, ValueError)  # the restore route answers 400


def _write_checkpoint(tmp_path, blob, spec_id):
    header = json.dumps({"tick": 7, "spec_id": spec_id, "rng_checkpoint": None}).encode()
    path = tmp_path / "pre_f3.bin"
    path.write_bytes(struct.pack("<I", len(header)) + header + blob)
    return path


def _pre_f3_blob(monkeypatch):
    """A checkpoint written before F3: the state pickles with a building whose trailing `beds` slot is not in the saved tuple (the current group fields are present)."""
    from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        def building_state(self):
            return [getattr(self, f.name) for f in dataclasses.fields(self) if f.name != "beds"]
        from src.core.state import BuildingState
        monkeypatch.setattr(BuildingState, "__getstate__", building_state, raising=False)
        try:
            return pickle.dumps(k._state)
        finally:
            monkeypatch.undo()
    finally:
        k.shutdown()


def test_a_pre_f3_checkpoint_of_the_same_scenario_is_still_refused_for_the_missing_beds(tmp_path, monkeypatch):
    """F3's refusal survives the restore reorder: same scenario id, spec check passes, the fill then refuses the building without `beds`."""
    from src.scenarios.schema import SimulationScenarioDefinition
    path = _write_checkpoint(tmp_path, _pre_f3_blob(monkeypatch), "s")
    spec = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    with pytest.raises(CheckpointFieldMissingError, match=r"'beds'"):
        ScenarioCheckpointer.restore(path, spec)


def test_a_pre_f3_checkpoint_of_a_different_scenario_raises_the_spec_id_mismatch_not_the_field_error(tmp_path, monkeypatch):
    """The spec check runs before the fill: a checkpoint of another scenario is refused for that reason even when it also lacks fields."""
    from src.scenarios.schema import SimulationScenarioDefinition
    path = _write_checkpoint(tmp_path, _pre_f3_blob(monkeypatch), "other_scenario")
    spec = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    with pytest.raises(ValueError, match="spec_id") as err:
        ScenarioCheckpointer.restore(path, spec)
    assert not isinstance(err.value, CheckpointFieldMissingError)
