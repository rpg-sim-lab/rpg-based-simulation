"""Subject trace for the designer's readiness and legality read (Q2; scope word for word at the planner's seat commit 246b065f5). READ-ONLY: it records evidence, it never judges.

One child process per cell, started by ``subject_trace_run`` with cwd = the frozen head tree and PYTHONPATH = that tree. ``--mode spy`` runs the SAME build as the person-attack spy (same pinned check, same
flags, same no-replay injection, recording OFF) with two pass-through wrappers; ``--mode plain`` (used only by the smoke run) runs the build with no wrapper and writes the final hash.

PER-TICK ROWS. For every subject (``--plan`` file, written by ``subject_trace_run derive`` from the SEALED O3 cells) and every tick inside one of its windows, one row built from the prior state (BEFORE the apply)
and the new state (AFTER it): movement mode; task work kind, action, reason and the payload's scalar fields (the goal the entity is executing); ``navigation.target`` (the goal tile), path length and
``navigation.last_failure_reason``; ``combat.readiness``, hp, alive; position; ``lodged_in``; the strategic current project and objective ids with the active objective's own record when it can be found;
the Chebyshev distance (max of the axis distances) to each counterpart (the attackers of a victim, the victims of an attacker) and to the goal tile. A body that is absent from a state reads ``present: false``.
The state has no single "goal" field: the fields above are every place a goal or objective lives in the entity (task payload, navigation target, strategic objective); nothing is derived from them.

LEGALITY WRAPPER. ``LegalityServiceV2.verify_attack_legality`` is wrapped by a pass-through: the ORIGINAL result object is returned unchanged; a row (tick, attacker, target, result, failure text, opportunity flag)
is recorded only where the attacker is a subject and the tick is inside that subject's window (a call whose state has no tick is recorded with ``in_window: null``). The engine calls it from these sites (re-grepped in both frozen trees, every match, no truncation):
at 87792e3e8 domain/combat_actions.py:56, combat.py:166, 268, 342, 444, tactical.py:423, tactical_flight_guard.py:71, tactical_hold.py:38; at e72270894 the same sites, with tactical.py at :434. The class-level wrapper sees every one of them.
One ATTACK action can give TWO calls (combat_actions.py:56, then combat.py:166 inside resolve_attack), so legality call counts are not attack counts. combat_actions.py:56 passes a context, not the state: a call whose
context has no tick is recorded with ``in_window: null`` and counts as in-window for the reach rule (``legality_calls_in_window`` counts every row whose ``in_window`` is not False).

NON-PERTURBATION AND FATALITY. The spy's final hash must equal the SEALED plain twin's (checked by ``subject_trace_run check``). Any exception raised inside a wrapper's own recording code is stored AND re-raised:
a kernel that swallows it still leaves ``spy_exceptions`` in the document, and the child exits 8 (fatal, the cell is void). The original verification's own exceptions are not the spy's: they pass through.

Heavy-job hygiene: the file name carries ``_spy`` so the shared busy gate sees it; put the command in a script file.
Usage: python subject_trace_spy.py <world> <seed> <ticks> <out.json> --arm new|base --plan <subjects.json> [--mode plain|spy]
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

EXIT_SPY_EXCEPTION = 8
EXIT_NOT_PINNED = 9


def load_sibling(name: str) -> Any:
    """A kit module loaded by file path from THIS file's directory (never through the frozen tree on PYTHONPATH, whose ``tools`` package would shadow it)."""
    key = f"_subject_trace_{name}"
    if key in sys.modules:
        return sys.modules[key]
    path = Path(__file__).resolve().with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def safe(value: Any) -> Any:
    """A JSON-safe copy of a small value: tuples and lists as lists, scalars as they are, everything else as its repr."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (tuple, list)):
        return [safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    return str(getattr(value, "value", value))


def chebyshev(a: Any, b: Any) -> Optional[float]:
    if a is None or b is None:
        return None
    return max(abs(float(a[0]) - float(b[0])), abs(float(a[1]) - float(b[1])))


def objective_view(entity: Any) -> Dict[str, Any]:
    """The strategic current project / objective ids and, when the project holds it, the active objective's own record (read by attribute, so a tree without a field reads None)."""
    strategic = getattr(entity, "strategic", None)
    project_id, objective_id = getattr(strategic, "current_project_id", None), getattr(strategic, "current_objective_id", None)
    view: Dict[str, Any] = {"project_id": safe(project_id), "objective_id": safe(objective_id), "project_kind": None, "objective": None}
    project = (getattr(strategic, "projects", None) or {}).get(project_id) if project_id is not None else None
    if project is None:
        return view
    view["project_kind"] = safe(getattr(project, "kind", None))
    wanted = objective_id if objective_id is not None else getattr(project, "active_objective_id", None)
    for record in project.canonical_objectives() if hasattr(project, "canonical_objectives") else []:
        if wanted is not None and wanted in (record.get("id"), record.get("objective_id")):
            view["objective"] = safe(record)
            break
    return view


def snapshot(entity: Any) -> Dict[str, Any]:
    """Everything the read asks of one body at one moment (module docstring)."""
    if entity is None:
        return {"present": False}
    nav, combat, task = entity.navigation, entity.combat, entity.task
    payload = task.payload if isinstance(task.payload, dict) else {}
    mode = nav.movement_mode
    return {
        "present": True, "mode": str(getattr(mode, "value", mode)), "work_kind": safe(task.work_kind), "action": safe(payload.get("action")), "reason": safe(payload.get("reason")),
        "payload": {str(k): safe(v) for k, v in payload.items() if v is None or isinstance(v, (bool, int, float, str, tuple, list))},
        "goal_tile": safe(nav.target), "path_len": len(nav.path or []), "failure_reason": safe(nav.last_failure_reason), "readiness": combat.readiness, "hp": combat.hp, "alive": bool(combat.alive),
        "position": safe(nav.position), "lodged_in": safe(getattr(nav, "lodged_in", None)), "strategic": objective_view(entity),
    }


def in_windows(tick: int, windows: List[List[int]]) -> bool:
    return any(lo <= tick <= hi for lo, hi in windows)


class SubjectSpy:
    """Record-only wrappers; ``install(apply_path, legality)`` patches, ``restore()`` undoes. ``subjects`` is the plan's list for this seed: {id, roles, windows, counterparts}."""

    def __init__(self, subjects: List[Dict[str, Any]]) -> None:
        self.subjects = {int(s["id"]): s for s in subjects}
        self.rows: List[Dict[str, Any]] = []
        self.legality_rows: List[Dict[str, Any]] = []
        self.spy_exceptions: List[str] = []
        self.apply_calls = 0
        self._patched: List[tuple] = []

    # ---- install / restore
    def install(self, apply_path: Any, legality: Any) -> "SubjectSpy":
        original_apply = apply_path.__dict__["apply_generation"].__func__
        original_legal = legality.__dict__["verify_attack_legality"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original_apply(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, prior_state, new_state)
            return new_state

        def verify_attack_legality(attacker, target, state_or_context, *args, **kwargs):
            result = original_legal(attacker, target, state_or_context, *args, **kwargs)
            spy.guarded(spy.legality, attacker, target, state_or_context, args, kwargs, result)
            return result  # the original result object, untouched

        self._patched += [(apply_path, "apply_generation", original_apply), (legality, "verify_attack_legality", original_legal)]
        apply_path.apply_generation = staticmethod(apply_generation)
        legality.verify_attack_legality = staticmethod(verify_attack_legality)
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    def guarded(self, recorder: Callable, *args: Any) -> None:
        """Run the recording code; any exception of it is stored for the document and re-raised (fatal; a kernel that swallows it still leaves the record)."""
        try:
            recorder(*args)
        except BaseException:
            self.spy_exceptions.append(traceback.format_exc()[-1500:])
            raise

    # ---- recording
    def observe(self, prior: Any, state: Any) -> None:
        self.apply_calls += 1
        tick = state.tick
        for subject_id, subject in self.subjects.items():
            if not in_windows(tick, subject["windows"]):
                continue
            before, after = prior.entities.get(subject_id), state.entities.get(subject_id)
            snap_before, snap_after = snapshot(before), snapshot(after)
            row: Dict[str, Any] = {"tick": tick, "id": subject_id, "roles": subject["roles"], "before": snap_before, "after": snap_after, "distance_before": {}, "distance_after": {}}
            for other in subject["counterparts"]:
                row["distance_before"][str(other)] = chebyshev(snap_before.get("position"), snapshot_position(prior, other))
                row["distance_after"][str(other)] = chebyshev(snap_after.get("position"), snapshot_position(state, other))
            row["goal_distance_before"] = chebyshev(snap_before.get("position"), snap_before.get("goal_tile"))
            row["goal_distance_after"] = chebyshev(snap_after.get("position"), snap_after.get("goal_tile"))
            self.rows.append(row)

    def legality(self, attacker: Any, target: Any, state_or_context: Any, args: tuple, kwargs: dict, result: Any) -> None:
        subject = self.subjects.get(getattr(attacker, "id", None))
        if subject is None:
            return
        tick = getattr(state_or_context, "tick", None)
        in_window = None if tick is None else in_windows(tick, subject["windows"])
        if in_window is False:
            return
        legal, reason = result[0], result[1]
        self.legality_rows.append({
            "tick": tick, "in_window": in_window, "attacker_id": attacker.id, "target_id": getattr(target, "id", None), "legal": bool(legal), "reason": safe(getattr(reason, "name", reason)),
            "failure_text": None if legal else str(getattr(reason, "value", reason)), "opportunity": bool(kwargs.get("is_opportunity_attack", args[0] if args else False)),
        })

    def report(self) -> Dict[str, Any]:
        in_window_calls = sum(1 for r in self.legality_rows if r["in_window"] is not False)
        return {"rows": self.rows, "row_count": len(self.rows), "legality_rows": self.legality_rows, "legality_call_count": len(self.legality_rows), "legality_calls_in_window": in_window_calls,
                "subject_ids": sorted(self.subjects), "apply_calls": self.apply_calls, "spy_exceptions": self.spy_exceptions}


def snapshot_position(state: Any, entity_id: int) -> Any:
    entity = state.entities.get(entity_id)
    return None if entity is None else entity.navigation.position


def run_ticks(kernel: Any, ticks: int, spy: Optional[SubjectSpy]) -> Any:
    """Run ``ticks`` ticks; whatever happens restore the wrappers and shut the kernel down."""
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        final_state = kernel.state
        if spy is not None:
            spy.restore()
        kernel.shutdown()
    return final_state


def main(argv: List[str]) -> int:
    from src.engine.checkpoint import CanonicalStateHasher
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.test_architecture.rpg_gate_run import build_kernel

    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "spy"
    arm = argv[argv.index("--arm") + 1]
    plan = json.loads(Path(argv[argv.index("--plan") + 1]).read_text(encoding="utf-8"))
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    if mode not in ("plain", "spy"):
        raise ValueError(f"--mode must be plain or spy, not {mode!r}")
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("subject_trace_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    errors = load_sibling("person_attack_spy").LoggingErrors()
    logging.getLogger().addHandler(errors)
    load_sibling("person_attack_spy").inject_no_replay_if_recording_off()
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"subject_trace_{mode}_{arm}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="subject_trace_spy build_kernel")
    spy: Optional[SubjectSpy] = None
    if mode == "spy":
        from src.engine.apply import ApplyPath
        from src.engine.legality import LegalityServiceV2

        spy = SubjectSpy(plan["subjects_by_seed"][str(seed)]).install(ApplyPath, LegalityServiceV2)
    fatal: Optional[str] = None
    try:
        final_state = run_ticks(kernel, ticks, spy)
    except BaseException:
        fatal = traceback.format_exc()[-1500:]
        final_state = kernel.state
    doc: Dict[str, Any] = {
        "world": world, "seed": seed, "arm": arm, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
        "final_hash": CanonicalStateHasher.get_hash(final_state), "final_tick": final_state.tick, "logging_errors": errors.rows, "fatal": fatal, "plan_sha256": plan.get("plan_sha256"),
    }
    if spy is not None:
        doc.update(spy.report())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    if fatal is not None or (spy is not None and spy.spy_exceptions):
        print(f"SPY EXCEPTION (fatal, the cell is void): {fatal or spy.spy_exceptions[-1]}", file=sys.stderr)
        return EXIT_SPY_EXCEPTION
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
