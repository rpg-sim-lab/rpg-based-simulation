"""Runner for the person-attack trace: per (arm, world, seed) cell the PLAIN twin first, then the spy, each in its OWN child process (cwd = that arm's frozen tree, PYTHONPATH = that tree), with the
environment the births re-check used (PYTHONHASHSEED=0, SIM_OBS_MODE=OFF, RPG_OBS_MODE=OFF). The kit runs from THIS checkout; each child imports the simulation from its tree.

Refuses to start without ``--go`` (the lead-planner GO for THIS run; a #715 record id) and deletes nothing: after every child the tree's ``data/runs`` (written by the kernel, cwd-relative) is MOVED to
``<out>/tree-data-runs/<name>`` so each frozen tree stays byte-clean. The two arms run side by side (one worker per arm, so at most 2 processes at a time); inside an arm the cells run in seed order.

INTERPRETER: ``--python`` (the shared main-checkout ``.venv``, read-only). ``freeze_sha`` (``uv pip freeze --python <python>``, sha256 of the text) is taken before the first process and again after EVERY process;
a change voids the run (``VOID_INTERPRETER_CHANGED``, the remaining cells are not started). Both numbers go into ``runner.json``.
TWIN CHECK: after a spy child, its ``final_hash`` must equal the plain twin's (``twin_equal`` in ``runner.json``); a difference is recorded, never hidden, and the cell does not count.
Files: ``<arm>__<world>__s<seed>__plain.json`` / ``__spy.json`` (the child outputs the summarizer reads), ``<same>.exit.json`` ({"returncode", "stderr_tail", "seconds"}), ``run_times.log``.
Heavy-job hygiene: the children are ``person_attack_spy.py`` (the name carries ``_spy`` for the shared busy gate); launch THIS runner from a script file (``person_attack_launch.sh``), never with kit words on a command line.
Usage: python person_attack_run.py --tree new=<tree> --tree base=<tree> --out <dir> --go <ref> --world W [--world W2] --seed 42 --seed 43 --ticks 5000 --python <python> [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

CHILD = Path(__file__).resolve().with_name("person_attack_spy.py")
HASHSEED = "0"
RECORDING_OFF_ENV = {"SIM_OBS_MODE": "OFF", "RPG_OBS_MODE": "OFF"}
MODES = ("plain", "spy")
FREEZE_COMMAND = ("uv", "pip", "freeze", "--python")


def child_env(tree: Path, out: Path) -> Dict[str, str]:
    return {**os.environ, "PYTHONHASHSEED": HASHSEED, "PYTHONPATH": str(tree), "TMPDIR": str(out / "tmp"), **RECORDING_OFF_ENV}


def child_command(python: str, world: str, seed: int, ticks: int, out_file: Path, mode: str) -> List[str]:
    return [python, str(CHILD), world, str(seed), str(ticks), str(out_file), "--mode", mode]


def cell_name(arm: str, world: str, seed: int, mode: str) -> str:
    return f"{arm}__{world}__s{seed}__{mode}"


def freeze_sha(python: str, runner=subprocess.run) -> str:
    """sha256 of ``uv pip freeze --python <python>`` (the installed distributions of the interpreter the run uses)."""
    proc = runner([*FREEZE_COMMAND, python], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"freeze failed: {proc.stderr.strip()[-300:]}")
    return hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest()


def move_tree_runs(tree: Path, destination: Path) -> Optional[Path]:
    """Move the tree's ``data/runs`` out to ``destination``; None when there is none (nothing is deleted; an empty ``data`` dir is left as the kernel made it)."""
    runs = tree / "data" / "runs"
    if not runs.exists():
        return None
    if destination.exists():
        raise RuntimeError(f"{destination} already exists: refusing to overwrite")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(runs), str(destination))
    return destination


def plan(arms: List[str], worlds: List[str], seeds: List[int], ticks: int) -> List[Dict[str, Any]]:
    """Every child in run order per arm: for each (world, seed) the plain twin, then the spy."""
    return [{"arm": arm, "world": world, "seed": seed, "ticks": ticks, "mode": mode, "name": cell_name(arm, world, seed, mode)} for arm in arms for world in worlds for seed in seeds for mode in MODES]


def run_child(python: str, tree: Path, out: Path, item: Dict[str, Any]) -> Dict[str, Any]:
    (out / "tmp").mkdir(parents=True, exist_ok=True)
    path = out / f"{item['name']}.json"
    started = time.time()
    proc = subprocess.run(child_command(python, item["world"], item["seed"], item["ticks"], path, item["mode"]), cwd=tree, env=child_env(tree, out), capture_output=True, text=True)
    seconds = round(time.time() - started, 1)
    moved = move_tree_runs(tree, out / "tree-data-runs" / item["name"])
    result = {"returncode": proc.returncode, "stderr_tail": proc.stderr.strip()[-400:], "seconds": seconds, "tree_data_runs_moved_to": None if moved is None else str(moved)}
    (out / f"{item['name']}.exit.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    with (out / "run_times.log").open("a", encoding="utf-8") as log:
        log.write(f"RUN {item['name']}: {seconds}s returncode {proc.returncode}\n")
    return result


def run_arm(arm: str, items: List[Dict[str, Any]], tree: Path, out: Path, python: str, before: str, stop: threading.Event, results: Dict[str, Any]) -> None:
    for item in items:
        if stop.is_set():
            results[item["name"]] = {"skipped": "run voided"}
            continue
        results[item["name"]] = run_child(python, tree, out, item)
        after = freeze_sha(python)
        if after != before:
            results[item["name"]]["interpreter_changed"] = {"before": before, "after": after}
            stop.set()


def twin_check(out: Path, items: List[Dict[str, Any]]) -> Dict[str, Optional[bool]]:
    """cell -> True/False when both files exist and their final hashes compare, None when a file is missing."""
    checks: Dict[str, Optional[bool]] = {}
    for item in items:
        if item["mode"] != "spy":
            continue
        plain, spy = out / f"{cell_name(item['arm'], item['world'], item['seed'], 'plain')}.json", out / f"{item['name']}.json"
        key = f"{item['arm']}/{item['world']}/s{item['seed']}"
        if plain.exists() and spy.exists():
            checks[key] = json.loads(plain.read_text(encoding="utf-8")).get("final_hash") == json.loads(spy.read_text(encoding="utf-8")).get("final_hash")
        else:
            checks[key] = None
    return checks


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", action="append", required=True, help="arm=path, once per arm (new=..., base=...)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--go", required=True, help="reference of the lead-planner go for THIS run")
    ap.add_argument("--world", action="append", required=True)
    ap.add_argument("--seed", action="append", required=True, type=int)
    ap.add_argument("--ticks", required=True, type=int)
    ap.add_argument("--python", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the plan and stop (starts no process)")
    args = ap.parse_args(argv)
    trees: Dict[str, Path] = {}
    for spec in args.tree:
        arm, _, path = spec.partition("=")
        trees[arm] = Path(path)
    items = plan(list(trees), args.world, args.seed, args.ticks)
    if args.dry_run:
        print(json.dumps([{**i, "cmd": child_command(args.python, i["world"], i["seed"], i["ticks"], args.out / f"{i['name']}.json", i["mode"]), "tree": str(trees[i["arm"]])} for i in items], indent=1))
        return 0
    for arm, tree in trees.items():
        if (tree / "data" / "runs").exists():
            print(f"ABORT: {tree / 'data' / 'runs'} already exists; move it out first", file=sys.stderr)
            return 3
    args.out.mkdir(parents=True, exist_ok=True)
    before = freeze_sha(args.python)
    stop, results = threading.Event(), {}
    with ThreadPoolExecutor(max_workers=len(trees)) as pool:
        futures = [pool.submit(run_arm, arm, [i for i in items if i["arm"] == arm], tree, args.out, args.python, before, stop, results) for arm, tree in trees.items()]
        for future in futures:
            future.result()
    after = freeze_sha(args.python)
    voided = stop.is_set() or after != before
    summary = {"go": args.go, "ticks": args.ticks, "worlds": args.world, "seeds": args.seed, "python": args.python, "freeze_sha_before": before, "freeze_sha_after": after,
               "status": "VOID_INTERPRETER_CHANGED" if voided else "COMPLETE", "returncodes": {k: v.get("returncode") for k, v in sorted(results.items())}, "twin_equal": twin_check(args.out, items)}
    (args.out / "runner.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": summary["status"], "twin_equal": summary["twin_equal"]}, sort_keys=True))
    return 4 if voided else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
