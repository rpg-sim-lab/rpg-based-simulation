"""Summarize the K2/K3 re-count cells (reads the cell JSONs of ``k2k3_count_spy``; evidence only, no verdict about the sim beyond the designer's fixed close rules).

Usage: python k2k3_count_summary.py <out dir>  ->  prints the table and writes <out dir>/k2k3_summary.json. Exit 0 only when every cell is valid.
A cell is VOID unless: spy final_hash == plain final_hash, 0 probe errors / spy exceptions / logging errors, no field finding, and reach (>= 1 service dispatch AND >= 1 escalated-need decision).
Close rules (the designer's): K2 = 0 in all three s42 cells AND urban_political s46 -> the ticket is proposed for close; any K2 count > 0 -> stays HARD. K3 = 0 in all three cells -> proposed for close; any > 0 -> stays HARD.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CELLS = [("crowded_frontier", 42), ("frontier_living_world", 42), ("urban_political", 42), ("urban_political", 46)]
K3_CELLS = [c for c in CELLS if c[1] == 42]       # K3's evidence set is the three s42 cells (the spec: "K3 = 0 in all three cells"); s46 is K2's seed rule
K2_CELLS = CELLS


def load(out: Path, world: str, seed: int, mode: str) -> Dict[str, Any]:
    path = out / f"{world}_s{seed}_{mode}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def cell_validity(plain: Dict[str, Any], spy: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    if not plain:
        return ["plain twin missing"]
    if not spy:
        return ["spy cell missing"]
    if plain.get("fatal") or spy.get("fatal"):
        problems.append("fatal exception")
    if spy.get("final_hash") != plain.get("final_hash"):
        problems.append("spy final_hash != plain final_hash")
    if spy.get("probe_errors") or spy.get("spy_exceptions") or spy.get("logging_errors") or plain.get("logging_errors"):
        problems.append("probe errors / spy exceptions / logging errors")
    if spy.get("findings"):
        problems.append("field findings: " + "; ".join(spy["findings"]))
    reach = spy.get("reach") or {}
    if reach.get("service_dispatches_seen", 0) < 1:
        problems.append("reach: no service dispatch seen")
    if reach.get("escalated_need_wins", 0) < 1:
        problems.append("reach: no escalated-need decision seen")
    return problems


def summarize(out: Path) -> Dict[str, Any]:
    cells: Dict[str, Any] = {}
    for world, seed in CELLS:
        plain, spy = load(out, world, seed, "plain"), load(out, world, seed, "spy")
        problems = cell_validity(plain, spy)
        entry: Dict[str, Any] = {"world": world, "seed": seed, "valid": not problems, "problems": problems, "plain_hash": plain.get("final_hash"), "spy_hash": spy.get("final_hash")}
        if spy:
            entry.update({"k2": spy.get("k2"), "k3": spy.get("k3"), "k3_if_acting_threat_test": spy.get("k3_if_acting_threat_test"), "reach": spy.get("reach"), "loss_rows": spy.get("loss_rows", []),
                          "service_actions_read": spy.get("service_actions_read"), "action_census_with_building_target": spy.get("action_census_with_building_target"),
                          "delivered_channel_counts": spy.get("delivered_channel_counts"), "refusal_reasons_seen": spy.get("refusal_reasons_seen")})
        cells[f"{world}_s{seed}"] = entry
    all_valid = all(c["valid"] for c in cells.values())
    k2_total = sum((cells[f"{w}_s{s}"].get("k2") or {}).get("k2_count", 0) for w, s in K2_CELLS)
    k3_total = sum((cells[f"{w}_s{s}"].get("k3") or {}).get("k3_count", 0) for w, s in K3_CELLS)
    return {"cells": cells, "all_valid": all_valid, "k2_count_all_cells": k2_total, "k3_count_s42_cells": k3_total,
            "k2_rule": "0 in all three s42 cells AND urban_political s46 -> propose close (post-2.224); any > 0 stays HARD" if all_valid else "VOID: a cell is invalid, no rule applied",
            "k3_rule": "0 in all three cells -> propose close (post-#995/#996); any > 0 stays HARD" if all_valid else "VOID: a cell is invalid, no rule applied"}


def main(argv: List[str]) -> int:
    out = Path(argv[0])
    doc = summarize(out)
    (out / "k2k3_summary.json").write_text(json.dumps(doc, sort_keys=True, indent=1, default=str), encoding="utf-8")
    for name, cell in doc["cells"].items():
        k2, k3 = cell.get("k2") or {}, cell.get("k3") or {}
        print(f"{name}: valid={cell['valid']} K2={k2.get('k2_count')} (runs {k2.get('runs_all')}, >10 {k2.get('runs_over_10')}, >100 {k2.get('runs_over_100')}, dispatch subjects {k2.get('subjects_with_dispatch')}, alive subject-ticks {k2.get('alive_subject_ticks')}) "
              f"K3={k3.get('k3_count')} {json.dumps({n: v.get('decisions') for n, v in (k3.get('per_need') or {}).items()})} problems={cell['problems']}")
    print(f"K2 all cells = {doc['k2_count_all_cells']}; K3 s42 cells = {doc['k3_count_s42_cells']}; all_valid={doc['all_valid']}")
    return 0 if doc["all_valid"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
