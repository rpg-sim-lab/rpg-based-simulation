"""One run of the births own-job: build the pinned kernel, run it tick by tick in one of three modes, and write typed facts plus the final state hash.

Executed by ``births_run.py`` with the FIX tree as the working directory and on PYTHONPATH, so ``tools.rpg_measure.arm_child`` and ``births_spy`` are the fix tree's own.
Modes: ``spied`` (births on, record-only spy), ``plain`` (births on, no spy; its hash must equal the spied arm's), ``control`` (the chance-0 twin: births made impossible by
forcing every ``birth_chance_per_check`` to 0.0 through the catalog accessor, the same code path with no birth, spied like ``spied``).

Usage: python births_child.py <world> <seed> <ticks> <spied|plain|control> <out.json>   (also writes <out>.positions.json.gz in the spied and control modes)
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from collections import Counter
from pathlib import Path

from src.engine.checkpoint import CanonicalStateHasher
from src.world import births
from tools.rpg_measure import arm_child
from tools.rpg_measure.births_spy import CALAMITY_NOTE, BirthSpy, CohortWatch, DeathWatch, TickWatch
from tools.test_architecture.rpg_gate_run import build_kernel


class _ChanceZeroCatalog:
    """The warmed catalog with every reproduction profile's birth chance forced to 0.0: the control arm's only difference from the births arm."""

    def __init__(self, real):
        self._real = real

    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 0.0})

    def __getattr__(self, name):
        return getattr(self._real, name)


def main(argv: list[str]) -> int:
    world, seed, ticks, mode, out = argv[0], int(argv[1]), int(argv[2]), argv[3], argv[4]
    if mode == "control":
        real = births.get_catalog()
        births.get_catalog = lambda: _ChanceZeroCatalog(real)
    pinned_runner = arm_child._pinned_runner()
    run_id = f"births_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)  # rpg_gate_run.build_kernel passes flags audit_mode and no_frame_pacing (line 65)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="births_child build_kernel")
    start_state = kernel.state
    spy = watch = deaths = cohorts = None
    if mode in ("spied", "control"):
        spy = BirthSpy().install()
        watch = TickWatch(spy, start_state)
        deaths = DeathWatch(spy, start_state)
        cohorts = CohortWatch(start_state)
    try:
        for _ in range(ticks):
            kernel.tick_once()
            if watch is not None:
                watch.after_tick(kernel.state)
                deaths.after_tick(kernel.state)
                cohorts.after_tick(kernel.state)
    finally:
        if spy is not None:
            spy.restore()
        state = kernel.state
        kernel.shutdown()
    final = {
        str(e.id): {"kind": e.kind, "alive": int(e.combat.alive), "cause": arm_child._cause(e), "newborn": int(e.id not in start_state.entities)}
        for e in state.entities.values()
    }
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
        "final_hash": CanonicalStateHasher.get_hash(state), "final": final,
        "births_by_kind": dict(Counter(e.kind for e in state.entities.values() if e.id not in start_state.entities)),
        "max_entity_id": max(state.entities, default=0),
    }
    if spy is not None:
        fails = {k: len(v) for k, v in {**spy.fails, **watch.fails}.items()}
        doc.update({
            "births": spy.births, "bars": {k: fails.get(k, 0) for k in ("K6", "K6b", "K8", "W1", "W2", "W3", "W4", "W5")},
            "fail_rows": {k: v[:20] for k, v in {**spy.fails, **watch.fails}.items()},
            "population": watch.population, "camp_census": watch.census, "max_entity_id_seen": watch.max_entity_id,
            "deaths": deaths.deaths, "live_entity_ticks": deaths.live_entity_ticks,
            "nudges": spy.nudges, "regionless": spy.regionless, "applied_cohorts": spy.applied_cohorts,
            "cohort_rows": cohorts.rows, "cohort_flags": cohorts.flags, "calamity_note": CALAMITY_NOTE,
        })
        with gzip.open(out + ".positions.json.gz", "wt", encoding="utf-8") as fh:
            json.dump(deaths.positions, fh)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
