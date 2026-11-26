"""Driver for the births own-job (rulings v2 Part C, checks 3 and 6 by owner request; the M1 reproduction rows G1-G6, R1-R4 and the trigger-neutrality arm added 2026-11-18).

Three blocks, each with its own ``--go <reference>`` (the id of the lead-planner go for THAT run) and its own ``--out``; the driver refuses to start without one and deletes nothing:
- ``--block evidence``: per world x seed the head arms ``spied`` (births on + record-only spy), ``control`` (the chance-0 twin, spied) and ``plain`` (births on, no spy; its final hash must equal
  the spied arm's), interleaved with a MAIN-tree cost run (``--main-tree``) of the same cell, serial; seed 42 also gets a repeat ``plain`` + ``main`` pair (the run-to-run noise band).
- ``--block trigger``: s42 (``--seeds``) x the three trigger arms, ``trigger_on`` / ``trigger_off`` / ``trigger_pos``, at 1000 ticks; a world whose ``trigger_on`` fired 0 times is rerun at 5000 ticks
  (both runs printed); a world with no cell that fired is a STOP to rpg-designer-ubuntu.
- ``--block probe`` (``--cost-probe``): one world x one seed, one arm at a time, wall time and peak RSS.
Run under ``systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`` with PYTHONHASHSEED=0 and the main checkout's python, detached under setsid.

HARD (any non-zero count fails; the report prints PASS/FAIL/STOP and never a judgement): K6, K6b, K8, W1-W5, G1-G6, R1-R4, 6a (``mismatch_total``), twin hash equality, and per trigger cell the
neutrality equalities (state hash, event stream, integer metrics including spatial_index_hits and the phase counters) with ON firings > 0 and extra runs > 0, OFF 0 and 0, and a positive control that
differs. STOP: zero births in total, zero regioned births (6a cannot be assessed), zero risings in the tier (R1-R4 vacuous). BALANCE, report only: everything else (check 3, 6b, unplaced, ended
pregnancies, father-dead-at-term, regionless births, the per-phase cost read).
The report reads alive bodies from state through species_of(); it never reads population_young or any region cohort counter except in the 6b BALANCE rows.

Usage: python -m tools.rpg_measure.births_run --block evidence|trigger --tree <fix tree> [--main-tree <frozen main>] --out <dir> --go <ref> [--ticks N] [--worlds ...] [--seeds ...] [--recording-off]
       python -m tools.rpg_measure.births_run --block probe --tree <fix tree> --out <dir> --go <ref> [--main-tree <frozen main>] [--ticks N]
"""
from __future__ import annotations

import argparse
import gzip
import statistics
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.rpg_measure import paired

CHILD = Path(__file__).resolve().with_name("births_child.py")
COST_CHILD = Path(__file__).resolve().with_name("births_cost_child.py")
BARS = ("K6", "K6b", "K8", "W1", "W2", "W3", "W4", "W5", "G1", "G2", "G3", "G4", "G5", "G6", "R1", "R2", "R3", "R4", "N1")
ARMS = ("spied", "plain", "control")
TRIGGER_ARMS = ("trigger_on", "trigger_off", "trigger_pos")
TRIGGER_TICKS = 1000
TRIGGER_RERUN_TICKS = 5000
TRIGGER_SEEDS = (42,)
STALL_FACTOR = 5.0  # a tick whose total time exceeds this multiple of the cell median is a stall tick (dropped from the phase medians, and counted)
STALL_REDO_FRACTION = 0.02  # a cell with more than this fraction of stall ticks is rerun, not accepted
JUMP_SINGLE = 0.5  # a single cell whose head/main median gap is at least this fraction is flagged
JUMP_HELD_GAP = 0.10  # a gap above this AND above the head-vs-head noise band, in HELD_CELLS or more cells, is a jump held across cells
HELD_CELLS = 3
RECORDING_OFF_ENV = {"SIM_OBS_MODE": "OFF", "RPG_OBS_MODE": "OFF"}
COMBAT_CAUSE = "COMBAT"  # check 3 verdict: the per-capita rate is combat deaths per 1000 live entity-ticks
Key = Tuple[str, int, str]
BASES = {"6a": "mother's region (births' write rule)", "check3_probe_c": "newborn tile (the region at the newborn's position)"}
COHORT_FLAG_RULE = "a flag row when the cohort rises while live bodies == 0, or the cohort == 0 while live bodies rise (reported rows, not bars)"
PROBE_WORLD = "frontier_living_world"  # the largest gate world (55 bodies), so its cost bounds the other two
LIMITS = (
    "the twin-hash check proves the spy read-only in the births arm only; the chance-0 control arm is spied with no plain twin, and runs the same spy code",
    "recording-off = OBS OFF + no_replay; hash-neutral at 100t (run 1, #715 6968789570) and at 5000t on frontier_living_world s42 (the probe's recording-on plain arm = its no_replay plain arm); replay is off on BOTH sides of the cost read (head children and the main-tree cost child)",
    "every row comes from the spy's own outputs (typed updates, the state after each tick) or from the final-state hash; no row reads simulation_events.jsonl, the replay chunks or a run dir, which is why --recording-off is allowed (the 100-tick no_replay/OFF check decides it)",
    "the trigger arms patch the name the scheduler calls, src.engine.phase_graph.rise_triggers_phase (defined at src/world/risen.py), in the child process only and restore it at exit; no source file changes; trigger_off also makes RisenService.process_rises the identity",
    "metrics equality uses the kernel's integer and boolean counters per tick (phase counters, spatial_index_hits); floats are left out because they may be timings; the event stream is the typed world events of each applied update",
    "R1 is keyed on RISEN adds; a corpse removed by the rise step without a RISEN add is caught only by the conservation audit and the event digest",
    "the cost read uses the kernel's stage timers (kernel._phase_costs): births sit inside governance_ecology, the rise and the trigger inside economy; a births-only or rise-only number is not readable, the delta of the bundle is",
    "every run is built under audit_mode and no_frame_pacing (births_child checks both flags and PINNED requires them); the counts are per-tick facts, not timing",
    "W4 is checked on the typed hunger update the births system returns, not on the mother's hunger after the tick (other phases move hunger on the same tick)",
)


def child_env(tree: Path, recording_off: bool) -> Dict[str, str]:
    env = {**os.environ, "PYTHONHASHSEED": paired.HASHSEED, "PYTHONPATH": str(tree)}
    return {**env, **RECORDING_OFF_ENV} if recording_off else env


def run_child(tree: Path, out: Path, world: str, seed: int, ticks: int, mode: str, recording_off: bool = False, tag: str = "") -> Path:
    path = out / f"{world}_{seed}_{mode}{tag}.json"
    proc = subprocess.run([sys.executable, str(CHILD), world, str(seed), str(ticks), mode, str(path)], cwd=tree, env=child_env(tree, recording_off), capture_output=True, text=True)
    if proc.returncode != 0 or not path.exists():
        raise RuntimeError(f"births child failed ({mode} {world} {seed}): {proc.stderr.strip()[-400:]}")
    return path


def run_cost_child(tree: Path, out: Path, world: str, seed: int, ticks: int, label: str, recording_off: bool = False) -> Path:
    """The cost-only child on any tree (the frozen main tree for the main arm); same pinned kernel, no births imports."""
    path = out / f"{world}_{seed}_{label}.json"
    proc = subprocess.run([sys.executable, str(COST_CHILD), world, str(seed), str(ticks), str(path)], cwd=tree, env=child_env(tree, recording_off), capture_output=True, text=True)
    if proc.returncode != 0 or not path.exists():
        raise RuntimeError(f"cost child failed ({label} {world} {seed}): {proc.stderr.strip()[-400:]}")
    return path


def run_child_measured(tree: Path, out: Path, world: str, seed: int, ticks: int, mode: str, recording_off: bool = False, tag: str = "") -> Dict[str, Any]:
    """The cost probe's child run: wall time and the child's own peak RSS (wait4's rusage, in MB), and the on-disk size of its output files."""
    path = out / f"{world}_{seed}_{mode}{tag}.json"
    cmd = [sys.executable, str(COST_CHILD if mode in ("main", "head_cost") else CHILD), world, str(seed), str(ticks)] + ([mode, str(path)] if mode not in ("main", "head_cost") else [str(path)])
    started = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=tree, env=child_env(tree, recording_off), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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


def bar_status(total_births: int, regioned_births: int, bars: Dict[str, int], twin_equal: bool, mismatches: int, risings: Optional[int] = None) -> str:
    """PASS / FAIL / STOP, mechanically: STOP when no births, no regioned births or (when given) no risings exist (nothing to assess), FAIL on any bar count or a differing twin hash, else PASS."""
    if total_births == 0 or regioned_births == 0 or risings == 0:
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


def reproduction_balance(spied: Dict[Tuple[str, int], dict]) -> Dict[str, Any]:
    """BALANCE rows, report only: conceptions and births per world x seed x kind, the litter distribution, unplaced newborns, pregnancies ended by the mother's death, births with a dead father,
    risings per source species, and the G5 vacuity note (0 conceptions on a bond species)."""
    out: Dict[str, Any] = {"conceptions_per_cell": {}, "births_per_cell": {}, "litter_sizes": {}, "unplaced": {}, "ended_by_mother_death": {}, "father_dead_at_term": {}, "risings_per_cell": {}}
    litters: Counter = Counter()
    for (world, seed), doc in sorted(spied.items()):
        cell = f"{world}/{seed}"
        out["conceptions_per_cell"][cell] = len(doc["conceptions"])
        out["births_per_cell"][cell] = doc["births_by_kind"]
        out["unplaced"][cell] = len(doc["unplaced"])
        out["ended_by_mother_death"][cell] = len(doc["ended"])
        out["father_dead_at_term"][cell] = doc["father_dead_at_term"]
        out["risings_per_cell"][cell] = len(doc["risings"])
        litters.update(c["litter"] for c in doc["conceptions"])
    out["litter_sizes"] = {str(k): v for k, v in sorted(litters.items())}
    out["conceptions_total"] = sum(out["conceptions_per_cell"].values())
    out["g5_vacuous"] = out["conceptions_total"] == 0
    out["step_report_lines"] = list(STEP_REPORT_LINES)
    return out


STEP_REPORT_LINES = (
    "gestation is compressed; maturity is not, so no newborn breeds in any run.",
    "the extinction line counts live bodies from state.entities and never reads population_young or any region cohort counter.",
    "a newborn stays CHILD for the whole run (D4); a newborn's body is its species' declared newborn body (newborn_archetype) at life stage CHILD, with no child stat scaling in M1.",
)


def summarise(docs: Dict[Key, dict]) -> dict:
    spied = {(w, s): d for (w, s, m), d in docs.items() if m == "spied"}
    twins = {(w, s): docs.get((w, s, "plain")) for (w, s) in spied}
    bars = {bar: sum(d["bars"][bar] for d in spied.values()) for bar in BARS}
    twin_equal = all((twins[k] or {}).get("final_hash") == d["final_hash"] for k, d in spied.items())
    cohort = cohort_summary(docs)
    total_births = sum(sum(d["births_by_kind"].values()) for d in spied.values())
    risings = sum(len(d["risings"]) for d in spied.values())
    return {
        "reproduction": reproduction_balance(spied),
        "bars": bars, "twin_hash_equal": {f"{w}/{s}": (twins[(w, s)] or {}).get("final_hash") == d["final_hash"] for (w, s), d in sorted(spied.items())},
        "pinned": sorted({d["runner"] for d in docs.values() if "runner" in d}), "total_births": total_births,
        "births_by_world_seed_kind": {f"{w}/{s}": d["births_by_kind"] for (w, s), d in sorted(spied.items())},
        "max_entity_id": max((d["max_entity_id_seen"] for d in spied.values()), default=0), "runs": len(docs),
        "check6": cohort, "check3": {"tables": death_tables(docs), "ratios": ratios_per_world(docs)},
        "bar_status": bar_status(total_births, cohort["regioned_births"], bars, twin_equal, cohort["mismatch_total"], risings),
        "risings_total": risings,
        "newborn_role_sources": {f"{w}/{s}": d.get("role_sources", {}) for (w, s), d in sorted(spied.items())},  # reported; other_no_archetype > 0 is a FINDING
        "other_no_archetype_total": sum(d.get("role_sources", {}).get("other_no_archetype", 0) for d in spied.values()),
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


# ---- the cost read (pure, unit-tested) ---------------------------------------------------------------------------------------------------------------
COST_STAGE_NAMES = ("governance_ecology", "economy", "cooperation", "combat_engagement")


def stage_stats(costs: List[List[float]], stage_index: int) -> Dict[str, Any]:
    """One stage of one run: the median, p90 and interquartile range per tick and the cost per entity-tick, with stall ticks dropped (total tick time above STALL_FACTOR x the run median) and counted.

    ``costs`` rows are [tick, governance_ecology, economy, cooperation, combat_engagement, total_ms, live_bodies]; ``stage_index`` is 1..4."""
    if not costs:
        return {"ticks": 0}
    totals = [row[5] for row in costs]
    median_total = statistics.median(totals)
    kept = [row for row in costs if row[5] <= STALL_FACTOR * median_total]
    dropped = len(costs) - len(kept)
    values = [row[stage_index] for row in kept]
    quantiles = statistics.quantiles(values, n=20) if len(values) >= 2 else [values[0] if values else 0.0] * 19
    quartiles = statistics.quantiles(values, n=4) if len(values) >= 2 else [values[0] if values else 0.0] * 3
    entity_ticks = sum(row[6] for row in kept)
    return {
        "ticks": len(costs), "stall_ticks_dropped": dropped, "stall_fraction": dropped / len(costs), "median_ms": statistics.median(values) if values else 0.0,
        "p90_ms": quantiles[17], "iqr_ms": quartiles[2] - quartiles[0], "ms_per_entity_tick": (sum(values) / entity_ticks) if entity_ticks else None,
    }


def host_summary(host: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The host load of one run: the highest 1-minute loadavg, the steal jiffies gained and the lowest MemAvailable (kB)."""
    loads = [float(h["loadavg"][0]) for h in host if h.get("loadavg")]
    steals = [h["steal_jiffies"] for h in host if h.get("steal_jiffies") is not None]
    mems = [h["mem_available_kb"] for h in host if h.get("mem_available_kb") is not None]
    return {"loadavg1_max": max(loads, default=None), "steal_jiffies_gained": (steals[-1] - steals[0]) if steals else None, "mem_available_kb_min": min(mems, default=None)}


def cost_report(docs: Dict[Key, dict]) -> Dict[str, Any]:
    """Per world x seed and stage: the head plain run(s) against the main run(s), medians with spread, cost per entity-tick, the head-vs-head noise band from the repeat pair, and the flags.

    Flags (fixed before any data): a cell whose head/main median gap is >= JUMP_SINGLE; a stage whose gap exceeds both JUMP_HELD_GAP and that cell's noise band in >= HELD_CELLS cells (held across
    cells); a cell with more than STALL_REDO_FRACTION stall ticks is marked for a rerun. Raw times and the host load are in the rows."""
    cells = sorted({(w, s) for (w, s, m) in docs if m in ("main", "main_r2")})
    rows: Dict[str, Any] = {}
    held: Dict[str, List[str]] = {stage: [] for stage in COST_STAGE_NAMES}
    single: List[str] = []
    redo: List[str] = []
    for world, seed in cells:
        head_runs = [docs[k] for k in ((world, seed, "plain"), (world, seed, "plain_r2")) if k in docs]
        main_runs = [docs[k] for k in ((world, seed, "main"), (world, seed, "main_r2")) if k in docs]
        cell = f"{world}/{seed}"
        rows[cell] = {"host": {"head": [host_summary(d["host"]) for d in head_runs], "main": [host_summary(d["host"]) for d in main_runs]}, "stages": {}}
        for index, stage in enumerate(COST_STAGE_NAMES, start=1):
            head = [stage_stats(d["phase_costs"], index) for d in head_runs]
            main = [stage_stats(d["phase_costs"], index) for d in main_runs]
            head_med = statistics.mean(h["median_ms"] for h in head) if head else None
            main_med = statistics.mean(m["median_ms"] for m in main) if main else None
            gap = (head_med - main_med) / main_med if head_med is not None and main_med else None
            noise = abs(head[0]["median_ms"] - head[1]["median_ms"]) / head[0]["median_ms"] if len(head) > 1 and head[0]["median_ms"] else None
            rows[cell]["stages"][stage] = {"head": head, "main": main, "gap": gap, "head_vs_head_noise": noise}
            if gap is not None and gap >= JUMP_SINGLE:
                single.append(f"{cell}/{stage}")
            if gap is not None and gap > JUMP_HELD_GAP and gap > (noise or 0.0):
                held[stage].append(cell)
            redo.extend(f"{cell}/{stage}/{label}" for label, run in (("head", head), ("main", main)) for r in run if r.get("stall_fraction", 0.0) > STALL_REDO_FRACTION)
    return {
        "cells": rows, "single_cell_jumps": single, "jumps_held_across_cells": {stage: cells_ for stage, cells_ in held.items() if len(cells_) >= HELD_CELLS},
        "rerun_for_stalls": sorted(set(redo)),
        "rule": {"stall": f"total tick time > {STALL_FACTOR} x run median", "single": JUMP_SINGLE, "held_gap": JUMP_HELD_GAP, "held_cells": HELD_CELLS, "redo_fraction": STALL_REDO_FRACTION},
    }


# ---- the trigger-neutrality read (pure, unit-tested) ---------------------------------------------------------------------------------------------------
def trigger_cell(on: dict, off: dict, pos: dict) -> Dict[str, Any]:
    """One world x seed: the HARD neutrality equalities between ON (real trigger, rise chance 0) and OFF (trigger off, rise off), the firing counts and the positive control.

    PASS needs: state hash, event stream and metrics all equal; ON firings > 0 and extra runs > 0; OFF 0 and 0; the positive control (trigger on, chance 1.0) differing from OFF; no corpse at tick 0.
    VACUOUS when ON fired 0 times OR fired but changed no phase run (extra_phase_runs == 0: resource_transactions ran anyway on every firing tick, so the trigger had nothing to change); it is rerun
    at the longer tick count. FAIL on any mismatch, a nonzero OFF count or a control that cannot fail."""
    equal = {"state_hash": on["final_hash"] == off["final_hash"], "events": on["event_digest"] == off["event_digest"], "metrics": on["metrics_digest"] == off["metrics_digest"]}
    on_t, off_t = on["trigger"], off["trigger"]
    control_differs = pos["final_hash"] != off["final_hash"] or pos["event_digest"] != off["event_digest"]
    row = {
        "equal": equal, "on": on_t, "off": off_t, "control_differs_from_off": control_differs, "corpses_at_t0": [on["corpses_at_t0"], off["corpses_at_t0"]],
        "ticks": on["ticks"],
    }
    if on_t["firings"] == 0 or on_t["extra_phase_runs"] == 0:
        return {**row, "verdict": "VACUOUS"}
    ok = all(equal.values()) and on_t["extra_phase_runs"] > 0 and off_t["firings"] == 0 and off_t["extra_phase_runs"] == 0 and control_differs and not any(row["corpses_at_t0"])
    return {**row, "verdict": "PASS" if ok else "FAIL"}


def trigger_report(docs: Dict[Key, dict]) -> Dict[str, Any]:
    """Every trigger cell, and the world-level STOP: a world with no cell where the trigger changed a phase run (extra_phase_runs > 0) is a STOP to rpg-designer-ubuntu."""
    cells = sorted({(w, s) for (w, s, m) in docs if m == "trigger_on"})
    rows = {f"{w}/{s}": trigger_cell(docs[(w, s, "trigger_on")], docs[(w, s, "trigger_off")], docs[(w, s, "trigger_pos")]) for (w, s) in cells}
    stops = sorted({w for (w, _) in cells if not any(r["on"]["extra_phase_runs"] > 0 for k, r in rows.items() if k.startswith(f"{w}/"))})
    verdict = "STOP" if stops else "FAIL" if any(r["verdict"] == "FAIL" for r in rows.values()) else "VACUOUS" if any(r["verdict"] == "VACUOUS" for r in rows.values()) else "PASS"
    return {"cells": rows, "worlds_with_no_firing": stops, "verdict": verdict}


def run_evidence(args: argparse.Namespace) -> int:
    """Evidence block, serial: per cell the head arms, then the interleaved head plain / main cost pair, and for seed 42 a second pair (the noise band)."""
    docs: Dict[Key, dict] = {}

    def head(world: str, seed: int, mode: str, tag: str = "") -> None:
        docs[(world, seed, mode + tag)] = json.loads(run_child(args.tree, args.out, world, seed, args.ticks, mode, args.recording_off, tag).read_text(encoding="utf-8"))

    def main_arm(world: str, seed: int, label: str) -> None:
        if args.main_tree is not None:
            docs[(world, seed, label)] = json.loads(run_cost_child(args.main_tree, args.out, world, seed, args.ticks, label, args.recording_off).read_text(encoding="utf-8"))

    for world in args.worlds:
        for seed in args.seeds:
            head(world, seed, "spied")
            head(world, seed, "control")
            head(world, seed, "plain")
            main_arm(world, seed, "main")
            if seed == paired.SEEDS[0]:
                head(world, seed, "plain", "_r2")
                main_arm(world, seed, "main_r2")
    keys = sorted(k for k in docs if k[2] in ARMS)
    summary = {**summarise({k: docs[k] for k in keys}), "first_position_divergence": divergence_report(args.out, {k: docs[k] for k in keys}), "limits": list(LIMITS), "bases": BASES,
               "cohort_flag_rule": COHORT_FLAG_RULE, "go": args.go, "ticks": args.ticks, "block": "evidence", "recording_off": args.recording_off}
    summary["twin_hash_equal_repeat"] = {f"{w}/{s}": docs[(w, s, "plain_r2")]["final_hash"] == docs[(w, s, "plain")]["final_hash"] for (w, s, m) in sorted(docs) if m == "plain_r2"}
    if args.main_tree is not None:
        summary["cost"] = cost_report(docs)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def run_trigger(args: argparse.Namespace) -> int:
    """Trigger block: s42 x (on, off, pos) at 1000 ticks; a world whose ON arm fired 0 times is rerun at 5000 ticks and BOTH runs are printed."""
    reports: Dict[str, Any] = {}
    for ticks in (args.ticks, TRIGGER_RERUN_TICKS):
        worlds = args.worlds if ticks == args.ticks else [w for w in args.worlds if reports[f"{args.ticks}t"]["cells"] and all(
            r["verdict"] == "VACUOUS" for k, r in reports[f"{args.ticks}t"]["cells"].items() if k.startswith(f"{w}/"))]
        if not worlds:
            continue
        docs: Dict[Key, dict] = {}
        out = args.out / f"{ticks}t"
        out.mkdir(parents=True, exist_ok=True)
        for world in worlds:
            for seed in args.seeds:
                for mode in TRIGGER_ARMS:
                    docs[(world, seed, mode)] = json.loads(run_child(args.tree, out, world, seed, ticks, mode, args.recording_off).read_text(encoding="utf-8"))
        reports[f"{ticks}t"] = trigger_report(docs)
        reports[f"{ticks}t"]["bars"] = {bar: sum(d["bars"][bar] for d in docs.values()) for bar in BARS}
    latest: Dict[str, List[Dict[str, Any]]] = {}
    for report in reports.values():
        for cell, row in report["cells"].items():
            latest[cell.split("/")[0]] = [r for c, r in report["cells"].items() if c.startswith(cell.split("/")[0] + "/")]
    cell_verdicts = [r["verdict"] for rows in latest.values() for r in rows]
    stop = any(not any(r["on"]["extra_phase_runs"] > 0 for r in rows) for rows in latest.values())
    final = "STOP" if stop else "FAIL" if "FAIL" in cell_verdicts else "PASS"
    summary = {"block": "trigger", "reports": reports, "verdict": final, "limits": list(LIMITS), "go": args.go, "recording_off": args.recording_off}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def probe_hash_check(recording_off_hash: str, recorded_hash: str) -> Dict[str, Any]:
    """The 5000-tick proof that recording-off is hash-neutral: the probe's plain arm run recording-off (OBS OFF + no_replay) against the same plain run with recording ON. Unequal hashes are a STOP."""
    equal = recording_off_hash == recorded_hash
    return {"equal": equal, "recording_off_plain": recording_off_hash, "recording_on_plain": recorded_hash, "verdict": "PASS" if equal else "STOP"}


def run_probe(args: argparse.Namespace) -> int:
    """Cost probe: one world x one seed, one arm at a time, the head arms, a trigger arm, (with --main-tree) the main cost run and, under --recording-off, one extra recording-ON plain arm."""
    seed = args.seeds[0]
    rows = [run_child_measured(args.tree, args.out, PROBE_WORLD, seed, args.ticks, mode, args.recording_off) for mode in (*ARMS, "trigger_on")]
    if args.main_tree is not None:
        rows.append(run_child_measured(args.main_tree, args.out, PROBE_WORLD, seed, args.ticks, "main", args.recording_off))
    report = {"cost_probe": rows, "world": PROBE_WORLD, "seed": seed, "ticks": args.ticks, "go": args.go, "scope_cap_mb": 3072, "recording_off": args.recording_off}
    if args.recording_off:
        rows.append({**run_child_measured(args.tree, args.out, PROBE_WORLD, seed, args.ticks, "plain", False, "_recorded"), "mode": "plain_recorded"})
        hash_of = lambda name: json.loads((args.out / f"{PROBE_WORLD}_{seed}_{name}.json").read_text(encoding="utf-8"))["final_hash"]
        report["recording_hash_check"] = probe_hash_check(hash_of("plain"), hash_of("plain_recorded"))
    (args.out / "cost_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report.get("recording_hash_check", {}).get("verdict") == "STOP":
        print("PROBE STOP: the recording-ON plain arm's final hash differs from the recording-off plain arm's; recording-off is not hash-neutral at 5000 ticks")
        return 1
    return 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", required=True, choices=("evidence", "trigger", "probe"))
    ap.add_argument("--tree", required=True, type=Path, help="the head (fix) tree")
    ap.add_argument("--main-tree", type=Path, default=None, help="a frozen main tree for the cost arm (evidence and probe blocks)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--go", required=True, help="reference of the lead-planner go for THIS block")
    ap.add_argument("--ticks", type=int, default=None, help=f"ticks per run (default {paired.TICKS}; {TRIGGER_TICKS} for the trigger block)")
    ap.add_argument("--recording-off", action="store_true", help="recording-off = observability mode OFF + the kernel flag no_replay, in every child including the main-tree cost child (allowed only after the 100-tick check passed)")
    ap.add_argument("--worlds", nargs="*", default=list(paired.WORLDS))
    ap.add_argument("--seeds", nargs="*", type=int, default=None, help=f"default: {list(paired.SEEDS)}; {list(TRIGGER_SEEDS)} for the trigger block")
    args = ap.parse_args(argv)
    args.ticks = args.ticks or (TRIGGER_TICKS if args.block == "trigger" else paired.TICKS)
    args.seeds = args.seeds or (list(TRIGGER_SEEDS) if args.block == "trigger" else list(paired.SEEDS))
    args.out.mkdir(parents=True, exist_ok=True)
    return {"evidence": run_evidence, "trigger": run_trigger, "probe": run_probe}[args.block](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
