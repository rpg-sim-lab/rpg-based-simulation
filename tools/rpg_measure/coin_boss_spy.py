"""Coin and world-boss counter for the births re-check (rpg-designer u24 rulings Q1 and Q2, rpg-planner-ubuntu relay record section 41).

One additive kit file, for the SPIED arm only (plain, control and the main-tree cost arm never import it). It wraps ``ApplyPath.apply_generation`` like ``s9_spy.GroupSpy`` does: it READS the
(prior, update, new state) of every applied tick and returns the new state untouched, so the run's final hash must equal the plain twin's (the re-check proves it). Nothing here writes simulation
state; the positive-control mode hands COPIES of the last state to the observers and never gives one back to the kernel.

COIN (Q1 = A). The kernel does not call ``RunLedger.observe`` under recording OFF (event_recorder.py:426-427), so this spy, in its OWN process only, calls ``RunLedger.reset_run_state()`` and
``RunLedger.configure(True)`` ONCE at run start (``start_ledger``, called after the kernel is built because the kernel's own ``reset_run_state`` runs at construction, kernel.py:301) and then calls the REAL
``RunLedger.observe(prior, current, update)`` for every applied update, with exactly the objects the apply path used, after the application. The returned events are DISCARDED: they never reach a recorder
or the run's output. V6 = ledger coin_last - coin_first - declared, read from the ledger at the end (``finish`` snapshots the counters and resets the ledger so a control run cannot pollute a real one).
It refuses to start unless the observability mode is OFF (with recording on, the kernel would feed the same class-level counters a second time).
CROSS-CHECK, cell-invalidating: the spy's own ``src.core.treasury.total_coin`` at the first and last tick must equal the ledger's coin_first and coin_last; a mismatch marks the cell
``WIRING_MISMATCH`` (exit 5) and the cell does not count. The non-vacuous guard counts COIN-MOVING ticks (some entity purse changed that tick); the cell FAILS (exit 4) at 0.

WORLD BOSSES (Q2, report only, expected 0 / 0 / 0). Three columns per tick:
1. ``predicate_post_964``: a VERBATIM copy of the post-#964 predicate, 1c5b0f074 boss.py:84-89 (``BossService.check_for_boss_spawn._is_active_living_boss``, still a nested function there, so it cannot be
   imported): ``species_of(entity) == "world_boss" and entity.lifecycle.active and entity.combat.alive``. ``species_of`` is imported from its real module. Re-check at the resync: if the final head exposes a
   named check, import it and cite it instead.
2. ``raw_kind_alive``: a raw scan of ``state.entities``: ``kind == "world_boss" and combat.alive``, ignoring lifecycle.
3. ``occupation_alive``: ``identity.occupation == "ancient_sentinel" and combat.alive``; the only column that does not read ``kind``.
Disagreement rows (tick, the three counts, the ids) and the max of each column. Record line, word for word: ``RECORD_LINE`` below.

POSITIVE CONTROL (built, NOT run until a GO; its own run only, never counted): ``--control coin:N`` has the spy observe a COPY of the LAST state with N more coin in one purse, for both the spy's own total and
the real ledger, so the LEDGER's V6 reads N more than the same run without it; ``--control boss:K`` observes a COPY with K living, active ``world_boss`` bodies (occupation ``ancient_sentinel``), which every column must read as K.
GUARDS: a root-handler ``logging_errors`` (every ERROR+ record becomes a row), the PINNED manifest check (as births_child), audit_mode and no_frame_pacing forced.

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
from typing import Any, Dict, List, Optional

from src.core.species import species_of
from src.core.treasury import total_coin
from src.engine.apply import ApplyPath
from src.observability.run_ledger import RunLedger

WORLD_BOSS_SPECIES = "world_boss"
BOSS_OCCUPATION = "ancient_sentinel"
RECORD_LINE = "the columns differ only on lifecycle.active; both read entity.kind, so not independent of the species field"
EXIT_VACUOUS = 4
EXIT_WIRING_MISMATCH = 5
COLUMNS = ("predicate_post_964", "raw_kind_alive", "occupation_alive")


def predicate_post_964(entity: Any) -> bool:
    """VERBATIM copy of 1c5b0f074 src/world/boss.py:84-89 (``_is_active_living_boss``, nested in ``BossService.check_for_boss_spawn``)."""
    return (
        species_of(entity) == "world_boss"
        and entity.lifecycle.active
        and entity.combat.alive
    )


def raw_kind_alive(entity: Any) -> bool:
    """Column 2: ``kind == "world_boss"`` and alive, ignoring lifecycle."""
    return entity.kind == WORLD_BOSS_SPECIES and entity.combat.alive


def occupation_alive(entity: Any) -> bool:
    """Column 3: ``identity.occupation == "ancient_sentinel"`` and alive; the only column that does not read kind."""
    return entity.identity.occupation == BOSS_OCCUPATION and entity.combat.alive


_COLUMN_FUNCTIONS = {"predicate_post_964": predicate_post_964, "raw_kind_alive": raw_kind_alive, "occupation_alive": occupation_alive}


def boss_ids(state: Any) -> Dict[str, List[int]]:
    """The ids each column counts in ``state``."""
    return {name: sorted(eid for eid, body in state.entities.items() if fn(body)) for name, fn in _COLUMN_FUNCTIONS.items()}


def entity_purse_moved(prior: Any, state: Any) -> bool:
    """True when some entity purse (a body in both states) changed between the two states: coin MOVED this tick (it may net out to nothing in the world total)."""
    before = prior.entities
    return any(before[eid].inventory.gold != body.inventory.gold for eid, body in state.entities.items() if eid in before)


def with_coin(state: Any, amount: float) -> Any:
    """A COPY of ``state`` in which the lowest-id entity holds ``amount`` more coin (positive control only; the kernel never sees it)."""
    eid = min(state.entities)
    body = state.entities[eid]
    moved = dataclasses.replace(body, inventory=dataclasses.replace(body.inventory, gold=body.inventory.gold + amount))
    return dataclasses.replace(state, entities={**state.entities, eid: moved})


def with_bosses(state: Any, count: int) -> Any:
    """A COPY of ``state`` in which ``count`` living entities are world bosses in every column: kind ``world_boss``, occupation ``ancient_sentinel``, lifecycle active (positive control only)."""
    living = [eid for eid in sorted(state.entities) if state.entities[eid].combat.alive][:count]
    entities = dict(state.entities)
    for eid in living:
        body = entities[eid]
        entities[eid] = dataclasses.replace(
            body, kind=WORLD_BOSS_SPECIES, identity=dataclasses.replace(body.identity, occupation=BOSS_OCCUPATION), lifecycle=dataclasses.replace(body.lifecycle, active=True))
    return dataclasses.replace(state, entities=entities)


def parse_control(spec: Optional[str]) -> Optional[tuple]:
    """``coin:N`` -> ("coin", float N); ``boss:K`` -> ("boss", int K); None -> None."""
    if spec is None:
        return None
    kind, _, amount = spec.partition(":")
    if kind == "coin":
        return ("coin", float(amount))
    if kind == "boss":
        return ("boss", int(amount))
    raise ValueError(f"unknown control {spec!r}: use coin:N or boss:K")


class LoggingErrors(logging.Handler):
    """Root handler: every ERROR+ record of the run becomes a row (a clean run has none)."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.rows: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.rows.append({"logger": record.name, "level": record.levelname, "message": record.getMessage()[:300]})


class CoinBossSpy:
    """Record-only wrapper over the apply path; ``install()`` patches, ``restore()`` undoes. ``ledger`` is the RunLedger class (injectable for unit tests)."""

    def __init__(self, start_state: Any, ledger: Any = RunLedger, control: Optional[tuple] = None, last_tick: Optional[int] = None) -> None:
        self.ledger = ledger
        self.control = control  # ("coin", N) | ("boss", K): applied to a COPY of the state at ``last_tick`` for every observer; the kernel never sees it
        self.last_tick = last_tick
        self.coin_first: float = total_coin(start_state)
        self.coin_last: float = self.coin_first
        self.coin_moving_ticks = 0
        self.ticks = 0
        self.delta_rows: List[Dict[str, Any]] = []  # every tick whose world total changed: tick, delta
        self.boss_rows: List[Dict[str, Any]] = []  # every tick on which any column is non-zero: counts and ids
        self.boss_max: Dict[str, int] = {name: 0 for name in COLUMNS}
        self.disagreements: List[Dict[str, Any]] = []
        self.ledger_snapshot: Optional[Dict[str, float]] = None
        self._previous_coin = self.coin_first
        self._patched: List[tuple] = []

    def start_ledger(self) -> "CoinBossSpy":
        """Reset and switch on the ledger ONCE, in this process only (call after the kernel is built: the kernel's own reset runs at construction)."""
        self.ledger.reset_run_state()
        self.ledger.configure(True)
        return self

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

    def finish(self) -> None:
        """Snapshot the ledger's counters, then reset it so nothing stays behind in the class-level counters."""
        self.ledger_snapshot = {"coin_first": self.ledger._coin_first, "coin_last": self.ledger._coin_last, "declared": self.ledger._declared_coin}
        self.ledger.reset_run_state()

    def observe(self, prior: Any, update: Any, state: Any) -> None:
        self.ticks += 1
        observed = state
        if self.control is not None and self.last_tick is not None and state.tick == self.last_tick:
            observed = with_coin(state, self.control[1]) if self.control[0] == "coin" else with_bosses(state, self.control[1])
        self.ledger.observe(prior, observed, update)  # the REAL ledger on the kernel's own objects; the returned events are discarded
        now = total_coin(observed)
        delta = now - self._previous_coin
        if entity_purse_moved(prior, observed):
            self.coin_moving_ticks += 1
        if delta != 0:
            self.delta_rows.append({"tick": state.tick, "delta": delta})
        self._previous_coin, self.coin_last = now, now
        ids = boss_ids(observed)
        counts = {name: len(found) for name, found in ids.items()}
        for name in COLUMNS:
            self.boss_max[name] = max(self.boss_max[name], counts[name])
        if any(counts.values()):
            self.boss_rows.append({"tick": state.tick, "counts": counts, "ids": ids})
        if len(set(counts.values())) > 1 or len({tuple(v) for v in ids.values()}) > 1:
            self.disagreements.append({"tick": state.tick, "counts": counts, "ids": ids})

    def report(self) -> Dict[str, Any]:
        ledger = self.ledger_snapshot
        if ledger is None:
            raise RuntimeError("finish() was not called: the ledger counters were not snapshotted")
        net = self.coin_last - self.coin_first
        wiring_ok = ledger["coin_first"] == self.coin_first and ledger["coin_last"] == self.coin_last
        return {
            "coin_first": self.coin_first, "coin_last": self.coin_last, "net_delta": net,
            "ledger_coin_first": ledger["coin_first"], "ledger_coin_last": ledger["coin_last"], "ledger_declared": ledger["declared"],
            "v6": ledger["coin_last"] - ledger["coin_first"] - ledger["declared"], "declared_source": "RunLedger.observe (real, events discarded)",
            "wiring": "OK" if wiring_ok else "WIRING_MISMATCH", "cell_valid": wiring_ok and self.control is None,
            "unexplained_delta_rows": self.delta_rows[:200], "delta_rows_total": len(self.delta_rows),
            "coin_moving_ticks": self.coin_moving_ticks, "ticks": self.ticks, "non_vacuous": self.coin_moving_ticks > 0,
            "boss_max": self.boss_max, "boss_rows": self.boss_rows[:200], "boss_disagreements": self.disagreements[:200], "boss_record_line": RECORD_LINE,
            "control": None if self.control is None else {"kind": self.control[0], "amount": self.control[1], "applied_at_tick": self.last_tick},
        }


def main(argv: List[str]) -> int:
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from tools.rpg_measure import arm_child
    from tools.rpg_measure.births_child import inject_no_replay_if_recording_off
    from tools.test_architecture.rpg_gate_run import build_kernel

    control = parse_control(argv[argv.index("--control") + 1] if "--control" in argv else None)
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    if ObservabilityConfig.get_mode() != ObservabilityMode.OFF:
        raise RuntimeError("coin_boss_spy runs only with observability mode OFF (SIM_OBS_MODE=OFF): with recording on the kernel feeds the same RunLedger counters a second time")
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
    spy = CoinBossSpy(kernel.state, control=control, last_tick=kernel.state.tick + ticks).start_ledger().install()
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        spy.restore()
        spy.finish()
        final_state = kernel.state
        kernel.shutdown()
    from src.engine.checkpoint import CanonicalStateHasher

    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"), "runner": pinned.verdict, "forced_flags": forced,
        "final_hash": CanonicalStateHasher.get_hash(final_state), **spy.report(), "logging_errors": errors.rows, "counts_for_recheck": control is None,
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    if doc["wiring"] != "OK":
        print("WIRING_MISMATCH: the spy's total_coin and the ledger's coin_first/coin_last differ; this cell does not count", file=sys.stderr)
        return EXIT_WIRING_MISMATCH
    if not doc["non_vacuous"]:
        print("VACUOUS: 0 coin-moving ticks in this cell", file=sys.stderr)
        return EXIT_VACUOUS
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
