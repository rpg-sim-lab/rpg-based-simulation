"""Own-job spy for the K2 fix (TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER; counts fixed by rpg-designer in rpg-designer-k2-fix-plan-rulings.md, a73bc655d487395b...).

ONE cell per process (cwd = the frozen tree, PYTHONPATH = that tree, recording OFF). READ-ONLY, hash-neutral: a pass-through on ``ApplyPath.apply_generation`` and one on ``ActionRouter.execute_action``, both returning the
ORIGINAL object. ``--mode plain`` runs the build with no wrapper and writes the final hash (the launcher requires spy final_hash == plain final_hash, else the cell is VOID). It runs on BOTH arms (main and fix): on
main the fix-only fields (``service_refusals``) read as absent, so the fix-only counts are 0 by construction there.

COUNTS (per cell, typed state only):
A(i)    fatigue projects newly ended WAY_CLOSED, split by the half that refused (judged on the PRIOR state): ``purse_half`` (a bed was free, the subject could not pay), ``bed_half`` (finds_no_bed), ``other`` (a resolved
        building, neither half) and ``other_unresolved`` (the active objective's target names no building: A is then NOT MEASURED for the cell). A real fatigue objective's target is a POSITION (trace v8: [40.0, 31.0]); the building is the
        one the tree's own lookup (``SpatialQueryService.get_building_at``) finds at exactly that tile (both coordinates whole numbers, no radius).
A(ii)   report-only: for EVERY WAY_CLOSED end (not only a purse-half one), what the subject does in its next 200 ticks (samples at +1, +10, +50, +100, +200: current project kind, sleep_debt, lodged_in, gold, alive, task action; ticks of a SLEEP or REST action),
        and, on both arms, the subjects that ever reach sleep_debt >= 98 (the collapse line), each with its LAST 200 ticks before the first reach
        (samples at -200, -100, -50, -10, -1: current project kind, task action, lodged_in, gold, sleep_debt; ticks of a SLEEP or REST action, ticks lodged, the project kinds held).
B(i)    service blockers filed (a ``blocker_service_<action>_<building>`` appearing on a subject), with the first tick, by action.
B(ii)   FALSE FIRES (must be 0): a blocker filed for a (subject, action, building) that was DELIVERED (a fresh accepted result for the building, or the paid transfer at the building) between the first refusal of its streak and its filing.
B(iii)  STILL LOOPING (must be 0): the same (subject, action, building) EXECUTED undelivered (the router channel, judged on the next apply) more than 100 ticks after its blocker was filed while the blocker stood. A REST that is HELD
        (post-apply payload action REST, target b, outcome SUCCESS, or lodged_in == b: the bed was paid once) is not an undelivered execution. The router covers EAT and REST only: a filing for any other action makes B(iii)
        "not readable for <action>", never 0.
(vi)    report-only: typed refusals appended per action and reason, blockers removed (quiet spell).
Usage: python k2fix_ownjob_spy.py <world> <seed> <ticks> <out.json> --mode plain|spy [--plain-hash <hex>]
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import traceback
from collections import Counter, deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

EXIT_SPY_EXCEPTION = 8
EXIT_HASH_MISMATCH = 3
EXIT_PROBE_ERROR = 5
SERVICE_PREFIX = "blocker_service_"
STILL_LOOPING_TICKS = 100
FOLLOW_UP_TICKS = 200
SAMPLE_OFFSETS = (1, 10, 50, 100, 200)
BEFORE_OFFSETS = (200, 100, 50, 10, 1)                  # ticks BEFORE the first sleep_debt >= 98 reach
COLLAPSE_LINE = 98.0
SOURCE_KINDS = {"EAT": "TOWN_SERVICE", "REST": "TOWN_SERVICE"}


def load_sibling(name: str) -> Any:
    """A kit module loaded by file path from THIS file's directory (never through the frozen tree on PYTHONPATH)."""
    key = f"_k2fix_ownjob_{name}"
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
    """The intent results that belong to THIS apply (patches.py keeps the previous tuple when an update has none): a result is fresh when its transaction_id is not among the prior state's results."""
    now = list(getattr(ent.identity, "latest_intent_results", ()) or ())
    before = list(getattr(prior_ent.identity, "latest_intent_results", ()) or ()) if prior_ent is not None else []
    prior_ids = {getattr(r, "transaction_id", None) for r in before if getattr(r, "transaction_id", None) is not None}
    return [r for r in now if not ((getattr(r, "transaction_id", None) is not None and r.transaction_id in prior_ids) or (getattr(r, "transaction_id", None) is None and r in before))]


def delivered(prior_ent: Any, ent: Any, prior_buildings: Any, buildings: Any, action: str, building: int) -> bool:
    """Whether the apply delivered (action, building) to the subject: a fresh accepted result of the action's source kind for the building, or the paid transfer (the subject's gold falls by D > 0 and the building's purse rises by at least D)."""
    if any(r.accepted and r.source_kind == SOURCE_KINDS.get(action) and r.source_id == building for r in fresh_results(prior_ent, ent)):
        return True
    pb, nb = prior_buildings.get(building), buildings.get(building)
    if pb is None or nb is None:
        return False
    spent = prior_ent.inventory.gold - ent.inventory.gold
    return bool(spent > 0 and (nb.inventory.gold - pb.inventory.gold) >= spent)


def active_objective(project: Any) -> Any:
    """The project's ACTIVE objective (``active_objective_id``), else its first, as the tree's own `project_target_matches` reads it (src/core/strategic.py)."""
    objectives = getattr(project, "objectives", None) or []
    return next((o for o in objectives if o.id == getattr(project, "active_objective_id", None)), None) or (objectives[0] if objectives else None)


def resolve_building(state: Any, project: Any, funcs: Dict[str, Callable]) -> Any:
    """The building the project's ACTIVE objective names: its target is a POSITION and the building is the one the tree's own tile lookup finds at exactly that tile (both coordinates whole numbers; no radius). None when it
    names no building (a missing objective, a target that is not a position, a fractional tile, no building there)."""
    objective = active_objective(project)
    target = getattr(objective, "target", None)
    if not isinstance(target, (list, tuple)) or len(target) != 2:
        return None
    try:
        x, y = float(target[0]), float(target[1])
    except (TypeError, ValueError):
        return None
    if x != int(x) or y != int(y):
        return None
    return funcs["building_at"](state, (int(x), int(y)))


def resolve_target(prior: Any, prior_ent: Any, project: Any, funcs: Dict[str, Callable]) -> Tuple[Any, Optional[str]]:
    """The building a WAY_CLOSED end names and how it was found: FIRST the PRIOR state's task payload ``target_id`` (an id of a building of the prior state: the building the REST or the arrival used), THEN the active
    objective's exact tile (`resolve_building`; no radius). ``(None, None)`` when neither names a building (a payload target that is not a building does not stop the tile)."""
    payload = prior_ent.task.payload if isinstance(prior_ent.task.payload, dict) else {}
    target_id = payload.get("target_id")
    if isinstance(target_id, int) and not isinstance(target_id, bool) and target_id in prior.buildings:
        return prior.buildings[target_id], "payload"
    building = resolve_building(prior, project, funcs)
    return (building, "tile") if building is not None else (None, None)


def classify_way_closed(prior: Any, prior_ent: Any, building: Any, funcs: Dict[str, Callable]) -> str:
    """Which half refused the bed on the PRIOR state: ``other_unresolved`` (no building), ``bed_half`` (the tree's own finds_no_bed), ``purse_half`` (a bed was free, the subject keeps coin and the REST price is not covered), else ``other``."""
    if building is None:
        return "other_unresolved"
    if funcs["finds_no_bed"](prior, prior_ent, building):
        return "bed_half"
    if building.functional and funcs["lodges"](building) and funcs["keeps_coin"](prior_ent) and not funcs["payment_covers"](prior_ent, "REST"):
        return "purse_half"
    return "other"


def is_held(ent: Any, action: str, building: int) -> bool:
    """A REST at ``building`` that is HELD after the bed was paid once (building_services.py:86-88): the post-apply payload is action REST, target ``building`` and ``outcome`` SUCCESS, or the subject is lodged in it."""
    if action != "REST":
        return False
    payload = ent.task.payload if isinstance(ent.task.payload, dict) else {}
    return (payload.get("action") == "REST" and payload.get("target_id") == building and payload.get("outcome") == "SUCCESS") or getattr(ent.navigation, "lodged_in", None) == building


class OwnJobSpy:
    def __init__(self, funcs: Dict[str, Callable], limit: Optional[int] = None) -> None:
        self.funcs = funcs
        self.limit = limit                                  # service_refusal_limit (the fix arm); None on main
        self.apply_calls = 0
        self.router_calls = 0
        self.router_seen: Dict[int, List[Tuple[int, str, Any]]] = {}
        self.way_closed: List[Dict[str, Any]] = []
        self.traces: List[Dict[str, Any]] = []
        self.sleep98: Dict[int, int] = {}
        self.recent: Dict[int, "deque[tuple]"] = {}
        self.collapse_windows: List[Dict[str, Any]] = []
        self.filed: List[Dict[str, Any]] = []
        self.standing: Dict[Tuple[int, str], Dict[str, Any]] = {}
        self.removed: List[Dict[str, Any]] = []
        self.delivery_ticks: Dict[Tuple[int, str, int], List[int]] = {}
        self.refusals_typed: Counter = Counter()
        self.undelivered_after_filing: List[Dict[str, Any]] = []
        self.executions_after_filing = 0
        self.held_executions_after_filing = 0
        self.spy_exceptions: List[str] = []
        self._patched: List[tuple] = []

    # ---- install / restore
    def install(self, apply_path: Any, router_cls: Any) -> "OwnJobSpy":
        original_apply = apply_path.__dict__["apply_generation"].__func__
        original_exec = router_cls.__dict__["execute_action"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original_apply(prior_state, update, *args, **kwargs)
            spy.guarded(spy.observe, prior_state, new_state)
            return new_state

        def execute_action(*args, **kwargs):
            result = original_exec(*args, **kwargs)
            spy.guarded(spy.router_call, args, kwargs)
            return result

        self._patched += [(apply_path, "apply_generation", original_apply), (router_cls, "execute_action", original_exec)]
        apply_path.apply_generation = staticmethod(apply_generation)
        router_cls.execute_action = staticmethod(execute_action)
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

    def router_call(self, args: tuple, kwargs: dict) -> None:
        self.router_calls += 1
        entity = args[0] if args else kwargs.get("entity")
        payload = args[1] if len(args) > 1 else kwargs.get("payload")
        tick = args[2] if len(args) > 2 else kwargs.get("current_tick", 0)
        if not isinstance(payload, dict) or str(val(payload.get("action"))) not in SOURCE_KINDS or payload.get("target_id") is None:
            return
        if entity is None:
            raise AttributeError("'NoneType' object has no attribute 'id'")
        self.router_seen.setdefault(int(tick), []).append((entity.id, str(val(payload["action"])), payload["target_id"]))

    # ---- one apply
    def observe(self, prior: Any, state: Any) -> None:
        self.apply_calls += 1
        tick = state.tick
        executions = self.router_seen.pop(tick - 1, [])
        for eid, ent in state.entities.items():
            prior_ent = prior.entities.get(eid)
            if prior_ent is None:
                continue
            alive = bool(ent.combat.alive)
            if alive:
                self._track(eid, ent, tick)
            self._way_closed(prior, prior_ent, ent, eid, tick)
            self._refusals(prior_ent, ent, eid, tick)
            self._blockers(prior_ent, ent, eid, tick)
            self._deliveries(prior, prior_ent, state, ent, eid, tick)
        for eid, action, target in executions:                            # B(iii): an execution of the way judged on the next apply
            ent, prior_ent = state.entities.get(eid), prior.entities.get(eid)
            standing = self.standing.get((eid, f"{action}_{target}"))
            if ent is None or prior_ent is None or standing is None:
                continue
            if is_held(ent, action, int(target)):                                  # a served, held REST repeats its action every tick: not an undelivered execution
                self.held_executions_after_filing += 1
                continue
            self.executions_after_filing += 1
            if not delivered(prior_ent, ent, prior.buildings, state.buildings, action, int(target)) and (tick - 1) - standing["filed"] > STILL_LOOPING_TICKS:
                self.undelivered_after_filing.append({"subject": eid, "action": action, "building": int(target), "filed": standing["filed"], "execution_tick": tick - 1})
        self._follow_up(state, tick)

    def _track(self, eid: int, ent: Any, tick: int) -> None:
        """The rolling record of a subject (its last 200 ticks) and, at its first sleep_debt >= 98, the window BEFORE the collapse."""
        payload = ent.task.payload if isinstance(ent.task.payload, dict) else {}
        project = ent.strategic.projects.get(ent.strategic.current_project_id or "")
        action = str(val(payload["action"])) if payload.get("action") is not None else None
        sample = (tick, ent.biological.sleep_debt, None if project is None else str(val(project.kind)), action, getattr(ent.navigation, "lodged_in", None), ent.inventory.gold)
        buffer = self.recent.setdefault(eid, deque(maxlen=FOLLOW_UP_TICKS))
        if ent.biological.sleep_debt >= COLLAPSE_LINE and eid not in self.sleep98:
            self.sleep98[eid] = tick
            window = list(buffer)
            samples = {}
            for offset in BEFORE_OFFSETS:
                hit = next((x for x in window if x[0] == tick - offset), None)
                if hit is not None:
                    samples[str(offset)] = {"tick": hit[0], "sleep_debt": hit[1], "project_kind": hit[2], "task_action": hit[3], "lodged_in": hit[4], "gold": hit[5]}
            self.collapse_windows.append({"subject": eid, "tick": tick, "samples": samples, "window_ticks": len(window), "sleep_action_ticks": sum(1 for x in window if x[3] == "SLEEP"),
                                          "rest_action_ticks": sum(1 for x in window if x[3] == "REST"), "lodged_ticks": sum(1 for x in window if x[4] is not None), "project_kinds": sorted({x[2] for x in window if x[2] is not None})})
        buffer.append(sample)

    def _deliveries(self, prior: Any, prior_ent: Any, state: Any, ent: Any, eid: int, tick: int) -> None:
        """Deliveries this apply, for B(ii): the buildings of a fresh accepted result, and the buildings whose purse rose when the subject paid."""
        fresh = [r for r in fresh_results(prior_ent, ent) if r.accepted]
        spent = prior_ent.inventory.gold - ent.inventory.gold
        if not fresh and spent <= 0:
            return
        candidates = {r.source_id for r in fresh}
        if spent > 0:
            candidates |= {b for b, nb in state.buildings.items() if b in prior.buildings and nb.inventory.gold > prior.buildings[b].inventory.gold}
        for building in candidates:
            for action in SOURCE_KINDS:
                if delivered(prior_ent, ent, prior.buildings, state.buildings, action, building):
                    self.delivery_ticks.setdefault((eid, action, building), []).append(tick)

    def _way_closed(self, prior: Any, prior_ent: Any, ent: Any, eid: int, tick: int) -> None:
        for pid, project in ent.strategic.projects.items():
            before = prior_ent.strategic.projects.get(pid)
            ended = getattr(project, "ended_by", None)
            if before is None or getattr(before, "ended_by", None) is not None or ended is None or str(val(ended)) != "WAY_CLOSED":
                continue
            if str(val(project.kind)).lower() != "fatigue":
                continue
            building, resolved_by = resolve_target(prior, prior_ent, project, self.funcs)
            half = classify_way_closed(prior, prior_ent, building, self.funcs)
            objective = active_objective(project)
            prior_payload = prior_ent.task.payload if isinstance(prior_ent.task.payload, dict) else {}
            raw_target = getattr(objective, "target", None)
            event = {"subject": eid, "tick": tick, "building": None if building is None else building.id, "half": half, "resolved_by": resolved_by, "gold": prior_ent.inventory.gold,
                     "sleep_debt": prior_ent.biological.sleep_debt, "project": pid, "objective_id": getattr(objective, "id", None), "objective_kind": None if objective is None else str(val(getattr(objective, "kind", None))),
                     "raw_target": list(raw_target) if isinstance(raw_target, (list, tuple)) else raw_target, "prior_payload_action": None if prior_payload.get("action") is None else str(val(prior_payload["action"])),
                     "prior_payload_target_id": prior_payload.get("target_id")}
            self.way_closed.append(event)
            self.traces.append({"subject": eid, "start": tick, "building": event["building"], "half": half, "samples": {}, "sleep_action_ticks": 0, "rest_action_ticks": 0})   # EVERY end is followed, not only a purse-half one

    def _refusals(self, prior_ent: Any, ent: Any, eid: int, tick: int) -> None:
        before = set(getattr(prior_ent.navigation, "service_refusals", ()) or ())
        for r in getattr(ent.navigation, "service_refusals", ()) or ():
            if r not in before:
                self.refusals_typed[(r.action, r.reason)] += 1

    def _blockers(self, prior_ent: Any, ent: Any, eid: int, tick: int) -> None:
        now = {b for b in ent.strategic.blockers if b.startswith(SERVICE_PREFIX)}
        before = {b for b in prior_ent.strategic.blockers if b.startswith(SERVICE_PREFIX)}
        for bid in sorted(now - before):
            way = bid[len(SERVICE_PREFIX):]
            action, building = way.rsplit("_", 1)
            records = sorted((r for r in getattr(ent.navigation, "service_refusals", ()) or () if r.action == action and r.building == int(building)), key=lambda r: r.tick)
            streak_start = records[-self.limit].tick if self.limit and len(records) >= self.limit else (records[0].tick if records else tick)
            delivered_in_streak = [t for t in self.delivery_ticks.get((eid, action, int(building)), []) if streak_start <= t <= tick]
            self.filed.append({"subject": eid, "action": action, "building": int(building), "tick": tick, "streak_start": streak_start, "false_fire": bool(delivered_in_streak), "delivery_ticks": delivered_in_streak})
            self.standing[(eid, way)] = {"filed": tick}
        for bid in sorted(before - now):
            way = bid[len(SERVICE_PREFIX):]
            gone = self.standing.pop((eid, way), None)
            self.removed.append({"subject": eid, "way": way, "tick": tick, "filed": None if gone is None else gone["filed"]})

    def _follow_up(self, state: Any, tick: int) -> None:
        for trace in self.traces:
            offset = tick - trace["start"]
            if offset < 1 or offset > FOLLOW_UP_TICKS:
                continue
            ent = state.entities.get(trace["subject"])
            if ent is None:
                continue
            payload = ent.task.payload if isinstance(ent.task.payload, dict) else {}
            action = str(val(payload.get("action"))) if payload.get("action") is not None else None
            trace["sleep_action_ticks"] += action == "SLEEP"
            trace["rest_action_ticks"] += action == "REST"
            if offset in SAMPLE_OFFSETS:
                project = ent.strategic.projects.get(ent.strategic.current_project_id or "")
                trace["samples"][str(offset)] = {"tick": tick, "alive": bool(ent.combat.alive), "project_kind": None if project is None else str(val(project.kind)), "sleep_debt": ent.biological.sleep_debt,
                                                 "lodged_in": getattr(ent.navigation, "lodged_in", None), "gold": ent.inventory.gold, "task_action": action}

    def report(self) -> Dict[str, Any]:
        halves = Counter(e["half"] for e in self.way_closed)
        unreadable = sorted({f["action"] for f in self.filed if f["action"] not in SOURCE_KINDS})          # the router covers EAT and REST only
        still_looping: Any = f"not readable for {', '.join(unreadable)}" if unreadable else len({(u["subject"], u["action"], u["building"]) for u in self.undelivered_after_filing})
        by_action = Counter(f["action"] for f in self.filed)
        return {"A_i": {"way_closed_total": len(self.way_closed), "purse_half": halves["purse_half"], "bed_half": halves["bed_half"], "other": halves["other"], "other_unresolved": halves["other_unresolved"], "resolved_by": dict(Counter(e["resolved_by"] for e in self.way_closed)), "events": self.way_closed},
                "A_ii": {"follow_ups": self.traces, "subjects_at_sleep_debt_98": len(self.sleep98), "first_tick_by_subject": {str(k): v for k, v in sorted(self.sleep98.items())}, "collapse_windows": self.collapse_windows},
                "B_i": {"filed": len(self.filed), "by_action": dict(by_action), "events": self.filed, "first_tick": min((f["tick"] for f in self.filed), default=None)},
                "B_ii_false_fires": sum(1 for f in self.filed if f["false_fire"]), "B_ii_events": [f for f in self.filed if f["false_fire"]],
                "B_iii_still_looping": still_looping, "B_iii_events": self.undelivered_after_filing, "B_iii_executions_after_filing": self.executions_after_filing, "B_iii_held_executions_after_filing": self.held_executions_after_filing,
                "B_iii_not_readable_for": unreadable,
                "vi": {"typed_refusals": {f"{a}:{r}": n for (a, r), n in sorted(self.refusals_typed.items())}, "blockers_removed": len(self.removed), "removed": self.removed},
                "reach": {"apply_calls": self.apply_calls, "router_calls": self.router_calls}, "spy_exceptions": self.spy_exceptions}


def read_funcs() -> Tuple[Dict[str, Callable], Optional[int], List[str]]:
    """Everything read from the TREE: the bed and payment predicates (present on main and on the fix) and, on the fix only, the refusal limit. A missing predicate is a finding, not a substitution."""
    findings: List[str] = []
    funcs: Dict[str, Callable] = {}
    for key, module, name in (("finds_no_bed", "src.engine.lodging", "finds_no_bed"), ("lodges", "src.engine.lodging", "lodges"), ("keeps_coin", "src.engine.serves", "keeps_coin"),
                              ("payment_covers", "src.engine.service_admission", "payment_covers")):
        try:
            funcs[key] = getattr(__import__(module, fromlist=[name]), name)
        except Exception as exc:
            findings.append(f"tree does not expose {module}.{name}: {type(exc).__name__}")
    try:
        from src.engine.spatial_query import SpatialQueryService
        funcs["building_at"] = SpatialQueryService.get_building_at
    except Exception as exc:
        findings.append(f"tree does not expose src.engine.spatial_query.SpatialQueryService.get_building_at: {type(exc).__name__}")
    limit: Optional[int] = None
    try:
        limit = int(__import__("src.content.blocker_settings", fromlist=["service_refusal_settings"]).service_refusal_settings().limit)
    except Exception:
        limit = None                                     # the main arm: no service refusal rule exists
    return funcs, limit, findings


def run_ticks(kernel: Any, ticks: int, spy: Optional[OwnJobSpy]) -> Any:
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
        raise RuntimeError("k2fix_ownjob_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF)")
    pa = load_sibling("person_attack_spy")
    errors = pa.LoggingErrors()
    logging.getLogger().addHandler(errors)
    pa.inject_no_replay_if_recording_off()
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    kernel = build_kernel(world, seed, f"k2fix_ownjob_{mode}_{world}_{seed}_{os.getpid()}")
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / f"k2fix_ownjob_{mode}_{world}_{seed}_{os.getpid()}" / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="k2fix_ownjob_spy build_kernel")
    spy: Optional[OwnJobSpy] = None
    findings: List[str] = []
    if mode == "spy":
        from src.engine.apply import ApplyPath
        from src.engine.domain.action_router import ActionRouter
        funcs, limit, findings = read_funcs()
        if findings:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps({"world": world, "seed": seed, "mode": mode, "findings": findings, "void": True}), encoding="utf-8")
            return 6
        spy = OwnJobSpy(funcs, limit).install(ApplyPath, ActionRouter)
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
        doc["limit"] = spy.limit
        doc["hash_equals_plain"] = None if plain_hash is None else final_hash == plain_hash
        code = EXIT_SPY_EXCEPTION if (fatal is not None or spy.spy_exceptions) else (EXIT_HASH_MISMATCH if plain_hash is not None and final_hash != plain_hash else 0)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    if code:
        print(f"CELL VOID rc={code}: {fatal or (spy.spy_exceptions[-1] if spy and spy.spy_exceptions else 'hash differs from the plain twin')}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
