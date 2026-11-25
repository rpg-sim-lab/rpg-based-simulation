"""K2 / K3 re-count spy: ONE cell per process (cwd = the frozen tree, PYTHONPATH = that tree, recording OFF). READ-ONLY; it counts, it never judges.
Definitions: the rpg-designer's, fixed before any data (rpg-designer-k2-k3-count-definitions.md, sha256 992b7ce37e1a...940cd5855); the pure logic is ``k2k3_count_logic``.

``--mode plain``  the build with NO wrapper; writes the final hash.      ``--mode spy``  the same build with ONE wrapper on ``ApplyPath.apply_generation`` (K2 and the K3 outcome side, post-apply)
and ONE pass-through on ``ScoreModifierSystem.apply_modifiers`` (the K3 decision side). Both return the ORIGINAL object untouched. The cell is VOID unless spy final_hash == plain final_hash (the launcher checks).

FIELD FINDINGS (a field the spec names that the tree does not expose is reported here, never substituted): see ``findings`` in the output document. Known at write time (d084b9248):
* ``IntentResult`` carries (transaction_id, accepted, reason, source_kind, source_id) and NO action/transfer kind, so an accepted TOWN_SERVICE result for building b cannot tell EAT from REST at the same inn;
  ``delivered`` is therefore the spec's own OR (accepted result for b with the action's source kind, or the action's own state change), and every channel that fired is counted.
* a refusal reason lives in ``IntentResult.reason`` (typed enum, None, or absent when the apply gave no result for b); recorded as found.
Usage: python k2k3_count_spy.py <world> <seed> <ticks> <out.json> --mode plain|spy [--plain-hash <hex>]
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
from typing import Any, Dict, List, Optional, Tuple

EXIT_SPY_EXCEPTION = 8
EXIT_HASH_MISMATCH = 3
EXIT_REACH_VOID = 4
EXIT_PROBE_ERROR = 5
EXIT_WRAPPER_MISSING = 6
SOURCE_KINDS = {"EAT": "TOWN_SERVICE", "REST": "TOWN_SERVICE", "REPAIR": "TOWN_SERVICE", "SELL": "SHOP_SELL", "BUY": "SHOP_BUY"}


def load_sibling(name: str) -> Any:
    """A kit module loaded by file path from THIS file's directory (never through the frozen tree on PYTHONPATH, whose ``tools`` package would shadow it)."""
    key = f"_k2k3_{name}"
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


def inventory_total(entity: Any) -> Optional[int]:
    try:
        return sum(int(getattr(s, "quantity", 1)) for s in entity.inventory.items)
    except Exception:
        return None


def service_dispatch(entity: Any, service_actions: frozenset, buildings: Any) -> Optional[Tuple[str, int]]:
    """(action, building id) when the post-apply task is ENTITY_ACT with a service action and a building target, else None."""
    task = entity.task
    if str(val(task.work_kind)) != "ENTITY_ACT" or not isinstance(task.payload, dict):
        return None
    action, target = task.payload.get("action"), task.payload.get("target_id")
    if action is None or str(val(action)) not in service_actions or target is None or target not in buildings:
        return None
    return str(val(action)), target


def delivered_pairs(prior_ent: Any, ent: Any, pairs: List[Tuple[str, int]]) -> Tuple[List[Tuple[str, int]], Dict[Tuple[str, int], List[Any]], Dict[str, int]]:
    """Which of the subject's pending (action, building) pairs the apply of this tick delivered: (delivered pairs, refusal reasons per pair, channel counts)."""
    results = list(getattr(ent.identity, "latest_intent_results", ()) or ())
    delivered: List[Tuple[str, int]] = []
    reasons: Dict[Tuple[str, int], List[Any]] = {}
    channels: Counter = Counter()
    gold0, gold1 = prior_ent.inventory.gold, ent.inventory.gold
    inv0, inv1 = inventory_total(prior_ent), inventory_total(ent)
    for action, b in pairs:
        kind = SOURCE_KINDS.get(action)
        mine = [r for r in results if r.source_kind == kind and r.source_id == b]
        ok = False
        if any(r.accepted for r in mine):
            ok = True
            channels["accepted_result"] += 1
        state_change = {"EAT": ent.biological.hunger < prior_ent.biological.hunger or gold1 < gold0, "REST": ent.biological.sleep_debt < prior_ent.biological.sleep_debt or gold1 < gold0,
                        "REPAIR": gold1 < gold0, "SELL": gold1 > gold0 or (inv0 is not None and inv1 is not None and inv1 < inv0), "BUY": gold1 < gold0 or (inv0 is not None and inv1 is not None and inv1 > inv0)}.get(action, False)
        if state_change:
            ok = True
            channels["state_change"] += 1
        if ok:
            delivered.append((action, b))
        else:
            reasons[(action, b)] = [str(val(r.reason)) if r.reason is not None else "None" for r in mine if not r.accepted] or ["absent"]
    return delivered, reasons, dict(channels)


def blockers_view(entity: Any) -> List[Dict[str, Any]]:
    out = []
    for blocker in (getattr(entity.strategic, "blockers", None) or {}).values():
        out.append({"id": str(blocker.id), "kind": str(val(blocker.kind)), "subject": str(blocker.subject), "resolved": bool(blocker.resolved)})
    return out


class CountSpy:
    def __init__(self, k: int, service_actions: frozenset, same_kind: Any, need_is_pressing: Any, present_threat_to: Any, acting_threat_to: Any, live_statuses: Any) -> None:
        logic = load_sibling("k2k3_count_logic")
        self.logic = logic
        self.k2 = logic.K2Tracker(k)
        self.service_actions = service_actions
        self.same_kind, self.need_is_pressing, self.present_threat_to, self.acting_threat_to, self.live_statuses = same_kind, need_is_pressing, present_threat_to, acting_threat_to, live_statuses
        self.pending_decisions: Dict[int, Dict[str, Any]] = {}     # eid -> the decision of state tick d awaiting row d+1
        self.decisions: List[Dict[str, Any]] = []
        self.loss_rows: List[Dict[str, Any]] = []
        self.dispatch_blockers: Dict[Tuple[int, str, int], Dict[str, Any]] = {}
        self.action_census: Counter = Counter()
        self.channel_counts: Counter = Counter()
        self.reasons_seen: Counter = Counter()
        self.apply_calls = 0
        self.goal_calls = 0
        self.goal_selections_seen = 0
        self.escalated_wins = 0
        self.duplicate_decisions = 0
        self.unresolved_decisions = 0
        self.spy_exceptions: List[str] = []
        self.probe_errors: List[str] = []
        self.service_dispatch_seen = 0
        self.run_blockers: Dict[Tuple[int, str, int], List[Dict[str, Any]]] = {}
        self._patched: List[tuple] = []

    # ---- install / restore
    def install(self, apply_path: Any, score_cls: Any) -> "CountSpy":
        original_apply = apply_path.__dict__["apply_generation"].__func__
        original_mod = score_cls.__dict__["apply_modifiers"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original_apply(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, prior_state, new_state)
            return new_state

        def apply_modifiers(entity, state, scores):
            result = original_mod(entity, state, scores)
            spy.guarded(spy.decision, entity, state, result)
            return result  # the ORIGINAL object, untouched

        self._patched += [(apply_path, "apply_generation", original_apply), (score_cls, "apply_modifiers", original_mod)]
        apply_path.apply_generation = staticmethod(apply_generation)
        score_cls.apply_modifiers = staticmethod(apply_modifiers)
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    def guarded(self, recorder: Any, *args: Any) -> None:
        try:
            recorder(*args)
        except BaseException:
            self.spy_exceptions.append(traceback.format_exc()[-1500:])
            raise

    # ---- K3 decision side (state tick d)
    def decision(self, entity: Any, state: Any, scores: Any) -> None:
        self.goal_calls += 1
        ranked = sorted(scores, key=lambda x: (-x.utility, str(val(x.kind))))
        win = next((s for s in ranked if s.utility >= 20.0 and not (getattr(s, "target_id", None) is None and getattr(s, "target_pos", None) is None)), None)
        if win is None:
            return
        self.goal_selections_seen += 1
        kind = str(val(win.kind))
        if kind not in self.logic.NEED_KINDS:
            return
        hunger, sleep = entity.biological.hunger, entity.biological.sleep_debt
        escalated = self.need_is_pressing(hunger, 0.0) if kind == self.logic.HUNGER_KIND else self.need_is_pressing(0.0, sleep)
        if not escalated:
            return
        self.escalated_wins += 1
        if entity.id in self.pending_decisions and self.pending_decisions[entity.id]["tick"] == state.tick:
            self.duplicate_decisions += 1
        self.pending_decisions[entity.id] = {"eid": entity.id, "tick": state.tick, "need": kind, "goal_kind": win.kind, "hunger": hunger, "sleep_debt": sleep,
                                              "threat": bool(self.present_threat_to(entity, state)), "acting_threat": bool(self.acting_threat_to(entity, state)),
                                              "current_before": getattr(entity.strategic, "current_project_id", None), "utility": float(win.utility)}

    # ---- post-apply side (row = state tick t)
    def observe(self, prior: Any, state: Any) -> None:
        self.apply_calls += 1
        tick = state.tick
        logic_classify = self.logic.classify_k3
        # K3 outcome: decisions of state tick d = tick-1 are read on this row (d+1)
        for eid in [e for e, d in self.pending_decisions.items() if d["tick"] == tick - 1]:
            d = self.pending_decisions.pop(eid)
            ent = state.entities.get(eid)
            if ent is None:
                d["klass"] = "removed_before_outcome"
                self.unresolved_decisions += 1
                self.decisions.append({k: v for k, v in d.items() if k != "goal_kind"})
                continue
            projects = getattr(ent.strategic, "projects", None) or {}
            cur_id = getattr(ent.strategic, "current_project_id", None)
            cur = projects.get(cur_id) if cur_id is not None else None
            live_same_kind_current = cur is not None and cur.status in self.live_statuses and self.same_kind(cur, d["goal_kind"])
            outcome = {"current_project_id": cur_id, "current_kind": None if cur is None else str(val(cur.kind)), "current_status": None if cur is None else str(val(cur.status)),
                       "live_kinds": sorted({str(val(p.kind)) for p in projects.values() if p.status in self.live_statuses})}
            outcome["same_kind_current_live"] = bool(live_same_kind_current)
            klass = logic_classify(d, outcome)
            row = {k: v for k, v in d.items() if k != "goal_kind"}
            row.update({"klass": klass, "outcome": outcome, "class_enum": None if cur is None else type(cur.kind).__name__})
            self.decisions.append(row)
            if klass in ("loss_L1", "loss_L2"):
                self.loss_rows.append(dict(row, row_d_plus_1_tick=tick, gate_outcome="not_readable_by_spy"))
        # K2: per subject
        buildings = state.buildings
        kinds = {b: str(val(getattr(bld, "kind", None))) for b, bld in buildings.items()}
        for eid, ent in state.entities.items():
            prior_ent = prior.entities.get(eid)
            alive = bool(ent.combat.alive)
            if prior_ent is None:
                dispatch = service_dispatch(ent, self.service_actions, buildings) if alive else None
                self.k2.step(tick, eid, True, alive, dispatch, [], None, kinds)
                continue
            pending = self.k2.pending.get(eid)
            pairs = [pending] if pending is not None else []
            delivered, reasons, channels = delivered_pairs(prior_ent, ent, pairs) if alive and pairs else ([], {}, {})
            for name, n in channels.items():
                self.channel_counts[name] += n
            for rs in reasons.values():
                for r in rs:
                    self.reasons_seen[r] += 1
            dispatch = service_dispatch(ent, self.service_actions, buildings) if alive else None
            if dispatch is not None:
                self.service_dispatch_seen += 1
                self.record_blockers(ent, eid, dispatch, tick)
            task = ent.task
            if str(val(task.work_kind)) == "ENTITY_ACT" and isinstance(task.payload, dict) and task.payload.get("action") is not None and task.payload.get("target_id") in buildings:
                self.action_census[str(val(task.payload["action"]))] += 1
            self.k2.step(tick, eid, True, alive, dispatch, delivered, reasons, kinds)
        for eid in [e for e in list(self.k2.pending) if e not in state.entities]:
            self.k2.step(tick, eid, False, False, None, [], None, kinds)

    def record_blockers(self, ent: Any, eid: int, dispatch: Tuple[str, int], tick: int) -> None:
        """Report-only: unresolved blockers whose subject names the building, seen while a dispatch of that triple is current."""
        b = dispatch[1]
        for blocker in blockers_view(ent):
            if not blocker["resolved"] and str(b) in blocker["subject"]:
                self.run_blockers.setdefault((eid, dispatch[0], b), []).append({"tick": tick, **blocker})

    def finish(self, final_tick: int) -> None:
        self.unresolved_decisions += len(self.pending_decisions)
        self.k2.finish(final_tick)

    def report(self) -> Dict[str, Any]:
        logic = self.logic
        k2 = self.k2.summary()
        for run in k2["runs"]:
            key = (run["subject"], run["action"], run["building"])
            run["blockers_named_building"] = [b for b in self.run_blockers.get(key, []) if run["first_failed"] <= b["tick"] <= run["last_failed"] + self.k2.k]
        k2["long_runs"] = [r for r in k2["runs"] if r["length"] > logic.K2_LONG]
        k3 = logic.k3_summary([d for d in self.decisions if d["klass"] in ("win", "loss_L1", "loss_L2", "excluded_threat")])
        acting = logic.k3_summary([dict(d, klass="excluded_threat" if d["acting_threat"] and d["klass"] in ("loss_L1", "loss_L2", "excluded_threat") else d["klass"]) for d in self.decisions
                                   if d["klass"] in ("win", "loss_L1", "loss_L2", "excluded_threat")])
        return {"k2": k2, "k3": k3, "k3_if_acting_threat_test": {"k3_count": acting["k3_count"], "per_need": acting["per_need"]}, "loss_rows": self.loss_rows,
                "decisions_unresolved": self.unresolved_decisions, "duplicate_decisions": self.duplicate_decisions,
                "reach": {"apply_calls": self.apply_calls, "goal_calls": self.goal_calls, "goal_selections_with_winner": self.goal_selections_seen, "escalated_need_wins": self.escalated_wins,
                          "service_dispatches_seen": self.service_dispatch_seen},
                "service_actions_read": sorted(self.service_actions), "action_census_with_building_target": dict(self.action_census), "delivered_channel_counts": dict(self.channel_counts),
                "refusal_reasons_seen": dict(self.reasons_seen), "spy_exceptions": self.spy_exceptions, "probe_errors": self.probe_errors}


def read_tree_facts() -> Dict[str, Any]:
    """Everything the kit reads from the TREE (never a number of its own): the service-action set, K, the need test, the threat tests, the live statuses, same_kind. Missing names are findings, not substitutions."""
    findings: List[str] = []
    facts: Dict[str, Any] = {}

    def need(module: str, name: str) -> Any:
        try:
            return getattr(__import__(module, fromlist=[name]), name)
        except Exception as exc:
            findings.append(f"tree does not expose {module}.{name}: {type(exc).__name__}")
            return None

    facts["service_kinds"] = need("src.engine.building_services", "SERVICE_KINDS")
    facts["k"] = need("src.engine.need_wake", "NEED_WAKE_CADENCE")
    facts["need_is_pressing"] = need("src.engine.need_pull", "need_is_pressing")
    facts["present_threat_to"] = need("src.ai.goals.present_threat", "present_threat_to")
    facts["acting_threat_to"] = need("src.ai.goals.present_threat", "acting_threat_to")
    facts["same_kind"] = need("src.core.strategic", "same_kind")
    facts["live_statuses"] = need("src.core.strategic", "LIVE_PROJECT_STATUSES")
    facts["findings"] = findings
    return facts


def run_ticks(kernel: Any, ticks: int, spy: Optional[CountSpy]) -> Any:
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
        raise RuntimeError("k2k3_count_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    pa = load_sibling("person_attack_spy")
    errors = pa.LoggingErrors()
    logging.getLogger().addHandler(errors)
    pa.inject_no_replay_if_recording_off()
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"k2k3_count_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="k2k3_count_spy build_kernel")
    spy: Optional[CountSpy] = None
    facts: Dict[str, Any] = {}
    if mode == "spy":
        from src.ai.score_modifiers import ScoreModifierSystem
        from src.engine.apply import ApplyPath

        facts = read_tree_facts()
        if facts["findings"]:
            print("FIELD FINDINGS: " + "; ".join(facts["findings"]), file=sys.stderr)
            doc = {"world": world, "seed": seed, "mode": mode, "findings": facts["findings"], "void": True}
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
            return EXIT_WRAPPER_MISSING
        spy = CountSpy(int(facts["k"]), frozenset(str(a) for a in facts["service_kinds"]), facts["same_kind"], facts["need_is_pressing"], facts["present_threat_to"], facts["acting_threat_to"],
                       facts["live_statuses"]).install(ApplyPath, ScoreModifierSystem)
    fatal: Optional[str] = None
    try:
        final_state = run_ticks(kernel, ticks, spy)
    except BaseException:
        fatal = traceback.format_exc()[-1500:]
        final_state = kernel.state
    final_hash = CanonicalStateHasher.get_hash(final_state)
    doc = {"world": world, "seed": seed, "ticks": ticks, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
           "final_hash": final_hash, "final_tick": final_state.tick, "logging_errors": errors.rows, "fatal": fatal, "findings": facts.get("findings", [])}
    code = 0
    if spy is not None:
        spy.finish(final_state.tick)
        doc.update(spy.report())
        reach = doc["reach"]
        doc["reach_void"] = reach["service_dispatches_seen"] < 1 or reach["escalated_need_wins"] < 1
        doc["hash_equals_plain"] = None if plain_hash is None else final_hash == plain_hash
        if fatal is not None or spy.spy_exceptions:
            code = EXIT_SPY_EXCEPTION
        elif spy.probe_errors:
            code = EXIT_PROBE_ERROR
        elif plain_hash is not None and final_hash != plain_hash:
            code = EXIT_HASH_MISMATCH
        elif doc["reach_void"]:
            code = EXIT_REACH_VOID
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    if code:
        print(f"CELL VOID rc={code}: {fatal or (spy.spy_exceptions[-1] if spy and spy.spy_exceptions else doc.get('reach'))}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
