"""Positive controls for the hidden-mutation detector (plan 3a): each known mutation kind is injected into a fake step run through the real recorder and dispatch call, and the
test asserts the step and the field are reported. One more control proves the second-tier blind spot is real, so the stated limits stay honest."""
from __future__ import annotations

import collections
import dataclasses
import sys
import types

from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.access_audit import observe
from src.engine.access_audit.hook import audited_phase_call
from src.engine.access_audit.recorder import AccessAuditRecorder


@dataclasses.dataclass(frozen=True, slots=True)
class _Event:
    n: int


@dataclasses.dataclass
class _Ent:
    id: int
    timeline: collections.deque


@dataclasses.dataclass
class _St:
    tick: int
    entities: dict
    route_plans: object = None
    transient_claims: object = None
    _has_hostiles_or_dead_cache: object = None
    other: object = None  # outside the watch list


def _state() -> _St:
    full = collections.deque((_Event(i) for i in range(200)), maxlen=200)
    return _St(3, {1: _Ent(1, full)}, route_plans={"a": 1, "b": 2}, transient_claims=["x", "y"], _has_hostiles_or_dead_cache=True, other={"k": 1})


def _run(step, state=None):
    state = state or _state()
    rec = AccessAuditRecorder()
    audited_phase_call(rec, "fake_step", state, StateUpdate(), lambda u: (step(state), u)[1])
    (ob,) = rec.observations
    return ob


def test_control_1_a_timeline_append_on_a_deque_already_at_maxlen_is_seen():
    ob = _run(lambda st: st.entities[1].timeline.append(_Event(999)))
    assert ob.phase == "fake_step"
    assert "entities[*].timeline" in ob.hidden_state_mutations
    assert "entities[*].timeline" not in ob.promote  # a watch-list field, not a Tier 2 hit


def test_control_2_a_route_plans_object_setattr_is_seen():
    ob = _run(lambda st: object.__setattr__(st, "route_plans", {"a": 1, "b": 3}))
    assert "route_plans" in ob.hidden_state_mutations


def test_control_3_an_in_place_dict_value_change_on_a_watch_attribute_is_seen():
    ob = _run(lambda st: st.route_plans.__setitem__("a", 99))
    assert "route_plans" in ob.hidden_state_mutations


def test_control_4_an_equal_length_list_element_swap_on_a_watch_attribute_is_seen():
    def swap(st):
        st.transient_claims[0], st.transient_claims[1] = st.transient_claims[1], st.transient_claims[0]

    assert "transient_claims" in _run(swap).hidden_state_mutations


def test_control_5_a_cache_flag_flip_is_seen():
    ob = _run(lambda st: object.__setattr__(st, "_has_hostiles_or_dead_cache", False))
    assert "_has_hostiles_or_dead_cache" in ob.hidden_state_mutations


def test_blind_spot_an_in_place_change_outside_the_watch_list_is_NOT_detected():
    ob = _run(lambda st: st.other.__setitem__("k", 2))
    assert "other" not in ob.hidden_state_mutations
    assert ob.promote == frozenset()


def test_blind_spot_an_in_place_edit_inside_a_mutable_timeline_element_is_NOT_detected_by_the_ids_only_token():
    @dataclasses.dataclass
    class Mutable:
        n: int

    st = _state()
    st.entities[1].timeline.append(Mutable(1))
    ob = _run(lambda s: setattr(s.entities[1].timeline[-1], "n", 2), st)
    assert "entities[*].timeline" not in ob.hidden_state_mutations


def test_a_tier2_hit_is_reported_for_promotion_to_the_watch_list():
    st = _state()
    st.other = []
    ob = _run(lambda s: s.other.append(1), st)
    assert "other" in ob.hidden_state_mutations and "other" in ob.promote


def test_a_process_global_change_is_reported(monkeypatch):
    mod = types.ModuleType("src.content.terrain_cost")
    mod._terrain_cache = {"plain": 1}
    monkeypatch.setitem(sys.modules, "src.content.terrain_cost", mod)
    ob = _run(lambda st: mod._terrain_cache.__setitem__("plain", 2))
    assert ob.global_changes == {"src.content.terrain_cost:_terrain_cache"}


def test_a_global_whose_module_is_not_loaded_is_skipped_not_imported(monkeypatch):
    for name in {m for m, _ in observe.GLOBAL_WATCH}:
        monkeypatch.delitem(sys.modules, name, raising=False)
    assert observe.snapshot_globals() == {}
    assert not any(name in sys.modules for name, _ in observe.GLOBAL_WATCH)


def test_identity_only_replacement_is_marked_and_a_value_change_is_not():
    a = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate())})
    b = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate())})
    same, unsafe = observe.update_identity_only(a, b)
    assert "eu:combat" in same and not unsafe


def test_cross_entity_proxies_count_created_entries_and_distinct_ids_per_bucket():
    before = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)})
    after = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1),
        2: EntityUpdate(entity_id=2, combat=CombatUpdate()),
        3: EntityUpdate(entity_id=3, combat=CombatUpdate()),
    })
    created, fanout = observe.entity_fanout(before, after)
    assert created == 2 and fanout == {"eu:combat": 2}


def test_the_recorder_counts_ticks_per_hidden_field():
    rec = AccessAuditRecorder()
    st = _state()
    for _ in range(3):
        audited_phase_call(rec, "s", st, StateUpdate(), lambda u: (st.route_plans.__setitem__("a", st.route_plans["a"] + 1), u)[1])
    assert rec.per_phase()["s"]["hidden_ticks"] == {"route_plans": 3}


def test_sampled_control_an_in_place_edit_of_a_mutable_element_is_reported_at_the_next_sample_with_entity_and_element():
    @dataclasses.dataclass
    class Mutable:
        n: int

    st = _state()
    st.entities[1].timeline.append(Mutable(1))
    rec = AccessAuditRecorder()
    st.tick = 0
    rec.before(st, StateUpdate())
    st.entities[1].timeline[-1].n = 2
    st.tick = 100
    rec.before(st, StateUpdate())
    assert rec.sampled_timeline_edits == [{"entity": 1, "element": "Mutable", "index": 200 - 1, "first_seen_tick": 0, "sample_tick": 100, "fields": [{"field": "n", "old": "1", "new": "2"}]}]
    assert rec.replaced_timeline_elements == 0


def test_sampled_baseline_drops_an_evicted_element():
    @dataclasses.dataclass
    class Mutable:
        n: int

    st = _state()
    st.entities[1].timeline.append(Mutable(1))
    rec = AccessAuditRecorder()
    st.tick = 0
    rec.before(st, StateUpdate())
    assert len(rec._baseline) == 1
    for i in range(200):
        st.entities[1].timeline.append(_Event(i))  # evicts the mutable element
    st.tick = 100
    rec.before(st, StateUpdate())
    assert rec._baseline == {} and rec.sampled_timeline_edits == []


def test_id_reuse_is_counted_as_replaced_not_reported_as_an_edit():
    @dataclasses.dataclass
    class Mutable:
        event_id: str
        n: int

    st = _state()
    old = Mutable("a", 1)
    st.entities[1].timeline.append(old)
    rec = AccessAuditRecorder()
    st.tick = 0
    rec.before(st, StateUpdate())
    (old_key,) = rec._baseline
    new = Mutable("b", 7)  # a different event that (as if) reuses the evicted element's id
    st.entities[1].timeline[-1] = new
    rec._baseline[id(new)] = rec._baseline.pop(old_key)
    st.tick = 100
    rec.before(st, StateUpdate())
    assert rec.sampled_timeline_edits == [] and rec.replaced_timeline_elements == 1


def test_stable_key_falls_back_to_tick_type_and_ordinal_without_an_event_id():
    @dataclasses.dataclass
    class Plain:
        tick: int

    seen: dict = {}
    keys = [observe._stable_key(Plain(5), "Plain", seen), observe._stable_key(Plain(5), "Plain", seen), observe._stable_key(Plain(6), "Plain", seen)]
    assert keys == [(5, "Plain", 1), (5, "Plain", 2), (6, "Plain", 1)]


def test_field_diff_names_the_changed_fields_with_truncated_values():
    long = "x" * 200
    old = {"a": "1", "b": repr(long)[: observe.FIELD_REPR_CHARS], "c": "same"}
    new = {"a": "2", "b": old["b"], "c": "same", "d": "9"}
    from src.engine.access_audit.recorder import _field_diff

    assert _field_diff(old, new) == [{"field": "a", "old": "1", "new": "2"}, {"field": "d", "old": "<absent>", "new": "9"}]
    assert all(len(v) <= observe.FIELD_REPR_CHARS for v in observe._field_reprs(types.SimpleNamespace(f=long)).values())
