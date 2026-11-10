"""Turns the ``*.audit.json`` files the evidence runner dumps into the report's markdown tables (plan section 2, item 6). Pure: paths in, text out; it imports the declarations (data) only,
never the simulation, so nothing here is on the run path."""
from __future__ import annotations

import fnmatch
import json
import sys
from typing import Any, Dict, Iterable, List, Sequence, Set

from src.engine.access_audit.declarations import DECLARATIONS, StepDeclaration

# Why a declared step can be unobserved on the gate worlds: read from a probe of the flag modes (the cell JSONs carry no skip counters).
FLAG_OFF_STEPS: Dict[str, str] = {
    "memory_update": "ENABLE_MEMORY_UPDATE",
    "habit_bias_action_style": "ENABLE_HABIT_BIAS_ACTION_STYLE",
    "role_model_selection": "ENABLE_ROLE_MODEL_IMITATION",
    "self_model": "ENABLE_SELF_MODEL_COGNITION",
    "information_intent_execution": "ENABLE_INFORMATION_INTENT_EXECUTION",
    "information_propagation": "ENABLE_INFORMATION_HUB_ACCUMULATION",
    "world_emergence": "ENABLE_WORLD_EMERGENCE",
    "progression_conversion": "ENABLE_PROGRESSION_EVOLUTION",
}


def load_cells(paths: Iterable[str]) -> List[Dict[str, Any]]:
    """Read each audit JSON (``per_phase`` plus the runner's extra facts)."""
    cells = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            cells.append(json.load(fh))
    return cells


def _row(*cols: Any) -> str:
    return "| " + " | ".join(str(c) for c in cols) + " |"


def _table(header: Sequence[str], rows: Iterable[str]) -> List[str]:
    return [_row(*header), _row(*["---"] * len(header)), *rows, ""]


def aggregate(cells: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per step: set-valued fields united over cells, per-field tick counters summed, ``*_max`` fields maxed."""
    agg: Dict[str, Dict[str, Any]] = {}
    for cell in cells:
        for step, rec in cell.get("per_phase", {}).items():
            _merge(agg.setdefault(step, {}), rec)
    return agg


def _merge(into: Dict[str, Any], rec: Dict[str, Any]) -> None:
    for key, value in rec.items():
        if isinstance(value, list):
            into.setdefault(key, set()).update(value)
        elif isinstance(value, dict):
            _merge_dict(into.setdefault(key, {}), value, take_max=key.endswith("_max"))
        elif isinstance(value, int):
            into[key] = max(into.get(key, 0), value) if key.endswith("_max") else into.get(key, 0) + value


def _merge_dict(into: Dict[str, int], value: Dict[str, int], take_max: bool) -> None:
    for k, v in value.items():
        into[k] = max(into.get(k, 0), v) if take_max else into.get(k, 0) + v


def _covered(write: str, declared: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(write, pattern) for pattern in declared)


def _declared(rows: Dict[str, StepDeclaration]) -> List[StepDeclaration]:
    return list(rows.values())


def run_table(cells: Sequence[Dict[str, Any]]) -> List[str]:
    """One row per cell: world, seed, observations, distinct steps observed, wall (informational)."""
    rows = [_row(f"{c.get('world')} s{c.get('seed')}", c.get("observations", 0), len(c.get("per_phase", {})), c.get("wall_s_not_a_measurement", "-")) for c in cells]
    return _table(["cell", "observations", "distinct steps observed", "wall s (informational, not a perf measurement)"], rows)


def unobserved_table(agg: Dict[str, Dict[str, Any]], rows: Dict[str, StepDeclaration]) -> List[str]:
    """Declared steps never observed, with the flag that is OFF when it is known."""
    missing = [d.name for d in _declared(rows) if d.name not in agg]
    return _table(["step", "flag (OFF = skipped by run_phase)"], [_row(m, FLAG_OFF_STEPS.get(m, "reason not recorded")) for m in missing])


def undeclared_writes(agg: Dict[str, Dict[str, Any]], rows: Dict[str, StepDeclaration]) -> List[str]:
    """Observed writes the step's declaration does not list (and how many of the observed steps have any)."""
    out = [(d.name, sorted(w for w in agg[d.name].get("writes", ()) if not _covered(w, d.writes))) for d in _declared(rows) if d.name in agg]
    out = [(name, extra) for name, extra in out if extra]
    lines = _table(["step", "undeclared observed writes"], [_row(n, ", ".join(e)) for n, e in out])
    return [*lines, f"{len(out)} of {sum(1 for d in _declared(rows) if d.name in agg)} observed steps write something their declaration does not list.", ""]


def hidden_table(agg: Dict[str, Dict[str, Any]], tier: str) -> List[str]:
    """Hidden mutations with tick counts; ``tier`` is ``watch`` (Tier 1) or ``promote`` (Tier 2 hits)."""
    rows = []
    for step, rec in agg.items():
        promote: Set[str] = set(rec.get("promote", ()))
        fields = [f for f in rec.get("hidden_state_mutations", ()) if (f in promote) == (tier == "promote")]
        if fields:
            ticks = rec.get("hidden_ticks", {})
            rows.append(_row(step, ", ".join(f"{f} ({ticks.get(f, '?')} ticks)" for f in sorted(fields))))
    return _table(["step", "field (ticks seen, summed over cells)"], rows)


def global_table(agg: Dict[str, Dict[str, Any]]) -> List[str]:
    """Process-global changes, or the explicit none-detected line."""
    rows = [_row(step, ", ".join(f"{g} ({n} ticks)" for g, n in sorted(rec["global_ticks"].items()))) for step, rec in agg.items() if rec.get("global_ticks")]
    return _table(["step", "process global"], rows) if rows else ["No process-global change detected (watch list: see Limits).", ""]


def fanout_table(agg: Dict[str, Dict[str, Any]]) -> List[str]:
    """Cross-entity proxies: entries created for an id absent from the input update, and the most distinct entity ids written per bucket in one tick."""
    rows = [_row(s, r.get("created_entries_ticks", 0), r.get("created_entries_max", 0), ", ".join(f"{b} ({n})" for b, n in sorted(r.get("fanout_max", {}).items())) or "-")
            for s, r in agg.items() if r.get("created_entries_ticks") or r.get("fanout_max")]
    return _table(["step", "ticks creating entries", "max entries created", "max distinct entity ids written per bucket"], rows)


def inplace_table(agg: Dict[str, Dict[str, Any]]) -> List[str]:
    """Steps that mutate the INPUT update in place."""
    return _table(["step", "bucket(s) mutated in place"], [_row(s, ", ".join(sorted(r["inplace_update_mutations"]))) for s, r in agg.items() if r.get("inplace_update_mutations")])


def identity_table(agg: Dict[str, Dict[str, Any]]) -> List[str]:
    """A3 column: buckets replaced by an equal object (identity changed, value did not), and buckets whose ``==`` raised."""
    rows = [_row(s, ", ".join(sorted(r.get("identity_only", ()))) or "-", ", ".join(sorted(r.get("unsafe_equality", ()))) or "-") for s, r in agg.items() if r.get("identity_only") or r.get("unsafe_equality")]
    return _table(["step", "identity-only (object replaced, value equal)", "== not safe (treated as changed)"], rows)


def sample_lines(cells: Sequence[Dict[str, Any]]) -> List[str]:
    """The sampled mutable-timeline-element check: samples taken and findings (each a finding to localise later)."""
    lines = []
    for c in cells:
        s = c.get("timeline_content_sampled")
        if s is not None:
            lines.append(f"- {c.get('world')} s{c.get('seed')}: {s.get('samples', 0)} samples every {s.get('every_ticks')} ticks, {len(s.get('findings', []))} finding(s)" + "".join(f"; {f}" for f in s.get("findings", [])))
    return [*lines, ""]


def render(cells: Sequence[Dict[str, Any]], rows: Dict[str, StepDeclaration] | None = None) -> str:
    """The data sections of the report as markdown (the prose sections are written around these)."""
    rows = DECLARATIONS if rows is None else rows
    agg = aggregate(cells)
    sections = [
        ("Run", run_table(cells)),
        ("Declared, not exercised on the gate worlds", unobserved_table(agg, rows)),
        ("In-place mutation of the input update", inplace_table(agg)),
        ("Observed writes not in the declaration", undeclared_writes(agg, rows)),
        ("Hidden mutations: watch list (Tier 1)", hidden_table(agg, "watch")),
        ("Hidden mutations: Tier 2 hits (promote to the watch list)", hidden_table(agg, "promote")),
        ("Sampled content check of mutable timeline elements (sampled, not per step)", sample_lines(cells)),
        ("Process globals", global_table(agg)),
        ("Cross-entity proxies", fanout_table(agg)),
        ("Identity-only replacements (A3)", identity_table(agg)),
    ]
    return "\n".join(line for title, body in sections for line in (f"## {title}", "", *body))


def main(argv: Sequence[str]) -> int:
    """``python -m src.engine.access_audit.report <out.md> <cell.audit.json>...``"""
    out, *paths = argv
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(load_cells(paths)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
