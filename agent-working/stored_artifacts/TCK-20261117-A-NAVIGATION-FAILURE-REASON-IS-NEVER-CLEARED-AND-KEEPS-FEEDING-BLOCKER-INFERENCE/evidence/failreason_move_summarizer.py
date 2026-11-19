#!/usr/bin/env python3
"""Stale-failure-reason RERUN summarizer (DRAFT for designer sha approval; NOT run). Read-only: reads <spy-dir>/*_s42_spy.json, <spy-dir>/driver.log and <twin-dir>/*_s42_plain.json; writes stdout only.
Both dirs are REQUIRED arguments (no defaults, no hard-coded paths). It prints the exact command line, then `INPUT <sha256> <path>` for EVERY input file, before any verdict.
Bars exactly per rpg-designer-stalereason-rerun-bars.md (sha256 6771e32f...), per cell unless stated:
  HARD  L1 = 0, M1 = 0, M2 = 0 (every non-None reason left after a move has a same-tick writer), R2 = 0.
  HARD  not vacuous: reasons_set >= 1, reasons_cleared >= 1, l1_calls >= 1 per cell; and across the three cells each move kind (step, swap, yield) seen >= 1.
  HARD  validity: spy process rc 0 (driver.log line '<world> s42 spy rc=0') and driver_rc=0 (the runner stops on a failed plain twin, so driver_rc=0 covers all 6 processes), PINNED, logging_errors 0,
        exceptions {}, match true, spy final_hash == the plain twin's final_hash (from --twin-dir), hook coverage lists no missing target.
  REPORTED  action-code rows after a move per primary writer and per code, yields and swaps per cell, OCCUPANCY_CONFLICT rejections, moves without an attributed kind, v1 R1 / R3 counts and rows
        (resolve_move-only, NOT bars), the blockers filed.
Exit 0 only if every hard bar holds; 1 on any hard-bar failure; 2 on a missing input file (nothing is judged then).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

W = ["frontier_living_world", "urban_political", "crowded_frontier"]
KINDS = ("step", "swap", "yield")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(spy_dir, twin_dir):
    s, t = Path(spy_dir), Path(twin_dir)
    print("command:", " ".join(sys.argv))
    files = [s / f"{w}_s42_spy.json" for w in W] + [s / "driver.log"] + [t / f"{w}_s42_plain.json" for w in W]
    missing = [f for f in files if not f.exists()]
    for f in files:
        print("INPUT", sha(f) if f.exists() else "MISSING", f.resolve() if f.exists() else f)
    if missing:
        print("RESULT: MISSING INPUT FILE(S), nothing judged:", ", ".join(str(m) for m in missing))
        return 2
    drv = (s / "driver.log").read_text()
    ok = True
    kinds_total = dict.fromkeys(KINDS, 0)
    for w in W:
        d = json.loads((s / f"{w}_s42_spy.json").read_text())
        p = json.loads((t / f"{w}_s42_plain.json").read_text())
        b, rep = d["bars"], d["reported"]
        counts = rep["counts"]
        mv = b["moves"]
        for k in KINDS:
            kinds_total[k] += mv[k]
        cov_missing = rep.get("hook_coverage", {}).get("missing", ["no hook_coverage in the file"])
        bars = {
            "L1_0": b["L1_post_ne_expected"] == 0,
            "M1_0": b["M1_moved_with_unattributed_code"] == 0,
            "M2_0": b["M2_moved_with_code_no_writer"] == 0,
            "R2_0": b["R2_blocker_filed_after_move"] == 0,
            "reasons_set_ge1": b["reasons_set"] >= 1,
            "reasons_cleared_ge1": b["reasons_cleared"] >= 1,
            "l1_calls_ge1": counts.get("l1_calls", 0) >= 1,
            "spy_rc0": f"{w} s42 spy rc=0" in drv,
            "driver_rc0": "driver_rc=0" in drv,
            "PINNED": d["pinned"] == "PINNED",
            "logging_errors0": d["logging_errors"] == 0,
            "exceptions_empty": d["exceptions"] == {},
            "match_true": d["match"] is True,
            "hash_equals_plain_in_twin_dir": d["final_hash"] == p["final_hash"],
            "no_missing_hook": cov_missing == [],
        }
        ok &= all(bars.values())
        print(f"== {w}: bars {bars}")
        print(f"   L1 {b['L1_post_ne_expected']} (l1_calls {counts.get('l1_calls', 0)})  M1 {b['M1_moved_with_unattributed_code']}  M2 {b['M2_moved_with_code_no_writer']}  R2 {b['R2_blocker_filed_after_move']}"
              f"  reasons_set {b['reasons_set']}  reasons_cleared {b['reasons_cleared']}")
        print(f"   moves {mv}  yields_proposed {counts.get('yields_proposed', 0)}  swaps_proposed {counts.get('swaps_proposed', 0)}  occupancy_conflict_rejections {counts.get('occupancy_conflict_rejections', 0)}"
              f"  moves_without_kind {counts.get('moves_without_kind', 0)}  lodging_position_changes_excluded {counts.get('position_changes_lodging_excluded', 0)}")
        print("   action codes after a move, by primary writer:", rep["action_codes_after_a_move_by_primary_writer"], " by code:", rep["action_codes_after_a_move_by_code"])
        print(f"   v1 (not bars): R1 {counts.get('r1_violations', 0)} of {counts.get('success_steps_scanned', 0)} success steps, R3 {counts.get('r3_violations', 0)} of {counts.get('failed_steps_scanned', 0)} failed steps;"
              f" blockers filed: {rep['blockers_filed_by_infer_blockers']}")
        for k in ("l1_rows", "m1_rows", "m2_rows", "r2_rows"):
            for r in b[k][:20]:
                print("   ", k, r)
        for r in rep["v1_r1_rows"][:5]:
            print("    v1_r1_rows", r)
        for r in rep["v1_r3_rows"][:5]:
            print("    v1_r3_rows", r)
    kinds_ok = all(kinds_total[k] >= 1 for k in KINDS)
    print(f"== across cells: moves by kind {kinds_total}  each kind >= 1: {kinds_ok}")
    ok &= kinds_ok
    print("RESULT:", "ALL HARD BARS HOLD" if ok else "FAIL (a hard bar missed)")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="failure-reason rerun summarizer: read-only; both input dirs are required")
    ap.add_argument("--spy-dir", required=True)
    ap.add_argument("--twin-dir", required=True)
    a = ap.parse_args()
    sys.exit(main(a.spy_dir, a.twin_dir))
