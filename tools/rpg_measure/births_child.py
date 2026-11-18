"""One run of the births own-job: build the pinned kernel, run it tick by tick in one mode, and write typed facts plus the final state hash.

Executed by ``births_run.py`` with the FIX tree as the working directory and on PYTHONPATH, so ``tools.rpg_measure.arm_child`` and ``births_spy`` are the fix tree's own.
Modes: ``spied`` (births on, record-only spy), ``plain`` (births on, no spy; its hash must equal the spied arm's), ``control`` (the chance-0 twin: births made impossible by
forcing every ``birth_chance_per_check`` to 0.0 through the catalog accessor, the same code path with no birth, spied like ``spied``).
Trigger-neutrality modes (both spied, births as normal, rise chance 0.0, differing ONLY in the rise trigger): ``trigger_on`` (the real trigger, counted), ``trigger_off`` (the trigger
rebound to False in this process and the rise made the identity; counted 0/0), and ``trigger_pos`` (the positive control: trigger on, rise chance 1.0, which must differ from ``trigger_off``).
Every mode also records, per tick, the kernel's per-stage wall times (``kernel._phase_costs``: governance_ecology holds the births, economy holds resource_transactions with the rise and the
trigger, cooperation, combat_engagement), the live body count, and the host load (loadavg, steal, MemAvailable) every 100 ticks; the runner reads them for the cost report.

Usage: python births_child.py <world> <seed> <ticks> <mode> <out.json>   (also writes <out>.positions.json.gz in the spied, control and trigger modes)
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

from src.engine.checkpoint import CanonicalStateHasher
from src.world import births
from tools.rpg_measure import arm_child
from tools.rpg_measure.births_spy import CALAMITY_NOTE, BirthSpy, CohortWatch, DeathWatch, TickWatch
from tools.rpg_measure.births_trigger import TriggerShim
from tools.test_architecture.rpg_gate_run import build_kernel

COST_STAGES = ("governance_ecology", "economy", "cooperation", "combat_engagement")
SPIED_MODES = ("spied", "control", "trigger_on", "trigger_off", "trigger_pos")
TRIGGER_MODES = {"trigger_on": ("on", 0.0), "trigger_off": ("off", 0.0), "trigger_pos": ("on", 1.0)}
HOST_EVERY_TICKS = 100


class _ChanceZeroCatalog:
    """The warmed catalog with every reproduction profile's birth chance forced to 0.0: the control arm's only difference from the births arm."""

    def __init__(self, real):
        self._real = real

    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 0.0})

    def __getattr__(self, name):
        return getattr(self._real, name)


def inject_no_replay_if_recording_off() -> bool:
    """Under --recording-off the runner sets SIM_OBS_MODE=OFF in the child's environment; the child then also injects the kernel flag ``no_replay`` (the same wrapper over ``Kernel.__init__`` that
    births_obs_check uses; no source file changes), because the OBS variables alone keep the replay chunks. Without the variable nothing changes. Returns whether the flag will be injected."""
    if os.environ.get("SIM_OBS_MODE") != "OFF":
        return False
    from src.engine import kernel as kernel_module

    original = kernel_module.Kernel.__init__

    def init(self, *args, **kwargs):
        flags = dict(kwargs.get("flags") or {})
        flags["no_replay"] = True
        kwargs["flags"] = flags
        return original(self, *args, **kwargs)

    kernel_module.Kernel.__init__ = init
    return True


def host_reading() -> dict:
    """Host load at this moment: loadavg, aggregate steal jiffies and MemAvailable (kB); read-only, no effect on the run."""
    reading = {"loadavg": open("/proc/loadavg").read().split()[:3]}
    cpu = open("/proc/stat").readline().split()
    reading["steal_jiffies"] = int(cpu[8]) if len(cpu) > 8 else None
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            reading["mem_available_kb"] = int(line.split()[1])
            break
    return reading


def metrics_digest(metrics: dict) -> str:
    """A digest of the kernel's integer and boolean counters for one tick (phase counters, spatial_index_hits...); floats are left out because they may be timings."""
    stable = {k: v for k, v in sorted(metrics.items()) if isinstance(v, (int, bool))}
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


def main(argv: list[str]) -> int:
    world, seed, ticks, mode, out = argv[0], int(argv[1]), int(argv[2]), argv[3], argv[4]
    if mode == "control":
        real = births.get_catalog()
        births.get_catalog = lambda: _ChanceZeroCatalog(real)
    inject_no_replay_if_recording_off()
    pinned_runner = arm_child._pinned_runner()
    run_id = f"births_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)  # rpg_gate_run.build_kernel passes flags audit_mode and no_frame_pacing (line 65)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="births_child build_kernel")
    start_state = kernel.state
    spy = watch = deaths = cohorts = shim = None
    metrics_hash = hashlib.sha256()
    if mode in SPIED_MODES:
        spy = BirthSpy().install()
        watch = TickWatch(spy, start_state)
        deaths = DeathWatch(spy, start_state)
        cohorts = CohortWatch(start_state)
    if mode in TRIGGER_MODES:
        trigger, chance = TRIGGER_MODES[mode]
        shim = TriggerShim().install(trigger, chance)
    corpses_at_t0 = len(start_state.corpses)
    costs: list = []
    host = [{"tick": 0, **host_reading()}]
    try:
        for _ in range(ticks):
            kernel.tick_once()
            phase = kernel._phase_costs
            state_now = kernel.state
            costs.append([state_now.tick, *(round(float(phase.get(stage, 0.0)), 4) for stage in COST_STAGES), round(float(kernel._final_compute_ms), 4), sum(1 for e in state_now.entities.values() if e.combat.alive)])
            if shim is not None:
                metrics_hash.update(metrics_digest(kernel._metrics).encode())
            if state_now.tick % HOST_EVERY_TICKS == 0:
                host.append({"tick": state_now.tick, **host_reading()})
            if watch is not None:
                watch.after_tick(state_now)
                deaths.after_tick(state_now)
                cohorts.after_tick(state_now)
    finally:
        if shim is not None:
            shim.restore()
        if spy is not None:
            spy.restore()
        state = kernel.state
        kernel.shutdown()
    host.append({"tick": ticks, **host_reading()})
    final = {
        str(e.id): {"kind": e.kind, "alive": int(e.combat.alive), "cause": arm_child._cause(e), "newborn": int(e.id not in start_state.entities)}
        for e in state.entities.values()
    }
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
        "final_hash": CanonicalStateHasher.get_hash(state), "final": final,
        "births_by_kind": dict(Counter(e.kind for e in state.entities.values() if e.id not in start_state.entities and e.lifecycle.parent_a_entity_id is not None)),
        "max_entity_id": max(state.entities, default=0), "phase_costs": costs, "cost_stages": list(COST_STAGES), "host": host,
    }
    if spy is not None:
        fails = {k: len(v) for k, v in {**spy.fails, **watch.fails}.items()}
        fails["G5"] = fails.get("G5", 0) + spy.none_gate_reads
        doc.update({
            "births": spy.births, "conceptions": spy.conceptions, "unplaced": spy.unplaced, "ended": spy.ended, "risings": spy.risings, "father_dead_at_term": spy.father_dead_at_term,
            "none_gate_reads": spy.none_gate_reads,
            "bars": {k: fails.get(k, 0) for k in ("K6", "K6b", "K8", "W1", "W2", "W3", "W4", "W5", "G1", "G2", "G3", "G4", "G5", "G6", "R1", "R2", "R3", "R4")},
            "fail_rows": {k: v[:20] for k, v in {**spy.fails, **watch.fails}.items()},
            "population": watch.population, "camp_census": watch.census, "max_entity_id_seen": watch.max_entity_id,
            "deaths": deaths.deaths, "live_entity_ticks": deaths.live_entity_ticks,
            "nudges": spy.nudges, "regionless": spy.regionless, "border_crossings": spy.border_crossings, "applied_cohorts": spy.applied_cohorts,
            "cohort_rows": cohorts.rows, "cohort_flags": cohorts.flags, "calamity_note": CALAMITY_NOTE,
            "event_digest": spy.event_digest, "corpses_at_t0": corpses_at_t0,
        })
        with gzip.open(out + ".positions.json.gz", "wt", encoding="utf-8") as fh:
            json.dump(deaths.positions, fh)
    if shim is not None:
        doc.update({"trigger": shim.counts(), "metrics_digest": metrics_hash.hexdigest()})
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
