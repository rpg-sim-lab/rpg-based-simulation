"""The 100-tick recording check (decides whether the own-job arms may run recording-off): the same run with recording ON, with the kernel flag ``no_replay``, and with the observability mode
OFF must end on the same canonical state hash; a fourth run with one deliberate state write must END ON A DIFFERENT hash (the positive control that proves the comparison can fail).

``no_replay`` is injected into the kernel's flags inside the child process only (a wrapper over ``Kernel.__init__``); the observability mode is the environment variable ``SIM_OBS_MODE`` /
``RPG_OBS_MODE`` read by ``src/observability/config.py``. No source file changes. The driver also prints each arm's run-dir size on disk so the disk plan is measured, not estimated.

Usage: python -m tools.rpg_measure.births_obs_check --tree <fix tree> --out <dir> --go <ref> [--world frontier_living_world] [--seed 42] [--ticks 100]
Run under ``systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`` with PYTHONHASHSEED=0; refuses to start without --go; deletes nothing.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ARMS = ("recording_on", "no_replay", "obs_off", "write_control")
RECORDING_OFF_ENV = {"SIM_OBS_MODE": "OFF", "RPG_OBS_MODE": "OFF"}


def dir_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) if path.exists() else 0


def child(world: str, seed: int, ticks: int, arm: str, out: str) -> int:
    """One arm: build the pinned kernel, optionally inject ``no_replay`` or a deliberate state write, run, write the final hash and the run id."""
    from src.engine import kernel as kernel_module
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    if arm == "no_replay":
        original = kernel_module.Kernel.__init__

        def init(self, *args, **kwargs):
            flags = dict(kwargs.get("flags") or {})
            flags["no_replay"] = True
            kwargs["flags"] = flags
            return original(self, *args, **kwargs)

        kernel_module.Kernel.__init__ = init
    run_id = f"births_obs_{arm}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    flags_seen = {"no_replay": getattr(kernel, "_no_replay", None), "audit_mode": getattr(kernel, "_audit_mode", None)}
    try:
        for tick in range(ticks):
            kernel.tick_once()
            if arm == "write_control" and tick == ticks // 2:
                state = kernel.state
                first = min(state.entities)
                body = state.entities[first]
                changed = dataclasses.replace(body, biological=dataclasses.replace(body.biological, hunger=body.biological.hunger + 1.0))
                kernel._state = dataclasses.replace(state, entities={**state.entities, first: changed})
        final = CanonicalStateHasher.get_hash(kernel.state)
    finally:
        kernel.shutdown()
    Path(out).write_text(json.dumps({"arm": arm, "final_hash": final, "run_id": run_id, "flags_seen": flags_seen}, sort_keys=True), encoding="utf-8")
    return 0


def judge(rows: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Mechanical verdict: PASS when no_replay and obs_off hash equal recording_on and the write control differs; FAIL otherwise (a control that does not differ means the comparison cannot fail)."""
    base = rows["recording_on"]["final_hash"]
    equal = {arm: rows[arm]["final_hash"] == base for arm in ("no_replay", "obs_off")}
    control_differs = rows["write_control"]["final_hash"] != base
    return {"equal_to_recording_on": equal, "control_differs": control_differs, "verdict": "PASS" if all(equal.values()) and control_differs else "FAIL"}


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", nargs=5, metavar=("WORLD", "SEED", "TICKS", "ARM", "OUT"))
    ap.add_argument("--tree", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--go", default=None)
    ap.add_argument("--world", default="frontier_living_world")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ticks", type=int, default=100)
    args = ap.parse_args(argv)
    if args.child:
        world, seed, ticks, arm, out = args.child
        return child(world, int(seed), int(ticks), arm, out)
    if not (args.tree and args.out and args.go):
        ap.error("--tree, --out and --go are required")
    args.out.mkdir(parents=True, exist_ok=True)
    rows: Dict[str, Dict[str, Any]] = {}
    for arm in ARMS:
        path = args.out / f"{arm}.json"
        env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(args.tree), **(RECORDING_OFF_ENV if arm == "obs_off" else {})}
        proc = subprocess.run([sys.executable, "-m", "tools.rpg_measure.births_obs_check", "--child", args.world, str(args.seed), str(args.ticks), arm, str(path)],
                              cwd=args.tree, env=env, capture_output=True, text=True)
        if proc.returncode != 0 or not path.exists():
            raise RuntimeError(f"obs check arm {arm} failed: {proc.stderr.strip()[-400:]}")
        rows[arm] = json.loads(path.read_text(encoding="utf-8"))
        rows[arm]["run_dir_bytes"] = dir_bytes(args.tree / "data" / "runs" / rows[arm]["run_id"])
    report = {"rows": rows, **judge(rows), "world": args.world, "seed": args.seed, "ticks": args.ticks, "go": args.go}
    (args.out / "obs_check.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
