"""Two runs of one world and seed write byte-equal replay chunks (draft for TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

from tools.test_architecture.rpg_gate_run import build_kernel

TICKS = 12


def _run_chunks(world: str, seed: int, tag: str) -> Dict[str, bytes]:
    run_id = f"replay_repro_{tag}_{world}_{seed}"
    run_dir = Path("data") / "runs" / run_id
    shutil.rmtree(run_dir, ignore_errors=True)
    kernel = build_kernel(world, seed, run_id)
    try:
        for _ in range(TICKS):
            kernel.tick_once()
        phase_costs = dict(kernel._phase_costs)
    finally:
        kernel.shutdown()
    chunks = {p.name: p.read_bytes() for p in sorted(run_dir.glob("chunk_*.json"))}
    shutil.rmtree(run_dir, ignore_errors=True)
    assert chunks, "the run wrote no replay chunk"
    assert phase_costs.get("locomotion") is not None or phase_costs, "the kernel keeps its phase costs"
    return chunks


def _float_leaves(node, path="") -> List[str]:
    out: List[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out += _float_leaves(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += _float_leaves(v, f"{path}[{i}]")
    elif isinstance(node, float) and (".metric_counters." in path or ".sub_phase_costs." in path):
        out.append(path)
    return out


def test_two_runs_of_one_world_and_seed_write_byte_equal_replay_chunks():
    first = _run_chunks("frontier_living_world", 42, "a")
    second = _run_chunks("frontier_living_world", 42, "b")
    assert first.keys() == second.keys()
    differing = [name for name in first if first[name] != second[name]]
    assert not differing, f"replay chunks differ byte for byte: {differing}"


def test_no_wall_clock_leaf_is_left_in_a_replayed_update():
    chunks = _run_chunks("frontier_living_world", 42, "c")
    leaves: List[str] = []
    for raw in chunks.values():
        for event in json.loads(raw):
            leaves += _float_leaves(event.get("payload", {}), "payload")
    assert not leaves, f"float timer leaves in replayed metric_counters / sub_phase_costs, e.g. {sorted(set(leaves))[:5]}"
