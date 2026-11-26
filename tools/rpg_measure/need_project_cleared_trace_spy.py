"""K3 Phase 0 trace spy (TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH; rulings rpg-designer-k3-plan-rulings.md, 972600b672863882...).

ONE cell per process (cwd = the frozen tree, PYTHONPATH = that tree, recording OFF). READ-ONLY, hash-neutral: pass-throughs on ``ApplyPath.apply_generation`` and ``ScoreModifierSystem.apply_modifiers`` that return the ORIGINAL object.
``--mode plain`` runs the build with no wrapper and writes the final hash (the launcher requires spy final_hash == plain final_hash, else the cell is VOID).

QUESTION (group D of the 30 K3 losses): at a decision d whose winner is an ESCALATED need (the tree's pressing test) the subject's CURRENT project was a live project of the SAME kind as the winner (so nothing had to be switched), and at d+1 it
is no longer current. Who ended or cleared it, and how? For EVERY such decision (not a hard-coded tick list) the spy records at d and d+1: the current project id; that project's id, status, ended_by and score; the subject's hunger and
sleep_debt; whether a service was delivered at d+1 (a fresh accepted result or the paid transfer, the A1 definition); and the update's strategic fields for that subject (current_project_id_set, the entries of the project in
projects_add_or_update, whether projects_remove names it). The writer phase is "not readable": the merged update carries no source.
CLASSES (fixed by the designer before data): D1 a lawful end: the project ended COMPLETED with the need met (the need's value fell, or a service was delivered) at d+1; D2 a typed end: ended_by is set (or COMPLETED with the need NOT met), listed by
reason; D3 cleared without an end: current_project_id set to "" while the project is still ACTIVE. Others: ``continues`` (still current, not counted), ``switched_away`` (SUSPENDED and another project current: an ordinary switch, a K3 L1 loss, reported),
``other`` (anything else, with the raw fields). HARD flag: a subject with 3 or more CONSECUTIVE escalated decisions that are D3 with hunger >= 95 (a pressing need that cannot stay current).
Usage: python need_project_cleared_trace_spy.py <world> <seed> <ticks> <out.json> --mode plain|spy [--plain-hash <hex>]
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
from typing import Any, Callable, Dict, List, Optional, Tuple

EXIT_SPY_EXCEPTION = 8
EXIT_HASH_MISMATCH = 3
EXIT_FINDING = 6
HARD_CONSECUTIVE = 3
HARD_LINE = 95.0
NEEDS = ("hunger", "fatigue")


def load_sibling(name: str) -> Any:
    """A kit module loaded by file path from THIS file's directory (never through the frozen tree on PYTHONPATH)."""
    key = f"_k3p0_{name}"
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


def fresh_results(prior_ent: Any, ent: Any) -> List[Any]:
    """The intent results that belong to THIS apply (patches.py keeps the previous tuple when an update has none): fresh = transaction_id not among the prior state's results."""
    now = list(getattr(ent.identity, "latest_intent_results", ()) or ())
    before = list(getattr(prior_ent.identity, "latest_intent_results", ()) or ()) if prior_ent is not None else []
    prior_ids = {getattr(r, "transaction_id", None) for r in before if getattr(r, "transaction_id", None) is not None}
    return [r for r in now if not ((getattr(r, "transaction_id", None) is not None and r.transaction_id in prior_ids) or (getattr(r, "transaction_id", None) is None and r in before))]


def service_delivered(prior_ent: Any, ent: Any, prior_buildings: Any, buildings: Any) -> bool:
    """A service reached the subject this apply: a fresh accepted result, or the paid transfer (its gold fell by D > 0 and some building's purse rose by at least D)."""
    if any(r.accepted for r in fresh_results(prior_ent, ent)):
        return True
    spent = prior_ent.inventory.gold - ent.inventory.gold
    if spent <= 0:
        return False
    return any(b in prior_buildings and nb.inventory.gold - prior_buildings[b].inventory.gold >= spent for b, nb in buildings.items())


def project_view(project: Any) -> Optional[Dict[str, Any]]:
    """id, kind, status, ended_by and score of one project record, or None when the record is absent."""
    if project is None:
        return None
    ended = getattr(project, "ended_by", None)
    return {"id": project.id, "kind": str(val(project.kind)), "status": str(val(project.status)), "ended_by": None if ended is None else str(val(ended)), "score": getattr(project, "score", None)}


def classify(before: Dict[str, Any], after: Dict[str, Any]) -> str:
    """The class of one D-family decision from its d view (``before``) and d+1 view (``after``); pure."""
    proj = after["project"]
    if after["current_project_id"] == before["current_project_id"] and proj is not None and proj["status"] == "ACTIVE":
        return "continues"
    if proj is not None and proj["status"] == "COMPLETED" and proj["ended_by"] is None:
        return "D1" if after["need_met"] else "D2"
    if proj is not None and proj["ended_by"] is not None:
        return "D2"
    if proj is not None and proj["status"] == "ACTIVE" and after["current_project_id"] in ("", None):
        return "D3"
    if proj is not None and proj["status"] == "SUSPENDED" and after["current_project_id"] not in ("", None) and after["current_project_id"] != before["current_project_id"]:
        return "switched_away"
    return "other"


class Phase0Spy:
    def __init__(self, funcs: Dict[str, Any]) -> None:
        self.funcs = funcs
        self.pending: Dict[int, Dict[str, Any]] = {}
        self.rows: List[Dict[str, Any]] = []
        self.sequence: Dict[int, List[Tuple[int, str, float]]] = {}      # subject -> [(decision tick, class, hunger)] of its escalated decisions
        self.hard: List[Dict[str, Any]] = []
        self.decisions = 0
        self.escalated_decisions = 0
        self.d_family_decisions = 0
        self.apply_calls = 0
        self.spy_exceptions: List[str] = []
        self._patched: List[tuple] = []

    def install(self, apply_path: Any, score_cls: Any) -> "Phase0Spy":
        original_apply = apply_path.__dict__["apply_generation"].__func__
        original_mod = score_cls.__dict__["apply_modifiers"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original_apply(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, prior_state, new_state, update)
            return new_state

        def apply_modifiers(entity, state, scores):
            result = original_mod(entity, state, scores)
            spy.guarded(spy.decision, entity, state, result)
            return result

        self._patched += [(apply_path, "apply_generation", original_apply), (score_cls, "apply_modifiers", original_mod)]
        apply_path.apply_generation = staticmethod(apply_generation)
        score_cls.apply_modifiers = staticmethod(apply_modifiers)
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    def guarded(self, recorder: Callable, *args: Any) -> None:
        try:
            recorder(*args)
        except BaseException:
            self.spy_exceptions.append(traceback.format_exc()[-1500:])
            raise

    # ---- decision d
    def decision(self, entity: Any, state: Any, scores: Any) -> None:
        self.decisions += 1
        ranked = sorted(scores, key=lambda x: (-x.utility, str(val(x.kind))))
        win = next((s for s in ranked if s.utility >= 20.0 and not (getattr(s, "target_id", None) is None and getattr(s, "target_pos", None) is None)), None)
        if win is None or str(val(win.kind)) not in NEEDS:
            return
        need = str(val(win.kind))
        hunger, sleep = entity.biological.hunger, entity.biological.sleep_debt
        escalated = self.funcs["need_is_pressing"](hunger, 0.0) if need == "hunger" else self.funcs["need_is_pressing"](0.0, sleep)
        if not escalated:
            return
        self.escalated_decisions += 1
        projects = entity.strategic.projects
        current_id = entity.strategic.current_project_id
        current = projects.get(current_id) if current_id else None
        same = current is not None and str(val(current.status)) in {str(val(x)) for x in self.funcs["live_statuses"]} and self.funcs["same_kind"](current, win.kind)
        if not same:
            return
        self.d_family_decisions += 1
        self.pending[entity.id] = {"eid": entity.id, "tick": state.tick, "need": need, "hunger": hunger, "sleep_debt": sleep, "current_project_id": current_id, "project": project_view(current),
                                    "threat": bool(self.funcs["present_threat_to"](entity, state)), "acting_threat": bool(self.funcs["acting_threat_to"](entity, state))}

    # ---- apply: d+1
    def observe(self, prior: Any, state: Any, update: Any) -> None:
        self.apply_calls += 1
        tick = state.tick
        for eid in [e for e, d in self.pending.items() if d["tick"] == tick - 1]:
            before = self.pending.pop(eid)
            ent, prior_ent = state.entities.get(eid), prior.entities.get(eid)
            if ent is None or prior_ent is None:
                continue
            need = before["need"]
            value_after = ent.biological.hunger if need == "hunger" else ent.biological.sleep_debt
            value_before = before["hunger"] if need == "hunger" else before["sleep_debt"]
            project = ent.strategic.projects.get(before["current_project_id"])
            ent_update = update.entity_updates.get(eid) if getattr(update, "entity_updates", None) else None
            strategic = getattr(ent_update, "strategic", None)
            entries = [project_view(p) for p in (getattr(strategic, "projects_add_or_update", None) or []) if p.id == before["current_project_id"]]
            after = {"current_project_id": ent.strategic.current_project_id, "project": project_view(project), "value": value_after, "need_met": value_after < value_before or service_delivered(prior_ent, ent, prior.buildings, state.buildings),
                     "service_delivered": service_delivered(prior_ent, ent, prior.buildings, state.buildings), "fresh_accepted_results": sum(1 for r in fresh_results(prior_ent, ent) if r.accepted),
                     "gold_delta": ent.inventory.gold - prior_ent.inventory.gold, "purse_rises": {b: nb.inventory.gold - prior.buildings[b].inventory.gold for b, nb in state.buildings.items() if b in prior.buildings and nb.inventory.gold > prior.buildings[b].inventory.gold},
                     "hunger": ent.biological.hunger, "sleep_debt": ent.biological.sleep_debt,
                     "update_strategic": None if strategic is None else {"current_project_id_set": getattr(strategic, "current_project_id_set", None), "project_entries": entries,
                                                                           "projects_remove_names_it": before["current_project_id"] in (getattr(strategic, "projects_remove", None) or [])},
                     "writer": "not readable"}
            klass = classify(before, after)
            self.sequence.setdefault(eid, []).append((before["tick"], klass, before["hunger"]))
            if klass != "continues":
                self.rows.append({"subject": eid, "tick": before["tick"], "need": need, "class": klass, "before": before, "after": after})
            self._hard_check(eid)

    def _hard_check(self, eid: int) -> None:
        seq = self.sequence[eid]
        if len(seq) >= HARD_CONSECUTIVE and all(k == "D3" and h >= HARD_LINE for _, k, h in seq[-HARD_CONSECUTIVE:]):
            last = seq[-HARD_CONSECUTIVE:]
            event = {"subject": eid, "ticks": [t for t, _, _ in last], "hunger": [round(h, 2) for _, _, h in last]}
            if not self.hard or self.hard[-1] != event:
                self.hard.append(event)

    def report(self) -> Dict[str, Any]:
        classes = Counter(r["class"] for r in self.rows)
        d2_reasons = Counter((r["after"]["project"] or {}).get("ended_by") or "COMPLETED_NOT_MET" for r in self.rows if r["class"] == "D2")
        return {"classes": dict(classes), "d2_by_reason": dict(d2_reasons), "hard_d3_cycles": self.hard, "rows": self.rows, "threat_at_decision": sum(1 for r in self.rows if r["before"]["threat"]),
                "reach": {"apply_calls": self.apply_calls, "decisions": self.decisions, "escalated_need_decisions": self.escalated_decisions, "d_family_decisions": self.d_family_decisions},
                "spy_exceptions": self.spy_exceptions}


def read_funcs() -> Tuple[Dict[str, Any], List[str]]:
    """The tree's own predicates; a missing name is a finding, not a substitution."""
    findings: List[str] = []
    funcs: Dict[str, Any] = {}
    for key, module, name in (("need_is_pressing", "src.engine.need_pull", "need_is_pressing"), ("present_threat_to", "src.ai.goals.present_threat", "present_threat_to"),
                              ("acting_threat_to", "src.ai.goals.present_threat", "acting_threat_to"), ("same_kind", "src.core.strategic", "same_kind"), ("live_statuses", "src.core.strategic", "LIVE_PROJECT_STATUSES")):
        try:
            funcs[key] = getattr(__import__(module, fromlist=[name]), name)
        except Exception as exc:
            findings.append(f"tree does not expose {module}.{name}: {type(exc).__name__}")
    return funcs, findings


def run_ticks(kernel: Any, ticks: int, spy: Optional[Phase0Spy]) -> Any:
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
    plain_hash = argv[argv.index("--plain-hash") + 1] if "--plain-hash" in argv else None
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    if mode not in ("plain", "spy"):
        raise ValueError(f"--mode must be plain or spy, not {mode!r}")
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("need_project_cleared_trace_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    pa = load_sibling("person_attack_spy")
    errors = pa.LoggingErrors()
    logging.getLogger().addHandler(errors)
    pa.inject_no_replay_if_recording_off()
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"need_project_cleared_trace_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="need_project_cleared_trace_spy build_kernel")
    spy: Optional[Phase0Spy] = None
    findings: List[str] = []
    if mode == "spy":
        from src.ai.score_modifiers import ScoreModifierSystem
        from src.engine.apply import ApplyPath

        funcs, findings = read_funcs()
        if findings:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps({"world": world, "seed": seed, "mode": mode, "findings": findings, "void": True}), encoding="utf-8")
            return EXIT_FINDING
        spy = Phase0Spy(funcs).install(ApplyPath, ScoreModifierSystem)
    fatal: Optional[str] = None
    try:
        final_state = run_ticks(kernel, ticks, spy)
    except BaseException:
        fatal = traceback.format_exc()[-1500:]
        final_state = kernel.state
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
