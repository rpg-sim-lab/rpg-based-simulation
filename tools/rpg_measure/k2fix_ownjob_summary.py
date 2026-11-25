"""Summarize the K2 fix own-job cells (reads the JSONs of ``k2fix_ownjob_spy``; evidence plus the designer's fixed verdict rules, nothing else).

Usage: python k2fix_ownjob_summary.py <OUT dir>  ->  prints the table and writes <OUT>/k2fix_ownjob_summary.json. Exit 0 only when every cell is valid and no STOP/FAIL line applies.
Layout: <OUT>/<arm>/<world>_s<seed>_t<ticks>_{plain,spy}.json for arm in main, fix.
Rules (rpg-designer-k2-fix-plan-rulings.md a73bc655d487395b): A(i) WAY_CLOSED ends from the purse half; A(ii) report-only; B(i) blockers filed; B(ii) FALSE FIRES must be 0; B(iii) STILL LOOPING must be 0;
(iv) NEUTRALITY: in a cell where A(i) (purse half) = 0 AND B(i) = 0 AND other_unresolved = 0 the fix's final hash must EQUAL main's, else STOP (with any other_unresolved the cell is NOT MEASURED for A, never neutral); a cell is VOID unless the spy final_hash equals its plain twin's on both arms.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CELLS = [("crowded_frontier", 42, 5000), ("frontier_living_world", 42, 5000), ("urban_political", 42, 5000), ("urban_political", 42, 2400)]


def load(out: Path, arm: str, world: str, seed: int, ticks: int, mode: str) -> Dict[str, Any]:
    path = out / arm / f"{world}_s{seed}_t{ticks}_{mode}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def arm_validity(plain: Dict[str, Any], spy: Dict[str, Any]) -> List[str]:
    if not plain or not spy:
        return ["plain or spy cell missing"]
    problems = []
    if plain.get("fatal") or spy.get("fatal") or spy.get("spy_exceptions") or spy.get("findings") or plain.get("logging_errors") or spy.get("logging_errors"):
        problems.append("fatal / spy exception / finding / logging error")
    if spy.get("final_hash") != plain.get("final_hash"):
        problems.append("spy final_hash != plain final_hash")
    return problems


def cell_summary(out: Path, world: str, seed: int, ticks: int) -> Dict[str, Any]:
    arms = {arm: (load(out, arm, world, seed, ticks, "plain"), load(out, arm, world, seed, ticks, "spy")) for arm in ("main", "fix")}
    problems = {arm: arm_validity(*docs) for arm, docs in arms.items()}
    valid = not any(problems.values())
    fix, main = arms["fix"][1], arms["main"][1]
    a_i = (fix.get("A_i") or {}).get("purse_half", 0)
    unresolved = {arm: ((arms[arm][1].get("A_i") or {}).get("other_unresolved", 0)) for arm in ("main", "fix")}
    b_i = (fix.get("B_i") or {}).get("filed", 0)
    main_hash, fix_hash = arms["main"][0].get("final_hash"), arms["fix"][0].get("final_hash")
    flags: List[str] = []
    if valid:
        if (fix.get("B_ii_false_fires") or 0) > 0:
            flags.append("FAIL: B(ii) false fires > 0")
        if isinstance(fix.get("B_iii_still_looping"), int) and fix["B_iii_still_looping"] > 0:
            flags.append("FAIL: B(iii) still looping > 0 (a finding to the designer: ways_in_reach reading the blocker is the next step)")
        if unresolved["fix"] or unresolved["main"]:
            flags.append(f"NOT MEASURED: A(i): {unresolved['fix']} fix and {unresolved['main']} main WAY_CLOSED ends name no building (other_unresolved); neutrality is not judged")
        elif a_i == 0 and b_i == 0 and main_hash != fix_hash:
            flags.append("STOP: neutrality: A(i) = 0 and B(i) = 0 but the fix hash differs from main (the fix leaks)")
        not_readable = fix.get("B_iii_not_readable_for")
        if not_readable:
            flags.append(f"NOT MEASURED: B(iii) is not readable for {', '.join(not_readable)} (the router channel covers EAT and REST only)")
    return {"cell": f"{world}_s{seed}_t{ticks}", "valid": valid, "problems": problems, "main_hash": main_hash, "fix_hash": fix_hash, "hash_equal": main_hash == fix_hash,
            "A_i_purse_half": a_i, "A_i_unresolved": unresolved, "A_i_bed_half_fix": (fix.get("A_i") or {}).get("bed_half"), "A_i_bed_half_main": (main.get("A_i") or {}).get("bed_half"), "B_i": b_i, "B_i_by_action": (fix.get("B_i") or {}).get("by_action"),
            "B_ii_false_fires": fix.get("B_ii_false_fires"), "B_iii_still_looping": fix.get("B_iii_still_looping"), "sleep_debt_98_main": (main.get("A_ii") or {}).get("subjects_at_sleep_debt_98"),
            "sleep_debt_98_fix": (fix.get("A_ii") or {}).get("subjects_at_sleep_debt_98"), "A_i_resolved_by": (fix.get("A_i") or {}).get("resolved_by"), "A_ii_follow_ups": (fix.get("A_ii") or {}).get("follow_ups"), "A_ii_collapse_windows_main": (main.get("A_ii") or {}).get("collapse_windows"), "A_ii_collapse_windows_fix": (fix.get("A_ii") or {}).get("collapse_windows"), "vi": fix.get("vi"), "flags": flags}


def summarize(out: Path) -> Dict[str, Any]:
    cells = [cell_summary(out, *c) for c in CELLS]
    flags = [f"{c['cell']}: {f}" for c in cells for f in c["flags"]]
    return {"cells": cells, "all_valid": all(c["valid"] for c in cells), "flags": flags}


def main(argv: List[str]) -> int:
    out = Path(argv[0])
    doc = summarize(out)
    (out / "k2fix_ownjob_summary.json").write_text(json.dumps(doc, sort_keys=True, indent=1, default=str), encoding="utf-8")
    for c in doc["cells"]:
        print(f"{c['cell']}: valid={c['valid']} A(i) purse_half={c['A_i_purse_half']} unresolved={c['A_i_unresolved']} (bed_half fix={c['A_i_bed_half_fix']} main={c['A_i_bed_half_main']}) B(i)={c['B_i']} {c['B_i_by_action']} "
              f"false_fires={c['B_ii_false_fires']} still_looping={c['B_iii_still_looping']} sleep98 main={c['sleep_debt_98_main']} fix={c['sleep_debt_98_fix']} hash_equal={c['hash_equal']} problems={c['problems']}")
    for f in doc["flags"]:
        print(f)
    print(f"all_valid={doc['all_valid']} flags={len(doc['flags'])}")
    return 0 if doc["all_valid"] and not doc["flags"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
