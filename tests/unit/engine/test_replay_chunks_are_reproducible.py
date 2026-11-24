"""Replay chunks carry no wall-clock value, so two runs of one world and seed write byte-equal chunks
(TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE).

The kernel's own update still carries the timers (the governor, `_metrics` and the perf baselines read them); only the copy handed to the
replay emit is stripped. No run id is written into a chunk, so no mask is applied: the chunks are compared raw.
"""
from __future__ import annotations

import dataclasses
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from src.core.updates import StateUpdate
from src.domains.optimization.feature_flags import FeatureMode
from src.engine.checkpoint import CanonicalStateHasher
from tools.test_architecture.rpg_gate_run import build_kernel

TICKS = 12
WORLD = "frontier_living_world"
EMERGENCE_ON = {"ENABLE_WORLD_EMERGENCE": FeatureMode.ON}


class _Run:
    """One real kernel run with replay on; keeps the chunks, the kernel's in-memory timers and the per-tick hashes."""

    def __init__(self, tag: str, flags: Optional[Dict[str, Any]] = None, seed: int = 42) -> None:
        run_id = f"replay_repro_{tag}_{seed}"
        run_dir = Path("data") / "runs" / run_id
        shutil.rmtree(run_dir, ignore_errors=True)
        kernel = build_kernel(WORLD, seed, run_id)
        if flags:
            kernel._state = replace(kernel._state, feature_flags={**kernel._state.feature_flags, **flags})
        self.tick_end_hashes: List[str] = []
        real_emit = kernel._replay.emit

        def spy(event, policy):
            if event.event_type == "TICK_END":
                self.tick_end_hashes.append(event.payload["hash"])
            return real_emit(event, policy)

        kernel._replay.emit = spy
        self.metric_keys: set = set()
        try:
            for _ in range(TICKS):
                kernel.tick_once()
                self.metric_keys |= set(kernel._metrics)
            self.phase_costs = dict(kernel._phase_costs)
            self.final_digest = CanonicalStateHasher.get_hash(kernel.state)
            self.final_metrics = dict(kernel._metrics)
        finally:
            kernel.shutdown()
        self.chunks: Dict[str, bytes] = {p.name: p.read_bytes() for p in sorted(run_dir.glob("chunk_*.json"))}
        shutil.rmtree(run_dir, ignore_errors=True)
        assert self.chunks, "the run wrote no replay chunk"

    def updates(self) -> List[dict]:
        out = []
        for raw in self.chunks.values():
            out += [e["payload"]["update"] for e in json.loads(raw) if e["event_type"] == "REFINED_UPDATE"]
        return out


def _timer_leaves(node: Any, path: str = "") -> List[str]:
    found: List[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            found += _timer_leaves(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found += _timer_leaves(v, f"{path}[{i}]")
    elif isinstance(node, float) and (".metric_counters." in path or ".sub_phase_costs." in path):
        found.append(path)
    return found


@pytest.fixture(scope="module")
def run_a() -> _Run:
    return _Run("a")


@pytest.fixture(scope="module")
def run_b() -> _Run:
    return _Run("b")


@pytest.fixture(scope="module")
def emergence_a() -> _Run:
    return _Run("ea", EMERGENCE_ON)


@pytest.fixture(scope="module")
def emergence_b() -> _Run:
    return _Run("eb", EMERGENCE_ON)


def test_two_runs_of_one_world_and_seed_write_byte_equal_replay_chunks(run_a, run_b):
    assert run_a.chunks.keys() == run_b.chunks.keys()
    assert [n for n in run_a.chunks if run_a.chunks[n] != run_b.chunks[n]] == []


def test_two_world_emergence_runs_write_byte_equal_replay_chunks(emergence_a, emergence_b):
    assert emergence_a.chunks.keys() == emergence_b.chunks.keys()
    assert [n for n in emergence_a.chunks if emergence_a.chunks[n] != emergence_b.chunks[n]] == []


def test_the_world_emergence_flag_really_ran_the_phase(emergence_a):
    # Otherwise the world-emergence reproducibility test would pass without ever touching `world_emergence_ms`.
    assert "world_emergence_ms" in emergence_a.metric_keys


@pytest.mark.parametrize("name", ["run_a", "emergence_a"])
def test_no_float_timer_is_left_in_a_replayed_update(name, request):
    run = request.getfixturevalue(name)
    leaves = sorted({leaf for upd in run.updates() for leaf in _timer_leaves({"update": upd}, "payload")})
    assert leaves == [], f"float leaves under the replayed metric_counters / sub_phase_costs: {leaves[:5]}"


def test_counts_stay_in_the_replayed_update(emergence_a):
    counters = emergence_a.updates()[-1]["metric_counters"]
    assert counters.get("cooperation_evaluations") is not None and "phase_runs" in counters
    assert "aggregates_generated" in counters


def test_the_kernel_keeps_the_timers_the_governor_and_the_perf_baselines_read(emergence_a):
    assert "cooperation_phase_ms" in emergence_a.metric_keys and "world_emergence_ms" in emergence_a.metric_keys
    assert len(emergence_a.phase_costs) >= 23, sorted(emergence_a.phase_costs)
    assert all(isinstance(v, float) for v in emergence_a.phase_costs.values())


def test_replay_form_does_not_change_the_final_hash_or_any_tick_end_hash(run_a, monkeypatch):
    """The old emit (replay_form returns self) and the new one give the same TICK_END hashes and the same final canonical digest."""
    monkeypatch.setattr(StateUpdate, "replay_form", lambda self: self)
    old_emit = _Run("old")
    assert old_emit.tick_end_hashes == run_a.tick_end_hashes and len(run_a.tick_end_hashes) == TICKS
    assert old_emit.final_digest == run_a.final_digest
    old_leaves = {leaf for upd in old_emit.updates() for leaf in _timer_leaves({"update": upd}, "payload")}
    assert old_leaves, "the old emit does carry the timers: this is the control for the equality above"


# --- StateUpdate.replay_form / WALL_CLOCK_METRIC_KEYS -------------------------------------------------------------------------------

def test_the_named_set_is_exactly_the_two_writers_keys():
    from src.core.updates import WALL_CLOCK_METRIC_KEYS

    assert WALL_CLOCK_METRIC_KEYS == frozenset({"cooperation_phase_ms", "world_emergence_ms"})


def test_replay_form_drops_exactly_the_named_keys_and_empties_the_sub_phase_costs():
    upd = StateUpdate(sub_phase_costs={"combat_engagement": 17.3},
                      metric_counters={"cooperation_phase_ms": 0.3, "world_emergence_ms": 1.2, "cooperation_evaluations": 4,
                                       "some_other_ms": 7, "phase_runs": 3})
    form = upd.replay_form()
    assert form.sub_phase_costs == {}
    assert form.metric_counters == {"cooperation_evaluations": 4, "some_other_ms": 7, "phase_runs": 3}
    assert dataclasses.replace(form, sub_phase_costs=upd.sub_phase_costs, metric_counters=upd.metric_counters) == upd


def test_replay_form_never_mutates_self():
    upd = StateUpdate(sub_phase_costs={"a": 1.0}, metric_counters={"cooperation_phase_ms": 0.3, "phase_runs": 3})
    upd.replay_form()
    assert upd.sub_phase_costs == {"a": 1.0} and upd.metric_counters == {"cooperation_phase_ms": 0.3, "phase_runs": 3}


@pytest.mark.parametrize("sub,counters", [({}, {}), (None, None), (None, {"phase_runs": 1}), ({"a": 1.0}, None)])
def test_replay_form_handles_empty_and_none_fields(sub, counters):
    upd = StateUpdate()
    object.__setattr__(upd, "sub_phase_costs", sub)
    object.__setattr__(upd, "metric_counters", counters)
    form = upd.replay_form()
    assert form.sub_phase_costs == {}
    assert form.metric_counters == ({} if counters is None else counters)


def test_replay_form_leaves_is_noop_alone_for_the_kernels_own_update():
    timers_only = StateUpdate(sub_phase_costs={"a": 1.0}, metric_counters={"cooperation_phase_ms": 0.3})
    before = timers_only.is_noop
    timers_only.replay_form()
    assert timers_only.is_noop == before
