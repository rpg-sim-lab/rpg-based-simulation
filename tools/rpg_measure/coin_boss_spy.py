"""Coin and world-boss counter for the births re-check (rpg-designer u24, approved in principle; relayed by lead-planner, rpg-planner-ubuntu relay record section 40).

One additive kit file. It wraps ``ApplyPath.apply_generation`` like ``s9_spy.GroupSpy`` does: it READS the (prior, update, new state) of every applied tick and returns the new state untouched, so the run's
final hash must equal the plain twin's (the re-check proves it). Nothing here writes simulation state; the positive-control mode observes COPIES of the last state and never hands one back to the kernel.

Per tick it records:
- COIN: ``src.core.treasury.total_coin`` of the new state (entity purses alive or dead + building purses + corpse gold + ground gold + treasuries: the partition RunLedger uses, not re-derived here),
  the delta against the previous tick, and a COIN-MOVING tick flag: some entity purse changed that tick (the non-vacuous guard counts these; total coin itself is conserved, so it cannot be the guard).
- V6 = coin_last - coin_first - declared. The "declared" amount comes from RunLedger. STUB: the source is not ruled yet (RunLedger.observe is silent under recording OFF, event_recorder.py:426-427; the
  options are with rpg-designer). Until it is ruled ``DECLARED_SOURCE`` is None, V6 reads None, and ``net_delta_before_declared`` (coin_last - coin_first) is reported instead. Every tick whose delta is not
  zero is kept as a row (tick, delta, declared that tick = None while stubbed) so the unexplained-delta count can be formed once the source exists.
- WORLD BOSSES: two columns side by side, per tick, BOTH STUBS until rpg-designer rules what each is (rpg-planner-ubuntu, relayed finding: at 6e7d76ef2 spawn writes species "world_boss" and occupation
  "ancient_sentinel", boss.py:151-152, so the old predicate at boss.py:83-87 never sees a boss; after #964 (1c5b0f074) the predicate reads ``species_of == "world_boss"``, the same field as a state count, so the two
  would not be independent). ``BOSS_STATE_COUNT`` and ``BOSS_PY_PREDICATE`` are None; ``state_boss_count`` below is a CANDIDATE helper (living entities whose species is ``world_boss``), not wired in.
  A disagreement between the two columns is a FINDING row; while either is a stub none can be formed. Expected 0 / 0; any non-zero count is reported as a finding once wired.
- POSITIVE CONTROL (built, NOT run until a GO): ``--control coin:N`` adds N to one entity purse in a COPY of the last observed state; ``--control boss:K`` re-kinds K living entities to ``world_boss`` in a COPY.
  The control output is kept apart from the real output; a coin control must read ``net_delta_before_declared == real net delta + N`` and a boss control must read K in the state column (None while the columns are stubs; the candidate helper's count is printed beside it).
- GUARDS: root-handler ``logging_errors`` (every ERROR+ record becomes a row), the PINNED manifest check (same as births_child), and the non-vacuous guard: the cell FAILS (exit 4) when it saw 0 coin-moving ticks.

Heavy-job hygiene: the file name carries ``_spy`` so the shared busy gate (``lib/busy_gate.sh`` RPG_HEAVY_WORDS) sees it; put the command in a script file and never put kit words on a launcher's command line.
Usage: python coin_boss_spy.py <world> <seed> <ticks> <out.json> [--control coin:N | boss:K]
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.core.species import species_of
from src.core.treasury import total_coin
from src.engine.apply import ApplyPath

WORLD_BOSS_SPECIES = "world_boss"
# STUB (not ruled): the source of the gold the world declares into existence. A callable (prior, update, new_state) -> float, or None. RunLedger.observe is not called under recording OFF.
DECLARED_SOURCE: Optional[Callable[[Any, Any, Any], float]] = None
# STUB (not ruled): boss.py's own predicate as a callable (entity) -> bool, or None. boss.py:83-87 defines it as a nested function; #964 (1c5b0f074) changed it to read species_of == "world_boss".
BOSS_PY_PREDICATE: Optional[Callable[[Any], bool]] = None
# STUB (not ruled): the "independent count from state" as a callable (state) -> int, or None. ``state_boss_count`` is the candidate; whether it is independent of the predicate after #964 is rpg-designer's call.
BOSS_STATE_COUNT: Optional[Callable[[Any], int]] = None
EXIT_VACUOUS = 4


def entity_purse_moved(prior: Any, state: Any) -> bool:
    """True when some entity purse (a body in both states) changed between the two states: coin MOVED this tick (it may net out to nothing in the world total)."""
    before = prior.entities
    return any(before[eid].inventory.gold != body.inventory.gold for eid, body in state.entities.items() if eid in before)


def state_boss_count(state: Any) -> int:
    """CANDIDATE (not wired in while ``BOSS_STATE_COUNT`` is a stub): living entities whose species is ``world_boss``."""
    return sum(1 for body in state.entities.values() if species_of(body) == WORLD_BOSS_SPECIES and body.combat.alive)


def predicate_boss_count(state: Any, predicate: Optional[Callable[[Any], bool]]) -> Optional[int]:
    """boss.py's own predicate applied to every entity; None while the predicate is a stub."""
    if predicate is None:
        return None
    return sum(1 for body in state.entities.values() if predicate(body))


def with_coin(state: Any, amount: float) -> Any:
    """A COPY of ``state`` in which the lowest-id entity holds ``amount`` more coin (positive control only; the kernel never sees it)."""
    eid = min(state.entities)
    body = state.entities[eid]
    moved = dataclasses.replace(body, inventory=dataclasses.replace(body.inventory, gold=body.inventory.gold + amount))
    return dataclasses.replace(state, entities={**state.entities, eid: moved})


def with_bosses(state: Any, count: int) -> Any:
    """A COPY of ``state`` in which ``count`` living entities are re-kinded ``world_boss`` (positive control only)."""
    living = [eid for eid in sorted(state.entities) if state.entities[eid].combat.alive][:count]
    entities = dict(state.entities)
    for eid in living:
        entities[eid] = dataclasses.replace(entities[eid], kind=WORLD_BOSS_SPECIES)
    return dataclasses.replace(state, entities=entities)


class LoggingErrors(logging.Handler):
    """Root handler: every ERROR+ record of the run becomes a row (a clean run has none)."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.rows: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.rows.append({"logger": record.name, "level": record.levelname, "message": record.getMessage()[:300]})


class CoinBossSpy:
    """Record-only wrapper over the apply path; ``install()`` patches, ``restore()`` undoes."""

    def __init__(self, start_state: Any) -> None:
        self.coin_first: float = total_coin(start_state)
        self.coin_last: float = self.coin_first
        self.declared_total: Optional[float] = 0.0 if DECLARED_SOURCE is not None else None
        self.coin_moving_ticks = 0
        self.ticks = 0
        self.delta_rows: List[Dict[str, Any]] = []  # every tick whose world total changed: tick, delta, declared that tick (None while stubbed)
        self.boss_rows: List[Dict[str, Any]] = []  # every tick on which either boss column is non-zero
        self.boss_state_max: Optional[int] = None
        self.boss_predicate_max: Optional[int] = None
        self.boss_ticks_over_one = 0
        self.disagreements: List[Dict[str, Any]] = []
        self.last_state: Any = start_state
        self._previous_coin = self.coin_first
        self._patched: List[tuple] = []

    def install(self) -> "CoinBossSpy":
        original = ApplyPath.__dict__["apply_generation"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original(prior_state, update, *args, **kwargs)
            spy.observe(prior_state, update, new_state)
            return new_state

        self._patched.append((ApplyPath, "apply_generation", original))
        ApplyPath.apply_generation = staticmethod(apply_generation)
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    def observe(self, prior: Any, update: Any, state: Any) -> None:
        self.ticks += 1
        self.last_state = state
        now = total_coin(state)
        delta = now - self._previous_coin
        declared_tick = DECLARED_SOURCE(prior, update, state) if DECLARED_SOURCE is not None else None
        if declared_tick is not None and self.declared_total is not None:
            self.declared_total += declared_tick
        if entity_purse_moved(prior, state):
            self.coin_moving_ticks += 1
        if delta != 0:
            self.delta_rows.append({"tick": state.tick, "delta": delta, "declared": declared_tick})
        self._previous_coin, self.coin_last = now, now
        by_state = BOSS_STATE_COUNT(state) if BOSS_STATE_COUNT is not None else None
        by_predicate = predicate_boss_count(state, BOSS_PY_PREDICATE)
        if by_state is not None:
            self.boss_state_max = max(self.boss_state_max or 0, by_state)
            self.boss_ticks_over_one += int(by_state > 1)
        if by_predicate is not None:
            self.boss_predicate_max = max(self.boss_predicate_max or 0, by_predicate)
        if by_state or by_predicate:
            self.boss_rows.append({"tick": state.tick, "state": by_state, "predicate": by_predicate})
        if by_state is not None and by_predicate is not None and by_predicate != by_state:
            self.disagreements.append({"tick": state.tick, "state": by_state, "predicate": by_predicate})

    def report(self) -> Dict[str, Any]:
        net = self.coin_last - self.coin_first
        declared = self.declared_total
        return {
            "coin_first": self.coin_first, "coin_last": self.coin_last, "net_delta_before_declared": net, "declared": declared,
            "declared_source": "STUB" if DECLARED_SOURCE is None else getattr(DECLARED_SOURCE, "__name__", "set"),
            "v6": (net - declared) if declared is not None else None, "unexplained_delta_rows": self.delta_rows[:200], "delta_rows_total": len(self.delta_rows),
            "coin_moving_ticks": self.coin_moving_ticks, "ticks": self.ticks, "non_vacuous": self.coin_moving_ticks > 0,
            "boss_state_max": self.boss_state_max, "boss_state_source": "STUB" if BOSS_STATE_COUNT is None else getattr(BOSS_STATE_COUNT, "__name__", "set"),
            "boss_predicate_max": self.boss_predicate_max,
            "boss_predicate_source": "STUB" if BOSS_PY_PREDICATE is None else getattr(BOSS_PY_PREDICATE, "__name__", "set"),
            "boss_ticks_over_one": self.boss_ticks_over_one, "boss_rows": self.boss_rows[:200], "boss_disagreements": self.disagreements[:200],
        }

    def control_report(self, spec: str) -> Dict[str, Any]:
        """The positive control on a COPY of the last observed state: ``coin:N`` reads the net delta plus N, ``boss:K`` reads K in the state column."""
        kind, _, amount = spec.partition(":")
        if kind == "coin":
            n = float(amount)
            injected = total_coin(with_coin(self.last_state, n))
            return {"control": spec, "net_delta_before_declared": injected - self.coin_first, "expected": (self.coin_last - self.coin_first) + n}
        if kind == "boss":
            k = int(amount)
            copy = with_bosses(self.last_state, k)
            by_state = BOSS_STATE_COUNT(copy) if BOSS_STATE_COUNT is not None else None
            return {"control": spec, "state": by_state, "predicate": predicate_boss_count(copy, BOSS_PY_PREDICATE),
                    "expected": (BOSS_STATE_COUNT(self.last_state) + k) if BOSS_STATE_COUNT is not None else None, "candidate_state_count": state_boss_count(copy)}
        raise ValueError(f"unknown control {spec!r}: use coin:N or boss:K")


def main(argv: List[str]) -> int:
    from tools.rpg_measure import arm_child
    from tools.rpg_measure.births_child import inject_no_replay_if_recording_off
    from tools.test_architecture.rpg_gate_run import build_kernel

    control = argv[argv.index("--control") + 1] if "--control" in argv else None
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    errors = LoggingErrors()
    logging.getLogger().addHandler(errors)
    inject_no_replay_if_recording_off()
    pinned_runner = arm_child._pinned_runner()
    run_id = f"coin_boss_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None), "no_replay": getattr(kernel, "_no_replay", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this tree's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {"run_conditions": arm_child._derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="coin_boss_spy build_kernel")
    spy = CoinBossSpy(kernel.state).install()
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        spy.restore()
        final_state = kernel.state
        kernel.shutdown()
    from src.engine.checkpoint import CanonicalStateHasher

    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
        "final_hash": CanonicalStateHasher.get_hash(final_state), **spy.report(), "logging_errors": errors.rows,
    }
    if control is not None:
        doc["control"] = spy.control_report(control)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    if not doc["non_vacuous"]:
        print("VACUOUS: 0 coin-moving ticks in this cell", file=sys.stderr)
        return EXIT_VACUOUS
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
