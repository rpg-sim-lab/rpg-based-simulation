"""S9 runner: urban_political seed 42 for 2000 ticks on the births head and on the frozen main tree, one arm after the other, then the mechanical per-eid verdict.

Four arms, serial, in this order: head spied, head plain, main spied, main plain. The plain arm of a side is the same run with NO spy; its final state hash must equal the spied arm's (the spy is read-only).
A mismatch on either side makes the verdict INVALID: no BLOCK, FINDINGS or CLEAR line is printed. Both hashes are printed in every case.
Each spied arm runs the same pinned kernel (``build_kernel``: audit_mode, no frame pacing, sequential executor) with the S9 spy installed from the HEAD checkout's ``births_measure_spy.py`` (loaded by file
path, so the main tree needs no copy of it); recording stays ON (the default run directory is written; the spy itself reads only state and the applied update). TMPDIR is set under ``--out``.
Output: every group's formation, last-seen and dissolution tick and typed reason on both arms; every hit row uncapped, split between t0 and newborn members; one class per eid
(BLOCK / MAIN-DEFECT / FINDING; an eid with no head hit has class none and is not listed); and one final line ``S9 VERDICT: BLOCK|FINDINGS|CLEAR``.

Usage: python -m tools.rpg_measure.births_measure_run --tree <head tree> --main-tree <frozen main 3aafdb383> --out <dir> --go <ref> [--world urban_political] [--seed 42] [--ticks 2000]
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
from typing import Any, Dict, List, Optional

SPY_FILE = Path(__file__).resolve().with_name("births_measure_spy.py")
WORLD, SEED, TICKS = "urban_political", 42, 2000


def load_spy(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("births_measure_spy_loaded", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child(world: str, seed: int, ticks: int, arm: str, out: str, spy_file: str) -> int:
    """One arm (``head``/``main`` spied, ``head_plain``/``main_plain`` with no spy): run the kernel and write the final state hash; a spied arm also writes the timelines and the group facts."""
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    spy_module = load_spy(Path(spy_file))
    kernel = build_kernel(world, seed, f"s9_{arm}_{world}_{seed}_{os.getpid()}")
    start = kernel.state
    spy = spy_module.GroupSpy(start).install() if not arm.endswith("_plain") else None
    try:
        for _ in range(ticks):
            kernel.tick_once()
        state = kernel.state
        final_hash = CanonicalStateHasher.get_hash(state)
    finally:
        if spy is not None:
            spy.restore()
        kernel.shutdown()
    if spy is None:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps({"arm": arm, "world": world, "seed": seed, "ticks": ticks, "final_hash": final_hash}, sort_keys=True), encoding="utf-8")
        return 0
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
        "births": spy_module.count_births(state.entities, spy.start_ids), "other_adds": spy_module.count_other_adds(state.entities, spy.start_ids), "conceptions": len(spy.conceptions),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    return 0


def follow_up(verdict: str, head_groups: Dict[str, Any], main_groups: Dict[str, Any]) -> Dict[str, Any]:
    """The cohesion-capture follow-up condition (rpg-designer): it FIRES when the verdict is not CLEAR (INVALID included) or when ANY group is still alive at the last tick on the head."""
    alive = lambda groups: sorted(int(g) for g, v in groups.items() if v.get("alive_at_end"))
    head_alive, main_alive = alive(head_groups), alive(main_groups)
    return {"fired": verdict != "CLEAR" or bool(head_alive), "verdict": verdict, "head_alive_at_end": head_alive, "main_alive_at_end": main_alive}


def follow_up_line(info: Dict[str, Any]) -> str:
    return (f"FOLLOW-UP: cohesion-capture {'FIRED' if info['fired'] else 'NOT FIRED'} (verdict {info['verdict']}; groups alive at the last tick: "
            f"head {info['head_alive_at_end']}, main {info['main_alive_at_end']})")


def judge(head: Dict[str, Any], main: Dict[str, Any], spy_module: Any, head_plain: Optional[Dict[str, Any]] = None, main_plain: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The mechanical read of the two arms: hits per eid, one class per eid, the final verdict, the split counts and the group lifetimes of both arms.

    With the plain arms given, a spied hash that differs from its plain twin on either side makes the verdict INVALID (the spy is not read-only there) and no class is reported."""
    twins = {"head": (head["final_hash"], (head_plain or {}).get("final_hash")), "main": (main["final_hash"], (main_plain or {}).get("final_hash"))}
    twin_equal = {side: spied == plain for side, (spied, plain) in twins.items()} if head_plain is not None and main_plain is not None else None
    if twin_equal is not None and not all(twin_equal.values()):
        return {"verdict": "INVALID", "reason": "a spied arm's final hash differs from its plain twin: the spy changed the run", "twin_hash": {s: {"spied": a, "plain": b} for s, (a, b) in twins.items()}, "eids": [],
                "follow_up": follow_up("INVALID", head["groups"], main["groups"])}
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
        "twin_hash": {s: {"spied": a, "plain": b} for s, (a, b) in twins.items()}, "twin_hash_equal": twin_equal,
        "births": {"head": head.get("births"), "main": main.get("births")}, "other_adds": {"head": head.get("other_adds"), "main": main.get("other_adds")}, "conceptions": {"head": head.get("conceptions"), "main": main.get("conceptions")},
        "follow_up": follow_up(spy_module.final_verdict(classified), head["groups"], main["groups"]),
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
    for arm, tree in (("head", args.tree), ("head_plain", args.tree), ("main", args.main_tree), ("main_plain", args.main_tree)):
        path = args.out / f"{arm}.json"
        env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(tree), "TMPDIR": str(args.out / "tmp")}
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", args.world, str(args.seed), str(args.ticks), arm, str(path), str(SPY_FILE)],
                              cwd=tree, env=env, capture_output=True, text=True)
        if proc.returncode != 0 or not path.exists():
            raise RuntimeError(f"S9 arm {arm} failed: {proc.stderr.strip()[-400:]}")
        docs[arm] = json.loads(path.read_text(encoding="utf-8"))
    report = judge(docs["head"], docs["main"], load_spy(SPY_FILE), docs["head_plain"], docs["main_plain"])
    report.update({"go": args.go, "world": args.world, "seed": args.seed, "ticks": args.ticks})
    (args.out / "s9_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print("twin hashes (spied vs plain):", json.dumps(report["twin_hash"], sort_keys=True))
    print("births / other_adds / conceptions:", json.dumps({"births": report.get("births"), "other_adds": report.get("other_adds"), "conceptions": report.get("conceptions")}, sort_keys=True))
    rows_in_group = report.get("newborn_in_group_head", [])
    print(f"newborns in any group at any tick (head, any kind): {len(rows_in_group)}")
    for entry in rows_in_group:
        print(f"  newborn eid {entry['newborn']} kind {entry.get('kind')} group {entry['group']} first tick in a group {entry['tick']}")
    if report["verdict"] == "INVALID":
        print("S9 VERDICT: INVALID (" + report["reason"] + ")")
        print(follow_up_line(report["follow_up"]))
        return 1
    for row in report["eids"]:
        print(f"eid {row['eid']:>6} {row['population']:<7} {row['class']:<11} {row['kinds']}")
    print(f"S9 VERDICT: {report['verdict']}")
    print(follow_up_line(report["follow_up"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
