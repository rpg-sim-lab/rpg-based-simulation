"""K3 own-job spy (TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH; rulings rpg-designer-k3-plan-rulings.md 972600b6...).

ONE cell per process (cwd = the frozen FIX tree, PYTHONPATH = that tree, recording OFF). Hash-neutral pass-throughs that return the ORIGINAL objects:
 - ``StrategicIntelligenceSystem.evaluate_project_switch`` (only to learn ``current_tick``, which the rule helper does not receive);
 - the module function ``intelligence.escalated_need_takes_switch`` (the RULE): every call that returns True is a TAKEN; at that moment the spy calls ``intelligence.ordinary_switch_allows`` READ-ONLY on the same arguments
   (a pure function) and records FIRES = rule True AND ordinary False, with the need, the current project's kind, id, score and lock, and ``present_threat_to`` (must be False at every TAKEN) and ``acting_threat_to``;
 - ``ApplyPath.apply_generation`` (to follow each TAKEN: ticks the need project stays current, the suspended project's fate, the subject's hp for 50 ticks, hunger >= 95 and sleep_debt >= 98 subjects).
``--mode plain`` runs with no wrapper and writes the final hash. A cell is VOID unless spy final_hash == plain final_hash.
Report-only guard (Q5): every TAKEN whose released current is ``combat_retreat`` or ``combat_engage``, with whether the subject lost hp within 50 ticks.
Usage: python k3_switch_spy.py <world> <seed> <ticks> <out.json> --mode plain|spy [--plain-hash <hex>]
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import traceback
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

EXIT_SPY_EXCEPTION = 8
EXIT_HASH_MISMATCH = 3
EXIT_FINDING = 6
GUARD_KINDS = ("combat_retreat", "combat_engage")
GUARD_WINDOW = 50
HUNGER_LINE, SLEEP_LINE = 95.0, 98.0


def load_sibling(name: str) -> Any:
    key = f"_k3sw_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, Path(__file__).resolve().with_name(f"{name}.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def val(x: Any) -> Any:
    return getattr(x, "value", x)


class SwitchSpy:
    def __init__(self, intel: Any, sis: Any, apply_path: Any) -> None:
        self.intel, self.sis, self.apply_path = intel, sis, apply_path
        self.tick = 0
        self.taken: List[Dict[str, Any]] = []
        self.follow: Dict[int, List[Dict[str, Any]]] = {}      # subject -> open fires being followed
        self.calls = {"switch_calls": 0, "rule_calls": 0, "apply_calls": 0}
        self.reached: Dict[str, set] = {"hunger_95": set(), "sleep_98": set()}
        self.spy_exceptions: List[str] = []
        self._patched: List[tuple] = []

    def install(self) -> "SwitchSpy":
        spy, intel = self, self.intel
        orig_switch = self.sis.__dict__["evaluate_project_switch"].__func__
        orig_rule = intel.escalated_need_takes_switch
        orig_ordinary = intel.ordinary_switch_allows
        orig_apply = self.apply_path.__dict__["apply_generation"].__func__

        def evaluate_project_switch(entity, candidate, current_tick, state=None):
            spy.tick = current_tick
            spy.calls["switch_calls"] += 1
            return orig_switch(entity, candidate, current_tick, state)

        def rule(entity, candidate, current, state):
            result = orig_rule(entity, candidate, current, state)
            spy.calls["rule_calls"] += 1
            if result:
                spy.guarded(spy.record_taken, orig_ordinary, entity, candidate, current, state)
            return result

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = orig_apply(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, new_state)
            return new_state

        self._patched += [(self.sis, "evaluate_project_switch", orig_switch, True), (intel, "escalated_need_takes_switch", orig_rule, False), (self.apply_path, "apply_generation", orig_apply, True)]
        self.sis.evaluate_project_switch = staticmethod(evaluate_project_switch)
        intel.escalated_need_takes_switch = rule
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

    def record_taken(self, ordinary: Any, entity: Any, candidate: Any, current: Any, state: Any) -> None:
        tick = state.tick if state is not None else self.tick
        allows = bool(ordinary(entity, candidate, current, self.tick, state))          # read-only, pure
        from src.ai.goals.present_threat import acting_threat_to, present_threat_to
        fire = {"subject": entity.id, "tick": tick, "need": str(val(candidate.kind)), "candidate_id": candidate.id, "candidate_score": candidate.score, "current_id": current.id, "current_kind": str(val(current.kind)),
                "current_score": current.score, "current_lock_until": current.lock_until_tick, "hunger": entity.biological.hunger, "sleep_debt": entity.biological.sleep_debt,
                "ordinary_allows": allows, "fire": not allows, "present_threat": bool(present_threat_to(entity, state)), "acting_threat": bool(acting_threat_to(entity, state)),
                "hp_at_fire": entity.combat.hp, "ticks_current": 0, "min_hp_in_window": entity.combat.hp, "guard": str(val(current.kind)) in GUARD_KINDS}
        self.taken.append(fire)
        self.follow.setdefault(entity.id, []).append(fire)

    def observe(self, state: Any) -> None:
        self.calls["apply_calls"] += 1
        for eid, ent in state.entities.items():
            if ent.biological.hunger >= HUNGER_LINE:
                self.reached["hunger_95"].add(eid)
            if ent.biological.sleep_debt >= SLEEP_LINE:
                self.reached["sleep_98"].add(eid)
        for eid in list(self.follow):
            ent = state.entities.get(eid)
            keep = []
            for fire in self.follow[eid]:
                age = state.tick - fire["tick"]
                if ent is not None and age >= 0:
                    if age <= GUARD_WINDOW:
                        fire["min_hp_in_window"] = min(fire["min_hp_in_window"], ent.combat.hp)
                    if ent.strategic.current_project_id == fire["candidate_id"] and age <= 1000:
                        fire["ticks_current"] += 1
                if age < GUARD_WINDOW:
                    keep.append(fire)
            if keep:
                self.follow[eid] = keep
            else:
                del self.follow[eid]

    def finish(self, final_state: Any) -> None:
        for fire in self.taken:
            ent = final_state.entities.get(fire["subject"])
            old = ent.strategic.projects.get(fire["current_id"]) if ent is not None else None
            fire["suspended_fate"] = None if old is None else {"status": str(val(old.status)), "ended_by": None if getattr(old, "ended_by", None) is None else str(val(old.ended_by)), "current_now": ent.strategic.current_project_id == old.id}
            fire["damage_within_50"] = fire["min_hp_in_window"] < fire["hp_at_fire"]

    def report(self) -> Dict[str, Any]:
        fires = [t for t in self.taken if t["fire"]]
        by = lambda rows: dict(sorted(Counter(f"{r['need']}|{r['current_kind']}" for r in rows).items()))  # noqa: E731
        guard = [t for t in self.taken if t["guard"]]
        return {"taken": len(self.taken), "fires": len(fires), "taken_by_need_and_current_kind": by(self.taken), "fires_by_need_and_current_kind": by(fires),
                "taken_under_present_threat": sum(1 for t in self.taken if t["present_threat"]), "taken_under_acting_threat": sum(1 for t in self.taken if t["acting_threat"]),
                "guard_rows": [{k: t[k] for k in ("subject", "tick", "need", "current_kind", "hp_at_fire", "min_hp_in_window", "damage_within_50", "fire")} for t in guard],
                "reached": {k: sorted(v) for k, v in self.reached.items()}, "rows": self.taken, "calls": self.calls, "spy_exceptions": self.spy_exceptions}


def main(argv: List[str]) -> int:
    from src.engine.checkpoint import CanonicalStateHasher
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.test_architecture.rpg_gate_run import build_kernel

    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "spy"
    plain_hash = argv[argv.index("--plain-hash") + 1] if "--plain-hash" in argv else None
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    if mode not in ("plain", "spy"):
        raise ValueError(f"--mode must be plain or spy, not {mode!r}")
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("k3_switch_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    pa = load_sibling("person_attack_spy")
    errors = pa.LoggingErrors()
    logging.getLogger().addHandler(errors)
    pa.inject_no_replay_if_recording_off()
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"k3_switch_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="k3_switch_spy build_kernel")
    spy: Optional[SwitchSpy] = None
    findings: List[str] = []
    if mode == "spy":
        from src.engine.apply import ApplyPath
        from src.systems.strategic_systems import intelligence as intel

        for name in ("escalated_need_takes_switch", "ordinary_switch_allows"):
            if not callable(getattr(intel, name, None)):
                findings.append(f"tree does not expose intelligence.{name}")
        if findings:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps({"world": world, "seed": seed, "mode": mode, "findings": findings}), encoding="utf-8")
            return EXIT_FINDING
        spy = SwitchSpy(intel, intel.StrategicIntelligenceSystem, ApplyPath).install()
    fatal: Optional[str] = None
    try:
        for _ in range(ticks):
            kernel.tick_once()
    except BaseException:
        fatal = traceback.format_exc()[-1500:]
    final_state = kernel.state
    if spy is not None:
        spy.restore()
        spy.finish(final_state)
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(final_state)
    doc: Dict[str, Any] = {"world": world, "seed": seed, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced, "final_hash": final_hash,
                           "final_tick": final_state.tick, "logging_errors": errors.rows, "fatal": fatal, "findings": findings}
    code = 0
    if spy is not None:
        doc.update(spy.report())
        doc["hash_equals_plain"] = None if plain_hash is None else final_hash == plain_hash
        code = EXIT_SPY_EXCEPTION if (fatal is not None or spy.spy_exceptions) else (EXIT_HASH_MISMATCH if plain_hash is not None and final_hash != plain_hash else 0)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    if code:
        print(f"CELL VOID rc={code}: {fatal or (spy.spy_exceptions[-1] if spy and spy.spy_exceptions else 'hash differs from the plain twin')}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
