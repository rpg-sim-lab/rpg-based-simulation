"""Summarize the K3 Phase 0 cell (reads the JSONs of ``k3_phase0_spy``; evidence plus the designer's fixed rules, nothing else; rpg-designer-k3-plan-rulings.md 972600b672863882...).

Usage: python k3_phase0_summary.py <OUT dir>  ->  prints the class table and writes <OUT>/k3_phase0_summary.json. Exit 0 only when the cell is valid, the baseline hash matches and there is no HARD flag.
Rules: VOID unless spy final_hash == plain final_hash and there is no exception or finding; BASELINE: the plain final_hash of urban_political s42 2,400 t at the K3 base head must equal 2a6e74f0 (282b25981's) for the 30-loss baseline to carry over, else
"re-count K3 with kit v6 STAGE=neg first"; classes D1 (lawful end, the need met) leaves K3 (baseline 30 - n(D1)), D2 listed by reason (ruled per reason by the designer), D3 cleared without an end; HARD when a subject has 3+ consecutive D3 escalated decisions at hunger >= 95.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CELL = ("urban_political", 42, 2400)
BASELINE_HASH = "2a6e74f04cd735a15215a19d34f099a01d006cff6ee571627dd06372a801fbbd"     # the plain final_hash at 282b25981 (run 2, kit v6 neg); the 30-loss baseline was counted there
BASELINE_LOSSES = 30


def load(out: Path, mode: str) -> Dict[str, Any]:
    world, seed, ticks = CELL
    path = out / f"{world}_s{seed}_t{ticks}_{mode}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def summarize(out: Path) -> Dict[str, Any]:
    plain, spy = load(out, "plain"), load(out, "spy")
    problems: List[str] = []
    if not plain or not spy:
        problems.append("plain or spy cell missing")
    else:
        if plain.get("fatal") or spy.get("fatal") or spy.get("spy_exceptions") or spy.get("findings") or plain.get("logging_errors") or spy.get("logging_errors"):
            problems.append("fatal / spy exception / finding / logging error")
        if spy.get("final_hash") != plain.get("final_hash"):
            problems.append("spy final_hash != plain final_hash")
    classes = spy.get("classes") or {}
    baseline_ok = plain.get("final_hash") == BASELINE_HASH
    flags: List[str] = []
    if plain and not baseline_ok:
        flags.append(f"BASELINE: the plain final_hash {plain.get('final_hash')} differs from {BASELINE_HASH}: the 30-loss baseline does NOT carry over; re-count K3 with kit v6 STAGE=neg on a fresh archive first")
    if spy.get("hard_d3_cycles"):
        flags.append(f"HARD: {len(spy['hard_d3_cycles'])} subject cycle(s) of 3+ consecutive D3 decisions at hunger >= 95 (a pressing need that cannot stay current): back to the designer for scope")
    return {"cell": "%s_s%d_t%d" % CELL, "valid": not problems, "problems": problems, "plain_hash": plain.get("final_hash"), "spy_hash": spy.get("final_hash"), "baseline_ok": baseline_ok, "classes": classes,
            "d2_by_reason": spy.get("d2_by_reason"), "baseline_after_d1": BASELINE_LOSSES - int(classes.get("D1", 0)), "hard_d3_cycles": spy.get("hard_d3_cycles"), "threat_at_decision": spy.get("threat_at_decision"),
            "reach": spy.get("reach"), "rows": spy.get("rows"), "flags": flags}


def main(argv: List[str]) -> int:
    out = Path(argv[0])
    doc = summarize(out)
    (out / "k3_phase0_summary.json").write_text(json.dumps(doc, sort_keys=True, indent=1, default=str), encoding="utf-8")
    print(f"{doc['cell']}: valid={doc['valid']} baseline_ok={doc['baseline_ok']} classes={doc['classes']} d2_by_reason={doc['d2_by_reason']} baseline_after_d1={doc['baseline_after_d1']} problems={doc['problems']}")
    for row in doc["rows"] or []:
        print(f"  subject {row['subject']} t{row['tick']} {row['need']} {row['class']}: project {row['before']['current_project_id']} -> current {row['after']['current_project_id']!r} status {(row['after']['project'] or {}).get('status')} ended_by {(row['after']['project'] or {}).get('ended_by')}")
    for f in doc["flags"]:
        print(f)
    return 0 if doc["valid"] and not doc["flags"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
