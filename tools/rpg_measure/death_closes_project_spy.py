"""Death-closes-project own-job spy (TCK-20261031-DEATH-CLOSES-NO-PROJECT; definition: rpg-designer-death-closes-ownjob-definition.md sha256 df2ba4b5...).

ONE cell per process (cwd = the frozen tree, PYTHONPATH = that tree, recording OFF). READ-ONLY: a wrapper on ``ApplyPath.apply_generation`` that returns the ORIGINAL new state, and (``--phase-rows on``, the default) read-only wrappers on
``CapacityEnforcementPhase.enforce`` and ``StrategicRedirectionSystem.enforce`` that return the ORIGINAL update. It runs on BOTH arms (BASE main and FIX): every tree read is a ``getattr``, so ``ended_by`` etc. are simply empty where the tree lacks them.
``--mode plain`` runs the build with no wrapper and writes the final hash; a spied cell is VOID unless its final_hash equals the plain twin's (rc 3).

Per applied tick it records (see ``death_closes_project_logic``): D1-D5 counts and the first rows, the LIVING PROJECTION digest (the canonical state with every dead body's ``strategic`` dropped) and the LIVING EVENT STREAM digest (the update's FULL typed world
event stream: the masked category set is empty in the run), both per tick, for the D7 comparison. ``--dump-tick N`` additionally writes that tick's living projection (canonical JSON) beside the output, for locating a divergence.
RUN ROOT: with recording OFF the kernel builds its default ``ReplayManager`` with the hard-coded relative run_dir ``data/runs/<run_id>`` (kernel.py:373), whose sink writes ``manifest.json`` INTO the frozen tree. This spy wraps
``ReplayManager.__init__`` (kit side, no src change; the same pattern as ``person_attack_spy.inject_no_replay_if_recording_off``) to rewrite exactly that relative path to ``<--run-root>/<run_id>``, in plain and spy mode alike.
The path is only where files go (never state), and the cell is VOID unless exactly that redirect happened (``replay_dirs_redirected`` >= 1).
redirection: ``StrategicRedirectionSystem`` is never called in the pipeline (its logic was hoisted into ``StrategicIntelligenceSystem``, intelligence.py:518), so its row is NOT MEASURED, not wrapped.
Usage: python death_closes_project_spy.py <world> <seed> <ticks> <out.json> --mode plain|spy [--plain-hash <hex>] [--phase-rows on|off] [--dump-tick N] [--run-root <dir, default <out dir>/runs>]
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

EXIT_SPY_EXCEPTION = 8
EXIT_HASH_MISMATCH = 3
EXIT_FINDING = 6
ROW_CAP = 20


def load_sibling(name: str) -> Any:
    key = f"_dcp_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, Path(__file__).resolve().with_name(f"{name}.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


REDIRECTION_NOT_MEASURED = {"status": "NOT MEASURED", "reason": "StrategicRedirectionSystem.enforce is never called by the pipeline (no phase names it; its logic was hoisted into StrategicIntelligenceSystem, intelligence.py:518)"}


def redirect_run_root(run_root: str) -> Dict[str, int]:
    """Wrap ``ReplayManager.__init__`` so a relative ``data/runs/<id>`` run_dir becomes ``<run_root>/<id>``; any other run_dir is left alone. Returns the counter ``{"redirected": n, "other": m}``."""
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


class DeathSpy:
    def __init__(self, hasher: Any, dump_tick: Optional[int] = None, dead_key: str = "death_record") -> None:
        self.logic = load_sibling("death_closes_project_logic")
        self.tracker = self.logic.DeathTracker(dead_key)
        self.hasher = hasher
        self.dump_tick = dump_tick
        self.dump: Optional[Dict[str, Any]] = None
        self.living_by_tick: Dict[int, str] = {}
        self.events_by_tick: Dict[int, str] = {}
        self.phase_rows: Dict[str, Dict[str, Any]] = {"redirection": dict(REDIRECTION_NOT_MEASURED)}
        self.spy_exceptions: List[str] = []
        self._patched: List[tuple] = []
        self.apply_calls = 0

    def install(self, apply_path: Any, phases: Dict[str, Any]) -> "DeathSpy":
        original = apply_path.__dict__["apply_generation"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, prior_state, update, new_state)
            return new_state  # the ORIGINAL object, untouched

        self._patched.append((apply_path, "apply_generation", original))
        apply_path.apply_generation = staticmethod(apply_generation)
        for label, cls in phases.items():
            original_enforce = cls.__dict__["enforce"].__func__

            def enforce(*args, _orig=original_enforce, _label=label, **kwargs):
                result = _orig(*args, **kwargs)
                spy.guarded(spy.phase_call, _label, args, result)
                return result  # the ORIGINAL update, untouched

            self._patched.append((cls, "enforce", original_enforce))
            cls.enforce = staticmethod(enforce)
        return self

    def restore(self) -> None:
        for owner, attr, original in reversed(self._patched):
            setattr(owner, attr, staticmethod(original))
        self._patched.clear()

    def guarded(self, recorder: Any, *args: Any) -> None:
        try:
            recorder(*args)
        except BaseException:
            self.spy_exceptions.append(traceback.format_exc()[-1500:])
            raise

    def phase_call(self, label: str, args: tuple, result: Any) -> None:
        """A phase's returned update that writes a strategic field of a DEAD body (dead in the state it was handed): one row per body and call. Read-only."""
        state = args[0]
        bucket = self.phase_rows.setdefault(label, {"calls": 0, "rows": 0, "first": []})
        bucket["calls"] += 1
        for eid, eu in (getattr(result, "entity_updates", None) or {}).items():
            ent = state.entities.get(eid)
            strat = getattr(eu, "strategic", None)
            if ent is None or strat is None:
                continue
            dying_now = getattr(getattr(eu, "combat", None), "alive_set", True) is False
            state_of_body = "dead" if self.logic.is_dead(ent) else ("dying" if (not ent.combat.alive or dying_now) else None)
            lives, cur = self.tracker._body_state(ent)
            if state_of_body is None or not (lives or cur):
                continue                       # only a dead-or-dying body that holds a live or current project (the dead-with-live set)
            fields = sorted(f.name for f in dataclasses.fields(strat) if getattr(strat, f.name) not in (None, [], {}, (), ""))
            if not fields:
                continue
            bucket["rows"] += 1
            if len(bucket["first"]) < ROW_CAP:
                bucket["first"].append({"tick": state.tick, "id": eid, "body": state_of_body, "fields": fields})

    def observe(self, prior_state: Any, update: Any, new_state: Any) -> None:
        self.apply_calls += 1
        tick = int(new_state.tick)
        self.tracker.observe(tick, prior_state.entities, new_state.entities)
        dead_ids = [eid for eid, e in new_state.entities.items() if self.logic.is_dead(e, self.tracker.dead_key)]
        canonical = self.hasher.to_canonical_data(new_state)
        self.living_by_tick[tick] = self.logic.living_projection_digest(canonical, dead_ids)
        self.events_by_tick[tick] = self.logic.living_event_digest(getattr(update, "world_events_add", None) or [], dead_ids)
        if self.dump_tick is not None and tick == self.dump_tick:
            entities = canonical.get("entities") or {}
            dead = {str(i) for i in dead_ids}
            self.dump = {**canonical, "entities": {k: ({kk: vv for kk, vv in v.items() if kk != "strategic"} if k in dead else v) for k, v in entities.items()}}

    def report(self) -> Dict[str, Any]:
        doc = self.tracker.report()
        doc.update({"apply_calls": self.apply_calls, "living_by_tick": {str(t): d for t, d in sorted(self.living_by_tick.items())}, "events_by_tick": {str(t): d for t, d in sorted(self.events_by_tick.items())},
                    "phase_rows": self.phase_rows, "spy_exceptions": self.spy_exceptions})
        return doc


def main(argv: List[str]) -> int:
    from src.engine.checkpoint import CanonicalStateHasher
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.test_architecture.rpg_gate_run import build_kernel

    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "spy"
    plain_hash = argv[argv.index("--plain-hash") + 1] if "--plain-hash" in argv else None
    phase_rows = (argv[argv.index("--phase-rows") + 1] if "--phase-rows" in argv else "on") == "on"
    dump_tick = int(argv[argv.index("--dump-tick") + 1]) if "--dump-tick" in argv else None
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    run_root = argv[argv.index("--run-root") + 1] if "--run-root" in argv else str(Path(out).parent / "runs")
    if mode not in ("plain", "spy"):
        raise ValueError(f"--mode must be plain or spy, not {mode!r}")
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("death_closes_project_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    pa = load_sibling("person_attack_spy")
    errors = pa.LoggingErrors()
    logging.getLogger().addHandler(errors)
    pa.inject_no_replay_if_recording_off()
    redirected = redirect_run_root(run_root)
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"death_closes_project_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path(run_root) / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="death_closes_project_spy build_kernel")
    spy: Optional[DeathSpy] = None
    findings: List[str] = []
    if mode == "spy":
        from src.engine.apply import ApplyPath
        phases: Dict[str, Any] = {}
        if phase_rows:
            from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
            phases = {"capacity_enforcement": CapacityEnforcementPhase}
        for label, cls in phases.items():
            if "enforce" not in cls.__dict__:
                findings.append(f"tree's {label} has no enforce")
        if findings:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps({"world": world, "seed": seed, "mode": mode, "findings": findings}), encoding="utf-8")
            return EXIT_FINDING
        spy = DeathSpy(CanonicalStateHasher, dump_tick).install(ApplyPath, phases)
    fatal: Optional[str] = None
    try:
        for _ in range(ticks):
            kernel.tick_once()
    except BaseException:
        fatal = traceback.format_exc()[-1500:]
    final_state = kernel.state
    if spy is not None:
        spy.restore()
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(final_state)
    doc: Dict[str, Any] = {"world": world, "seed": seed, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced, "final_hash": final_hash,
                           "final_tick": final_state.tick, "logging_errors": errors.rows, "fatal": fatal, "findings": findings, "phase_rows_on": phase_rows, "run_root": str(Path(run_root).resolve()), "replay_dirs_redirected": redirected["redirected"], "replay_dirs_other": redirected["other"]}
    code = 0
    if spy is not None:
        doc.update(spy.report())
        doc["hash_equals_plain"] = None if plain_hash is None else final_hash == plain_hash
        code = EXIT_SPY_EXCEPTION if (fatal is not None or spy.spy_exceptions) else (EXIT_HASH_MISMATCH if plain_hash is not None and final_hash != plain_hash else 0)
        if spy.dump is not None:
            Path(str(out) + f".tick{dump_tick}.living.json").write_text(json.dumps(spy.dump, sort_keys=True, separators=(",", ":"), default=str), encoding="utf-8")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    if code:
        print(f"CELL VOID rc={code}: {fatal or (spy.spy_exceptions[-1] if spy and spy.spy_exceptions else 'hash differs from the plain twin')}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
