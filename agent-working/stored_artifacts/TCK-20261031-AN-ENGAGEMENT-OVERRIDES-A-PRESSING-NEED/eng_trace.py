"""Phase 2 trace of the urban s44 victims (read-only; wrappers only record, never change a result). Works on both arm trees (imports only what both have).

Usage (cwd = arm tree root, PYTHONPATH=.): eng_trace.py world seed ticks out.json id1,id2,...

Per tick it records the state hash (to find the first divergence between the arms) and a decision tuple per entity (to find which entity decides differently first).
For the listed victims it records, every tick they are alive: position, hp, hunger, sleep debt, the task action/reason/target after the tick, the project kind, and the ENG
branch view: whether hostiles were in sight at the tactical decision, whether the need was pressing, whether a hostile was acting on the subject, whether an adjacent hostile was
present, and what the tactical decision returned (EAT / REST / walk to a target / other). Deaths: tick, cause, killer id and the killer's task.
"""
import collections, json, os, shutil, sys
from pathlib import Path

world, seed, ticks, out, victims = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], {int(x) for x in sys.argv[5].split(",")}
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing
from src.engine.tactical_threat import hostile_acts_on
import src.engine.tactical as _tac
from tools.test_architecture.rpg_gate_run import build_kernel

TACT = {}                # (tick, eid) -> tactical view recorded at the decision
_cur = [0]
_hood = {}
_orig_cls = _tac.classify_neighbours


def _cls(entity, neighbors, src, *a, **kw):
    hood = _orig_cls(entity, neighbors, src, *a, **kw)
    _hood[entity.id] = len(hood.hostiles)
    return hood


_tac.classify_neighbours = _cls
_orig_eval = _tac.TacticalDecisionSystem.evaluate_entity_intent


def _eval(state, entity, *a, **kw):
    _hood.pop(entity.id, None)
    r = _orig_eval(state, entity, *a, **kw)
    n = _hood.get(entity.id)
    if n and entity.id in victims:
        hs = perceived_hostiles(entity, state)
        pr = need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt)
        adj = any(abs(h.navigation.position[0] - entity.navigation.position[0]) + abs(h.navigation.position[1] - entity.navigation.position[1]) <= 1 for h in hs)
        acting = any(hostile_acts_on(h, entity, state.tick) for h in hs)
        p = (r.task.payload_set if r.task is not None else None) or {}
        TACT[(_cur[0], entity.id)] = {"hostiles_in_sight": n, "pressing": pr, "adjacent": adj, "acting": acting,
                                      "ret_action": p.get("action"), "ret_reason": p.get("reason"), "ret_target": p.get("target_id"),
                                      "ret_nav": list(r.navigation.target_set) if (r.navigation is not None and r.navigation.target_set is not None) else None,
                                      "ret_strat_suspends": bool(r.strategic is not None and getattr(r.strategic, "projects_add_or_update", None))}
    return r


_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

rid = f"trace_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
hashes, decisions, rows, deaths = [], [], collections.defaultdict(list), {}
prev_dec = {}
for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    hashes.append(CanonicalStateHasher.get_hash(st)[:16])
    dec = {}
    for eid, e in st.entities.items():
        if not e.combat.alive:
            continue
        pl = e.task.payload or {}
        d = (pl.get("action"), pl.get("reason"), pl.get("target_id"), tuple(e.navigation.target) if e.navigation.target is not None else None)
        dec[eid] = d
    decisions.append(dec)
    for eid in victims:
        e = st.entities.get(eid)
        if e is None:
            continue
        if not e.combat.alive:
            if eid not in deaths:
                kid = e.combat.last_attacker_id
                ke = st.entities.get(kid) if kid is not None else None
                kt = (ke.task.payload or {}) if ke is not None else {}
                dr = getattr(e.lifecycle, "death_record", None)
                deaths[eid] = {"tick": t, "cause": str(getattr(getattr(dr, "cause", None), "value", getattr(e.lifecycle, "death_reason", None))), "killer": kid,
                               "killer_kind": getattr(ke, "kind", None), "killer_task": [kt.get("action"), kt.get("reason"), kt.get("target_id")], "killer_pos": list(ke.navigation.position) if ke is not None else None,
                               "pos": list(e.navigation.position), "last_hit_tick": e.combat.last_hit_tick}
            continue
        pl = e.task.payload or {}
        cp = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
        row = {"t": t, "pos": [round(e.navigation.position[0], 1), round(e.navigation.position[1], 1)], "hp": e.combat.hp, "hunger": round(e.biological.hunger, 1),
               "debt": round(e.biological.sleep_debt, 1), "action": pl.get("action"), "reason": pl.get("reason"), "target": pl.get("target_id"),
               "proj": str(getattr(cp.kind, "value", cp.kind)) if cp is not None else None, "last_attacker": e.combat.last_attacker_id, "last_hit": e.combat.last_hit_tick}
        tv = TACT.get((t - 1, eid)) or TACT.get((t, eid))
        if tv:
            row["tact"] = tv
        rows[eid].append(row)
doc = {"world": world, "seed": seed, "ticks": ticks, "final_hash": CanonicalStateHasher.get_hash(k.state), "hashes": hashes,
       "decisions_sample_len": len(decisions), "deaths": deaths, "rows": {str(a): b for a, b in rows.items()}}
# per-tick decision map is large: keep only the decision tuples as a compact list of dicts of changed entities vs the previous tick
changed = []
for i, dec in enumerate(decisions):
    prev = decisions[i - 1] if i else {}
    changed.append({str(e): list(d) for e, d in dec.items() if prev.get(e) != d})
doc["decision_changes"] = changed
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
