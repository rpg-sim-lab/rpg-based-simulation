"""The audit is off by default and hash-neutral.

Off: no recorder, no snapshot, no module state is touched. On (flag + a recorder passed in): same final state hash and the same event count as off."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
from src.engine.access_audit import hook, observe, recorder
from src.engine.access_audit.declarations import DECLARATIONS
from src.engine.checkpoint import CanonicalStateHasher
from tools.test_architecture.rpg_gate_run import build_kernel

_TICKS = 25


def _run(world: str, seed: int, *, audit: bool):
    run_id = f"access_audit_{world}_{seed}_{'on' if audit else 'off'}"
    kernel = build_kernel(world, seed, run_id)
    rec = None
    if audit:
        rec = recorder.AccessAuditRecorder()
        kernel._state.feature_flags[hook.AUDIT_FLAG] = FeatureMode.ON
        kernel._state.feature_flags[hook.SINK_KEY] = rec
    for _ in range(_TICKS):
        kernel.tick_once()
    state_hash = CanonicalStateHasher.get_hash(kernel.state)
    kernel.shutdown()
    run_dir = Path("data") / "runs" / run_id
    events = run_dir / "simulation_events.jsonl"
    count = sum(1 for _ in events.open(encoding="utf-8")) if events.exists() else 0
    shutil.rmtree(run_dir, ignore_errors=True)
    return state_hash, count, rec


def test_the_flag_is_registered_and_off_by_default():
    assert FeatureFlagManager().get_flag_mode(hook.AUDIT_FLAG) == FeatureMode.OFF


def test_with_the_flag_off_no_recorder_or_snapshot_is_ever_built(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the audit ran with the flag off")

    monkeypatch.setattr(recorder.AccessAuditRecorder, "__init__", boom)
    monkeypatch.setattr(observe, "snapshot_state", boom)
    monkeypatch.setattr(observe, "snapshot_update", boom)
    monkeypatch.setattr(hook, "audited_phase_call", boom)
    h, _, rec = _run("crowded_frontier", 42, audit=False)
    assert rec is None and h


def test_the_flag_on_without_a_recorder_does_nothing():
    class _Mgr:
        def get_flag_mode(self, name):
            return FeatureMode.ON

    assert hook.audit_sink_for(type("S", (), {"feature_flags": {}})(), _Mgr()) is None


@pytest.mark.parametrize("world,seed", [("crowded_frontier", 42), ("urban_political", 46)])
def test_audit_on_and_off_give_the_same_hash_and_event_count(world, seed):
    off_hash, off_events, _ = _run(world, seed, audit=False)
    on_hash, on_events, rec = _run(world, seed, audit=True)
    assert on_hash == off_hash
    assert on_events == off_events
    assert rec is not None and rec.observations, "the audit was on but observed nothing"
    assert {o.phase for o in rec.observations} <= set(DECLARATIONS)
