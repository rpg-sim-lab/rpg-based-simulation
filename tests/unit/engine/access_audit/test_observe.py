"""The pure observation helpers: they see an in-place append, a replaced attribute and the update entries a step wrote; they write nothing."""
from __future__ import annotations

import dataclasses

from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.access_audit import observe


@dataclasses.dataclass
class _Ent:
    id: int
    timeline: list
    hp: float


@dataclasses.dataclass
class _St:
    tick: int
    entities: dict
    note: object = None


def test_an_in_place_list_append_on_an_entity_is_a_hidden_mutation():
    st = _St(1, {7: _Ent(7, [], 5.0)})
    pre = observe.snapshot_state(st)
    st.entities[7].timeline.append("x")
    assert observe.diff_state(pre, observe.snapshot_state(st)) == {"entities[*].timeline"}


def test_a_replaced_attribute_and_an_object_setattr_flag_are_seen_and_an_untouched_state_is_not():
    st = _St(1, {})
    pre = observe.snapshot_state(st)
    assert observe.diff_state(pre, observe.snapshot_state(st)) == frozenset()
    object.__setattr__(st, "_cache_flag", True)
    st.note = object()
    assert observe.diff_state(pre, observe.snapshot_state(st)) == {"note", "_cache_flag"}


def test_update_writes_names_added_entity_buckets_and_changed_fields():
    before = StateUpdate()
    after = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate())}, next_node_id_set=4)
    assert observe.update_writes(before, after) == {"su:next_node_id_set", "eu:combat"}
    assert observe.update_writes(after, after) == frozenset()


def test_update_inplace_flags_a_mutation_of_the_input_update():
    upd = StateUpdate()
    pre = observe.snapshot_update(upd)
    upd.rejection_events.append(object())
    assert observe.update_inplace(pre, upd) == {"su:rejection_events"}
