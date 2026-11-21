"""Attack-on-people recorder for the frontier-world meat-eater trace (rpg-planner (u24) brief, relayed by rpg-planner-ubuntu; owner ruling #715 7063603750).

One child process per cell, started by ``person_attack_run`` with cwd = the frozen head tree and PYTHONPATH = that tree. ``--mode plain`` runs the pinned kernel and writes only the final hash (the twin);
``--mode spy`` runs the SAME build (same pinned check, same flags, same no-replay injection) with a record-only wrapper over ``ApplyPath.apply_generation``. The wrapper READS (prior, update, new state)
and returns the new state untouched, so the spy's final hash must equal the plain twin's (the runner and the summarizer both check it).

WHAT IT RECORDS. For every entity update with ``combat.attacker_id`` set whose victim (in the new state) is a person (``is_person``, the ledger's own definition), one row: tick, world_time, attacker id / kind / species /
group (``kind_group``) / declared diet (read straight from the kind's content, a second read of the same fact) / person flag / ``in_o3_group`` (``rpg_gate_metrics._is_wild_meat_eater``, the gate's own predicate), victim
id / kind / species, ``hit`` (``hp_delta < 0``, the ledger's definition; a row with ``attacker_id`` set and no hp loss is a miss), hp_delta, outcome_kind, the victim's alive flag after, the victim's state BEFORE the
hit (asleep = its task action is in ``lodging_rules.SLEEP_ACTIONS``; lodged = ``navigation.lodged_in`` set), the victim's movement mode before and after, whether the victim itself attacked on the same tick,
and the attacker's movement mode after. A watched id (every victim and every attacker of an O3-group row) also gets a row each time its movement mode changes, until the end of the run (``mode_rows``).

COUNTING CROSS-CHECK (cell-invalidating). In its own process only the spy calls ``RunLedger.reset_run_state()`` and ``RunLedger.configure(True)`` once after the kernel is built and then the REAL
``RunLedger.observe(prior, current, update)`` on every applied update (recording is OFF, so the kernel does not feed it: event_recorder.py), discarding the returned events. At the end the ledger's own
``attacks`` counter, summed the way ``rpg_gate_metrics._combat_rows`` sums it (victim_person == "1", attacker kept by ``_is_wild_meat_eater``), must equal the spy's count of O3-group hit rows, per attacker group
and in total; a difference marks the cell ``WIRING_MISMATCH`` (exit 5). The kit reads the ledger only through the public ``tally_event().payload``.

GUARDS: a root handler turns every ERROR+ record into a row; the pinned-runner check as ``arm_child`` does it; audit_mode and no_frame_pacing must be forced; the global observability mode is re-asserted
OFF on every apply. A control run (``--control``) hands COPIES of the state to the recorder and is never counted.

POSITIVE CONTROLS (built; a real run of any size needs a GO): ``--control inject_hit`` has the recorder see a COPY of one tick's state/update in which a wild meat-eater body hits a person, so a run that saw no real attack
still reports a non-zero count (the recorder and the ledger must agree on it); ``--control never_fire`` names a tick no state reaches and must exit 6.

Heavy-job hygiene: the file name carries ``_spy`` so the shared busy gate sees it; put the command in a script file; never put kit words on a launcher's command line.
Usage: python person_attack_spy.py <world> <seed> <ticks> <out.json> [--mode plain|spy] [--control inject_hit|never_fire] [--control-tick T]
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

EXIT_WIRING_MISMATCH = 5
EXIT_CONTROL_NOT_APPLIED = 6
ROW_LIMIT = 500_000  # a safety bound on the event rows, never reached by a normal run; reaching it marks the cell invalid (rows_truncated)


def load_sibling(name: str) -> Any:
    """A kit module loaded by file path from THIS file's directory (the kit checkout), never through the frozen tree on PYTHONPATH (the tree's ``tools`` package would shadow it)."""
    path = Path(__file__).resolve().with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_person_attack_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LoggingErrors(logging.Handler):
    """Root handler: every ERROR+ record of the run becomes a row (a clean run has none)."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.rows: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.rows.append({"logger": record.name, "level": record.levelname, "message": record.getMessage()[:300]})


class TreeReads:
    """The tree's own definitions the recorder reads (imported from the tree on PYTHONPATH; injectable for unit tests with plain functions)."""

    def __init__(self, kind_group: Callable, is_person: Callable, species_of: Callable, is_wild_meat_eater: Callable, declared_diet: Callable, is_asleep: Callable, is_lodged: Callable, split_key: Callable) -> None:
        self.kind_group, self.is_person, self.species_of = kind_group, is_person, species_of
        self.is_wild_meat_eater, self.declared_diet, self.is_asleep, self.is_lodged, self.split_key = is_wild_meat_eater, declared_diet, is_asleep, is_lodged, split_key

    @classmethod
    def from_tree(cls) -> "TreeReads":
        from src.ai.goals.kind_group import is_person, kind_group
        from src.core.lodging_rules import SLEEP_ACTIONS, is_lodged
        from src.engine.behavior_consumers import get_kind_properties
        from src.observability.rpg_gate_metrics import _is_wild_meat_eater, _split

        species_of = species_reader()

        def declared_diet(entity: Any) -> Optional[List[str]]:
            _, body = get_kind_properties(species_of(entity))
            diet = getattr(body, "diet", None)
            return None if diet is None else sorted(diet)

        def is_asleep(entity: Any) -> bool:
            payload = entity.task.payload
            return (payload.get("action") if isinstance(payload, dict) else None) in SLEEP_ACTIONS

        return cls(kind_group, is_person, species_of, _is_wild_meat_eater, declared_diet, is_asleep, is_lodged, _split)


def species_reader() -> Callable[[Any], str]:
    """The tree's OWN way to read an entity's species, the one its ``kind_group`` uses: ``src.core.species.species_of`` (kind = species) where the tree has it (87792e3e8), else
    ``src.content_semantics.faction.get_species_id_str`` (e72270894 predates ``src/core/species.py``). Imported lazily so the module itself needs no tree."""
    try:
        from src.core.species import species_of
        return species_of
    except ModuleNotFoundError:
        from src.content_semantics.faction import get_species_id_str
        return get_species_id_str


def mode_name(entity: Any) -> str:
    mode = entity.navigation.movement_mode
    return str(getattr(mode, "value", mode))


class PersonAttackSpy:
    """Record-only wrapper over the apply path; ``install()`` patches, ``restore()`` undoes. ``ledger`` is the RunLedger class (injectable); ``apply_path`` the ApplyPath class (injectable)."""

    def __init__(self, reads: TreeReads, ledger: Any, first_tick: int = 0, control: Optional[str] = None, control_tick: Optional[int] = None, last_tick: Optional[int] = None,
                 mode_getter: Optional[Callable[[], str]] = None) -> None:
        self.reads, self.ledger = reads, ledger
        self.control, self.control_tick, self.last_tick = control, control_tick, last_tick
        self.control_applied_count = 0
        self.rows: List[Dict[str, Any]] = []
        self.mode_rows: List[Dict[str, Any]] = []
        self.watched: Dict[int, str] = {}
        self.apply_calls = 0
        self.last_tick_seen = first_tick
        self.mode_breaches: List[Dict[str, Any]] = []
        self.rows_truncated = False
        self.mode_getter = mode_getter
        self.final_alive: Dict[str, bool] = {}
        self.ledger_attacks: Optional[Dict[str, int]] = None
        self._patched: List[tuple] = []

    # ---- ledger, in this process only
    def start_ledger(self) -> "PersonAttackSpy":
        self.ledger.reset_run_state()
        self.ledger.configure(True)
        return self

    def install(self, apply_path: Any) -> "PersonAttackSpy":
        original = apply_path.__dict__["apply_generation"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original(prior_state, update, *args, **kwargs)
            spy.observe(prior_state, update, new_state)
            return new_state

        self._patched.append((apply_path, "apply_generation", original))
        apply_path.apply_generation = staticmethod(apply_generation)
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    # ---- one applied update
    def observe(self, prior: Any, update: Any, state: Any) -> None:
        self.apply_calls += 1
        self.last_tick_seen = state.tick
        if self.mode_getter is not None:
            mode = self.mode_getter()
            if mode != "OFF":
                self.mode_breaches.append({"tick": state.tick, "mode": mode})
        observed, observed_update = state, update
        if self.control == "inject_hit" and self.control_tick is not None and state.tick == self.control_tick:
            observed, observed_update = self.injected(prior, state, update)
            self.control_applied_count += 1
        self.ledger.observe(prior, observed, observed_update)  # the REAL ledger on the kernel's own objects; the returned events are discarded
        self.record(prior, observed_update, observed)

    def injected(self, prior: Any, state: Any, update: Any) -> tuple:
        """Positive control: COPIES in which the first wild meat-eater body hits the first person body (the kernel never sees them). Returns (state copy, update copy)."""
        import dataclasses

        from src.core.update_models.combat import CombatUpdate
        from src.core.updates import EntityUpdate

        wild = next((eid for eid, body in sorted(state.entities.items()) if body.combat.alive and eid in prior.entities and self.reads.is_wild_meat_eater(self.reads.kind_group(body), int(self.reads.is_person(body)))), None)
        person = next((eid for eid, body in sorted(state.entities.items()) if body.combat.alive and self.reads.is_person(body) and eid != wild), None)
        if wild is None or person is None:
            return state, update
        updates = dict(getattr(update, "entity_updates", None) or {})
        hit = CombatUpdate(attacker_id=wild, hp_delta=-1, outcome_kind="SURVIVE")
        existing = updates.get(person)
        updates[person] = dataclasses.replace(existing, combat=hit) if existing is not None else EntityUpdate(entity_id=person, combat=hit)
        return state, dataclasses.replace(update, entity_updates=updates)

    def record(self, prior: Any, update: Any, state: Any) -> None:
        updates = getattr(update, "entity_updates", None) or {}
        attackers_this_tick = {getattr(getattr(upd, "combat", None), "attacker_id", None) for upd in updates.values()} - {None}
        for victim_id, upd in updates.items():
            combat = getattr(upd, "combat", None)
            attacker_id = getattr(combat, "attacker_id", None)
            if attacker_id is None:
                continue
            victim_after, attacker_before = state.entities.get(victim_id), prior.entities.get(attacker_id)
            if victim_after is None or attacker_before is None or not self.reads.is_person(victim_after):
                continue
            victim_before = prior.entities.get(victim_id, victim_after)
            attacker_after = state.entities.get(attacker_id, attacker_before)
            group, person = self.reads.kind_group(attacker_before), int(self.reads.is_person(attacker_before))
            o3 = bool(self.reads.is_wild_meat_eater(group, person))
            hp_delta = getattr(combat, "hp_delta", 0)
            if len(self.rows) >= ROW_LIMIT:
                self.rows_truncated = True
                continue
            self.rows.append({
                "tick": state.tick, "world_time": state.world_time, "attacker_id": attacker_id, "attacker_kind": attacker_before.kind, "attacker_species": self.reads.species_of(attacker_before),
                "attacker_group": group, "attacker_diet": self.reads.declared_diet(attacker_before), "attacker_person": person, "in_o3_group": o3, "victim_id": victim_id, "victim_kind": victim_after.kind,
                "victim_species": self.reads.species_of(victim_after), "hit": hp_delta < 0, "hp_delta": hp_delta, "outcome_kind": getattr(combat, "outcome_kind", None),
                "victim_alive_after": bool(victim_after.combat.alive), "victim_asleep_before": bool(self.reads.is_asleep(victim_before)), "victim_lodged_before": bool(self.reads.is_lodged(victim_before)),
                "victim_mode_before": mode_name(victim_before), "victim_mode_after": mode_name(victim_after), "victim_attacked_same_tick": victim_id in attackers_this_tick,
                "attacker_mode_after": mode_name(attacker_after), "hit_attackers": list(getattr(getattr(victim_after, "combat", None), "last_hit_attackers", None) or []),
            })
            if o3:
                for watch in (victim_id, attacker_id):
                    if watch not in self.watched:
                        entity = state.entities.get(watch)
                        self.watched[watch] = mode_name(entity) if entity is not None else "ABSENT"
                        self.mode_rows.append({"tick": state.tick, "id": watch, "mode": self.watched[watch], "first": True})
        for watch, last in list(self.watched.items()):
            entity = state.entities.get(watch)
            now = mode_name(entity) if entity is not None and entity.combat.alive else "DEAD_OR_ABSENT"
            if now != last:
                self.watched[watch] = now
                self.mode_rows.append({"tick": state.tick, "id": watch, "mode": now, "first": False})

    # ---- end of run
    def finish(self, final_state: Any) -> None:
        payload = self.ledger.tally_event().payload
        self.ledger_attacks = dict(payload["attacks"])
        self.ledger.reset_run_state()
        self.final_alive = {str(eid): bool(final_state.entities[eid].combat.alive) if eid in final_state.entities else False for eid in sorted(self.watched)}

    def o3_from_rows(self) -> Dict[str, int]:
        """The spy's own O3: hit rows of the O3 group, per attacker group."""
        counts: Dict[str, int] = {}
        for row in self.rows:
            if row["in_o3_group"] and row["hit"]:
                counts[row["attacker_group"]] = counts.get(row["attacker_group"], 0) + 1
        return counts

    def o3_from_ledger(self) -> Dict[str, int]:
        """The ledger's attacks counter summed the way ``_combat_rows`` sums it (victim_person == "1", attacker kept by the gate's predicate)."""
        counts: Dict[str, int] = {}
        for key, n in (self.ledger_attacks or {}).items():
            attacker, attacker_person, victim_person, _outcome = self.reads.split_key(key, 4)
            if victim_person == "1" and self.reads.is_wild_meat_eater(attacker, attacker_person):
                counts[attacker] = counts.get(attacker, 0) + n
        return counts

    def report(self) -> Dict[str, Any]:
        if self.ledger_attacks is None:
            raise RuntimeError("finish() was not called")
        spy_counts, ledger_counts = self.o3_from_rows(), self.o3_from_ledger()
        wiring_ok = spy_counts == ledger_counts and not self.mode_breaches and not self.rows_truncated
        return {
            "o3_by_group_spy": spy_counts, "o3_by_group_ledger": ledger_counts, "o3_total_spy": sum(spy_counts.values()), "o3_total_ledger": sum(ledger_counts.values()),
            "wiring": "OK" if wiring_ok else "WIRING_MISMATCH", "mode_breaches": self.mode_breaches[:50], "mode_breach_count": len(self.mode_breaches), "rows_truncated": self.rows_truncated,
            "apply_calls": self.apply_calls, "rows": self.rows, "row_count": len(self.rows), "mode_rows": self.mode_rows, "final_alive": self.final_alive,
            "control": self.control, "control_tick": self.control_tick, "control_applied_count": self.control_applied_count, "cell_valid": wiring_ok and self.control is None,
        }


def exit_status(doc: Dict[str, Any]) -> tuple:
    """(exit code, message): 6 when a control never fired, 5 on a WIRING_MISMATCH, else 0."""
    if doc.get("control") is not None and doc["control_applied_count"] == 0:
        return EXIT_CONTROL_NOT_APPLIED, f"CONTROL NOT APPLIED: no observed state had tick {doc['control_tick']}; the control never fired, so this run proves nothing"
    if doc["wiring"] != "OK":
        return EXIT_WIRING_MISMATCH, "WIRING_MISMATCH: the spy's O3 and the ledger's O3 differ (or the mode left OFF, or the row limit was hit); this cell does not count"
    return 0, ""


def inject_no_replay_if_recording_off() -> bool:
    """Under SIM_OBS_MODE=OFF the child also injects the kernel flag ``no_replay`` (the OBS variables alone keep the replay chunks): a wrapper over ``Kernel.__init__``, no source file changes. Applied to
    the plain twin and the spy alike."""
    if os.environ.get("SIM_OBS_MODE") != "OFF":
        return False
    from src.engine import kernel as kernel_module

    original = kernel_module.Kernel.__init__

    def init(self, *args, **kwargs):
        flags = dict(kwargs.get("flags") or {})
        flags["no_replay"] = True
        kwargs["flags"] = flags
        return original(self, *args, **kwargs)

    kernel_module.Kernel.__init__ = init
    return True


def main(argv: List[str]) -> int:
    from src.engine.checkpoint import CanonicalStateHasher
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.test_architecture.rpg_gate_run import build_kernel

    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "spy"
    control = argv[argv.index("--control") + 1] if "--control" in argv else None
    control_tick = int(argv[argv.index("--control-tick") + 1]) if "--control-tick" in argv else None
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    if mode not in ("plain", "spy"):
        raise ValueError(f"--mode must be plain or spy, not {mode!r}")
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("person_attack_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF): with recording on the kernel feeds the same RunLedger counters a second time")
    errors = LoggingErrors()
    logging.getLogger().addHandler(errors)
    inject_no_replay_if_recording_off()
    arm_child = load_sibling("arm_child")
    pinned_runner = arm_child._pinned_runner()
    run_id = f"person_attack_{mode}_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="person_attack_spy build_kernel")
    start_tick = kernel.state.tick
    spy: Optional[PersonAttackSpy] = None
    if mode == "spy":
        from src.engine.apply import ApplyPath
        from src.observability.run_ledger import RunLedger

        spy = PersonAttackSpy(TreeReads.from_tree(), RunLedger, first_tick=start_tick, control=control, control_tick=control_tick if control_tick is not None else (start_tick + ticks if control else None),
                              mode_getter=lambda: getattr(ObservabilityConfig.get_mode(), "value", str(ObservabilityConfig.get_mode()))).start_ledger().install(ApplyPath)
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        if spy is not None:
            spy.restore()
        final_state = kernel.state
        kernel.shutdown()
    doc: Dict[str, Any] = {
        "world": world, "seed": seed, "ticks": ticks, "start_tick": start_tick, "mode": mode, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
        "final_hash": CanonicalStateHasher.get_hash(final_state), "final_tick": final_state.tick, "final_world_time": final_state.world_time, "logging_errors": errors.rows,
    }
    code, message = 0, ""
    if spy is not None:
        spy.finish(final_state)
        doc.update(spy.report())
        code, message = exit_status(doc)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
