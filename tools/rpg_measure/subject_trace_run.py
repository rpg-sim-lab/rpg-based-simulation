"""Planner, runner and cell checks for the subject trace (Q2). Subcommands (every one is meant to be called as ``cd $KIT && PYTHONPATH=$KIT python subject_trace_run.py <sub> ...``; nothing here imports the frozen tree):

``plan``     (the #992 wolf-starvation read) hand-written subjects: ``--subject seed:id:lo:hi`` (once per subject; counterparts are rows, never subjects), ``--expect-death seed:id:tick:CAUSE`` (NEW arm), ``--world``, ``--out subjects.json``; the plan carries ``plan_sha256`` and ``way_reads: true``
``plan-check`` exit 0 only when the plan's own plan_sha256 recomputes (and equals ``--sha`` when given)
``summarize`` the side-by-side evidence tables per subject and arm (``--cells``, ``--plan``, ``--out``): NO verdict line
``derive``  subjects and windows from the stage-1 SEALED cells (``--sealed <cells dir>``, ``--seed`` once per seed) -> ``--out subjects.json`` with the sha256 of every sealed cell it read
``seeds``   the seeds that have at least one subject (``--plan``), space separated
``seal-check`` exit 0 only when sha256(stage-1 SHA256SUMS) equals its SEAL line (``--dir``)
``one``     ONE child process (the launcher puts it in its own scope): cwd = that arm's frozen tree, PYTHONPATH = that tree, recording OFF; moves the tree's ``data/runs`` out; writes ``<name>.exit.json``
``check``   the validity of every spy cell against the SEALED plain twins (hash equality, spy exceptions, reach) -> ``cell_validity.json``; evidence only, no verdict about the sim
``record``  ``runner.json`` from the exit files and the launcher's status; a failed write exits non-zero

SUBJECTS (``derive_subjects``, pure): from the stage-1 SEALED NEW spy cells only. A subject is a victim of a NEW meat engagement with at least 10 hits, or a victim of an R7 chain (``hit_chains`` per victim: a
no-decision run of 5 or more, an asleep/lodged run of 3 or more), plus every attacker in those engagements or chains. WINDOW: first hit - 100 ticks to END + 100, END = the victim's death tick when it dies inside the
engagement or chain, otherwise the last hit; a subject's windows are merged; an attacker stays a subject for the whole padded window (a NEW victim inside the padding is a row of that attacker, never a new subject).
Cells run: for each seed with at least one subject, the NEW spy cell and the same-seed BASE cell, reading the same ids. ``seal-check`` refuses stage 2 unless sha256(stage-1 SHA256SUMS) equals its SEAL line.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PAD = 100
ENGAGEMENT_GAP = 50                       # the same gap as the engagements and ``hit_chains``
DECISION_MODES = ("RETREAT", "PURSUE")   # the summarizer's own
MIN_HITS = 10
MIN_NO_DECISION_CHAIN, MIN_ASLEEP_CHAIN = 5, 3
HASHSEED = "0"
RECORDING_OFF_ENV = {"SIM_OBS_MODE": "OFF", "RPG_OBS_MODE": "OFF"}
CHILD = Path(__file__).resolve().with_name("subject_trace_spy.py")
EXIT_NOT_RECORDED = 6
WOLF_PLAN_KIND = "hand_written"


def load_sibling(name: str) -> Any:
    key = f"_subject_trace_run_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, Path(__file__).resolve().with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_name(arm: str, world: str, seed: int, mode: str) -> str:
    return f"{arm}__{world}__s{seed}__{mode}"


def merge_windows(windows: List[List[int]]) -> List[List[int]]:
    merged: List[List[int]] = []
    for lo, hi in sorted([max(0, int(a)), int(b)] for a, b in windows):
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return merged


def padded_window(start: int, end: int) -> List[int]:
    """First hit minus 100 ticks to END plus 100 ticks (rpg-designer's amendment: death gets the padding too)."""
    return [max(0, start - PAD), end + PAD]


def victim_death_tick(rows: List[Dict[str, Any]], victim_id: int, start: int, end: int) -> Optional[int]:
    """The tick of the first row inside [start, end] in which the victim is not alive after the hit (from any attacker), or None."""
    deaths = [r["tick"] for r in rows if r["victim_id"] == victim_id and not r["victim_alive_after"] and start <= r["tick"] <= end]
    return min(deaths) if deaths else None


def last_hit_tick(rows: List[Dict[str, Any]], victim_id: int, attackers: List[int], start: int, end: int) -> int:
    hits = [r["tick"] for r in rows if r["victim_id"] == victim_id and r["attacker_id"] in attackers and r["hit"] and start <= r["tick"] <= end]
    return max(hits) if hits else end


def chain_runs(hits: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """PURE: EVERY qualifying R7 run of ONE victim's hits (``person_attack_summary.hit_states`` output, any order): every no-decision run of 5 or more and every asleep/lodged run of 3 or more, as MAXIMAL runs.
    The reset rules are ``hit_chains``' own (a gap of more than 50 ticks between consecutive hits resets both; a decision between two hits restarts the no-decision run; a victim not asleep or lodged
    ends the asleep run), so the longest run listed here equals what ``hit_chains`` reports. Each run: {run, start_tick, end_tick, attackers}."""
    hits = sorted(hits, key=lambda h: h["tick"])
    found: Dict[str, List[Dict[str, Any]]] = {"no_decision_run": [], "asleep_or_lodged_run": []}
    starts: Dict[str, Optional[int]] = {"no_decision_run": None, "asleep_or_lodged_run": None}
    minimum = {"no_decision_run": MIN_NO_DECISION_CHAIN, "asleep_or_lodged_run": MIN_ASLEEP_CHAIN}

    def close(key: str, end: int) -> None:
        start = starts[key]
        if start is not None and end - start + 1 >= minimum[key]:
            found[key].append({"run": end - start + 1, "start_tick": hits[start]["tick"], "end_tick": hits[end]["tick"], "attackers": sorted({h["attacker_id"] for h in hits[start:end + 1]})})
        starts[key] = None

    for i, hit in enumerate(hits):
        asleep = hit["victim_state"] in ("asleep", "lodged")
        if i == 0:
            starts["no_decision_run"], starts["asleep_or_lodged_run"] = 0, 0 if asleep else None
            continue
        prev = hits[i - 1]
        if hit["tick"] - prev["tick"] > ENGAGEMENT_GAP:                      # a gap resets both runs
            close("no_decision_run", i - 1)
            close("asleep_or_lodged_run", i - 1)
            starts["no_decision_run"], starts["asleep_or_lodged_run"] = i, i if asleep else None
            continue
        if asleep:
            if starts["asleep_or_lodged_run"] is None:
                starts["asleep_or_lodged_run"] = i
        else:
            close("asleep_or_lodged_run", i - 1)
        decided = prev["decision"] != "none" or hit["victim_mode_before"] in DECISION_MODES or any(prev["tick"] <= t <= hit["tick"] for t in hit["_decisions"])
        if decided:
            close("no_decision_run", i - 1)
            starts["no_decision_run"] = i
    close("no_decision_run", len(hits) - 1)
    close("asleep_or_lodged_run", len(hits) - 1)
    return found


def derive_subjects(cells: Dict[int, Dict[str, Any]], summary: Any) -> Dict[str, List[Dict[str, Any]]]:
    """PURE: ``cells`` = seed -> that seed's NEW spy cell (the stage-1 sealed document). Returns seed -> subjects, only from the cells:
    a victim of a NEW meat engagement with at least 10 hits, or of an R7 chain (no-decision run >= 5 or asleep/lodged run >= 3, judged per victim), plus every attacker in those engagements or chains.
    The window of an engagement or chain is its first hit - 100 to END + 100, END = the victim's death tick when it dies inside it, else the last hit; a subject's windows are merged."""
    plans: Dict[str, List[Dict[str, Any]]] = {}
    for seed, cell in sorted(cells.items()):
        rows = [r for r in cell["rows"] if r["in_o3_group"]]
        all_rows = cell["rows"]
        subjects: Dict[int, Dict[str, Any]] = {}

        def add(subject_id: int, role: str, window: List[int], counterparts: List[int]) -> None:
            entry = subjects.setdefault(subject_id, {"id": subject_id, "roles": [], "windows": [], "counterparts": []})
            if role not in entry["roles"]:
                entry["roles"].append(role)
            entry["windows"].append(window)
            entry["counterparts"] = sorted(set(entry["counterparts"]) | set(counterparts))

        for eng in summary.build_engagements(rows, cell["mode_rows"], cell["final_tick"], lambda tick: False):
            if eng["hits"] < MIN_HITS:
                continue
            start, end = eng["start_tick"], eng["end_tick"]
            death = victim_death_tick(all_rows, eng["victim_id"], start, end)
            window = padded_window(start, death if death is not None else last_hit_tick(all_rows, eng["victim_id"], [eng["attacker_id"]], start, end))
            add(eng["victim_id"], "victim", window, [eng["attacker_id"]])
            add(eng["attacker_id"], "attacker", window, [eng["victim_id"]])
        for victim_id in sorted({r["victim_id"] for r in rows}):                   # EVERY qualifying chain of every victim (not only the worst one), each with its own window and attackers
            victim_hits = summary.hit_states([r for r in rows if r["victim_id"] == victim_id], cell["mode_rows"], attack_rows=cell.get("attack_rows"))
            for chains in chain_runs(victim_hits).values():
                for chain in chains:
                    start, end = chain["start_tick"], chain["end_tick"]
                    death = victim_death_tick(all_rows, victim_id, start, end)
                    window = padded_window(start, death if death is not None else end)
                    add(victim_id, "chain_victim", window, chain["attackers"])
                    for attacker_id in chain["attackers"]:
                        add(attacker_id, "attacker", window, [victim_id])
        for entry in subjects.values():
            entry["windows"] = merge_windows(entry["windows"])
            entry["roles"] = sorted(entry["roles"])
        plans[str(seed)] = [subjects[k] for k in sorted(subjects)]
    return plans


def derive_plan(sealed: Path, world: str, seeds: List[int], summary: Any) -> Dict[str, Any]:
    """subjects.json: ``derive_subjects`` on the stage-1 SEALED NEW spy cells, with the sha256 of every sealed cell read (the spy cells and both arms' plain twins)."""
    derived_from: Dict[str, str] = {}
    cells: Dict[int, Dict[str, Any]] = {}
    for seed in seeds:
        spy_path = sealed / f"{cell_name('new', world, seed, 'spy')}.json"
        derived_from[spy_path.name] = sha256_file(spy_path)
        cells[seed] = json.loads(spy_path.read_text(encoding="utf-8"))
        for arm in ("new", "base"):
            plain = sealed / f"{cell_name(arm, world, seed, 'plain')}.json"
            derived_from[plain.name] = sha256_file(plain)
    by_seed = derive_subjects(cells, summary)
    body = {"derived_from": derived_from, "pad": PAD, "min_hits": MIN_HITS, "world": world, "subjects_by_seed": by_seed, "seeds_with_subjects": [int(k) for k, v in by_seed.items() if v]}
    return {**body, "plan_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()}


def plan_sha(body: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


def parse_subject(text: str) -> Dict[str, int]:
    """``seed:id:lo:hi`` -> {seed, id, lo, hi}; a malformed or empty window is a ValueError (a plan is never guessed)."""
    parts = text.split(":")
    if len(parts) != 4 or not all(part.lstrip("-").isdigit() for part in parts):
        raise ValueError(f"--subject must be seed:id:lo:hi (four integers), not {text!r}")
    seed, subject_id, lo, hi = (int(part) for part in parts)
    if lo < 0 or hi < lo:
        raise ValueError(f"--subject window {lo}-{hi} is empty or negative")
    return {"seed": seed, "id": subject_id, "lo": lo, "hi": hi}


def parse_expect(text: str) -> Dict[str, Any]:
    """``seed:id:tick:CAUSE`` -> {seed, id, tick, cause}."""
    parts = text.split(":")
    if len(parts) != 4 or not all(part.isdigit() for part in parts[:3]) or not parts[3].isupper():
        raise ValueError(f"--expect-death must be seed:id:tick:CAUSE, not {text!r}")
    return {"seed": int(parts[0]), "id": int(parts[1]), "tick": int(parts[2]), "cause": parts[3]}


def build_plan(world: str, subjects: List[Dict[str, int]], expect_deaths: List[Dict[str, Any]]) -> Dict[str, Any]:
    """PURE: the hand-written plan in the ``derive`` schema (subjects_by_seed -> [{id, roles, windows, counterparts}]), plus the NEW-arm death expectations the check reads. Counterparts stay empty on purpose: a body the subject meets is a ROW of the subject
    (the spy records it per tick), never a new subject. ``plan_sha256`` is the sha256 of the body, as in ``derive_plan``."""
    by_seed: Dict[str, List[Dict[str, Any]]] = {}
    for item in sorted(subjects, key=lambda x: (x["seed"], x["id"], x["lo"])):
        group = by_seed.setdefault(str(item["seed"]), [])
        entry = next((e for e in group if e["id"] == item["id"]), None)
        if entry is None:
            entry = {"id": item["id"], "roles": ["subject"], "windows": [], "counterparts": []}
            group.append(entry)
        entry["windows"] = merge_windows(entry["windows"] + [[item["lo"], item["hi"]]])
    body = {"kind": WOLF_PLAN_KIND, "derived_from": {}, "pad": 0, "min_hits": MIN_HITS, "world": world, "way_reads": True, "subjects_by_seed": by_seed, "seeds_with_subjects": sorted(int(k) for k in by_seed),
            "expect_deaths": sorted(expect_deaths, key=lambda e: (e["seed"], e["id"]))}
    return {**body, "plan_sha256": plan_sha(body)}


def plan_matches(plan: Dict[str, Any], expected: Optional[str] = None) -> Dict[str, Any]:
    """{"ok", "computed", "recorded"}: the plan's own sha256 recomputes from its body, and equals ``expected`` when one is given."""
    body = {k: v for k, v in plan.items() if k != "plan_sha256"}
    computed = plan_sha(body)
    recorded = plan.get("plan_sha256")
    return {"ok": computed == recorded and (expected is None or computed == expected), "computed": computed, "recorded": recorded, "expected": expected}


def death_reasons(spy: Dict[str, Any], arm: str, seed: int, expect_deaths: List[Dict[str, Any]]) -> List[str]:
    """VOID reasons for the NEW arm only: every expected death must be in the run's OWN typed death record at the expected tick and cause. BASE alive is expected context and is never judged here."""
    reasons: List[str] = []
    if arm != "new":
        return reasons
    for expected in expect_deaths:
        if expected["seed"] != seed:
            continue
        found = (spy.get("death_records") or {}).get(str(expected["id"]))
        label = f"NEW s{seed} subject {expected['id']} expected {expected['cause']} at t{expected['tick']}"
        if found is None:
            reasons.append(f"VOID: {label}, but the run holds no death record for it")
            continue
        record = found.get("record") or {}
        if record.get("cause") != expected["cause"] or record.get("tick") != expected["tick"]:
            reasons.append(f"VOID: {label}, but the run's death record says {record.get('cause')} at t{record.get('tick')} (first seen at t{found.get('first_seen_tick')}, passive cause {found.get('passive_cause')} at t{found.get('passive_cause_tick')})")
    return reasons


def seal_matches(stage1_out: Path) -> Dict[str, Any]:
    """Stage 2 starts only if sha256(stage-1 SHA256SUMS) equals the SEAL line the stage-1 launcher wrote: {"ok", "computed", "recorded"}."""
    sums, seal_log = stage1_out / "SHA256SUMS", stage1_out / "SHA256SUMS.seal.log"
    if not sums.exists() or not seal_log.exists():
        return {"ok": False, "computed": None, "recorded": None, "reason": "SHA256SUMS or its seal log is missing"}
    lines = [ln.split() for ln in seal_log.read_text(encoding="utf-8").splitlines() if ln.startswith("SEAL ")]
    recorded = lines[-1][1] if lines else None
    computed = hashlib.sha256(sums.read_bytes()).hexdigest()
    return {"ok": recorded is not None and computed == recorded, "computed": computed, "recorded": recorded}


def check_cell(spy: Dict[str, Any], sealed_plain: Dict[str, Any], arm: str, seed: int, plan_sha256: Optional[str] = None, expect_deaths: Optional[List[Dict[str, Any]]] = None, new_s42_needs_a_legality_call: bool = True) -> Dict[str, Any]:
    """Validity of one spy cell against its plain twin (SEALED in stage 2; the SAME run's in the #992 read). Evidence-only: a void cell says why; nothing here judges the simulation.
    ``plan_sha256``: both documents must carry the plan's sha256. ``expect_deaths``: the NEW arm's expected deaths (``death_reasons``). ``new_s42_needs_a_legality_call``: the stage-2 rule; the #992 plan switches it off (its VOID list is the ticket's)."""
    reasons: List[str] = []
    if plan_sha256 is not None and (spy.get("plan_sha256") != plan_sha256 or sealed_plain.get("plan_sha256") != plan_sha256):
        reasons.append(f"PLAN_SHA256 mismatch: spy {spy.get('plan_sha256')}, plain {sealed_plain.get('plan_sha256')}, pinned {plan_sha256}")
    reasons += death_reasons(spy, arm, seed, expect_deaths or [])
    if spy.get("spy_exceptions") or spy.get("fatal"):
        reasons.append("SPY_EXCEPTION (fatal)")
    if spy.get("final_hash") != sealed_plain.get("final_hash"):
        reasons.append("PERTURBATION: the spy's final hash differs from the sealed plain twin's")
    if spy.get("ticks") != sealed_plain.get("ticks"):
        reasons.append("TICKS differ from the sealed plain twin")
    if spy.get("offset_drift"):
        reasons.append("OFFSET_DRIFT: state.tick - state.world_time was not constant, so legality ticks derived from world_time are not reliable")
    if spy.get("row_count", 0) == 0:
        reasons.append("VOID: 0 subject rows in the windows")
    if new_s42_needs_a_legality_call and arm == "new" and seed == 42 and spy.get("legality_calls_in_window", 0) == 0:
        reasons.append("VOID: NEW s42 has no legality call by any subject in its window")
    return {"arm": arm, "seed": seed, "valid": not reasons, "reasons": reasons, "row_count": spy.get("row_count"), "legality_calls_in_window": spy.get("legality_calls_in_window"),
            "final_hash_spy": spy.get("final_hash"), "final_hash_sealed_plain": sealed_plain.get("final_hash")}


def child_env(tree: Path, out: Path) -> Dict[str, str]:
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": HASHSEED, "PYTHONPATH": str(tree), "TMPDIR": str(out / "tmp"), **RECORDING_OFF_ENV}


def run_child(python: str, tree: Path, out: Path, item: Dict[str, Any], plan: Path) -> Dict[str, Any]:
    (out / "tmp").mkdir(parents=True, exist_ok=True)
    path = out / f"{item['name']}.json"
    command = [python, str(CHILD), item["world"], str(item["seed"]), str(item["ticks"]), str(path), "--arm", item["arm"], "--plan", str(plan), "--mode", item["mode"]]
    started = time.time()
    proc = subprocess.run(command, cwd=tree, env=child_env(tree, out), capture_output=True, text=True)
    seconds = round(time.time() - started, 1)
    moved = load_sibling("person_attack_run").move_tree_runs(tree, out / "tree-data-runs" / item["name"])
    result = {"returncode": proc.returncode, "stderr_tail": proc.stderr.strip()[-400:], "seconds": seconds, "tree_data_runs_moved_to": None if moved is None else str(moved)}
    (out / f"{item['name']}.exit.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    with (out / "run_times.log").open("a", encoding="utf-8") as log:
        log.write(f"RUN {item['name']}: {seconds}s returncode {proc.returncode}\n")
    return result


def check_all(cells: Path, sealed: Path, world: str, items: List[Dict[str, Any]], plan_sha256: Optional[str] = None, expect_deaths: Optional[List[Dict[str, Any]]] = None, legacy_rules: bool = True) -> Dict[str, Any]:
    results = {}
    for item in items:
        if item["mode"] != "spy":
            continue
        key = f"{item['arm']}/s{item['seed']}"
        spy_path, plain_path = cells / f"{item['name']}.json", sealed / f"{cell_name(item['arm'], world, item['seed'], 'plain')}.json"
        if not spy_path.exists() or not plain_path.exists():
            results[key] = {"arm": item["arm"], "seed": item["seed"], "valid": False, "reasons": ["VOID: the spy cell or the sealed plain twin file is missing"]}
            continue
        results[key] = check_cell(json.loads(spy_path.read_text(encoding="utf-8")), json.loads(plain_path.read_text(encoding="utf-8")), item["arm"], item["seed"], plan_sha256, expect_deaths, legacy_rules)
    return {"cells": results, "all_valid": bool(results) and all(c["valid"] for c in results.values())}


def write_record(out: Path, status: str, go: str, items: List[Dict[str, Any]], freeze: Dict[str, str], python: str) -> Dict[str, Any]:
    """``runner.json``: the launcher's status, the exit file of every item and the freeze values. The write is checked by reading it back; the caller exits non-zero when this raises."""
    codes = {}
    for item in items:
        exit_file = out / "cells" / f"{item['name']}.exit.json"
        codes[item["name"]] = json.loads(exit_file.read_text(encoding="utf-8"))["returncode"] if exit_file.exists() else None
    record = {"go": go, "status": status, "python": python, "freeze": freeze, "returncodes": codes, "items": [i["name"] for i in items]}
    target = out / "runner.json"
    target.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    if json.loads(target.read_text(encoding="utf-8")) != record:
        raise RuntimeError("runner.json read back differently")
    return record


def items_for(kind: str, world: str, seeds: List[int], ticks: int) -> List[Dict[str, Any]]:
    """cells: the four spy cells, NEW first; smoke: NEW s42 plain then spy at ``ticks``; wolf: every (arm, seed) plain then spy."""
    if kind == "smoke":
        modes = [("new", seeds[0], "plain"), ("new", seeds[0], "spy")]
    elif kind == "wolf":   # the #992 read: for each arm (NEW first) and seed, the plain run THEN its spy twin: 2 seeds x 2 arms x 2 = 8 processes
        modes = [(arm, seed, mode) for arm in ("new", "base") for seed in seeds for mode in ("plain", "spy")]
    else:
        modes = [(arm, seed, "spy") for arm in ("new", "base") for seed in seeds]
    return [{"arm": arm, "world": world, "seed": seed, "ticks": ticks, "mode": mode, "name": cell_name(arm, world, seed, mode)} for arm, seed, mode in modes]


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("derive")
    d.add_argument("--sealed", required=True, type=Path)
    d.add_argument("--world", required=True)
    d.add_argument("--seed", action="append", type=int, required=True)
    sub.add_parser("seeds").add_argument("--plan", required=True, type=Path)
    sub.add_parser("seal-check").add_argument("--dir", required=True, type=Path)
    d.add_argument("--out", required=True, type=Path)
    o = sub.add_parser("one")
    for name in ("arm", "world", "mode", "tree", "out", "python", "plan"):
        o.add_argument(f"--{name}", required=True)
    o.add_argument("--seed", required=True, type=int)
    o.add_argument("--ticks", required=True, type=int)
    c = sub.add_parser("check")
    c.add_argument("--cells", required=True, type=Path)
    c.add_argument("--sealed", required=True, type=Path)
    c.add_argument("--world", required=True)
    c.add_argument("--seed", action="append", type=int, required=True)
    c.add_argument("--ticks", required=True, type=int)
    c.add_argument("--out", required=True, type=Path)
    c.add_argument("--arm", action="append", choices=("new", "base"), help="judge only these arms (the smoke runs NEW only)")
    c.add_argument("--plan", type=Path, help="the #992 read: pin the plan's sha256 and read its NEW-arm death expectations (``--sealed`` is then the run's own cells dir: the plain twin is the SAME run's)")
    pl = sub.add_parser("plan")
    pl.add_argument("--world", required=True)
    pl.add_argument("--subject", action="append", required=True)
    pl.add_argument("--expect-death", action="append", default=[])
    pl.add_argument("--out", required=True, type=Path)
    pc = sub.add_parser("plan-check")
    pc.add_argument("--plan", required=True, type=Path)
    pc.add_argument("--sha")
    sm = sub.add_parser("summarize")
    sm.add_argument("--cells", required=True, type=Path)
    sm.add_argument("--plan", required=True, type=Path)
    sm.add_argument("--world", required=True)
    sm.add_argument("--out", required=True, type=Path)
    r = sub.add_parser("record")
    r.add_argument("--out", required=True, type=Path)
    r.add_argument("--status", required=True)
    r.add_argument("--go", required=True)
    r.add_argument("--kind", required=True, choices=("cells", "smoke", "wolf"))
    r.add_argument("--world", required=True)
    r.add_argument("--seed", action="append", type=int, required=True)
    r.add_argument("--ticks", required=True, type=int)
    r.add_argument("--python", required=True)
    r.add_argument("--freeze-expected", required=True)
    r.add_argument("--freeze-final", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "plan":
        plan = build_plan(args.world, [parse_subject(x) for x in args.subject], [parse_expect(x) for x in args.expect_death])
        args.out.write_text(json.dumps(plan, indent=1, sort_keys=True), encoding="utf-8")
        print(json.dumps({"plan_sha256": plan["plan_sha256"], "subjects": {k: [x["id"] for x in v] for k, v in plan["subjects_by_seed"].items()}}, sort_keys=True))
        return 0
    if args.cmd == "plan-check":
        verdict = plan_matches(json.loads(args.plan.read_text(encoding="utf-8")), args.sha)
        print(json.dumps(verdict, sort_keys=True))
        return 0 if verdict["ok"] else 1
    if args.cmd == "summarize":
        summary = load_sibling("subject_trace_summary")
        document = summary.summarize(args.cells, json.loads(args.plan.read_text(encoding="utf-8")), args.world)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "summary.json").write_text(json.dumps(document, indent=1, sort_keys=True), encoding="utf-8")
        (args.out / "summary.md").write_text(summary.render(document), encoding="utf-8")
        print(json.dumps({"subjects": sorted(document["subjects"])}, sort_keys=True))
        return 0
    if args.cmd == "derive":
        plan = derive_plan(args.sealed, args.world, args.seed, load_sibling("person_attack_summary"))
        args.out.write_text(json.dumps(plan, indent=1, sort_keys=True), encoding="utf-8")
        print(json.dumps({"plan_sha256": plan["plan_sha256"], "subjects": {s: [x["id"] for x in v] for s, v in plan["subjects_by_seed"].items()}}, sort_keys=True))
        return 0
    if args.cmd == "seeds":
        print(" ".join(str(x) for x in json.loads(args.plan.read_text(encoding="utf-8"))["seeds_with_subjects"]))
        return 0
    if args.cmd == "seal-check":
        verdict = seal_matches(args.dir)
        print(json.dumps(verdict, sort_keys=True))
        return 0 if verdict["ok"] else 1
    if args.cmd == "one":
        item = {"arm": args.arm, "world": args.world, "seed": args.seed, "ticks": args.ticks, "mode": args.mode, "name": cell_name(args.arm, args.world, args.seed, args.mode)}
        result = run_child(args.python, Path(args.tree), Path(args.out), item, Path(args.plan))
        print(json.dumps(result, sort_keys=True))
        return result["returncode"]
    if args.cmd == "check":
        items = [i for i in items_for("cells", args.world, args.seed, args.ticks) if not args.arm or i["arm"] in args.arm]
        plan = json.loads(args.plan.read_text(encoding="utf-8")) if args.plan else None
        verdict = check_all(args.cells, args.sealed, args.world, items, plan["plan_sha256"] if plan else None, plan.get("expect_deaths") if plan else None, not (plan and plan.get("kind") == WOLF_PLAN_KIND))
        args.out.write_text(json.dumps(verdict, indent=1, sort_keys=True), encoding="utf-8")
        print(json.dumps({"all_valid": verdict["all_valid"]}))
        return 0 if verdict["all_valid"] else 1
    try:
        items = items_for(args.kind, args.world, args.seed, args.ticks)
        write_record(args.out, args.status, args.go, items, {"expected": args.freeze_expected, "final": args.freeze_final}, args.python)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"RECORD NOT WRITTEN: {exc}", file=sys.stderr)
        return EXIT_NOT_RECORDED
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
