"""Summarizer for the coin and world-boss counter (tools/rpg_measure/coin_boss_spy.py): reads the runner's output files and applies the fixed criteria (rpg-designer u24, relayed by rpg-planner-ubuntu).

Per REAL cell, all HARD: (1) the plain twin file exists and carries a ``final_hash`` (else FAIL, reason stated); (2) it is the SAME cell: ``world``, ``seed`` and ``ticks`` of the spy's out json equal the plain json's;
(3) the spy's ``final_hash`` equals the plain twin's ``final_hash`` (the births re-check's ``<world>_<seed>_plain.json``); (4) the out json is not a control: ``control`` is None, ``control_tick`` is None and ``counts_for_recheck`` is True;
(5) ``logging_errors`` is empty; (6) the child exited 0 (4, 5 and 6 FAIL); (7) ``v6`` is 0; (8) the out json is present, valid JSON and has every key the checks read (missing or partial = FAIL).
REPORTED, not bars: ``unexplained_total_count`` with its rows (non-zero is a FINDING), ``apply_calls`` against ``distinct_ticks``, and ``boss_max`` for the three columns plus any disagreement row (non-zero or a row is a FINDING).
CONTROLS (criteria fixed now): coin:N (a-f, section 43): exit 0 and control_applied_count >= 1; same final hash, world, seed and ticks as the real run; control v6 - real v6 == N; last_tick_unexplained difference == N; unexplained-count difference == (0 if the real run
has a row at the last tick, else 1); the rows before the last tick are equal (in full with uncapped lists on both sides, else only when both counts <= 200, otherwise skipped and noted "per-tick compare capped").
boss:K: boss_max == K in all three columns, no disagreement row at the last tick, control_applied_count >= 1, final_hash == real, exit 0. never-fire: exit 6 and control_applied_count == 0.
Every control (coin, boss, never-fire) also needs ``logging_errors == []`` and coin and boss ``wiring == "OK"``, all HARD; ``control_applied_count`` is reported for coin and boss, with a note when it is > 1.
The controls SET is validated first: its ``real.json`` needs exit 0 (``real.exit.json``), ``wiring == "OK"`` and ``logging_errors == []``; otherwise the set's verdict is VOID (a value apart from PASS and FAIL, exit 2) with the reasons,
and the real run's ``unexplained_total_count`` and ``boss_max`` are reported as findings.
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
             "control_applied_count", "control", "control_tick", "counts_for_recheck", "last_tick_unexplained", "last_tick_has_unexplained_row", "unexplained_rows_capped",
             "ticks", "world", "seed")
BOSS_COLUMNS = ("predicate_post_964", "raw_kind_alive", "occupation_alive")
ROW_CAP = 200  # the spy's cap on a capped unexplained_rows list (coin_boss_spy.ROW_CAP)


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


def real_verdict(doc: Optional[Dict[str, Any]], reason: str, returncode: Optional[int], plain: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """HARD checks and REPORTED facts for one real cell. ``plain`` is the plain twin's json (None when the file is missing)."""
    if doc is None:
        return {"verdict": "FAIL", "hard": {"out_json_complete": False}, "failed": ["out_json_complete"], "reasons": {"out_json_complete": reason or "out json unreadable"}, "reported": {}, "findings": []}
    plain_hash = plain.get("final_hash") if plain is not None else None
    plain_present = plain_hash is not None
    reasons: Dict[str, str] = {}
    if not plain_present:
        reasons["plain_twin_present"] = "the plain twin file is missing" if plain is None else "the plain twin file has no final_hash"
    same_cell = plain_present and all(plain.get(key) is not None and doc[key] == plain[key] for key in ("world", "seed", "ticks"))
    if plain_present and not same_cell:
        reasons["same_cell"] = f"spy cell {(doc['world'], doc['seed'], doc['ticks'])} != plain cell {(plain.get('world'), plain.get('seed'), plain.get('ticks'))}"
    not_a_control = doc["control"] is None and doc.get("counts_for_recheck") is True and doc.get("control_tick") is None
    if not not_a_control:
        reasons["not_a_control"] = f"control {doc['control']!r}, counts_for_recheck {doc.get('counts_for_recheck')!r}, control_tick {doc.get('control_tick')!r}: a control output cannot count as a real cell"
    hard = {
        "out_json_complete": True,
        "plain_twin_present": plain_present,
        "same_cell": same_cell,
        "hash_equals_plain": plain_present and doc["final_hash"] == plain_hash,
        "not_a_control": not_a_control,
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
    return {"verdict": "FAIL" if failed else "PASS", "hard": hard, "failed": failed, "reasons": reasons, "reported": reported, "findings": findings}


def _applied_note(control: Dict[str, Any]) -> List[str]:
    """A note (not a bar) when the control was applied more than once: the injection happened on several applies of the last tick."""
    count = control["control_applied_count"]
    return [f"control_applied_count {count} > 1: the control was applied on more than one apply of the last tick"] if count > 1 else []


def coin_control_verdict(real: Optional[Dict[str, Any]], control: Optional[Dict[str, Any]], returncode: Optional[int], amount: float) -> Dict[str, Any]:
    """The coin:N verdict, rpg-designer u24 section 43, all HARD: (a) exit 0 and control_applied_count >= 1; (b) same final hash and the same world, seed and ticks as the real run; (c) control v6 - real v6 == N;
    (d) control last_tick_unexplained - real last_tick_unexplained == N; (e) the unexplained-count difference == (0 if the real run has a row at the last tick, else 1); (f) the rows BEFORE the last tick are equal:
    in full when both lists are uncapped, else only when both counts are <= 200 (otherwise skipped and noted as "per-tick compare capped"; c-e carry the proof)."""
    if real is None or control is None:
        return {"verdict": "FAIL", "failed": ["real or control out json unreadable"], "criteria": {}, "notes": []}
    last = (control.get("control") or {}).get("applied_at_tick")
    notes: List[str] = []
    both_uncapped = not control["unexplained_rows_capped"] and not real["unexplained_rows_capped"]
    comparable = both_uncapped or (control["unexplained_total_count"] <= ROW_CAP and real["unexplained_total_count"] <= ROW_CAP)
    if comparable:
        rows_before_equal = [r for r in real["unexplained_rows"] if r["tick"] < last] == [r for r in control["unexplained_rows"] if r["tick"] < last]
    else:
        rows_before_equal = True  # skipped, not passed by evidence: c-e carry the proof
        notes.append("per-tick compare capped")
    expected_count_difference = 0 if real["last_tick_has_unexplained_row"] else 1
    criteria = {
        "a_exit_zero": returncode == 0,
        "a_control_applied_count_at_least_1": control["control_applied_count"] >= 1,
        "b_final_hash_equals_real": control["final_hash"] == real["final_hash"],
        "b_same_cell": all(control[key] == real[key] for key in ("world", "seed", "ticks")),
        "c_v6_delta_equals_n": control["v6"] - real["v6"] == amount,
        "d_last_tick_unexplained_delta_equals_n": control["last_tick_unexplained"] - real["last_tick_unexplained"] == amount,
        "e_unexplained_count_delta": control["unexplained_total_count"] - real["unexplained_total_count"] == expected_count_difference,
        "f_rows_before_last_tick_equal": rows_before_equal,
        "logging_errors_empty": control["logging_errors"] == [],
        "wiring_ok": control["wiring"] == "OK",
    }
    failed = [name for name, ok in criteria.items() if not ok]
    notes += _applied_note(control)
    return {"verdict": "FAIL" if failed else "PASS", "failed": failed, "criteria": criteria, "notes": notes, "v6_delta": control["v6"] - real["v6"], "f_compared": comparable,
            "control_applied_count": control["control_applied_count"]}


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
        "logging_errors_empty": control["logging_errors"] == [],
        "wiring_ok": control["wiring"] == "OK",
    }
    failed = [name for name, ok in criteria.items() if not ok]
    return {"verdict": "FAIL" if failed else "PASS", "failed": failed, "criteria": criteria, "notes": _applied_note(control), "control_applied_count": control["control_applied_count"]}


def never_fire_verdict(control: Optional[Dict[str, Any]], returncode: Optional[int]) -> Dict[str, Any]:
    criteria = {"exit_6": returncode == 6, "control_applied_count_zero": control is not None and control["control_applied_count"] == 0,
                "logging_errors_empty": control is not None and control["logging_errors"] == []}
    failed = [name for name, ok in criteria.items() if not ok]
    return {"verdict": "FAIL" if failed else "PASS", "failed": failed, "criteria": criteria}


def _seal(directory: Path, names: List[str]) -> None:
    lines = [f"{hashlib.sha256((directory / n).read_bytes()).hexdigest()}  {n}" for n in sorted(names) if (directory / n).exists()]
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_real(directory: Path, plain: Path) -> Dict[str, Any]:
    """Every ``real_*.json`` in the directory against the plain twin json (one world/seed/ticks per call)."""
    try:
        plain_doc: Optional[Dict[str, Any]] = json.loads(plain.read_text(encoding="utf-8")) if plain.exists() else None
    except (ValueError, OSError):
        plain_doc = {}  # present but unreadable: no final_hash, so every cell FAILs with that reason
    if plain_doc is not None and not isinstance(plain_doc, dict):
        plain_doc = {}
    cells = {}
    for path in sorted(directory.glob("real_*.json")):
        if path.name.endswith(".exit.json"):
            continue
        doc, reason = load_doc(path)
        cells[path.name] = real_verdict(doc, reason, load_exit(path.with_suffix(".exit.json")), plain_doc)
    verdicts = {c["verdict"] for c in cells.values()}
    summary = {"mode": "real", "plain": str(plain), "plain_final_hash": (plain_doc or {}).get("final_hash"), "cells": cells, "verdict": "FAIL" if (not cells or "FAIL" in verdicts) else "PASS",
               "findings": {name: c["findings"] for name, c in cells.items() if c["findings"]}}
    (directory / "summary_real.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _seal(directory, [p.name for p in directory.iterdir() if p.is_file() and p.name != "SHA256SUMS"])
    return summary


def real_void_reasons(real: Optional[Dict[str, Any]], reason: str, returncode: Optional[int]) -> List[str]:
    """Why the set's real.json cannot anchor the controls (the set is then VOID, not FAIL): unreadable, a non-zero exit, a wiring mismatch or a logging error."""
    if real is None:
        return [reason or "real.json unreadable"]
    out = []
    if returncode != 0:
        out.append(f"real.exit.json returncode {returncode!r}, not 0")
    if real["wiring"] != "OK":
        out.append(f"real wiring {real['wiring']!r}, not OK")
    if real["logging_errors"] != []:
        out.append(f"real logging_errors {real['logging_errors']!r}")
    return out


def summarize_controls(directory: Path) -> Dict[str, Any]:
    """``real.json`` and the control files written by the runner's controls mode (``control_coin_<N>.json``, ``control_boss_<K>.json``, ``control_never_fire.json``) with their ``.exit.json``."""
    real, real_reason = load_doc(directory / "real.json")
    void_reasons = real_void_reasons(real, real_reason, load_exit(directory / "real.exit.json"))
    out: Dict[str, Any] = {"mode": "controls", "real_reason": real_reason, "void_reasons": void_reasons, "controls": {},
                           "real_findings": None if real is None else {"unexplained_total_count": real["unexplained_total_count"], "boss_max": real["boss_max"]}}
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
    if void_reasons:
        out["verdict"] = "VOID"  # distinct from PASS and FAIL: the set's real run cannot anchor the controls
    else:
        out["verdict"] = "PASS" if out["controls"] and all(c["verdict"] == "PASS" for c in out["controls"].values()) else "FAIL"
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
    return {"PASS": 0, "FAIL": 1, "VOID": 2}[summary["verdict"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
