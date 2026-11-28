"""The pregnancy record (M1 reproduction): typed and frozen, omitted from the canonical state while None, set and cleared by typed updates, cleared in the death's own update."""
from __future__ import annotations

import dataclasses
import pickle

import pytest

from src.core.builder import V2EntityBuilder
from src.core.pregnancy import PregnancyState
from src.core.state import AuthoritativeState, RegionState
from src.core.update_models.body import LifecycleUpdate
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.checkpoint_fields import FIELD_RULES, fill_missing_fields
from src.systems.lifecycle_systems.genetics import GeneticProfile
from src.systems.lifecycle_systems.lifecycle import LifecycleSystem

_PREGNANCY = PregnancyState(father_entity_id=2, conceived_tick=30, due_tick=2430, litter_size=2, father_genetic_profile=GeneticProfile(strength_mult=1.1))


def _mother(eid=1, pregnancy=None):
    body = V2EntityBuilder(eid).kind("human").location(5.0, 5.0).build()
    return dataclasses.replace(body, lifecycle=dataclasses.replace(body.lifecycle, pregnancy=pregnancy))


def _state(*entities, tick=100):
    return AuthoritativeState(tick=tick, seed=42, entities={e.id: e for e in entities}, regions={"town": RegionState(id="town", name="Town", bounds=(0, 0, 200, 200))})


def test_the_record_is_frozen_and_hashes_by_value():
    with pytest.raises(dataclasses.FrozenInstanceError):
        _PREGNANCY.due_tick = 5  # type: ignore[misc]
    assert _PREGNANCY == dataclasses.replace(_PREGNANCY)


def test_a_body_with_no_pregnancy_hashes_exactly_as_before_the_field_existed():
    assert "pregnancy" not in _mother().lifecycle.to_canonical_dict()
    assert _mother(pregnancy=_PREGNANCY).lifecycle.to_canonical_dict()["pregnancy"] == _PREGNANCY.to_canonical_dict()


def test_a_set_then_a_clear_is_applied_by_typed_updates():
    state = _state(_mother())
    with_it = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=LifecycleUpdate(pregnancy_set=_PREGNANCY))}), 101, 101)
    assert with_it.entities[1].lifecycle.pregnancy == _PREGNANCY
    cleared = ApplyPath.apply_generation(with_it, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=LifecycleUpdate(pregnancy_clear=True))}), 102, 102)
    assert cleared.entities[1].lifecycle.pregnancy is None


def test_the_update_merge_keeps_a_clear_and_a_set():
    merged = LifecycleUpdate(pregnancy_set=_PREGNANCY).merge(LifecycleUpdate(pregnancy_clear=True))
    assert merged.pregnancy_clear and merged.pregnancy_set == _PREGNANCY and not merged.is_noop()
    assert LifecycleUpdate().is_noop()


def test_a_checkpoint_round_trip_keeps_the_pregnancy_and_the_hash():
    state = _state(_mother(pregnancy=_PREGNANCY))
    back = pickle.loads(pickle.dumps(state))
    fill_missing_fields(back)
    assert back.entities[1].lifecycle.pregnancy == _PREGNANCY
    assert CanonicalStateHasher.to_canonical_data(back) == CanonicalStateHasher.to_canonical_data(state)


def test_an_older_checkpoint_without_the_field_is_filled_with_none(monkeypatch):
    from src.core.state import LifecycleComponent
    monkeypatch.setattr(LifecycleComponent, "__getstate__", lambda self: [getattr(self, f.name) for f in dataclasses.fields(self) if f.name != "pregnancy"], raising=False)
    blob = pickle.dumps(_state(_mother()))
    monkeypatch.undo()
    old = pickle.loads(blob)
    fill_missing_fields(old)
    assert old.entities[1].lifecycle.pregnancy is None
    assert any(r.field == "pregnancy" and r.record == "LifecycleComponent" and r.ruling for r in FIELD_RULES)


def _dying(outcome_kind, tick=100):
    mother = _mother(pregnancy=_PREGNANCY)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(outcome_kind=outcome_kind, alive_set=False))})
    state = _state(mother, tick=tick)
    return state, LifecycleSystem.resolve_lifecycle(state, update)


@pytest.mark.parametrize("outcome", ["DEFEAT", "HAZARD"])
def test_a_death_by_combat_or_hazard_clears_the_pregnancy_in_that_tick_s_update(outcome):
    state, update = _dying(outcome)
    assert update.entity_updates[1].lifecycle.pregnancy_clear
    events = [e for e in update.world_events_add if e.category == WorldEventCategory.PREGNANCY_ENDED]
    assert len(events) == 1 and events[0].tick == 100 and events[0].subject == "1"
    assert events[0].payload == {"reason": "MOTHER_DIED", "litter_size": 2}
    after = ApplyPath.apply_generation(state, update, 101, 101)
    assert after.entities[1].lifecycle.pregnancy is None and after.entities[1].lifecycle.death_record is not None


def test_a_mother_who_is_not_pregnant_emits_no_event_and_no_clear():
    mother = _mother()
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(outcome_kind="DEFEAT", alive_set=False))})
    out = LifecycleSystem.resolve_lifecycle(_state(mother), update)
    assert not out.entity_updates[1].lifecycle.pregnancy_clear
    assert not [e for e in out.world_events_add if e.category == WorldEventCategory.PREGNANCY_ENDED]
