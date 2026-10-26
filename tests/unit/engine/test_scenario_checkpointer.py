"""
Unit tests for ScenarioCheckpointer.

Ticket: TCK-20260619-E31C-CHECKPOINT
AC coverage:
  AC1 — save() raises RuntimeError when kernel not started
  AC2 — restore() raises ValueError on spec_id mismatch
  AC3 — save/restore round-trip preserves tick counter
  AC4 — checkpoint file header contains rng_checkpoint field
  Guard — INFRA-215 parity entry exists in infrastructure.yaml
  Guard — rng_checkpoint is non-None after one real tick
"""
from __future__ import annotations

import json
import pytest


def _make_spec(**kwargs):
    from src.scenarios.schema import SimulationScenarioDefinition
    defaults = {
        "id": "test_scenario",
        "world_composition": "frontier_living_world",
        "perspective": "hero_guild_perspective",
    }
    defaults.update(kwargs)
    return SimulationScenarioDefinition(**defaults)


def _make_service(**spec_kwargs):
    from src.engine.scenario_runtime import ScenarioRuntimeService
    return ScenarioRuntimeService(_make_spec(**spec_kwargs))


# ── AC1: save raises when kernel not started ───────────────────────────────────


def test_save_raises_when_kernel_none(tmp_path):
    """save() raises RuntimeError when the service has not been started."""
    from src.engine.scenario_checkpoint import ScenarioCheckpointer

    svc = _make_service()
    with pytest.raises(RuntimeError, match="not been started"):
        ScenarioCheckpointer.save(svc, tmp_path / "ckpt.bin")


# ── AC2: restore raises on spec_id mismatch ───────────────────────────────────


def test_restore_raises_on_spec_id_mismatch(tmp_path):
    """restore() raises ValueError if checkpoint spec_id differs from supplied spec."""
    from src.engine.scenario_checkpoint import ScenarioCheckpointer
    import struct

    # Write a minimal valid checkpoint file with spec_id "scenario_a"
    path = tmp_path / "ckpt.bin"
    header = {"tick": 5, "spec_id": "scenario_a", "rng_checkpoint": None}
    header_bytes = json.dumps(header).encode("utf-8")
    # Need a valid pickle blob — use a dummy object
    import pickle
    payload = pickle.dumps({"dummy": True})
    with path.open("wb") as f:
        f.write(struct.pack("<I", len(header_bytes)))
        f.write(header_bytes)
        f.write(payload)

    spec = _make_spec(id="scenario_b")
    with pytest.raises(ValueError, match="spec_id"):
        ScenarioCheckpointer.restore(path, spec)


# ── AC3: save/restore round-trip preserves tick counter ───────────────────────


@pytest.mark.slow
def test_save_restore_round_trip_tick(tmp_path):
    """save/restore round-trip: restored service._tick matches saved tick."""
    from src.engine.scenario_checkpoint import ScenarioCheckpointer

    spec = _make_spec()
    svc = _make_service()
    try:
        svc.start(tick_limit=10)
        saved_tick = svc.tick
        assert saved_tick == 10

        path = tmp_path / "ckpt.bin"
        ScenarioCheckpointer.save(svc, path)
    finally:
        svc.abort()

    restored = ScenarioCheckpointer.restore(path, spec)
    try:
        assert restored.tick == saved_tick
        assert restored._kernel.state.tick == saved_tick
    finally:
        restored.abort()


# ── AC4: checkpoint file header contains rng_checkpoint ───────────────────────


@pytest.mark.slow
def test_checkpoint_header_contains_rng_checkpoint(tmp_path):
    """Checkpoint file JSON header contains rng_checkpoint field (non-None after ticks)."""
    import struct
    from src.engine.scenario_checkpoint import ScenarioCheckpointer

    svc = _make_service()
    try:
        svc.start(tick_limit=5)
        path = tmp_path / "ckpt.bin"
        ScenarioCheckpointer.save(svc, path)
    finally:
        svc.abort()

    with path.open("rb") as f:
        header_len = struct.unpack("<I", f.read(4))[0]
        header = json.loads(f.read(header_len).decode("utf-8"))

    assert "rng_checkpoint" in header
    assert header["rng_checkpoint"] is not None


# ── Guard: INFRA-215 parity entry must exist ──────────────────────────────────


def test_infra_215_parity_entry_exists():
    """INFRA-215 must be present in docs/parity_ledger/infrastructure.yaml."""
    import yaml
    from pathlib import Path

    ledger_path = Path(__file__).parents[3] / "docs/parity_ledger/infrastructure.yaml"
    ledger = yaml.safe_load(ledger_path.read_text())
    ids = {e["id"] for e in ledger if isinstance(e, dict) and "id" in e}
    assert "INFRA-215" in ids, (
        "INFRA-215 not found in parity ledger — add it before merging E31C"
    )


# ── Guard: rng_checkpoint non-None after one tick ─────────────────────────────


@pytest.mark.slow
def test_rng_checkpoint_populated_after_tick():
    """After one real tick, state.rng_checkpoint must be non-None."""
    from src.engine.scenario_runtime import ScenarioRuntimeService

    svc = ScenarioRuntimeService(_make_spec())
    try:
        svc.step()
        assert svc._kernel.state.rng_checkpoint is not None, (
            "rng_checkpoint is None after tick 1 — "
            "phases are not writing StateUpdate.rng_checkpoint"
        )
    finally:
        svc.abort()


# ── F3: a restored episode keeps its real base seed (#593 F3) ─────────────────
# The checkpoint stores only the stateful per-domain streams; the stateless draws
# (get_int/get_float/choice/sample) and any domain first used after the restore
# derive from the base seed, so restore must rebuild the RNG with state.seed.

_SEED = 12345


def _seeded_service(spec_id="f3_seeded", entity_count=30, seed=_SEED):
    from src.engine.scenario_runtime import ScenarioRuntimeService
    from src.perf.scenarios import build_movement_state

    state = build_movement_state(entity_count=entity_count, seed=seed)
    return ScenarioRuntimeService(_make_spec(id=spec_id), initial_state=state)


def test_restore_rebuilds_rng_with_the_episode_seed(tmp_path):
    """Restored RNG answers stateless draws and fresh domains like a RNG with the episode seed."""
    from src.core.enums import Domain
    from src.engine.scenario_checkpoint import ScenarioCheckpointer
    from src.platform.rng import DeterministicRNG

    svc = _seeded_service()
    svc.step()
    path = tmp_path / "ckpt.bin"
    ScenarioCheckpointer.save(svc, path)
    svc.abort()

    restored = ScenarioCheckpointer.restore(path, _make_spec(id="f3_seeded"))
    rng = restored._kernel._rng
    reference = DeterministicRNG(base_seed=_SEED)

    assert rng.seed == _SEED
    assert rng.get_int(Domain.DEFAULT, 7, 3, 0, 10**6) == reference.get_int(Domain.DEFAULT, 7, 3, 0, 10**6)
    assert rng.get_float(Domain.TACTICAL, 7, 3, 1) == reference.get_float(Domain.TACTICAL, 7, 3, 1)
    # a domain absent from the checkpoint is seeded lazily from the base seed
    fresh = [d for d in Domain if d.value not in (restored._kernel.state.rng_checkpoint or {})][0]
    assert rng.next_float(fresh) == reference.next_float(fresh)
    restored.abort()


@pytest.mark.slow
def test_restore_at_n_then_k_ticks_equals_unbroken_n_plus_k(tmp_path):
    """Restore at tick N + K more ticks reaches the unbroken N+K run's state hash and draws."""
    from src.core.enums import Domain
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.scenario_checkpoint import ScenarioCheckpointer

    n, k = 5, 5
    unbroken = _seeded_service()
    for _ in range(n + k):
        unbroken.step()

    first = _seeded_service()
    for _ in range(n):
        first.step()
    path = tmp_path / "ckpt.bin"
    ScenarioCheckpointer.save(first, path)
    first.abort()
    restored = ScenarioCheckpointer.restore(path, _make_spec(id="f3_seeded"))
    for _ in range(k):
        restored.step()

    assert restored.tick == unbroken.tick == n + k
    assert CanonicalStateHasher.get_hash(restored._kernel.state) == CanonicalStateHasher.get_hash(unbroken._kernel.state)
    a, b = restored._kernel._rng, unbroken._kernel._rng
    for entity_id in (1, 7, 19):
        assert a.get_float(Domain.TACTICAL, n + k, entity_id, 0) == b.get_float(Domain.TACTICAL, n + k, entity_id, 0)
    unbroken.abort()
    restored.abort()
