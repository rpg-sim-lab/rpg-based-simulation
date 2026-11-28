"""Perception-gate calibration own-job spy (TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT; rpg-designer ruling 9c42fb88). NOT RUN by the author.

ONE cell per process (cwd = the frozen tree of the arm, PYTHONPATH = that tree, recording OFF). READ-ONLY: pass-throughs that return the ORIGINAL objects:
 - ``PerceptionGate.can_perceive`` (every call: the result, its channels, the target's signals, day or night -> the perception counters and the two NON-VACUITY rows);
 - ``ApplyPath.apply_generation`` (per applied tick: objectives that start (hunts, engagements), hits landed, and every ``SAMPLE_EVERY``-th tick a sample of perceived hostile and perceived prey pairs, by
   ``appraisal.perceives`` over the 10-tile neighbour view: the same query on both arms, so the counts are comparable).
It runs on BOTH arms (BASE main ac759e0ba, FIX the calibration head): every tree read is a ``getattr``. ``--mode plain`` runs with no wrapper, times the ticks and writes the final hash; a spied cell is VOID
unless its final_hash equals the plain twin's (rc 3). Wall per tick is recorded on both modes for the PERF FLAG (the summary compares the two PLAIN cells).
RUN ROOT: with recording OFF the kernel writes ``data/runs/<run_id>`` into the frozen tree; ``ReplayManager.__init__`` is wrapped (kit side, no src change) to rewrite exactly that relative path to ``<--run-root>/<run_id>``; the
cell is VOID unless a redirect happened.
Usage: python perception_gate_calibration_spy.py <world> <seed> <ticks> <out.json> --mode plain|spy [--plain-hash <hex>] [--run-root <dir, default <out dir>/runs>]
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

EXIT_SPY_EXCEPTION = 8
EXIT_HASH_MISMATCH = 3
EXIT_FINDING = 6
SAMPLE_EVERY = 10
RADIUS = 10.0


def load_sibling(name: str) -> Any:
    key = f"_pgc_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, Path(__file__).resolve().with_name(f"{name}.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def redirect_run_root(run_root: str) -> Dict[str, int]:
    """Wrap ``ReplayManager.__init__`` so a relative ``data/runs/<id>`` run_dir becomes ``<run_root>/<id>``; any other run_dir is left alone. Returns ``{"redirected": n, "other": m}``."""
    from src.engine import replay_manager as module

    original = module.ReplayManager.__init__
    counts = {"redirected": 0, "other": 0}
    root = Path(run_root).resolve()

    def init(self, *args, **kwargs):
        given = kwargs["run_dir"] if "run_dir" in kwargs else (args[0] if args else None)
        path = Path(given) if given is not None else None
        if path is not None and not path.is_absolute() and path.parent == Path("data") / "runs":
            moved = root / path.name
            counts["redirected"] += 1
            if "run_dir" in kwargs:
                kwargs["run_dir"] = moved
            else:
                args = (moved,) + tuple(args[1:])
        else:
            counts["other"] += 1
        return original(self, *args, **kwargs)

    module.ReplayManager.__init__ = init
    return counts


def val(x: Any) -> Any:
    return getattr(x, "value", x)


def current_objective(entity: Any) -> Optional[Dict[str, Any]]:
    """The body's current objective as plain values (``None`` when it has none)."""
    strat = getattr(entity, "strategic", None)
    if strat is None or not getattr(strat, "current_objective_id", None):
        return None
    project = (getattr(strat, "projects", None) or {}).get(strat.current_project_id or "")
    if project is None:
        return None
    for obj in project.objectives:
        if obj.id == strat.current_objective_id:
            return {"id": obj.id, "kind": str(val(obj.kind)), "project_kind": str(val(project.kind)), "target_entity_id": getattr(obj, "target_entity_id", None)}
    return None


class CalibrationSpy:
    def __init__(self, logic: Any, gate_cls: Any, apply_path: Any) -> None:
        self.logic, self.gate_cls, self.apply_path = logic, gate_cls, apply_path
        self.counters = logic.Counters()
        self.levels: Dict[str, str] = logic.size_levels(None)
        self.objective_before: Dict[int, Optional[str]] = {}
        self.sampled = {"samples": 0, "hostile_pairs": 0, "prey_pairs": 0}
        self.spy_exceptions: List[str] = []
        self._patched: List[tuple] = []

    def install(self) -> "CalibrationSpy":
        spy = self
        orig_gate = self.gate_cls.can_perceive
        orig_apply = self.apply_path.__dict__["apply_generation"].__func__

        def can_perceive(gate_self, source_entity, target_signals, context=None):
            result = orig_gate(gate_self, source_entity, target_signals, context)
            spy.guarded(spy.record_gate, gate_self, target_signals, context, result)
            return result  # the ORIGINAL result, untouched

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = orig_apply(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, new_state)
            return new_state  # the ORIGINAL object, untouched

        self._patched += [(self.gate_cls, "can_perceive", orig_gate, False), (self.apply_path, "apply_generation", orig_apply, True)]
        self.gate_cls.can_perceive = can_perceive
        self.apply_path.apply_generation = staticmethod(apply_generation)
        return self

    def restore(self) -> None:
        for owner, name, original, static in reversed(self._patched):
            setattr(owner, name, staticmethod(original) if static else original)
        self._patched.clear()

    def guarded(self, recorder: Any, *args: Any) -> None:
        try:
            recorder(*args)
        except BaseException:
            self.spy_exceptions.append(traceback.format_exc()[-1500:])
            raise

    def record_gate(self, gate: Any, target_signals: Any, context: Any, result: Any) -> None:
        settings = getattr(gate, "settings", None)  # the fix arm's calibration record; the base arm has none
        self.levels = self.logic.size_levels(getattr(settings, "size_visibility", None))
        signals = target_signals if isinstance(target_signals, dict) else {k: getattr(target_signals, k, None) for k in ("visibility", "noise")}
        row = self.logic.classify_perception(bool(result.perceived), result.signals_used, signals, bool((context or {}).get("night", False)), self.levels)
        self.counters.gate(row)

    def observe(self, state: Any) -> None:
        self.counters.apply_calls += 1
        tick = int(state.tick)
        first = self.counters.apply_calls == 1  # the first applied tick only records what bodies already hold: those are not starts
        for eid, ent in state.entities.items():
            kind = None if first else self.logic.objective_started(self.objective_before.get(eid), current_objective(ent))
            self.counters.started(kind)
            cur = current_objective(ent)
            self.objective_before[eid] = None if cur is None else cur["id"]
            if getattr(ent.combat, "last_hit_tick", None) == tick:
                self.counters.hits_landed += 1
        if tick % SAMPLE_EVERY == 0:
            self.sample(state)

    def sample(self, state: Any) -> None:
        """Perceived hostile and prey pairs at this tick: each living body against the bodies in its 10-tile view, through ``appraisal.perceives`` (day or night as the state's clock says)."""
        from src.content_semantics.faction import are_entities_hostile
        from src.content_semantics.relation import RelationContext
        from src.core.calendar import is_night
        from src.engine.appraisal import can_eat, perceives
        from src.engine.domain_logic import SimulationDomainLogic

        self.sampled["samples"] += 1
        night = is_night(state.world_time)
        for ent in state.entities.values():
            if not ent.combat.alive:
                continue
            for _, other in SimulationDomainLogic.get_neighbor_view(state, ent, radius=RADIUS):
                if not other.combat.alive or not perceives(ent, other, night=night, tick=state.tick):
                    continue
                dist = abs(other.navigation.position[0] - ent.navigation.position[0]) + abs(other.navigation.position[1] - ent.navigation.position[1])
                if are_entities_hostile(ent, other, RelationContext(distance=dist, combat_engaged=True)):
                    self.sampled["hostile_pairs"] += 1
                if can_eat(ent, other):
                    self.sampled["prey_pairs"] += 1

    def report(self) -> Dict[str, Any]:
        doc = self.counters.report()
        doc.update({"sampled": dict(self.sampled), "size_levels": dict(self.levels), "spy_exceptions": self.spy_exceptions})
        return doc


def main(argv: List[str]) -> int:
    from src.engine.checkpoint import CanonicalStateHasher
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.test_architecture.rpg_gate_run import build_kernel

    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "spy"
    plain_hash = argv[argv.index("--plain-hash") + 1] if "--plain-hash" in argv else None
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    run_root = argv[argv.index("--run-root") + 1] if "--run-root" in argv else str(Path(out).parent / "runs")
    if mode not in ("plain", "spy"):
        raise ValueError(f"--mode must be plain or spy, not {mode!r}")
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("perception_gate_calibration_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    pa = load_sibling("person_attack_spy")
    errors = pa.LoggingErrors()
    logging.getLogger().addHandler(errors)
    pa.inject_no_replay_if_recording_off()
    redirected = redirect_run_root(run_root)
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"perception_gate_calibration_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path(run_root) / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="perception_gate_calibration_spy build_kernel")
    spy: Optional[CalibrationSpy] = None
    findings: List[str] = []
    if mode == "spy":
        from src.engine.apply import ApplyPath
        from src.world.perception.gate import PerceptionGate
        logic = load_sibling("perception_gate_calibration_logic")
        spy = CalibrationSpy(logic, PerceptionGate, ApplyPath).install()
    fatal: Optional[str] = None
    wall = 0.0
    try:
        for _ in range(ticks):
            started = time.perf_counter()
            kernel.tick_once()
            wall += time.perf_counter() - started
    except BaseException:
        fatal = traceback.format_exc()[-1500:]
    final_state = kernel.state
    if spy is not None:
        spy.restore()
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(final_state)
    doc: Dict[str, Any] = {"world": world, "seed": seed, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
                           "final_hash": final_hash, "final_tick": final_state.tick, "wall_seconds": wall, "wall_per_tick": wall / max(1, ticks), "logging_errors": errors.rows, "fatal": fatal,
                           "findings": findings, "run_root": str(Path(run_root).resolve()), "replay_dirs_redirected": redirected["redirected"], "replay_dirs_other": redirected["other"]}
    code = 0
    if spy is not None:
        doc.update(spy.report())
        doc["hash_equals_plain"] = None if plain_hash is None else final_hash == plain_hash
        code = EXIT_SPY_EXCEPTION if (fatal is not None or spy.spy_exceptions) else (EXIT_HASH_MISMATCH if plain_hash is not None and final_hash != plain_hash else 0)
    elif fatal is not None:
        code = EXIT_SPY_EXCEPTION
    if redirected["redirected"] < 1 and code == 0:
        code = EXIT_FINDING
        doc["findings"].append("no ReplayManager run_dir was redirected: the kernel may have written into the frozen tree")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    if not code:
        print(f"PERCEPTION CALIBRATION CELL OK mode={mode} {world} s{seed} {ticks}t")
    if code:
        print(f"CELL VOID rc={code}: {fatal or (spy.spy_exceptions[-1] if spy and spy.spy_exceptions else 'hash differs from the plain twin or no redirect')}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
