"""S9 runner: urban_political seed 42 for 2000 ticks on the births head and on the frozen main tree, one arm after the other, then the mechanical per-eid verdict.

Each arm runs the same pinned kernel (``build_kernel``: audit_mode, no frame pacing, sequential executor) with the S9 spy installed from the HEAD checkout's ``s9_spy.py`` (loaded by file
path, so the main tree needs no copy of it); recording stays ON (the default run directory is written; the spy itself reads only state and the applied update). TMPDIR is set under ``--out``.
Output: every group's formation, last-seen and dissolution tick and typed reason on both arms; every hit row uncapped, split between t0 and newborn members; one class per eid
(BLOCK / MAIN-DEFECT / FINDING; an eid with no head hit has class none and is not listed); and one final line ``S9 VERDICT: BLOCK|FINDINGS|CLEAR``.

Usage: python -m tools.rpg_measure.s9_run --tree <head tree> --main-tree <frozen main 3aafdb383> --out <dir> --go <ref> [--world urban_political] [--seed 42] [--ticks 2000]
Run under ``systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`` with PYTHONHASHSEED=0, detached under setsid; refuses to start without --go; deletes nothing.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

SPY_FILE = Path(__file__).resolve().with_name("s9_spy.py")
WORLD, SEED, TICKS = "urban_political", 42, 2000


def load_spy(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("s9_spy_loaded", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child(world: str, seed: int, ticks: int, arm: str, out: str, spy_file: str) -> int:
    """One arm: run the kernel with the spy and write the timelines, the group facts and the final state hash."""
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    spy_module = load_spy(Path(spy_file))
    kernel = build_kernel(world, seed, f"s9_{arm}_{world}_{seed}_{os.getpid()}")
    start = kernel.state
    spy = spy_module.GroupSpy(start).install()
    try:
        for _ in range(ticks):
            kernel.tick_once()
        state = kernel.state
        final_hash = CanonicalStateHasher.get_hash(state)
    finally:
        spy.restore()
        kernel.shutdown()
    groups = {}
    for gid, seen in sorted(spy.group_seen.items()):
        record = state.groups.get(gid)
        groups[str(gid)] = {**seen, "alive_at_end": record is not None and getattr(record, "dissolution_tick", None) is None,
                            "formation_tick": getattr(record, "formation_tick", None), "leader_at_end": getattr(record, "leader_id", None),
                            "members_at_end": sorted(record.member_ids) if record is not None else None}
    doc = {
        "arm": arm, "world": world, "seed": seed, "ticks": ticks, "final_hash": final_hash, "start_ids": sorted(spy.start_ids), "rows": {str(k): v for k, v in spy.rows.items()},
        "groups": groups, "mother": {str(k): v for k, v in spy.mother.items()}, "newborn_in_group": spy.newborn_in_group, "not_captured": list(spy_module.NOTHING_CAPTURED),
        "starving_line": spy_module.STARVING_LINE, "window": spy_module.WINDOW,
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    return 0


def judge(head: Dict[str, Any], main: Dict[str, Any], spy_module: Any) -> Dict[str, Any]:
    """The mechanical read of the two arms: hits per eid, one class per eid, the final verdict, the split counts and the group lifetimes of both arms."""
    rows = lambda doc: {int(k): v for k, v in doc["rows"].items()}
    head_rows, main_rows = rows(head), rows(main)
    head_hits, main_hits = spy_module.hits_by_eid(head_rows, head["window"]), spy_module.hits_by_eid(main_rows, main["window"])
    t0_both = set(head["start_ids"]) & set(main["start_ids"])
    mother = {int(k): v for k, v in head["mother"].items()}
    classified = spy_module.classify(head_hits, main_hits, t0_both, mother, head_rows)
    return {
        "verdict": spy_module.final_verdict(classified), "eids": classified, "counts_head": spy_module.split_counts(classified),
        "main_hits_by_eid": {str(k): {c: len(v) for c, v in hits.items()} for k, hits in main_hits.items()},
        "groups": {"head": head["groups"], "main": main["groups"]}, "newborn_in_group_head": head["newborn_in_group"],
        "window": head["window"], "starving_line": head["starving_line"], "cap": "none: every hit row is listed", "not_captured": head["not_captured"],
        "final_hash": {"head": head["final_hash"], "main": main["final_hash"]},
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", nargs=6, metavar=("WORLD", "SEED", "TICKS", "ARM", "OUT", "SPY_FILE"))
    ap.add_argument("--tree", type=Path)
    ap.add_argument("--main-tree", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--go", default=None)
    ap.add_argument("--world", default=WORLD)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--ticks", type=int, default=TICKS)
    args = ap.parse_args(argv)
    if args.child:
        world, seed, ticks, arm, out, spy_file = args.child
        return child(world, int(seed), int(ticks), arm, out, spy_file)
    if not (args.tree and args.main_tree and args.out and args.go):
        ap.error("--tree, --main-tree, --out and --go are required")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "tmp").mkdir(exist_ok=True)
    docs: Dict[str, Dict[str, Any]] = {}
    for arm, tree in (("head", args.tree), ("main", args.main_tree)):
        path = args.out / f"{arm}.json"
        env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(tree), "TMPDIR": str(args.out / "tmp")}
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", args.world, str(args.seed), str(args.ticks), arm, str(path), str(SPY_FILE)],
                              cwd=tree, env=env, capture_output=True, text=True)
        if proc.returncode != 0 or not path.exists():
            raise RuntimeError(f"S9 arm {arm} failed: {proc.stderr.strip()[-400:]}")
        docs[arm] = json.loads(path.read_text(encoding="utf-8"))
    report = judge(docs["head"], docs["main"], load_spy(SPY_FILE))
    report.update({"go": args.go, "world": args.world, "seed": args.seed, "ticks": args.ticks})
    (args.out / "s9_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    for row in report["eids"]:
        print(f"eid {row['eid']:>6} {row['population']:<7} {row['class']:<11} {row['kinds']}")
    print(f"S9 VERDICT: {report['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
