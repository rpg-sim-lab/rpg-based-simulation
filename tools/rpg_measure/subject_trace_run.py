"""Planner, runner and cell checks for the subject trace (Q2). Subcommands (every one is meant to be called as ``cd $KIT && PYTHONPATH=$KIT python subject_trace_run.py <sub> ...``; nothing here imports the frozen tree):

``derive``  subjects and windows from the SEALED O3 cells (``--sealed <cells dir>``, ``--seed`` once per seed, optional ``--extra <json>``) -> ``--out subjects.json`` with the sha256 of every sealed cell it read
``one``     ONE child process (the launcher puts it in its own scope): cwd = that arm's frozen tree, PYTHONPATH = that tree, recording OFF; moves the tree's ``data/runs`` out; writes ``<name>.exit.json``
``check``   the validity of every spy cell against the SEALED plain twins (hash equality, spy exceptions, reach) -> ``cell_validity.json``; evidence only, no verdict about the sim
``record``  ``runner.json`` from the exit files and the launcher's status; a failed write exits non-zero

SUBJECTS (module ``derive_plan``): per seed, from the NEW spy cell's O3 rows grouped into engagements by ``person_attack_summary.build_engagements`` (one attacker on one victim, a gap over 50 ticks opens a new one):
every victim of an engagement with at least 10 hits; every victim with an R7 chain (``hit_chains`` per victim: a no-decision run of 5 or more, an asleep/lodged run of 3 or more) with all engagements on it; every attacker of those
engagements; and the explicit extra subjects (``{"seed": 42, "id": N, "windows": [[lo, hi]]}``). WINDOW of an engagement: from its first hit minus 100 ticks to the victim's death (``victim_killed``: the engagement's last
tick) or, when the victim lived, to the engagement's end plus 100 ticks; a subject's windows are merged. COUNTERPARTS of a subject: the other side of every engagement it is in. BASE reads the same ticks (the same plan).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PAD = 100
MIN_HITS = 10
MIN_NO_DECISION_CHAIN, MIN_ASLEEP_CHAIN = 5, 3
HASHSEED = "0"
RECORDING_OFF_ENV = {"SIM_OBS_MODE": "OFF", "RPG_OBS_MODE": "OFF"}
CHILD = Path(__file__).resolve().with_name("subject_trace_spy.py")
EXIT_NOT_RECORDED = 6


def load_sibling(name: str) -> Any:
    key = f"_subject_trace_run_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, Path(__file__).resolve().with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_name(arm: str, world: str, seed: int, mode: str) -> str:
    return f"{arm}__{world}__s{seed}__{mode}"


def merge_windows(windows: List[List[int]]) -> List[List[int]]:
    merged: List[List[int]] = []
    for lo, hi in sorted([max(0, int(a)), int(b)] for a, b in windows):
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return merged


def engagement_window(engagement: Dict[str, Any]) -> List[int]:
    """First hit minus 100 to the victim's death, or the engagement's end plus 100 when the victim lived."""
    end = engagement["end_tick"] if engagement["outcome"] == "victim_killed" else engagement["end_tick"] + PAD
    return [max(0, engagement["start_tick"] - PAD), end]


def derive_seed(spy_cell: Dict[str, Any], summary: Any, extra: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The subject list of one seed from its NEW spy cell (module docstring)."""
    rows = [r for r in spy_cell["rows"] if r["in_o3_group"]]
    engagements = summary.build_engagements(rows, spy_cell["mode_rows"], spy_cell["final_tick"], lambda tick: False)
    chain_victims = set()
    for victim_id in sorted({r["victim_id"] for r in rows}):   # every victim with a qualifying R7 chain, not only the single worst one
        chains = summary.hit_chains([r for r in rows if r["victim_id"] == victim_id], spy_cell["mode_rows"], attack_rows=spy_cell.get("attack_rows"))
        if chains["no_decision_run"]["run"] >= MIN_NO_DECISION_CHAIN or chains["asleep_or_lodged_run"]["run"] >= MIN_ASLEEP_CHAIN:
            chain_victims.add(victim_id)
    subjects: Dict[int, Dict[str, Any]] = {}

    def add(subject_id: int, role: str, windows: List[List[int]], counterparts: List[int]) -> None:
        entry = subjects.setdefault(subject_id, {"id": subject_id, "roles": [], "windows": [], "counterparts": []})
        if role not in entry["roles"]:
            entry["roles"].append(role)
        entry["windows"] += windows
        entry["counterparts"] = sorted(set(entry["counterparts"]) | set(counterparts))

    for eng in engagements:
        big, chain = eng["hits"] >= MIN_HITS, eng["victim_id"] in chain_victims
        if not (big or chain):
            continue
        window = engagement_window(eng)
        add(eng["victim_id"], "chain_victim" if chain else "victim", [window], [eng["attacker_id"]])
        if big and chain:
            add(eng["victim_id"], "victim", [window], [eng["attacker_id"]])
        add(eng["attacker_id"], "attacker", [window], [eng["victim_id"]])
    for item in extra:
        add(int(item["id"]), "extra", item["windows"], [])
    for entry in subjects.values():
        entry["windows"] = merge_windows(entry["windows"])
        entry["roles"] = sorted(entry["roles"])
    return [subjects[k] for k in sorted(subjects)]


def derive_plan(sealed: Path, world: str, seeds: List[int], extra: List[Dict[str, Any]], summary: Any) -> Dict[str, Any]:
    derived_from: Dict[str, str] = {}
    by_seed: Dict[str, List[Dict[str, Any]]] = {}
    for seed in seeds:
        spy_path = sealed / f"{cell_name('new', world, seed, 'spy')}.json"
        derived_from[spy_path.name] = sha256_file(spy_path)
        by_seed[str(seed)] = derive_seed(json.loads(spy_path.read_text(encoding="utf-8")), summary, [e for e in extra if int(e.get("seed", seed)) == seed])
        for arm in ("new", "base"):
            plain = sealed / f"{cell_name(arm, world, seed, 'plain')}.json"
            derived_from[plain.name] = sha256_file(plain)
    body = {"derived_from": derived_from, "pad": PAD, "min_hits": MIN_HITS, "world": world, "subjects_by_seed": by_seed, "extra_input": extra}
    return {**body, "plan_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()}


def check_cell(spy: Dict[str, Any], sealed_plain: Dict[str, Any], arm: str, seed: int) -> Dict[str, Any]:
    """Validity of one spy cell against its SEALED plain twin. Evidence-only: a void cell says why; nothing here judges the simulation."""
    reasons: List[str] = []
    if spy.get("spy_exceptions") or spy.get("fatal"):
        reasons.append("SPY_EXCEPTION (fatal)")
    if spy.get("final_hash") != sealed_plain.get("final_hash"):
        reasons.append("PERTURBATION: the spy's final hash differs from the sealed plain twin's")
    if spy.get("ticks") != sealed_plain.get("ticks"):
        reasons.append("TICKS differ from the sealed plain twin")
    if spy.get("row_count", 0) == 0:
        reasons.append("VOID: 0 subject rows in the windows")
    if arm == "new" and seed == 42 and spy.get("legality_calls_in_window", 0) == 0:
        reasons.append("VOID: NEW s42 has no legality call by any subject in its window")
    return {"arm": arm, "seed": seed, "valid": not reasons, "reasons": reasons, "row_count": spy.get("row_count"), "legality_calls_in_window": spy.get("legality_calls_in_window"),
            "final_hash_spy": spy.get("final_hash"), "final_hash_sealed_plain": sealed_plain.get("final_hash")}


def child_env(tree: Path, out: Path) -> Dict[str, str]:
    return {**os.environ, "PYTHONHASHSEED": HASHSEED, "PYTHONPATH": str(tree), "TMPDIR": str(out / "tmp"), **RECORDING_OFF_ENV}


def run_child(python: str, tree: Path, out: Path, item: Dict[str, Any], plan: Path) -> Dict[str, Any]:
    (out / "tmp").mkdir(parents=True, exist_ok=True)
    path = out / f"{item['name']}.json"
    command = [python, str(CHILD), item["world"], str(item["seed"]), str(item["ticks"]), str(path), "--arm", item["arm"], "--plan", str(plan), "--mode", item["mode"]]
    started = time.time()
    proc = subprocess.run(command, cwd=tree, env=child_env(tree, out), capture_output=True, text=True)
    seconds = round(time.time() - started, 1)
    moved = load_sibling("person_attack_run").move_tree_runs(tree, out / "tree-data-runs" / item["name"])
    result = {"returncode": proc.returncode, "stderr_tail": proc.stderr.strip()[-400:], "seconds": seconds, "tree_data_runs_moved_to": None if moved is None else str(moved)}
    (out / f"{item['name']}.exit.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    with (out / "run_times.log").open("a", encoding="utf-8") as log:
        log.write(f"RUN {item['name']}: {seconds}s returncode {proc.returncode}\n")
    return result


def check_all(cells: Path, sealed: Path, world: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = {}
    for item in items:
        if item["mode"] != "spy":
            continue
        key = f"{item['arm']}/s{item['seed']}"
        spy_path, plain_path = cells / f"{item['name']}.json", sealed / f"{cell_name(item['arm'], world, item['seed'], 'plain')}.json"
        if not spy_path.exists() or not plain_path.exists():
            results[key] = {"arm": item["arm"], "seed": item["seed"], "valid": False, "reasons": ["VOID: the spy cell or the sealed plain twin file is missing"]}
            continue
        results[key] = check_cell(json.loads(spy_path.read_text(encoding="utf-8")), json.loads(plain_path.read_text(encoding="utf-8")), item["arm"], item["seed"])
    return {"cells": results, "all_valid": bool(results) and all(c["valid"] for c in results.values())}


def write_record(out: Path, status: str, go: str, items: List[Dict[str, Any]], freeze: Dict[str, str], python: str) -> Dict[str, Any]:
    """``runner.json``: the launcher's status, the exit file of every item and the freeze values. The write is checked by reading it back; the caller exits non-zero when this raises."""
    codes = {}
    for item in items:
        exit_file = out / "cells" / f"{item['name']}.exit.json"
        codes[item["name"]] = json.loads(exit_file.read_text(encoding="utf-8"))["returncode"] if exit_file.exists() else None
    record = {"go": go, "status": status, "python": python, "freeze": freeze, "returncodes": codes, "items": [i["name"] for i in items]}
    target = out / "runner.json"
    target.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    if json.loads(target.read_text(encoding="utf-8")) != record:
        raise RuntimeError("runner.json read back differently")
    return record


def items_for(kind: str, world: str, seeds: List[int], ticks: int) -> List[Dict[str, Any]]:
    """cells: the four spy cells, NEW first; smoke: NEW s42 plain then spy at ``ticks``."""
    if kind == "smoke":
        modes = [("new", seeds[0], "plain"), ("new", seeds[0], "spy")]
    else:
        modes = [(arm, seed, "spy") for arm in ("new", "base") for seed in seeds]
    return [{"arm": arm, "world": world, "seed": seed, "ticks": ticks, "mode": mode, "name": cell_name(arm, world, seed, mode)} for arm, seed, mode in modes]


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("derive")
    d.add_argument("--sealed", required=True, type=Path)
    d.add_argument("--world", required=True)
    d.add_argument("--seed", action="append", type=int, required=True)
    d.add_argument("--extra", type=Path)
    d.add_argument("--out", required=True, type=Path)
    o = sub.add_parser("one")
    for name in ("arm", "world", "mode", "tree", "out", "python", "plan"):
        o.add_argument(f"--{name}", required=True)
    o.add_argument("--seed", required=True, type=int)
    o.add_argument("--ticks", required=True, type=int)
    c = sub.add_parser("check")
    c.add_argument("--cells", required=True, type=Path)
    c.add_argument("--sealed", required=True, type=Path)
    c.add_argument("--world", required=True)
    c.add_argument("--seed", action="append", type=int, required=True)
    c.add_argument("--ticks", required=True, type=int)
    c.add_argument("--out", required=True, type=Path)
    r = sub.add_parser("record")
    r.add_argument("--out", required=True, type=Path)
    r.add_argument("--status", required=True)
    r.add_argument("--go", required=True)
    r.add_argument("--kind", required=True, choices=("cells", "smoke"))
    r.add_argument("--world", required=True)
    r.add_argument("--seed", action="append", type=int, required=True)
    r.add_argument("--ticks", required=True, type=int)
    r.add_argument("--python", required=True)
    r.add_argument("--freeze-expected", required=True)
    r.add_argument("--freeze-final", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "derive":
        extra = json.loads(args.extra.read_text(encoding="utf-8")) if args.extra else []
        plan = derive_plan(args.sealed, args.world, args.seed, extra, load_sibling("person_attack_summary"))
        args.out.write_text(json.dumps(plan, indent=1, sort_keys=True), encoding="utf-8")
        print(json.dumps({"plan_sha256": plan["plan_sha256"], "subjects": {s: [x["id"] for x in v] for s, v in plan["subjects_by_seed"].items()}}, sort_keys=True))
        return 0
    if args.cmd == "one":
        item = {"arm": args.arm, "world": args.world, "seed": args.seed, "ticks": args.ticks, "mode": args.mode, "name": cell_name(args.arm, args.world, args.seed, args.mode)}
        result = run_child(args.python, Path(args.tree), Path(args.out), item, Path(args.plan))
        print(json.dumps(result, sort_keys=True))
        return result["returncode"]
    if args.cmd == "check":
        items = items_for("cells", args.world, args.seed, args.ticks)
        verdict = check_all(args.cells, args.sealed, args.world, items)
        args.out.write_text(json.dumps(verdict, indent=1, sort_keys=True), encoding="utf-8")
        print(json.dumps({"all_valid": verdict["all_valid"]}))
        return 0 if verdict["all_valid"] else 1
    try:
        items = items_for(args.kind, args.world, args.seed, args.ticks)
        write_record(args.out, args.status, args.go, items, {"expected": args.freeze_expected, "final": args.freeze_final}, args.python)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"RECORD NOT WRITTEN: {exc}", file=sys.stderr)
        return EXIT_NOT_RECORDED
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
