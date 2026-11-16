"""Group-hit and felt-lethal-hold spy (TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER, measurement cell, rpg-designer #634 6883569761). READ-ONLY.

Run with the tree under test as cwd and on PYTHONPATH (base tree and fix tree alike), same build and tick loop as arm_child.py (tools.test_architecture.rpg_gate_run.build_kernel).
Two wrappers, each calls the real function with its own arguments and returns the real result unchanged; nothing writes to state:
  CombatResolutionSystem.resolve_multi_attack: records every call with 2 or more valid attackers (tick, subject, attackers in order, each intent's damage share).
  MovementSystem.resolve_move: a "held step" is a returned update for the subject whose navigation.failure_reason is FELT_LETHAL_FREE_SWING (by value, so a tree without it counts 0).
After each tick, for each two-attacker hit within 12 ticks, the subject's hp, engaged hostiles, the felt swing under the OLD rule (last_hit_damage if last_attacker_id is engaged and alive)
and under the NEW rule (sum of the shares of last_hit_attackers that are engaged and alive; null in a tree without the fields), and whether the subject was held that tick.
  python group_hit_spy.py <world> <seed> <ticks> <out.json> [<plain_cell.json>]
With <plain_cell.json> (the plain twin's result holding "final_hash") the end hash is compared; a mismatch exits 3 and the file must not be used.
Output: meta, final_hash, final_hash_v4_form (fix tree only: the v5 state hashed as v4, comparable with a base tree's final_hash), match, hits[], held_ticks_total, held_runs_total, held_total_length, longest_run, held_at_last_tick[], runs_ge_50[{entity, ticks, first_tick, no_hit}], deaths.
A run is "no_hit" when the subject's last_hit_tick did not change between the first and the last held tick of the run.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

WATCH_TICKS = 12


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    cell = argv[4] if len(argv) > 4 else None
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.combat import CombatResolutionSystem
    from src.engine.legality import LegalityServiceV2
    from src.engine.movement import MovementSystem
    from tools.rpg_measure.arm_child import _cause
    from tools.test_architecture.rpg_gate_run import build_kernel

    hits: list = []
    held: dict = {}           # entity id -> [(tick, last_hit_tick)]
    held_now: set = set()     # (tick, subject) pairs held this tick
    real_multi = CombatResolutionSystem.__dict__["resolve_multi_attack"].__func__
    real_move = MovementSystem.__dict__["resolve_move"].__func__

    def multi(attackers, defender, state, *a, **kw):
        res = real_multi(attackers, defender, state, *a, **kw)
        try:
            intents = list(res.simultaneous_intents or [])
            if len(intents) >= 2:
                hits.append({"tick": int(state.tick), "subject": defender.id, "hp_before": defender.combat.hp, "attackers": [i.attacker_id for i in intents],
                             "shares": [i.damage for i in intents], "outcome": res.outcome_kind, "watch": []})
        except Exception:  # logging only
            pass
        return res

    def move(state, entity, target, *a, **kw):
        res = real_move(state, entity, target, *a, **kw)
        try:
            upd = res.get(entity.id) if isinstance(res, dict) else res
            reason = getattr(getattr(upd, "navigation", None), "failure_reason", None)
            if reason is not None and getattr(reason, "value", reason) == "FELT_LETHAL_FREE_SWING":
                tick = int(getattr(state, "tick", -1))
                held.setdefault(entity.id, []).append((tick, entity.combat.last_hit_tick))
                held_now.add((tick, entity.id))
        except Exception:  # logging only
            pass
        return res

    CombatResolutionSystem.resolve_multi_attack = staticmethod(multi)
    MovementSystem.resolve_move = staticmethod(move)
    run_id = f"rpggh_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced")
        return 2
    try:
        for _ in range(ticks):
            kernel.tick_once()
            state = kernel.state
            t = int(state.tick)
            for h in hits:
                if h["tick"] <= t <= h["tick"] + WATCH_TICKS:
                    e = state.entities.get(h["subject"])
                    if e is None:
                        continue
                    c = e.combat
                    engaged = set(LegalityServiceV2.get_engaged_hostiles(e, state)) if c.alive else set()

                    def alive(i):
                        o = state.entities.get(i)
                        return o is not None and o.combat.alive

                    old = c.last_hit_damage if (c.last_attacker_id in engaged and alive(c.last_attacker_id)) else 0
                    atts = getattr(c, "last_hit_attackers", None)
                    new = None if atts is None else sum(s for a, s in zip(atts, c.last_hit_damages) if a in engaged and alive(a))
                    h["watch"].append({"tick": t, "hp": c.hp, "alive": c.alive, "engaged": sorted(engaged), "last_hit_tick": c.last_hit_tick, "old_swing": old, "new_swing": new,
                                       "old_lethal": bool(old and old >= c.hp), "new_lethal": None if new is None else bool(new and new >= c.hp), "held": any(x[1] == h["subject"] and x[0] in (t, t - 1) for x in held_now)})
    finally:
        CombatResolutionSystem.resolve_multi_attack = staticmethod(real_multi)
        MovementSystem.resolve_move = staticmethod(real_move)
    state = kernel.state
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    v4_form_hash = None
    if any(hasattr(e.combat, "last_hit_attackers") for e in state.entities.values()):
        # the fix tree's digest is flat-sha256-v5; the v4 form (the two new combat keys removed) is the hash a v4 tree computes, so base and fix are comparable
        import hashlib
        data = CanonicalStateHasher.to_canonical_data(state)
        for ent in data["entities"].values():
            ent["combat"] = {k: v for k, v in ent["combat"].items() if k not in ("last_hit_attackers", "last_hit_damages")}
        v4_form_hash = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"] if cell else None
    ok = None if want is None else final_hash == want

    def runs(rows):
        ts = sorted({r[0] for r in rows})
        by_tick = {r[0]: r[1] for r in rows}
        res, start, prev = [], None, None
        for t in ts:
            if prev is not None and t == prev + 1:
                prev = t
                continue
            if prev is not None:
                res.append((start, prev))
            start = prev = t
        if prev is not None:
            res.append((start, prev))
        return [(a, b, by_tick[a] == by_tick[b]) for a, b in res]

    all_runs, ge50, longest = [], [], {"entity": None, "ticks": 0, "first_tick": None}
    for eid, rows in held.items():
        for a, b, no_hit in runs(rows):
            n = b - a + 1
            all_runs.append((eid, a, n))
            if n > longest["ticks"]:
                longest = {"entity": eid, "ticks": n, "first_tick": a}
            if n >= 50:
                ge50.append({"entity": eid, "ticks": n, "first_tick": a, "no_hit": no_hit})
    last_tick = int(state.tick)
    at_last = sorted(eid for eid, rows in held.items() if any(r[0] >= last_tick - 1 for r in rows))
    deaths = {}
    for e in state.entities.values():
        if not e.combat.alive:
            rec = getattr(e.lifecycle, "death_record", None)
            deaths[str(e.id)] = [None if rec is None else rec.tick, _cause(e), e.kind]
    res = {"meta": {"world": world, "seed": seed, "ticks": ticks, "cwd": os.getcwd()}, "final_hash": final_hash, "final_hash_v4_form": v4_form_hash, "cell_final_hash": want, "match": ok, "hits": hits,
           "held_ticks_total": sum(len({r[0] for r in v}) for v in held.values()), "held_runs_total": len(all_runs), "held_total_length": sum(n for _, _, n in all_runs), "longest_run": longest,
           "held_at_last_tick": at_last, "runs_ge_50": ge50, "held_by_entity": {str(k): sorted({r[0] for r in v}) for k, v in held.items()}, "deaths": deaths, "deaths_total": len(deaths)}
    Path(out).write_text(json.dumps(res, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    print(("MATCH " if ok else ("NOCELL " if ok is None else "MISMATCH ")) + final_hash[:12] + f" hits2={len(hits)} held_ticks={res['held_ticks_total']} runs={res['held_runs_total']} longest={longest['ticks']} ge50={len(ge50)} deaths={len(deaths)}")
    return 3 if ok is False else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
