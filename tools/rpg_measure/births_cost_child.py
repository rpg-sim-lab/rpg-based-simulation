"""The cost-only child (perf regression read, owner rule #715 6968328816): run a world tick by tick on ANY tree and record the kernel's per-stage wall times and the live body count.

It imports nothing from the births system, the spy or the risen code, so it runs on the frozen MAIN tree (the cwd and PYTHONPATH the runner gives it) exactly as it runs on the head. It reads
``kernel._phase_costs`` after each tick (an existing attribute; reading it changes nothing) and the host load every 100 ticks, and writes no state hash beyond the final one.

Usage: python births_cost_child.py <world> <seed> <ticks> <out.json>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from src.engine.checkpoint import CanonicalStateHasher
from tools.test_architecture.rpg_gate_run import build_kernel

COST_STAGES = ("governance_ecology", "economy", "cooperation", "combat_engagement")
HOST_EVERY_TICKS = 100


def host_reading() -> dict:
    """Host load now: loadavg, aggregate steal jiffies, MemAvailable (kB)."""
    reading = {"loadavg": open("/proc/loadavg").read().split()[:3]}
    cpu = open("/proc/stat").readline().split()
    reading["steal_jiffies"] = int(cpu[8]) if len(cpu) > 8 else None
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            reading["mem_available_kb"] = int(line.split()[1])
            break
    return reading


def main(argv: list[str]) -> int:
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    kernel = build_kernel(world, seed, f"births_cost_{world}_{seed}_{os.getpid()}")
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    costs, host = [], [{"tick": 0, **host_reading()}]
    try:
        for _ in range(ticks):
            kernel.tick_once()
            phase, state = kernel._phase_costs, kernel.state
            costs.append([state.tick, *(round(float(phase.get(stage, 0.0)), 4) for stage in COST_STAGES), round(float(kernel._final_compute_ms), 4), sum(1 for e in state.entities.values() if e.combat.alive)])
            if state.tick % HOST_EVERY_TICKS == 0:
                host.append({"tick": state.tick, **host_reading()})
        final = CanonicalStateHasher.get_hash(kernel.state)
    finally:
        kernel.shutdown()
    host.append({"tick": ticks, **host_reading()})
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps({"world": world, "seed": seed, "ticks": ticks, "mode": "cost", "forced_flags": forced, "final_hash": final, "phase_costs": costs, "cost_stages": list(COST_STAGES), "host": host}, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
