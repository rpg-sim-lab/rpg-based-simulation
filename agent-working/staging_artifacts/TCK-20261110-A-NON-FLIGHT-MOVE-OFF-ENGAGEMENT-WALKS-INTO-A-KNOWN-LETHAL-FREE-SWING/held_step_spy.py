"""Held-step spy (TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING, design section Measurement). READ-ONLY: DRAFT for rpg-designer approval; NOT run, NOT smoked.

Run with the tree under test as cwd and on PYTHONPATH, same build and tick loop as arm_child_flight.py / free_swing_trace.py (tools.test_architecture.rpg_gate_run.build_kernel; audit_mode and
no_frame_pacing are checked). One spy: MovementSystem.resolve_move is wrapped; it calls the real function with its own arguments and returns the real result unchanged; nothing writes to state.
A "held step" is a returned update for the subject whose navigation.failure_reason is the typed ReasonCode FELT_LETHAL_FREE_SWING (compared by value, so a tree without the code counts 0).
  python held_step_spy.py <world> <seed> <ticks> <out.json> [<plain_cell.json>]
When <plain_cell.json> (the plain, un-spied cell's result with "final_hash") is given, the run's end hash is compared with it; a mismatch exits 3 and the file must not be used.
Output JSON: {meta, final_hash, cell_final_hash, match, held_total, held_by_entity{id: [ticks]}, longest_run{entity, ticks, first_tick}, runs_ge_50[{entity, ticks, first_tick}],
death{id: [tick, cause]} for every person that died (cause as arm_child_flight's _cause), held_rows[first 40: tick, subject, hp, last_attacker_id, last_hit_damage, felt_attacker_engaged]}.
PIN STOP (the design's): any entity held for 50 or more consecutive ticks: rows to rpg-designer before any ruling. This script only reports it (runs_ge_50).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    cell = argv[4] if len(argv) > 4 else None
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.movement import MovementSystem
    from tools.rpg_measure.arm_child import _cause
    from tools.test_architecture.rpg_gate_run import build_kernel

    held: dict = {}
    rows: list = []
    real = MovementSystem.__dict__["resolve_move"]
    fn = real.__func__

    def spy(state, entity, target, *a, **kw):
        res = fn(state, entity, target, *a, **kw)
        try:
            upd = res.get(entity.id) if isinstance(res, dict) else res
            nav = getattr(upd, "navigation", None)
            reason = getattr(nav, "failure_reason", None)
            if reason is not None and getattr(reason, "value", reason) == "FELT_LETHAL_FREE_SWING":
                tick = int(getattr(state, "tick", -1))
                held.setdefault(entity.id, []).append(tick)
                if len(rows) < 40:
                    c = entity.combat
                    rows.append({"tick": tick, "subject": entity.id, "hp": c.hp, "last_attacker_id": c.last_attacker_id, "last_hit_damage": getattr(c, "last_hit_damage", None)})
        except Exception:  # logging only
            pass
        return res

    MovementSystem.resolve_move = staticmethod(spy)
    run_id = f"rpgheld_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced")
        return 2
    try:
        for _ in range(ticks):
            kernel.tick_once()
        state = kernel.state
    finally:
        MovementSystem.resolve_move = real
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"] if cell else None
    ok = None if want is None else final_hash == want

    def runs(ts):
        best, cur_start, prev, length = (0, None), None, None, 0
        out_runs = []
        for t in ts:
            if prev is not None and t == prev + 1:
                length += 1
            else:
                if prev is not None:
                    out_runs.append((length, cur_start))
                cur_start, length = t, 1
            prev = t
        if prev is not None:
            out_runs.append((length, cur_start))
        return out_runs

    longest = {"entity": None, "ticks": 0, "first_tick": None}
    ge50 = []
    for eid, ts in held.items():
        for length, start in runs(sorted(ts)):
            if length > longest["ticks"]:
                longest = {"entity": eid, "ticks": length, "first_tick": start}
            if length >= 50:
                ge50.append({"entity": eid, "ticks": length, "first_tick": start})
    deaths = {}
    for e in state.entities.values():
        if not e.combat.alive:
            rec = getattr(e.lifecycle, "death_record", None)
            deaths[str(e.id)] = [None if rec is None else rec.tick, _cause(e)]
    res = {"meta": {"world": world, "seed": seed, "ticks": ticks, "cwd": os.getcwd()}, "final_hash": final_hash, "cell_final_hash": want, "match": ok,
           "held_total": sum(len(v) for v in held.values()), "held_by_entity": {str(k): sorted(v) for k, v in held.items()}, "longest_run": longest, "runs_ge_50": ge50,
           "death": deaths, "held_rows": rows}
    Path(out).write_text(json.dumps(res, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    print(("MATCH " if ok else ("NOCELL " if ok is None else "MISMATCH ")) + final_hash[:12] + (f" vs cell {want[:12]}" if want else "") + f" held_total={res['held_total']} longest={longest['ticks']}")
    return 3 if ok is False else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
