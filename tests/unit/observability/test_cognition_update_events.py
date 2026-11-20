"""cognition_update_events: the COGNITION pair StrategyShaper.shape emits (blocker_removed, then self_model_updated), moved out of shape unchanged (divergence 2.214)."""
from __future__ import annotations

from types import SimpleNamespace

from src.core.strategic import BlockerRemoval
from src.observability.extraction.strategy import cognition_update_events


def _update(removed=None, bundle=None):
    return SimpleNamespace(strategic=SimpleNamespace(blockers_removed_for=removed), self_model_bundle_set=bundle)


def _shape(events):
    return [(e.event_type, e.event_category, e.tick, e.entity_id, e.severity, e.source_system, e.message, e.payload) for e in events]


def test_blocker_removals_come_first_in_blocker_id_order_then_self_model_updated():
    upd = _update({"blocker_z": BlockerRemoval.QUIET_SPELL, "blocker_a": BlockerRemoval.QUIET_SPELL}, bundle=object())
    assert _shape(cognition_update_events(7, upd, 300)) == [
        ("blocker_removed", "strategy", 300, 7, "INFO", "event_shapers", "", {"entity_id": 7, "blocker_id": "blocker_a", "reason": "QUIET_SPELL", "tick": 300}),
        ("blocker_removed", "strategy", 300, 7, "INFO", "event_shapers", "", {"entity_id": 7, "blocker_id": "blocker_z", "reason": "QUIET_SPELL", "tick": 300}),
        ("self_model_updated", "strategy", 300, 7, "INFO", "event_shapers", "", {}),
    ]


def test_self_model_updated_alone():
    assert _shape(cognition_update_events(3, _update(bundle=object()), 5)) == [("self_model_updated", "strategy", 5, 3, "INFO", "event_shapers", "", {})]


def test_blocker_removals_alone_and_nothing_at_all():
    assert [e.event_type for e in cognition_update_events(3, _update({"b": BlockerRemoval.QUIET_SPELL}), 5)] == ["blocker_removed"]
    assert cognition_update_events(3, _update(), 5) == []
    assert cognition_update_events(3, SimpleNamespace(), 5) == []
