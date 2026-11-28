"""Perception-gate calibration own-job summary (PERC 3a; rpg-designer ruling 9c42fb88). NOT RUN by the author.

Usage: python perception_gate_calibration_summary.py [--smoke] <BASE_OUT> <FIX_OUT>   (each dir holds ``<world>_s<seed>_t<ticks>_plain.json`` and ``_spy.json`` per cell)

HARD (exit 2 on a failure): H1 every spied cell's final hash equals its plain twin's, on both arms; every cell exit-clean (no fatal, no logging errors, no spy exception, a replay redirect).
STOP (exit 4): a collapse to 0: in a cell where the BASE count is > 0, the FIX count of perceived hostile pairs, perceived prey pairs, hunts started or engagements started is 0.
REPORTED (not gated): those counts per cell, base vs fix, the perception counters by channel, hits landed, the NON-VACUITY rows (fix: vision-channel perceptions of a still small body by day and of a still medium body
at night must be > 0 in the cells; a cell with 0 is NOT MEASURED, stated, not a pass), and the PERF FLAG (wall per tick, FIX plain / BASE plain, > 1.10 in any cell, with the numbers).
Exit 0 only when no HARD failure and no STOP; a PERF FLAG or a NOT MEASURED row is printed, never silent, and does not change the exit code.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PERF_RATIO = 1.10
COUNTS = ("hunts_started", "engagements_started")
SAMPLED = ("hostile_pairs", "prey_pairs")


def load_cells(out_dir: Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """``{cell: {"plain": doc, "spy": doc}}`` from the arm's output directory."""
    cells: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for path in sorted(out_dir.glob("*_s*_t*_*.json")):
        stem = path.stem
        cell, _, mode = stem.rpartition("_")
        if mode in ("plain", "spy"):
            cells.setdefault(cell, {})[mode] = json.loads(path.read_text(encoding="utf-8"))
    return cells


FIX_LEVELS = {"small": "medium_high", "medium": "high"}
BASE_LEVELS = {"small": "low", "medium": "medium"}


def hard_failures(arm: str, cells: Dict[str, Dict[str, Dict[str, Any]]]) -> List[str]:
    out: List[str] = []
    for cell, modes in cells.items():
        plain, spy = modes.get("plain"), modes.get("spy")
        if plain is None or spy is None:
            out.append(f"{arm} {cell}: missing the {'plain' if plain is None else 'spy'} cell")
            continue
        if spy.get("final_hash") != plain.get("final_hash"):
            out.append(f"{arm} {cell}: H1 spy final_hash != plain twin's")
        for mode, doc in (("plain", plain), ("spy", spy)):
            if doc.get("fatal") or doc.get("logging_errors") or doc.get("spy_exceptions") or doc.get("findings"):
                out.append(f"{arm} {cell} {mode}: not exit-clean (fatal {bool(doc.get('fatal'))}, logging_errors {len(doc.get('logging_errors') or [])}, findings {doc.get('findings')})")
            if (doc.get("replay_dirs_redirected") or 0) < 1:
                out.append(f"{arm} {cell} {mode}: no replay dir redirected")
        expected = FIX_LEVELS if arm == "fix" else BASE_LEVELS
        if spy.get("size_levels") != expected:
            out.append(f"{arm} {cell}: size_levels {spy.get('size_levels')} != the {arm} arm's record {expected} (the spy read the wrong calibration)")
    return out


def collapse_stops(base: Dict[str, Any], fix: Dict[str, Any]) -> List[str]:
    """A count that is > 0 on the BASE arm and 0 on the FIX arm in the same cell."""
    rows = []
    pairs: List[Tuple[str, Any, Any]] = [(k, base.get(k), fix.get(k)) for k in COUNTS]
    pairs += [(f"sampled.{k}", (base.get("sampled") or {}).get(k), (fix.get("sampled") or {}).get(k)) for k in SAMPLED]
    for name, b, f in pairs:
        if (b or 0) > 0 and (f or 0) == 0:
            rows.append(f"{name}: base {b} -> fix {f}")
    return rows


def perf_flags(base_cells: Dict[str, Any], fix_cells: Dict[str, Any]) -> List[str]:
    flags = []
    for cell in sorted(set(base_cells) & set(fix_cells)):
        b, f = base_cells[cell].get("plain"), fix_cells[cell].get("plain")
        if not b or not f or not b.get("wall_per_tick"):
            continue
        ratio = f["wall_per_tick"] / b["wall_per_tick"]
        if ratio > PERF_RATIO:
            flags.append(f"{cell}: wall per tick fix/base = {ratio:.3f} (> {PERF_RATIO}; base {b['wall_per_tick']*1000:.2f} ms, fix {f['wall_per_tick']*1000:.2f} ms)")
    return flags


def render(base_cells: Dict[str, Any], fix_cells: Dict[str, Any]) -> Tuple[List[str], int]:
    lines: List[str] = []
    code = 0
    hard = hard_failures("base", base_cells) + hard_failures("fix", fix_cells)
    for row in hard:
        lines.append(f"HARD FAIL: {row}")
    if hard:
        code = 2
    lines.append("| cell | measure | base | fix |")
    lines.append("|---|---|---|---|")
    stops: List[str] = []
    nv_small = nv_medium = 0
    for cell in sorted(set(base_cells) & set(fix_cells)):
        b, f = base_cells[cell].get("spy") or {}, fix_cells[cell].get("spy") or {}
        for key in ("perceived", "hunts_started", "engagements_started", "bodies_hit", "vision_still_small_day", "vision_still_medium_night"):
            lines.append(f"| {cell} | {key} | {b.get(key)} | {f.get(key)} |")
        for key in SAMPLED:
            lines.append(f"| {cell} | sampled.{key} | {(b.get('sampled') or {}).get(key)} | {(f.get('sampled') or {}).get(key)} |")
        lines.append(f"| {cell} | by_channel | {b.get('by_channel')} | {f.get('by_channel')} |")
        for row in collapse_stops(b, f):
            stops.append(f"{cell} {row}")
        lines.append(f"| {cell} | size_levels | {b.get('size_levels')} | {f.get('size_levels')} |")
        nv_small += f.get("vision_still_small_day") or 0
        nv_medium += f.get("vision_still_medium_night") or 0
        if (f.get("vision_still_small_day") or 0) + (f.get("vision_still_medium_night") or 0) == 0:
            lines.append(f"(info) {cell}: 0 non-vacuity perceptions in this cell")
    lines.append(f"NON-VACUITY total (fix, all cells): vision_still_small_day {nv_small}, vision_still_medium_night {nv_medium}")
    if nv_small + nv_medium == 0:
        lines.append("NOT MEASURED: the fix arm has 0 vision perceptions of a still small body by day and of a still medium body at night in EVERY cell (the ticket's own rows never occurred)")
    for row in stops:
        lines.append(f"STOP (collapse to 0): {row}")
    if stops and code == 0:
        code = 4
    for row in perf_flags(base_cells, fix_cells):
        lines.append(f"PERF FLAG: {row}")
    return lines, code


def main(argv: List[str]) -> int:
    args = [a for a in argv if a != "--smoke"]
    base_cells, fix_cells = load_cells(Path(args[0])), load_cells(Path(args[1]))
    if not base_cells or not fix_cells:
        print("no cells found in one of the output directories", file=sys.stderr)
        return 5
    lines, code = render(base_cells, fix_cells)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
