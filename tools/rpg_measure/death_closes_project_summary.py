"""Summarize the death-closes-project own-job cells (reads the JSONs of ``death_closes_project_spy``; the designer's fixed bars D1-D7, rpg-designer-death-closes-ownjob-definition.md sha256 df2ba4b5...).

Usage: python death_closes_project_summary.py [--smoke] <BASE_OUT> <FIX_OUT>   (each dir holds <world>_s<seed>_t<ticks>_{plain,spy}.json; BASE has the spy only, FIX the spy and its plain twin)
Per cell: D1 dead_with_live == 0 every tick (FIX); D2 DEATH ends are ABANDONED at the body's death tick on a dead body (FIX); D3 records kept (FIX); D4 non-vacuity (BASE: dead_with_live sum > 0 and >= 5 dead bodies with a live
project at death; a thin cell is D4 NOT MEASURED, its D1 NOT MEASURED and the world is widened to s43-46: exit 5, not a failure); D5 lag rows resolved by T+1 (FIX); D6 FIX spied hash == FIX plain hash; D7 neutrality: the LIVING PROJECTION digest (the masked strategic hash) equal at every tick, the FULL event
stream digest equal (no category is masked in the run: quest events stay visible, 2.226 leaves quest_status alone), (the state-diff ended count, DEATH ends vs FIX minus BASE ended transitions, sits in the D7 dict and is REPORT-ONLY: on BASE another writer can end a dead body's project later, so a mismatch is printed, never a status); a cell with no death that held a live or current project must be FULL-hash equal. A D7 divergence is a STOP (exit 4) to the designer; it is never attributed here.
REPORTED, never bars: the ACTIVE/SUSPENDED split, quest-open rows, the typed ABANDONED-by-ended_by figure (SimQ project_abandoned is NOT MEASURED: recording is off),
and the capacity_enforcement / redirection writes on a dead-or-dying body that holds a live or current project. Exit: 0 no bar failed and nothing to widen, 2 a bar failed or a cell is void, 4 a D7 STOP, 5 no bar failed but a thin cell needs widening to s43-46. ``--smoke`` only checks that the pipeline observed the run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORLDS = ("crowded_frontier", "frontier_living_world", "urban_political")
SEED, TICKS = 42, 5000
WIDEN_SEEDS = (43, 44, 45, 46)
MIN_DEAD_WITH_LIVE = 5
PASS, FAIL, NM, STOP = "PASS", "FAIL", "NOT MEASURED", "STOP"
SIMQ_LINE = "NOT MEASURED (recording is off in this kit); the typed figure is abandoned_by below"


def load(out: Path, world: str, seed: int, ticks: int, mode: str) -> Dict[str, Any]:
    path = out / f"{world}_s{seed}_t{ticks}_{mode}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def void_reasons(doc: Dict[str, Any], label: str) -> List[str]:
    if not doc:
        return [f"{label}: cell missing"]
    out = []
    if doc.get("fatal") or doc.get("findings") or doc.get("spy_exceptions") or doc.get("logging_errors"):
        out.append(f"{label}: fatal / finding / spy exception / logging error")
    return out


def first_divergence(a: Dict[str, str], b: Dict[str, str]) -> Optional[Tuple[str, str, str]]:
    for tick in sorted(set(a) | set(b), key=int):
        if a.get(tick) != b.get(tick):
            return tick, str(a.get(tick)), str(b.get(tick))
    return None


def cell_summary(base_dir: Path, fix_dir: Path, world: str, seed: int, ticks: int, smoke: bool = False) -> Dict[str, Any]:
    base, fix, twin = load(base_dir, world, seed, ticks, "spy"), load(fix_dir, world, seed, ticks, "spy"), load(fix_dir, world, seed, ticks, "plain")
    problems = void_reasons(base, "BASE spy") + void_reasons(fix, "FIX spy") + void_reasons(twin, "FIX plain twin")
    cell = {"cell": f"{world}_s{seed}_t{ticks}", "problems": problems, "bars": {}, "reported": {}, "widen": False}
    if problems:
        return cell
    bars: Dict[str, Dict[str, Any]] = cell["bars"]
    cell["observed"] = {"base_ticks": base.get("distinct_ticks"), "fix_ticks": fix.get("distinct_ticks"), "base_dead_bodies": base.get("dead_bodies"), "fix_dead_bodies": fix.get("dead_bodies"), "base_apply_calls": base.get("apply_calls"), "fix_apply_calls": fix.get("apply_calls")}
    bars["D6"] = {"status": PASS if fix.get("final_hash") == twin.get("final_hash") else FAIL, "fix_spy_hash": fix.get("final_hash"), "fix_plain_hash": twin.get("final_hash")}
    if smoke:
        ok = base.get("distinct_ticks") == ticks and fix.get("distinct_ticks") == ticks
        bars["SMOKE"] = {"status": PASS if ok and bars["D6"]["status"] == PASS else FAIL, "ticks_observed_base_fix": [base.get("distinct_ticks"), fix.get("distinct_ticks")]}
        return cell
    measured = base.get("dwl_sum", 0) > 0 and base.get("dead_at_death_with_live", 0) >= MIN_DEAD_WITH_LIVE
    bars["D4"] = {"status": PASS if measured else NM, "base_dwl_sum": base.get("dwl_sum"), "base_dead_at_death_with_live": base.get("dead_at_death_with_live"), "min": MIN_DEAD_WITH_LIVE}
    cell["widen"] = not measured
    d1_zero = fix.get("dwl_total_rows", 0) == 0
    bars["D1"] = {"status": (PASS if d1_zero else FAIL) if measured else NM, "fix_dwl_sum": fix.get("dwl_sum"), "first_rows": fix.get("dwl_rows", [])[:5]}
    if not measured and not d1_zero:
        bars["D1"]["status"] = FAIL          # a violation is a violation even where the cell is thin
    bars["D2"] = {"status": PASS if fix.get("d2_violations") == 0 else FAIL, "violations": fix.get("d2_violations"), "rows": fix.get("d2_rows", [])[:5]}
    bars["D3"] = {"status": PASS if fix.get("d3_violations") == 0 else FAIL, "violations": fix.get("d3_violations"), "rows": fix.get("d3_rows", [])[:5]}
    bars["D5"] = {"status": PASS if fix.get("lag_over_one_tick") == 0 else FAIL, "lag_rows": fix.get("lag_total"), "over_one_tick": fix.get("lag_over_one_tick"), "unjudged_at_run_end": fix.get("lag_unjudged_at_run_end"), "rows": fix.get("lag_over_one_tick_rows", [])[:5]}
    d7_living = first_divergence(base.get("living_by_tick", {}), fix.get("living_by_tick", {}))
    d7_events = first_divergence(base.get("events_by_tick", {}), fix.get("events_by_tick", {}))
    no_such_death = base.get("dead_at_death_with_live", 0) == 0
    full_equal = base.get("final_hash") == fix.get("final_hash")
    death_ends = fix.get("ends_by", {}).get("DEATH", 0)
    extra = fix.get("ends_total", 0) - base.get("ends_total", 0)
    d7: Dict[str, Any] = {"living_projection_first_divergence": d7_living, "living_event_stream_first_divergence": d7_events, "no_death_held_live_or_current": no_such_death, "full_hash_equal": full_equal,
                          "ended_count": {"death_ends": death_ends, "extra_ended_transitions_fix_minus_base": extra, "equal": death_ends == extra}}
    if d7_living or d7_events:
        d7["status"] = STOP
        d7["note"] = "STOP to the designer: first tick shown; locate the field path and body with death_closes_project_divergence_locate on --dump-tick runs. Not attributed here."
    elif no_such_death and not full_equal:
        d7["status"] = FAIL
        d7["note"] = "a cell with no such death must be FULL-hash equal"
    else:
        d7["status"] = PASS
    bars["D7"] = d7
    cell["reported"] = {"death_ends": death_ends, "extra_ended_transitions_fix_minus_base": extra, "death_ends_equal_extra": death_ends == extra, "death_split_active_suspended": fix.get("death_split"),
                        "suspended_branch_unit_only": fix.get("death_split", {}).get("SUSPENDED", 0) == 0, "quest_open_after_death": fix.get("quest_open_after_death_count"),
                        "abandoned_by_ended_by": {"base": base.get("abandoned_by"), "fix": fix.get("abandoned_by")}, "simq_project_abandoned": SIMQ_LINE,
                        "phase_writes_on_dead_or_dying_with_live": {"base": base.get("phase_rows"), "fix": fix.get("phase_rows")}}
    return cell


def cells_in(base_dir: Path, fix_dir: Path) -> List[Tuple[str, int, int]]:
    found: List[Tuple[str, int, int]] = []
    for path in sorted(fix_dir.glob("*_spy.json")):
        stem = path.name[: -len("_spy.json")]
        world, _, rest = stem.rpartition("_s")
        seed, _, ticks = rest.partition("_t")
        found.append((world, int(seed), int(ticks)))
    return found


def verdict(cells: List[Dict[str, Any]]) -> int:
    if any(b["status"] == STOP for c in cells for b in c["bars"].values()):
        return 4
    if not cells or any(c["problems"] or any(b["status"] == FAIL for b in c["bars"].values()) for c in cells):
        return 2
    return 5 if any(c["widen"] for c in cells) else 0


def main(argv: List[str]) -> int:
    smoke = "--smoke" in argv
    args = [a for a in argv if a != "--smoke"]
    base_dir, fix_dir = Path(args[0]), Path(args[1])
    cells = [cell_summary(base_dir, fix_dir, w, s, t, smoke) for w, s, t in cells_in(base_dir, fix_dir)]
    (fix_dir / "death_closes_project_summary.json").write_text(json.dumps({"cells": cells}, sort_keys=True, indent=1, default=str), encoding="utf-8")
    for c in cells:
        marks = " ".join(f"{k}={b['status']}" for k, b in sorted(c["bars"].items()))
        print(f"{c['cell']}: {marks}{' WIDEN to s43-46' if c['widen'] else ''} problems={c['problems']}")
        ended = c["bars"].get("D7", {}).get("ended_count")
        if ended and not ended["equal"]:
            print(f"    ended_count MISMATCH (report-only): death_ends={ended['death_ends']} extra_ended_transitions_fix_minus_base={ended['extra_ended_transitions_fix_minus_base']}")
        if not smoke and c["reported"]:
            print(f"    reported: {json.dumps(c['reported'], sort_keys=True, default=str)}")
    return verdict(cells)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
