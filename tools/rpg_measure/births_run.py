"""Driver for the births own-job (rulings v2 Part C, checks 3 and 6 added by owner request): per world x seed three arms, then the mechanical report.

Arms: ``spied`` (births on + record-only spy), ``plain`` (births on, no spy: its final hash must equal the spied arm's), ``control`` (the chance-0 twin, spied).
Refuses to start without ``--go <reference>``, the id of the lead-planner go for THIS run. Run under
``systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`` with PYTHONHASHSEED=0 and the main checkout's python. Deletes nothing.

HARD (any non-zero count fails; the report prints PASS/FAIL/STOP and never a judgement): K6, K6b, K8, W1-W5, 6a (``mismatch_total``), twin hash equality.
STOP: zero births in total, or zero regioned births (6a cannot be assessed). BALANCE, report only: everything else (check 3 tables and ratios, 6b rows, regionless births).
The report reads alive bodies from state through species_of(); it never reads population_young or any region cohort counter except in the 6b BALANCE rows.

Usage: python -m tools.rpg_measure.births_run --tree <fix tree> --out <dir> --go <ref> [--ticks 5000] [--jobs 2] [--worlds ...] [--seeds ...] [--cost-probe]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.rpg_measure import paired

CHILD = Path(__file__).resolve().with_name("births_child.py")
BARS = ("K6", "K6b", "K8", "W1", "W2", "W3", "W4", "W5")
ARMS = ("spied", "plain", "control")
COMBAT_CAUSE = "COMBAT"  # check 3 verdict: the per-capita rate is combat deaths per 1000 live entity-ticks
Key = Tuple[str, int, str]
BASES = {"6a": "mother's region (births' write rule)", "check3_probe_c": "newborn tile (the region at the newborn's position)"}
COHORT_FLAG_RULE = "a flag row when the cohort rises while live bodies == 0, or the cohort == 0 while live bodies rise (reported rows, not bars)"
PROBE_WORLD = "frontier_living_world"  # the largest gate world (55 bodies), so its cost bounds the other two
LIMITS = (
    "the twin-hash check proves the spy read-only in the births arm only; the chance-0 control arm is spied with no plain twin, and runs the same spy code",
    "every run is built under audit_mode and no_frame_pacing (births_child checks both flags and PINNED requires them); the counts are per-tick facts, not timing",
    "W4 is checked on the typed hunger update the births system returns, not on the mother's hunger after the tick (other phases move hunger on the same tick)",
)


def run_child(tree: Path, out: Path, world: str, seed: int, ticks: int, mode: str) -> Path:
    path = out / f"{world}_{seed}_{mode}.json"
    env = {**os.environ, "PYTHONHASHSEED": paired.HASHSEED, "PYTHONPATH": str(tree)}
    proc = subprocess.run([sys.executable, str(CHILD), world, str(seed), str(ticks), mode, str(path)], cwd=tree, env=env, capture_output=True, text=True)
    if proc.returncode != 0 or not path.exists():
        raise RuntimeError(f"births child failed ({mode} {world} {seed}): {proc.stderr.strip()[-400:]}")
    return path


def run_child_measured(tree: Path, out: Path, world: str, seed: int, ticks: int, mode: str) -> Dict[str, Any]:
    """The cost probe's child run: wall time and the child's own peak RSS (wait4's rusage, in MB), and the on-disk size of its output files."""
    path = out / f"{world}_{seed}_{mode}.json"
    env = {**os.environ, "PYTHONHASHSEED": paired.HASHSEED, "PYTHONPATH": str(tree)}
    started = time.perf_counter()
    proc = subprocess.Popen([sys.executable, str(CHILD), world, str(seed), str(ticks), mode, str(path)], cwd=tree, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    _, status, usage = os.wait4(proc.pid, 0)
    wall = time.perf_counter() - started
    positions = Path(str(path) + ".positions.json.gz")
    return {
        "mode": mode, "wall_s": round(wall, 1), "peak_rss_mb": round(usage.ru_maxrss / 1024.0, 1), "exit_status": os.waitstatus_to_exitcode(status),
        "json_bytes": path.stat().st_size if path.exists() else None, "positions_gz_bytes": positions.stat().st_size if positions.exists() else None,
    }


# ---- pure aggregations (unit-tested) -------------------------------------------------------------------------------------------------------------------
def mismatch_total(nudges: List[Dict[str, Any]]) -> int:
    """6a: the number of (region, tick) rows where the births system's write differs from the newborns it added there."""
    return sum(1 for row in nudges if row["mismatch"] != 0)


def per_capita_rate(deaths: List[Dict[str, Any]], live_entity_ticks: int, cause: str = COMBAT_CAUSE) -> Optional[float]:
    """Deaths of ``cause`` per 1000 live entity-ticks (None when no entity was ever alive)."""
    if live_entity_ticks <= 0:
        return None
    return 1000.0 * sum(1 for d in deaths if d["cause"] == cause) / live_entity_ticks


def ratio_verdict(ratios: Dict[int, Optional[float]]) -> str:
    """"holds" when every seed's head/control per-capita ratio is above 1, else "mixed" (a seed at or below 1, or with no ratio, makes it mixed)."""
    return "holds" if ratios and all(r is not None and r > 1 for r in ratios.values()) else "mixed"


def rate_ratio(head: Optional[float], control: Optional[float]) -> Optional[float]:
    """head/control; infinity when the control rate is 0 and the head's is above 0; None when both are 0 or either is missing."""
    if head is None or control is None:
        return None
    if control == 0:
        return float("inf") if head > 0 else None
    return head / control


def bar_status(total_births: int, regioned_births: int, bars: Dict[str, int], twin_equal: bool, mismatches: int) -> str:
    """PASS / FAIL / STOP, mechanically: STOP when no births or no regioned births exist (nothing to assess), FAIL on any bar count or a differing twin hash, else PASS."""
    if total_births == 0 or regioned_births == 0:
        return "STOP"
    if any(bars.values()) or not twin_equal or mismatches:
        return "FAIL"
    return "PASS"


def first_position_divergence(a: List[List[Any]], b: List[List[Any]]) -> Optional[Dict[str, Any]]:
    """Check 3 probe (b): the first tick where the original bodies' positions differ between two arms, and which ids differ."""
    for tick, (pa, pb) in enumerate(zip(a, b), start=1):
        if pa != pb:
            da, db = {r[0]: (r[1], r[2]) for r in pa}, {r[0]: (r[1], r[2]) for r in pb}
            return {"tick": tick, "ids": sorted(i for i in set(da) | set(db) if da.get(i) != db.get(i))}
    return None


def death_tables(docs: Dict[Key, dict]) -> Dict[str, Any]:
    """Check 3 tables per arm (spied = births, control): deaths per world x cause x seed (raw and per 1000 live entity-ticks), killer kind -> victim kind with newborn victims
    as their own row, and newborn involvement counts."""
    table: Dict[str, Any] = {"per_cause": {}, "kill_matrix": {}, "newborn_involvement": {}}
    for arm in ("spied", "control"):
        for (world, seed, mode), doc in sorted(docs.items()):
            if mode != arm:
                continue
            ent_ticks = doc["live_entity_ticks"]
            for cause, n in sorted(Counter(d["cause"] for d in doc["deaths"]).items()):
                table["per_cause"][f"{arm}|{world}|{cause}|{seed}"] = {"deaths": n, "per_1000_entity_ticks": 1000.0 * n / ent_ticks if ent_ticks else None}
            for d in doc["deaths"]:
                victim = "NEWBORN:" + d["victim_kind"] if d["victim_newborn"] else d["victim_kind"]
                key = f"{arm}|{d['killer_kind']}->{victim}"
                table["kill_matrix"][key] = table["kill_matrix"].get(key, 0) + 1
            inv = table["newborn_involvement"].setdefault(arm, {"killer_newborn": 0, "victim_newborn": 0})
            inv["killer_newborn"] += sum(1 for d in doc["deaths"] if d["killer_newborn"])
            inv["victim_newborn"] += sum(1 for d in doc["deaths"] if d["victim_newborn"])
    return table


def ratios_per_world(docs: Dict[Key, dict]) -> Dict[str, Any]:
    """Per world: for each seed the head/control combat per-capita ratio, the per-seed delta (head - control combat deaths), the sign column and the verdict."""
    out: Dict[str, Any] = {}
    worlds = sorted({w for (w, _, _) in docs})
    for world in worlds:
        seeds = sorted({s for (w, s, m) in docs if w == world and m == "spied"})
        ratios: Dict[int, Optional[float]] = {}
        rows = []
        for seed in seeds:
            head, ctrl = docs[(world, seed, "spied")], docs[(world, seed, "control")]
            rh = per_capita_rate(head["deaths"], head["live_entity_ticks"])
            rc = per_capita_rate(ctrl["deaths"], ctrl["live_entity_ticks"])
            ratio = rate_ratio(rh, rc)
            ratios[seed] = ratio
            delta = sum(1 for d in head["deaths"] if d["cause"] == COMBAT_CAUSE) - sum(1 for d in ctrl["deaths"] if d["cause"] == COMBAT_CAUSE)
            rows.append({"seed": seed, "head_rate": rh, "control_rate": rc, "ratio": ratio, "combat_delta": delta, "sign": "+" if delta > 0 else "-" if delta < 0 else "0"})
        out[world] = {"rows": rows, "verdict": ratio_verdict(ratios)}
    return out


def cohort_summary(docs: Dict[Key, dict]) -> Dict[str, Any]:
    """Check 6: 6a (the bar) from the births' own writes, apply-side exactness and collisions, regionless births with tiles, and the 6b divergence flags."""
    spied = {k: d for k, d in docs.items() if k[2] == "spied"}
    nudges = [r for d in spied.values() for r in d["nudges"]]
    applied = [r for d in spied.values() for r in d["applied_cohorts"]]
    return {
        "mismatch_total": mismatch_total(nudges),
        "regioned_births": sum(r["written"] for r in nudges),
        "same_tick_collisions_with_rebuild": sum(1 for r in applied if r["collision_with_rebuild"]),
        "apply_inexact": sum(1 for r in applied if not r["exact"]),
        "regionless_births": {f"{w}/{s}": d["regionless"] for (w, s, _), d in sorted(spied.items()) if d["regionless"]},
        "cohort_flags": {f"{w}/{s}": d["cohort_flags"] for (w, s, _), d in sorted(spied.items()) if d["cohort_flags"]},
        "calamity_note": next((d["calamity_note"] for d in spied.values()), None),
    }


def summarise(docs: Dict[Key, dict]) -> dict:
    spied = {(w, s): d for (w, s, m), d in docs.items() if m == "spied"}
    twins = {(w, s): docs.get((w, s, "plain")) for (w, s) in spied}
    bars = {bar: sum(d["bars"][bar] for d in spied.values()) for bar in BARS}
    twin_equal = all((twins[k] or {}).get("final_hash") == d["final_hash"] for k, d in spied.items())
    cohort = cohort_summary(docs)
    total_births = sum(sum(d["births_by_kind"].values()) for d in spied.values())
    return {
        "bars": bars, "twin_hash_equal": {f"{w}/{s}": (twins[(w, s)] or {}).get("final_hash") == d["final_hash"] for (w, s), d in sorted(spied.items())},
        "pinned": sorted({d["runner"] for d in docs.values()}), "total_births": total_births,
        "births_by_world_seed_kind": {f"{w}/{s}": d["births_by_kind"] for (w, s), d in sorted(spied.items())},
        "max_entity_id": max((d["max_entity_id_seen"] for d in spied.values()), default=0), "runs": len(docs),
        "check6": cohort, "check3": {"tables": death_tables(docs), "ratios": ratios_per_world(docs)},
        "bar_status": bar_status(total_births, cohort["regioned_births"], bars, twin_equal, cohort["mismatch_total"]),
    }


def divergence_report(out: Path, docs: Dict[Key, dict]) -> Dict[str, Any]:
    """Check 3 probe (b), from the positions files: per world x seed the first tick where births and control disagree for an original body."""
    rep = {}
    for (w, s, m) in sorted(docs):
        if m != "spied":
            continue
        loaded = {}
        for arm in ("spied", "control"):
            with gzip.open(out / f"{w}_{s}_{arm}.json.positions.json.gz", "rt", encoding="utf-8") as fh:
                loaded[arm] = json.load(fh)
        rep[f"{w}/{s}"] = first_position_divergence(loaded["spied"], loaded["control"])
    return rep


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--go", required=True, help="reference of the lead-planner go for this run")
    ap.add_argument("--ticks", type=int, default=paired.TICKS)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--cost-probe", action="store_true", help=f"one world ({PROBE_WORLD}) x one seed x the three arms, one at a time: print wall time, peak RSS and the .positions.json.gz sizes, nothing else")
    ap.add_argument("--worlds", nargs="*", default=list(paired.WORLDS))
    ap.add_argument("--seeds", nargs="*", type=int, default=list(paired.SEEDS))
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.cost_probe:
        rows = [run_child_measured(args.tree, args.out, PROBE_WORLD, args.seeds[0], args.ticks, mode) for mode in ARMS]
        report = {"cost_probe": rows, "world": PROBE_WORLD, "seed": args.seeds[0], "ticks": args.ticks, "go": args.go, "scope_cap_mb": 3072}
        (args.out / "cost_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    keys: List[Key] = [(w, s, m) for w in args.worlds for s in args.seeds for m in ARMS]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        paths = list(pool.map(lambda k: run_child(args.tree, args.out, k[0], k[1], args.ticks, k[2]), keys))
    docs = {k: json.loads(p.read_text(encoding="utf-8")) for k, p in zip(keys, paths)}
    summary = {**summarise(docs), "first_position_divergence": divergence_report(args.out, docs), "limits": list(LIMITS), "bases": BASES, "cohort_flag_rule": COHORT_FLAG_RULE, "go": args.go, "ticks": args.ticks}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
