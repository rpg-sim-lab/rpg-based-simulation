"""Summarize the K3 own-job cells (reads the JSONs of ``k3_switch_spy``; the designer's fixed counts, rpg-designer-k3-plan-rulings.md 972600b6...).

Usage: python k3_switch_summary.py <OUT dir> <base OUT dir with the base-head plain hashes: <cell>_base_plain.json>  -> prints the table, writes <OUT>/k3_switch_summary.json. Exit 0 only when every cell is valid and no bar fails.
VOID: spy final_hash != plain final_hash, a fatal/finding/spy exception/logging error. (i) FIRES and TAKEN by need and current kind; (iii) TAKEN under a present threat must be 0 (FAIL otherwise);
(iv) NEUTRALITY: a cell with TAKEN = 0 must hash EQUAL to the base head's plain hash (STOP otherwise); (v) report-only: ticks current after a fire, the suspended project's fate, hunger >= 95 / sleep_debt >= 98 subjects, the guard list.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CELLS = [("crowded_frontier", 42, 5000), ("frontier_living_world", 42, 5000), ("urban_political", 42, 5000), ("urban_political", 42, 2400)]


def load(out: Path, world: str, seed: int, ticks: int, mode: str) -> Dict[str, Any]:
    path = out / f"{world}_s{seed}_t{ticks}_{mode}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def cell_summary(out: Path, base: Path, world: str, seed: int, ticks: int) -> Dict[str, Any]:
    plain, spy, basep = load(out, world, seed, ticks, "plain"), load(out, world, seed, ticks, "spy"), load(base, world, seed, ticks, "plain")
    problems: List[str] = []
    if not plain or not spy:
        problems.append("plain or spy cell missing")
    else:
        if plain.get("fatal") or spy.get("fatal") or spy.get("spy_exceptions") or spy.get("findings") or plain.get("logging_errors") or spy.get("logging_errors"):
            problems.append("fatal / spy exception / finding / logging error")
        if spy.get("final_hash") != plain.get("final_hash"):
            problems.append("spy final_hash != plain final_hash")
    bars: Dict[str, Any] = {}
    if not problems:
        taken = int(spy.get("taken", 0))
        bars["iii_taken_under_present_threat"] = {"count": spy.get("taken_under_present_threat"), "ok": spy.get("taken_under_present_threat") == 0}
        if taken == 0:
            bars["iv_neutrality"] = {"fix_hash": plain.get("final_hash"), "base_hash": basep.get("final_hash"), "ok": bool(basep) and plain.get("final_hash") == basep.get("final_hash")}
    rows = spy.get("rows") or []
    return {"cell": f"{world}_s{seed}_t{ticks}", "valid": not problems, "problems": problems, "plain_hash": plain.get("final_hash"), "base_hash": basep.get("final_hash"), "taken": spy.get("taken"), "fires": spy.get("fires"),
            "taken_by_need_and_current_kind": spy.get("taken_by_need_and_current_kind"), "fires_by_need_and_current_kind": spy.get("fires_by_need_and_current_kind"), "taken_under_acting_threat": spy.get("taken_under_acting_threat"),
            "bars": bars, "guard_rows": spy.get("guard_rows"), "reached_counts": {k: len(v) for k, v in (spy.get("reached") or {}).items()}, "reached": spy.get("reached"),
            "ticks_current_after_fire": sorted(r["ticks_current"] for r in rows), "suspended_fate": [{"subject": r["subject"], "tick": r["tick"], "fate": r.get("suspended_fate")} for r in rows], "calls": spy.get("calls")}


def main(argv: List[str]) -> int:
    out, base = Path(argv[0]), Path(argv[1])
    cells = [cell_summary(out, base, *c) for c in CELLS if load(out, *c, "plain") or load(out, *c, "spy")]
    (out / "k3_switch_summary.json").write_text(json.dumps({"cells": cells}, sort_keys=True, indent=1, default=str), encoding="utf-8")
    bad = False
    for c in cells:
        failed = [k for k, b in c["bars"].items() if not b["ok"]]
        bad = bad or not c["valid"] or bool(failed)
        print(f"{c['cell']}: valid={c['valid']} taken={c['taken']} fires={c['fires']} by_kind={c['fires_by_need_and_current_kind']} threat_taken={c['bars'].get('iii_taken_under_present_threat')} neutrality={c['bars'].get('iv_neutrality')} "
              f"guard_rows={len(c['guard_rows'] or [])} reached={c['reached_counts']} failed_bars={failed} problems={c['problems']}")
    return 2 if bad or not cells else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
