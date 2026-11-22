"""Subject trace for the designer's readiness and legality read (Q2; scope word for word at the planner's seat commit 246b065f5). READ-ONLY: it records evidence, it never judges.

One child process per cell, started by ``subject_trace_run`` with cwd = the frozen head tree and PYTHONPATH = that tree. ``--mode spy`` runs the SAME build as the person-attack spy (same pinned check, same
flags, same no-replay injection, recording OFF) with two pass-through wrappers; ``--mode plain`` (used only by the smoke run) runs the build with no wrapper and writes the final hash.

PER-TICK ROWS. For every subject (``--plan`` file, written by ``subject_trace_run derive`` from the SEALED O3 cells) and every tick inside one of its windows, one row built from the prior state (BEFORE the apply)
and the new state (AFTER it): movement mode; task work kind, action, reason and the payload's scalar fields (the goal the entity is executing); ``navigation.target`` (the goal tile), path length and
``navigation.last_failure_reason``; ``combat.readiness``, hp, alive; position; ``lodged_in``; the strategic current project and objective ids with the active objective's own record when it can be found;
the Chebyshev distance (max of the axis distances) to each counterpart (the attackers of a victim, the victims of an attacker) and to the goal tile. A body that is dead reads ``state: DEAD`` (``alive: false``), one that has been removed reads ``present: false, state: ABSENT``; the rows of a subject are never skipped after its death or removal.
The state has no single "goal" field: the fields above are every place a goal or objective lives in the entity (task payload, navigation target, strategic objective); nothing is derived from them.

LEGALITY WRAPPER. ``LegalityServiceV2.verify_attack_legality`` is wrapped by a pass-through: the ORIGINAL result object is returned unchanged; a row (tick, attacker, target, result, failure text, opportunity flag)
is recorded only where the attacker is a subject and the call's TICK is inside that subject's window. The tick is the context's own ``tick`` when it has one, else ``world_time + offset`` (offset = state.tick - state.world_time of the apply wrapper's latest state); each row carries ``tick_source`` and the raw ``world_time``. A non-constant offset sets ``offset_drift`` and voids the cell; a call with neither tick nor world_time raises (the original call raises first when it needs the clock, and that passes through); a call before any offset exists is counted in ``legality_calls_unplaced`` and never meets reach. The engine calls it from these sites (re-grepped in both frozen trees, every match):
at 87792e3e8 domain/combat_actions.py:56, combat.py:166, 268, 342, 444, tactical.py:423, tactical_flight_guard.py:71, tactical_hold.py:38; at e72270894 the same sites, with tactical.py at :434. The class-level wrapper sees every one of them.
One ATTACK action can give TWO calls (combat_actions.py:56, then combat.py:166 inside resolve_attack), so legality call counts are not attack counts. combat_actions.py:56 passes a context, not the state, which has no ``tick``: its rows use the
derived tick, and only rows with a known in-window tick meet the reach rule (``legality_calls_in_window``). Stage-1 ``attack_rows`` (read by the derivation) are attacks BY watched ids, not by every attacker.

WAY READS (the #992 wolf-starvation read, ``WayReads``; each is a read of an existing pure function, on a SHALLOW COPY of the prior state so a cache the call writes (``world_indexes``, the spatial caches) lands on the copy and never on the state the kernel
keeps): the biological need fields (hunger, sleep_debt, rest_pressure, last_meal_tick, last_sleep_tick, well_rested_until) of every snapshot; ``ways_in_reach`` and ``open_food_step_kinds`` (src/ai/goals/ways.py), ``opening_steps`` (the same step tests with
each step's own reason string and target), the carcasses within the scavenge radius (id, tile, Manhattan distance, in-range, edible, own species); the typed hit record (``last_hit_*``) turned into ``hits_taken`` events; the typed death record. The kit note
(wolf_starve_kit_note.md) says why each call is pure.

NON-PERTURBATION AND FATALITY. The spy's final hash must equal the SEALED plain twin's (checked by ``subject_trace_run check``). Any exception raised inside a wrapper's own recording code is stored AND re-raised:
a kernel that swallows it still leaves ``spy_exceptions`` in the document, and the child exits 8 (fatal, the cell is void). The original verification's own exceptions are not the spy's: they pass through.

Heavy-job hygiene: the file name carries ``_spy`` so the shared busy gate sees it; put the command in a script file.
Usage: python subject_trace_spy.py <world> <seed> <ticks> <out.json> --arm new|base --plan <subjects.json> [--mode plain|spy]
"""
from __future__ import annotations

import copy
import enum
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


def kind_name(kind: Any) -> str:
    """An enum member by its NAME (``OpeningStepKind.HUNT`` -> "HUNT", ``WayKind.HUNT_EAT_RAW`` -> "HUNT_EAT_RAW": the values of OpeningStepKind are lower case), anything else by ``str``."""
    return kind.name if isinstance(kind, enum.Enum) else str(kind)


def manhattan(a: Any, b: Any) -> Optional[float]:
    if a is None or b is None:
        return None
    return abs(float(a[0]) - float(b[0])) + abs(float(a[1]) - float(b[1]))


NEED_FIELDS = ("hunger", "sleep_debt", "rest_pressure", "last_meal_tick", "last_sleep_tick", "well_rested_until")


def read_view(state: Any) -> Any:
    """The state the pure reads run on: a SHALLOW COPY, so the cache attributes some reads write (``object.__setattr__(state, "world_indexes", ...)`` and the like) land on the copy, never on the state the kernel keeps.
    Nothing is deep-copied: the entities and every dict are the real ones and are only read."""
    return copy.copy(state)


class WayReads:
    """The food ways of one body at one moment (the #992 read). The functions are injected so a control can pass fakes; ``from_tree()`` binds the frozen tree's own."""

    def __init__(self, ways_in_reach: Callable, open_food_step_kinds: Callable, opening_steps: Callable, way_in_range: Callable, can_eat_item: Callable, scavenge_radius: float = 20.0) -> None:
        self.ways_in_reach, self.open_food_step_kinds, self.opening_steps = ways_in_reach, open_food_step_kinds, opening_steps
        self.way_in_range, self.can_eat_item, self.scavenge_radius = way_in_range, can_eat_item, scavenge_radius

    @classmethod
    def from_tree(cls) -> "WayReads":
        from src.ai.goals import opening_steps as steps_module
        from src.ai.goals.ways import ways_in_reach
        from src.engine.appraisal import can_eat_item
        from src.engine.rpg_depth import LeashService

        return cls(ways_in_reach, steps_module.open_food_step_kinds, steps_module.opening_steps, LeashService.way_in_range, can_eat_item, float(getattr(steps_module, "SCAVENGE_RADIUS", 20.0)))

    def carcasses(self, view: Any, entity: Any) -> List[Dict[str, Any]]:
        found = []
        for corpse in view.corpses.values():
            distance = manhattan(entity.navigation.position, corpse.position)
            if distance is None or distance > self.scavenge_radius:
                continue
            dead = view.entities.get(corpse.original_entity_id)
            found.append({"id": safe(corpse.id), "tile": safe(corpse.position), "distance": distance, "in_way_range": bool(self.way_in_range(entity, corpse.position)),
                          "edible": any(stack.quantity > 0 and self.can_eat_item(entity, stack.item_id) for stack in corpse.items),
                          "own_species": dead is not None and dead.kind == entity.kind})
        return sorted(found, key=lambda c: (c["distance"], str(c["id"])))

    def reads(self, state: Any, entity: Any) -> Dict[str, Any]:
        view = read_view(state)
        ways = [kind_name(w) for w in self.ways_in_reach(entity, view)]
        open_kinds = sorted(kind_name(k) for k in self.open_food_step_kinds(entity, view))
        steps = {}
        for step in self.opening_steps(entity, view):
            steps[kind_name(step.kind)] = {"available": bool(step.available), "reason": step.reason, "target_id": step.target_id, "target_entity_id": step.target_entity_id, "target_pos": safe(step.target_pos)}
        food_steps = sorted(k for k, v in steps.items() if v["available"] and k in ("FORAGE", "SCAVENGE", "HUNT"))
        return {"ways": ways, "open_food_steps": open_kinds, "steps": steps, "steps_consistent": food_steps == open_kinds, "carcasses": self.carcasses(view, entity), "scavenge_radius": self.scavenge_radius}


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
        return {"present": False, "state": "ABSENT"}
    nav, combat, task = entity.navigation, entity.combat, entity.task
    payload = task.payload if isinstance(task.payload, dict) else {}
    mode = nav.movement_mode
    return {
        "present": True, "state": "ALIVE" if combat.alive else "DEAD", "mode": str(getattr(mode, "value", mode)), "work_kind": safe(task.work_kind), "action": safe(payload.get("action")), "reason": safe(payload.get("reason")),
        "payload": {str(k): safe(v) for k, v in payload.items() if v is None or isinstance(v, (bool, int, float, str, tuple, list))},
        "goal_tile": safe(nav.target), "path_len": len(nav.path or []), "failure_reason": safe(nav.last_failure_reason), "readiness": combat.readiness, "hp": combat.hp, "alive": bool(combat.alive),
        "position": safe(nav.position), "lodged_in": safe(getattr(nav, "lodged_in", None)), "strategic": objective_view(entity),
        "kind": safe(getattr(entity, "kind", None)), "needs": {name: safe(getattr(getattr(entity, "biological", None), name, None)) for name in NEED_FIELDS},
        "last_hit": {"tick": safe(getattr(combat, "last_hit_tick", None)), "attackers": safe(getattr(combat, "last_hit_attackers", ())), "damages": safe(getattr(combat, "last_hit_damages", ()))},
        "death_record": death_record_view(entity), "leash": {"radius": safe(getattr(nav, "leash_radius", None)), "home": safe(getattr(nav, "home_position", None))},
    }


def death_record_view(entity: Any) -> Optional[Dict[str, Any]]:
    """The typed death record (cause, tick, last attacker, hazard kind) and the passive cause the lifecycle holds, or None while the body has neither."""
    lifecycle = getattr(entity, "lifecycle", None)
    record = getattr(lifecycle, "death_record", None)
    passive = getattr(lifecycle, "passive_death_cause", None)
    if record is None and passive is None:
        return None
    return {"record": record.to_dict() if hasattr(record, "to_dict") else safe(record), "passive_cause": safe(passive), "passive_cause_tick": safe(getattr(lifecycle, "passive_death_cause_tick", None))}


def in_windows(tick: int, windows: List[List[int]]) -> bool:
    return any(lo <= tick <= hi for lo, hi in windows)


class SubjectSpy:
    """Record-only wrappers; ``install(apply_path, legality)`` patches, ``restore()`` undoes. ``subjects`` is the plan's list for this seed: {id, roles, windows, counterparts}."""

    def __init__(self, subjects: List[Dict[str, Any]], motive: Any = None, ways: Optional[WayReads] = None) -> None:
        self.ways = ways   # a ``WayReads`` (None in older unit tests): the way/step/carcass reads, per tick, on the PRIOR state
        self.hits_taken: Dict[int, List[Dict[str, Any]]] = {}
        self.death_records: Dict[int, Dict[str, Any]] = {}
        self._legality_cursor = 0
        self.motive = motive   # a ``person_attack_spy.MotiveReads`` (None in unit tests): the stage-1 motive reads, repeated per tick for each subject and counterpart on the PRIOR state
        self.subjects = {int(s["id"]): s for s in subjects}
        self.rows: List[Dict[str, Any]] = []
        self.legality_rows: List[Dict[str, Any]] = []
        self.spy_exceptions: List[str] = []
        self.unplaced_calls = 0
        self.apply_calls = 0
        self.offset: Optional[float] = None   # state.tick - state.world_time of the apply wrapper's latest state
        self.offsets_seen: List[float] = []   # every distinct offset seen; more than one is offset_drift (the cell is void)
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
        world_time = getattr(state, "world_time", None)
        if world_time is not None:
            self.offset = tick - world_time
            if self.offset not in self.offsets_seen:
                self.offsets_seen.append(self.offset)
        fresh = self.legality_rows[self._legality_cursor:]   # the legality calls made since the previous apply: this tick's
        for subject_id, subject in self.subjects.items():
            if not in_windows(tick, subject["windows"]):
                continue
            before, after = prior.entities.get(subject_id), state.entities.get(subject_id)
            snap_before, snap_after = snapshot(before), snapshot(after)
            row: Dict[str, Any] = {"tick": tick, "id": subject_id, "roles": subject["roles"], "before": snap_before, "after": snap_after, "distance_before": {}, "distance_after": {}}
            for other in subject["counterparts"]:
                row["distance_before"][str(other)] = chebyshev(snap_before.get("position"), snapshot_position(prior, other))
                row["distance_after"][str(other)] = chebyshev(snap_after.get("position"), snapshot_position(state, other))
            if self.motive is not None:   # the same reads as stage 1 (relation both ways with the tree's own call form, attacked_me_recently both ways, the objective, the task reason), per counterpart, on the PRIOR state
                row["motive_reads"] = {str(other): self.motive.inputs(prior, subject_id, other) for other in subject["counterparts"] if subject_id in prior.entities and other in prior.entities}
            row["goal_distance_before"] = chebyshev(snap_before.get("position"), snap_before.get("goal_tile"))
            row["goal_distance_after"] = chebyshev(snap_after.get("position"), snap_after.get("goal_tile"))
            if self.ways is not None:
                self.observe_wolf_reads(row, subject_id, prior, state, before, snap_before, snap_after, fresh)
            self.rows.append(row)
        self._legality_cursor = len(self.legality_rows)

    def observe_wolf_reads(self, row: Dict[str, Any], subject_id: int, prior: Any, state: Any, before: Any, snap_before: Dict[str, Any], snap_after: Dict[str, Any], fresh: List[Dict[str, Any]]) -> None:
        """The #992 reads of one subject-tick (module docstring, WAY READS): the ways and steps the pull saw (PRIOR state), the hit just taken, the death record, and a compact row for every body the subject met this tick."""
        row["ways"] = self.ways.reads(prior, before) if before is not None and snap_before.get("alive") else None
        before_tick, after_tick = snap_before.get("last_hit", {}).get("tick"), snap_after.get("last_hit", {}).get("tick")
        if after_tick is not None and after_tick != before_tick:
            event = {"tick": state.tick, "hit_tick": after_tick, "attackers": snap_after["last_hit"]["attackers"], "damages": snap_after["last_hit"]["damages"], "hp_delta": (snap_before.get("hp") or 0) - (snap_after.get("hp") or 0)}
            self.hits_taken.setdefault(subject_id, []).append(event)
            row["hit_taken"] = event
        if snap_after.get("death_record") is not None and subject_id not in self.death_records:
            self.death_records[subject_id] = {"first_seen_tick": state.tick, **snap_after["death_record"]}
        row["legality_this_tick"] = [{"target_id": r["target_id"], "legal": r["legal"], "reason": r["reason"]} for r in fresh if r["attacker_id"] == subject_id]
        met = {r["target_id"] for r in row["legality_this_tick"]} | set((row.get("hit_taken") or {}).get("attackers") or ())
        for step in ((row["ways"] or {}).get("steps") or {}).values():
            met.add(step.get("target_entity_id"))
        met.add((snap_after.get("strategic", {}).get("objective") or {}).get("target_entity_id"))
        met.add(snap_after.get("payload", {}).get("target_id"))
        row["counterparts"] = {str(other): self.counterpart_row(state, snap_after, other) for other in sorted(m for m in met if isinstance(m, int) and m != subject_id)}

    @staticmethod
    def counterpart_row(state: Any, subject_after: Dict[str, Any], other_id: int) -> Dict[str, Any]:
        entity = state.entities.get(other_id)
        if entity is None:
            return {"present": False}
        position = safe(entity.navigation.position)
        return {"present": True, "alive": bool(entity.combat.alive), "hp": entity.combat.hp, "kind": safe(getattr(entity, "kind", None)), "position": position,
                "chebyshev": chebyshev(subject_after.get("position"), position), "manhattan": manhattan(subject_after.get("position"), position)}

    def legality_tick(self, state_or_context: Any) -> tuple:
        """(tick, tick_source, raw world_time) of a legality call. The context's own ``tick`` when it has one; else ``world_time + offset`` (offset = state.tick - state.world_time of the apply wrapper's latest
        state); no tick, no world_time: the call cannot be placed, which is a spy exception (the original call is what raises first when it needs the clock, and that error passes through)."""
        world_time = getattr(state_or_context, "world_time", None)
        tick = getattr(state_or_context, "tick", None)
        if tick is not None:
            return tick, "context", world_time
        if world_time is None:
            raise RuntimeError("a legality call whose context has neither tick nor world_time cannot be placed in a window")
        if self.offset is None:
            return None, "no_offset_yet", world_time
        return world_time + self.offset, "world_time+offset", world_time

    def legality(self, attacker: Any, target: Any, state_or_context: Any, args: tuple, kwargs: dict, result: Any) -> None:
        subject = self.subjects.get(getattr(attacker, "id", None))
        if subject is None:
            return
        tick, source, world_time = self.legality_tick(state_or_context)
        if tick is None:
            self.unplaced_calls += 1                      # known subject, unknown tick: counted, never an in-window call
            return
        if not in_windows(tick, subject["windows"]):
            return
        legal, reason = result[0], result[1]
        self.legality_rows.append({
            "tick": tick, "tick_source": source, "world_time": safe(world_time), "in_window": True, "attacker_id": attacker.id, "target_id": getattr(target, "id", None), "legal": bool(legal),
            "reason": safe(getattr(reason, "name", reason)), "failure_text": None if legal else str(getattr(reason, "value", reason)),
            "opportunity": bool(kwargs.get("is_opportunity_attack", args[0] if args else False)),
        })

    def report(self) -> Dict[str, Any]:
        return {"rows": self.rows, "row_count": len(self.rows), "legality_rows": self.legality_rows, "legality_call_count": len(self.legality_rows), "legality_calls_in_window": len(self.legality_rows),
                "legality_calls_unplaced": self.unplaced_calls, "offsets_seen": self.offsets_seen, "offset_drift": len(self.offsets_seen) > 1,
                "subject_ids": sorted(self.subjects), "apply_calls": self.apply_calls, "spy_exceptions": self.spy_exceptions,
                "hits_taken": {str(k): v for k, v in self.hits_taken.items()}, "death_records": {str(k): v for k, v in self.death_records.items()}, "way_reads": self.ways is not None}


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
    sys.dont_write_bytecode = True   # FIRST: this process imports the frozen tree, and whatever the environment says no .pyc may land in it
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

        spy = SubjectSpy(plan["subjects_by_seed"][str(seed)], load_sibling("person_attack_spy").MotiveReads.from_tree(), WayReads.from_tree() if plan.get("way_reads") else None).install(ApplyPath, LegalityServiceV2)
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
