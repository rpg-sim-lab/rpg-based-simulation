"""Runner for the coin and world-boss counter (tools/rpg_measure/coin_boss_spy.py): one world/seed/ticks per call, each cell in its OWN child process (cwd = the head tree, PYTHONPATH = the head tree), with the
same environment births_run gives its children (``births_run.child_env``: PYTHONHASHSEED, SIM_OBS_MODE=OFF and RPG_OBS_MODE=OFF). Refuses to start without ``--go`` (the lead-planner go for THIS run) and deletes nothing.

Modes: ``real`` runs the spy for the cell (the spied arm of the re-check; the summarizer compares its final hash with the plain twin's). ``controls`` runs, on ONE world/seed (short ticks allowed): the matching real run
(``real.json``), a coin control (``control_coin_<N>.json``), a boss control (``control_boss_<K>.json``) and one never-fire control (``control_never_fire.json``: a coin control whose tick no state reaches, which must exit 6).
In controls mode EVERY child, the real run included, gets ``--uncapped-rows``; real mode keeps the cap. Every child writes ``<name>.json`` and the runner writes ``<name>.exit.json`` ({"returncode", "stderr_tail"}); a non-zero code is recorded, never raised, because exits 4, 5 and 6 are results.
The kernel writes ``data/runs/<id>`` under the tree (cwd-relative, even with recording off); after the cell the runner MOVES that dir out to ``<out>/tree-data-runs`` (never deletes) so the frozen tree stays byte-clean.
Heavy-job hygiene: the children are ``coin_boss_spy.py`` (the file name carries ``_spy`` for the shared busy gate); launch THIS runner from a script file, with the kit words only inside that file, on the planner's HOST FREE.
Usage: python -m tools.rpg_measure.coin_boss_run --tree <head tree> --out <dir> --go <ref> --mode real|controls --world W --seed S --ticks N [--coin N] [--boss K]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.rpg_measure.births_run import child_env

CHILD = Path(__file__).resolve().with_name("coin_boss_spy.py")
NEVER_FIRE_TICK_OFFSET = 1_000_000  # a control tick no state reaches


def child_command(world: str, seed: int, ticks: int, out: Path, control: Optional[str] = None, control_tick: Optional[int] = None, uncapped_rows: bool = False) -> List[str]:
    cmd = [sys.executable, str(CHILD), world, str(seed), str(ticks), str(out)]
    if control is not None:
        cmd += ["--control", control]
    if control_tick is not None:
        cmd += ["--control-tick", str(control_tick)]
    if uncapped_rows:
        cmd.append("--uncapped-rows")
    return cmd


def plan(mode: str, world: str, seed: int, ticks: int, coin: int, boss: int) -> List[Tuple[str, Optional[str], Optional[int]]]:
    """(output name, --control spec, --control-tick) for every child the mode runs, in order. The real run of a control set is named ``real`` so the summarizer finds it."""
    if mode == "real":
        return [(f"real_{world}_{seed}_{ticks}", None, None)]
    return [("real", None, None), (f"control_coin_{coin}", f"coin:{coin}", None), (f"control_boss_{boss}", f"boss:{boss}", None),
            ("control_never_fire", f"coin:{coin}", ticks + NEVER_FIRE_TICK_OFFSET)]


def run_cell(tree: Path, out: Path, name: str, world: str, seed: int, ticks: int, control: Optional[str] = None, control_tick: Optional[int] = None, uncapped_rows: bool = False) -> int:
    """Run one child, record its exit code and the tail of its stderr next to its output, and return the code (never raises on a non-zero exit)."""
    path = out / f"{name}.json"
    env: Dict[str, str] = {**child_env(tree, True), "TMPDIR": str(out / "tmp")}
    (out / "tmp").mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(child_command(world, seed, ticks, path, control, control_tick, uncapped_rows), cwd=tree, env=env, capture_output=True, text=True)
    (out / f"{name}.exit.json").write_text(json.dumps({"returncode": proc.returncode, "stderr_tail": proc.stderr.strip()[-400:]}, sort_keys=True), encoding="utf-8")
    return proc.returncode


def move_tree_runs(tree: Path, out: Path) -> Optional[Path]:
    """Move the tree's ``data/runs`` (written by the kernel, cwd-relative) into ``<out>/tree-data-runs``; None when there is none. Never deletes."""
    runs = tree / "data" / "runs"
    if not runs.exists():
        return None
    destination = out / "tree-data-runs"
    if destination.exists():
        raise RuntimeError(f"{destination} already exists: refusing to overwrite")
    shutil.move(str(runs), str(destination))
    return destination


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--go", required=True, help="reference of the lead-planner go for THIS run")
    ap.add_argument("--mode", required=True, choices=("real", "controls"))
    ap.add_argument("--world", required=True)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--ticks", required=True, type=int)
    ap.add_argument("--coin", type=int, default=5, help="N of the coin control (controls mode)")
    ap.add_argument("--boss", type=int, default=2, help="K of the boss control (controls mode)")
    args = ap.parse_args(argv)
    if (args.tree / "data" / "runs").exists():
        print(f"ABORT: {args.tree / 'data' / 'runs'} already exists; move it out first", file=sys.stderr)
        return 3
    args.out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, control, control_tick in plan(args.mode, args.world, args.seed, args.ticks, args.coin, args.boss):
        results[name] = run_cell(args.tree, args.out, name, args.world, args.seed, args.ticks, control, control_tick, uncapped_rows=args.mode == "controls")  # controls mode: every child, the real run included, writes uncapped rows
    moved = move_tree_runs(args.tree, args.out)
    (args.out / "runner.json").write_text(json.dumps({"go": args.go, "mode": args.mode, "world": args.world, "seed": args.seed, "ticks": args.ticks, "returncodes": results,
                                                      "tree_data_runs_moved_to": None if moved is None else str(moved)}, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"returncodes": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
