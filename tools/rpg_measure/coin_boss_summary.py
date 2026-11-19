"""Summarizer for the coin and world-boss counter (tools/rpg_measure/coin_boss_spy.py): reads the runner's output files and applies the fixed criteria (rpg-designer u24, relayed by rpg-planner-ubuntu).

Per REAL cell, all HARD: (1) the spy's ``final_hash`` equals the plain twin's ``final_hash`` (the births re-check's ``<world>_<seed>_plain.json``, field ``final_hash``); (2) ``logging_errors`` is empty;
(3) the child exited 0 (4, 5 and 6 FAIL); (4) ``v6`` is 0; (5) the out json is present, valid JSON and has every key the checks read (missing or partial = FAIL).
REPORTED, not bars: ``unexplained_total_count`` with its rows (non-zero is a FINDING), ``apply_calls`` against ``distinct_ticks``, and ``boss_max`` for the three columns plus any disagreement row (non-zero or a row is a FINDING).
CONTROLS (criteria fixed now): coin:N: control v6 - real v6 == N exactly, exactly one unexplained row, at the last tick, equal to N, control_applied_count >= 1, control final_hash == real final_hash, exit 0.
boss:K: boss_max == K in all three columns, no disagreement row at the last tick, control_applied_count >= 1, final_hash == real, exit 0. never-fire: exit 6 and control_applied_count == 0.
The runner (coin_boss_run.py) writes ``<name>.json`` and ``<name>.exit.json`` ({"returncode", "stderr_tail"}); this module only reads files, runs nothing and writes one summary json and a SHA256SUMS.
Usage: python -m tools.rpg_measure.coin_boss_summary --dir <out> --mode real --plain <plain.json> | --mode controls
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REAL_KEYS = ("final_hash", "logging_errors", "v6", "wiring", "unexplained_total_count", "unexplained_rows", "apply_calls", "distinct_ticks", "boss_max", "boss_disagreements", "coin_moving_ticks",
             "control_applied_count", "control", "ticks", "world", "seed")
BOSS_COLUMNS = ("predicate_post_964", "raw_kind_alive", "occupation_alive")


def load_doc(path: Path) -> Tuple[Optional[Dict[str, Any]], str]:
    """(doc, "") for a complete out json, else (None, reason): missing, bad JSON, or a missing key."""
    if not path.exists():
        return None, f"{path.name}: missing"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return None, f"{path.name}: not valid JSON ({exc})"
    if not isinstance(doc, dict):
        return None, f"{path.name}: not a JSON object"
    absent = [k for k in REAL_KEYS if k not in doc]
    if absent:
        return None, f"{path.name}: partial, missing keys {absent}"
    return doc, ""


def load_exit(path: Path) -> Optional[int]:
    try:
        return int(json.loads(path.read_text(encoding="utf-8"))["returncode"])
    except (ValueError, OSError, KeyError, TypeError):
        return None


def real_verdict(doc: Optional[Dict[str, Any]], reason: str, returncode: Optional[int], plain_hash: Optional[str]) -> Dict[str, Any]:
    """HARD checks and REPORTED facts for one real cell."""
    if doc is None:
        return {"verdict": "FAIL", "hard": {"out_json_complete": False}, "failed": [reason or "out json unreadable"], "reported": {}, "findings": []}
    hard = {
        "out_json_complete": True,
        "hash_equals_plain": plain_hash is not None and doc["final_hash"] == plain_hash,
        "logging_errors_empty": doc["logging_errors"] == [],
        "exit_zero": returncode == 0,
        "v6_zero": doc["v6"] == 0,
    }
    failed = [name for name, ok in hard.items() if not ok]
    findings: List[str] = []
    if doc["unexplained_total_count"]:
        findings.append(f"unexplained_total_count {doc['unexplained_total_count']}")
    if any(doc["boss_max"].get(col, 0) for col in BOSS_COLUMNS) or doc["boss_disagreements"]:
        findings.append(f"boss_max {doc['boss_max']} disagreement rows {len(doc['boss_disagreements'])}")
    reported = {
        "unexplained_total_count": doc["unexplained_total_count"], "unexplained_rows": doc["unexplained_rows"], "apply_calls": doc["apply_calls"], "distinct_ticks": doc["distinct_ticks"],
        "boss_max": doc["boss_max"], "boss_disagreements": doc["boss_disagreements"], "coin_moving_ticks": doc["coin_moving_ticks"], "returncode": returncode, "plain_hash": plain_hash, "final_hash": doc["final_hash"],
    }
    return {"verdict": "FAIL" if failed else "PASS", "hard": hard, "failed": failed, "reported": reported, "findings": findings}


def coin_control_verdict(real: Optional[Dict[str, Any]], control: Optional[Dict[str, Any]], returncode: Optional[int], amount: float) -> Dict[str, Any]:
    if real is None or control is None:
        return {"verdict": "FAIL", "failed": ["real or control out json unreadable"], "criteria": {}}
    last = (control.get("control") or {}).get("applied_at_tick")
    rows = control["unexplained_rows"]
    criteria = {
        "v6_delta_equals_n": control["v6"] - real["v6"] == amount,
        "exactly_one_unexplained_row_at_last_tick_equal_n": len(rows) == 1 and rows[0]["tick"] == last and rows[0]["unexplained"] == amount,
        "control_applied_count_at_least_1": control["control_applied_count"] >= 1,
        "final_hash_equals_real": control["final_hash"] == real["final_hash"],
        "exit_zero": returncode == 0,
    }
    failed = [name for name, ok in criteria.items() if not ok]
    return {"verdict": "FAIL" if failed else "PASS", "failed": failed, "criteria": criteria, "v6_delta": control["v6"] - real["v6"]}


def boss_control_verdict(real: Optional[Dict[str, Any]], control: Optional[Dict[str, Any]], returncode: Optional[int], count: int) -> Dict[str, Any]:
    if real is None or control is None:
        return {"verdict": "FAIL", "failed": ["real or control out json unreadable"], "criteria": {}}
    last = (control.get("control") or {}).get("applied_at_tick")
    criteria = {
        "boss_max_equals_k_in_all_columns": all(control["boss_max"].get(col) == count for col in BOSS_COLUMNS),
        "no_disagreement_row_at_last_tick": not [row for row in control["boss_disagreements"] if row.get("tick") == last],
        "control_applied_count_at_least_1": control["control_applied_count"] >= 1,
        "final_hash_equals_real": control["final_hash"] == real["final_hash"],
        "exit_zero": returncode == 0,
    }
    failed = [name for name, ok in criteria.items() if not ok]
    return {"verdict": "FAIL" if failed else "PASS", "failed": failed, "criteria": criteria}


def never_fire_verdict(control: Optional[Dict[str, Any]], returncode: Optional[int]) -> Dict[str, Any]:
    criteria = {"exit_6": returncode == 6, "control_applied_count_zero": control is not None and control["control_applied_count"] == 0}
    failed = [name for name, ok in criteria.items() if not ok]
    return {"verdict": "FAIL" if failed else "PASS", "failed": failed, "criteria": criteria}


def _seal(directory: Path, names: List[str]) -> None:
    lines = [f"{hashlib.sha256((directory / n).read_bytes()).hexdigest()}  {n}" for n in sorted(names) if (directory / n).exists()]
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_real(directory: Path, plain: Path) -> Dict[str, Any]:
    """Every ``real_*.json`` in the directory against the plain twin json (one world/seed/ticks per call)."""
    plain_doc = json.loads(plain.read_text(encoding="utf-8")) if plain.exists() else {}
    plain_hash = plain_doc.get("final_hash")
    cells = {}
    for path in sorted(directory.glob("real_*.json")):
        if path.name.endswith(".exit.json"):
            continue
        doc, reason = load_doc(path)
        cells[path.name] = real_verdict(doc, reason, load_exit(path.with_suffix(".exit.json")), plain_hash)
    verdicts = {c["verdict"] for c in cells.values()}
    summary = {"mode": "real", "plain": str(plain), "plain_final_hash": plain_hash, "cells": cells, "verdict": "FAIL" if (not cells or "FAIL" in verdicts) else "PASS",
               "findings": {name: c["findings"] for name, c in cells.items() if c["findings"]}}
    (directory / "summary_real.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _seal(directory, [p.name for p in directory.iterdir() if p.is_file() and p.name != "SHA256SUMS"])
    return summary


def summarize_controls(directory: Path) -> Dict[str, Any]:
    """``real.json`` and the control files written by the runner's controls mode (``control_coin_<N>.json``, ``control_boss_<K>.json``, ``control_never_fire.json``) with their ``.exit.json``."""
    real, real_reason = load_doc(directory / "real.json")
    out: Dict[str, Any] = {"mode": "controls", "real_reason": real_reason, "controls": {}}
    for path in sorted(directory.glob("control_coin_*.json")):
        if path.name.endswith(".exit.json"):
            continue
        doc, _ = load_doc(path)
        out["controls"][path.name] = coin_control_verdict(real, doc, load_exit(path.with_suffix(".exit.json")), float(path.stem.rsplit("_", 1)[1]))
    for path in sorted(directory.glob("control_boss_*.json")):
        if path.name.endswith(".exit.json"):
            continue
        doc, _ = load_doc(path)
        out["controls"][path.name] = boss_control_verdict(real, doc, load_exit(path.with_suffix(".exit.json")), int(path.stem.rsplit("_", 1)[1]))
    never = directory / "control_never_fire.json"
    never_doc, _ = load_doc(never)
    out["controls"][never.name] = never_fire_verdict(never_doc, load_exit(never.with_suffix(".exit.json")))
    out["verdict"] = "PASS" if real is not None and out["controls"] and all(c["verdict"] == "PASS" for c in out["controls"].values()) else "FAIL"
    (directory / "summary_controls.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    _seal(directory, [p.name for p in directory.iterdir() if p.is_file() and p.name != "SHA256SUMS"])
    return out


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--mode", required=True, choices=("real", "controls"))
    ap.add_argument("--plain", type=Path, default=None, help="the births re-check's plain twin json for the same world/seed/ticks (real mode)")
    args = ap.parse_args(argv)
    if args.mode == "real":
        if args.plain is None:
            ap.error("--plain is required in real mode")
        summary = summarize_real(args.dir, args.plain)
    else:
        summary = summarize_controls(args.dir)
    print(json.dumps({"verdict": summary["verdict"]}, sort_keys=True))
    return 0 if summary["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
