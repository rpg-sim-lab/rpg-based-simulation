"""Summarize the K2/K3 re-count cells (reads the cell JSONs of ``k2k3_count_spy``; evidence only, no verdict about the sim beyond the designer's fixed close rules).

Usage: python k2k3_count_summary.py <stage-1 out dir> [<stage-2 out dir>]  ->  prints the table and writes k2k3_summary.json into the last dir. Exit 0 only when every cell is valid.
A cell is VOID unless: spy final_hash == plain final_hash, 0 probe errors / spy exceptions / logging errors, no field finding, and reach (>= 1 service dispatch AND >= 1 escalated-need decision).
Close rules (the designer's, 992b7ce3 + Amendment 1 e6cc644c): K2 = 0 in the four stage-1 cells (three s42 + urban_political s46) AND no service action NOT MEASURED -> proposed for close; any K2 count > 0 -> stays HARD. K3: a nonzero s42 total stays HARD;
a close needs K3 = 0 in all 7 cells (A3: the three s42 cells plus frontier_living_world s43-46, stage 2, run only when the s42 total is 0). `close_verdicts` (k2k3_count_logic) can never print a K3 close with fewer than 7 valid cells.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

STAGE1 = [("crowded_frontier", 42), ("frontier_living_world", 42), ("urban_political", 42), ("urban_political", 46)]
STAGE2 = [("frontier_living_world", 43), ("frontier_living_world", 44), ("frontier_living_world", 45), ("frontier_living_world", 46)]   # A3: K3's pooled evidence seeds; their K2 is reported and decides nothing
CELLS = STAGE1 + STAGE2
K3_S42 = [("crowded_frontier", 42), ("frontier_living_world", 42), ("urban_political", 42)]


def load(outs: Any, world: str, seed: int, mode: str) -> Dict[str, Any]:
    """The cell JSON from the first of ``outs`` (a dir or a list of dirs: stage 1 and stage 2 are separate OUT dirs) that has it."""
    for out in ([outs] if isinstance(outs, Path) else outs):
        path = Path(out) / f"{world}_s{seed}_{mode}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def cell_validity(plain: Dict[str, Any], spy: Dict[str, Any], needs_k2: bool = True) -> List[str]:
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
    if reach.get("escalated_need_wins", 0) < 1:
        problems.append("reach: no escalated-need decision seen")
    if needs_k2:
        if reach.get("service_dispatches_seen", 0) < 1:
            problems.append("reach: no service dispatch seen")
        if reach.get("router_service_calls", 0) < 1:
            problems.append("fire control: the router pass-through saw no service call (A2 channel did not fire)")
    return problems


def summarize(out: Any) -> Dict[str, Any]:
    cells: Dict[str, Any] = {}
    verdict_cells: List[Dict[str, Any]] = []
    for stage, group in ((1, STAGE1), (2, STAGE2)):
        for world, seed in group:
            plain, spy = load(out, world, seed, "plain"), load(out, world, seed, "spy")
            if stage == 2 and not plain and not spy:
                continue                                                  # stage 2 not run (only when the s42 total is 0)
            problems = cell_validity(plain, spy, needs_k2=stage == 1)
            name = f"{world}_s{seed}"
            entry: Dict[str, Any] = {"world": world, "seed": seed, "stage": stage, "valid": not problems, "problems": problems, "plain_hash": plain.get("final_hash"), "spy_hash": spy.get("final_hash")}
            if spy:
                entry.update({"k2": spy.get("k2"), "k3": spy.get("k3"), "k3_if_acting_threat_test": spy.get("k3_if_acting_threat_test"), "reach": spy.get("reach"), "loss_rows": spy.get("loss_rows", []),
                              "dispatch_visibility": spy.get("dispatch_visibility"), "decision_policy": spy.get("decision_policy"), "service_actions_read": spy.get("service_actions_read"),
                              "action_census_with_building_target": spy.get("action_census_with_building_target"), "delivered_channel_counts": spy.get("delivered_channel_counts"),
                              "refusal_reasons_seen": spy.get("refusal_reasons_seen")})
            cells[name] = entry
            k2, k3 = spy.get("k2") or {}, spy.get("k3") or {}
            verdict_cells.append({"name": name, "world": world, "seed": seed, "stage": stage, "valid": not problems, "k2_count_measured": k2.get("k2_count_measured", 0),
                                  "k2_not_measured": k2.get("not_measured_actions", []), "k3_count": k3.get("k3_count", 0)})
    logic = load_logic()
    verdicts = logic.close_verdicts(verdict_cells)
    return {"cells": cells, "all_valid": all(c["valid"] for c in cells.values()), "verdicts": verdicts, "rule_source": logic.RULE_SOURCE}


def load_logic() -> Any:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_k2k3_summary_logic", Path(__file__).resolve().with_name("k2k3_count_logic.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: List[str]) -> int:
    outs = [Path(a) for a in argv]                      # stage-1 dir first, then the stage-2 dir when it exists; the summary is written into the LAST one
    out = outs[-1]
    doc = summarize(outs)
    (out / "k2k3_summary.json").write_text(json.dumps(doc, sort_keys=True, indent=1, default=str), encoding="utf-8")
    for name, cell in doc["cells"].items():
        k2, k3 = cell.get("k2") or {}, cell.get("k3") or {}
        print(f"{name} (stage {cell['stage']}): valid={cell['valid']} K2={k2.get('k2_count_measured')} not_measured={k2.get('not_measured_actions')} (runs {k2.get('runs_all')}, >10 {k2.get('runs_over_10')}, >100 {k2.get('runs_over_100')}) "
              f"K3={k3.get('k3_count')} {json.dumps({n: v.get('decisions') for n, v in (k3.get('per_need') or {}).items()})} problems={cell['problems']}")
    print(f"rule: {doc['rule_source']}; K2: {doc['verdicts']['k2']}; K3: {doc['verdicts']['k3']}; all_valid={doc['all_valid']}")
    return 0 if doc["all_valid"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
