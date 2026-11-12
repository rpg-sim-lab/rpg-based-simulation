"""WINDOWED COPY of free_swing_trace.py (approved 7c22df89…), DRAFT for rpg-designer approval, NOT run. Changes vs 7c22df89, all read-only logging: (1) a subject spec may be "id:lo-hi" (every tick lo..hi); "id:t" still means t-3..t. (2) the attack-call row is recorded for EVERY outermost attack call where a subject is an attacker or the defender, under key "attacks" (was "opp_calls": OA only), with the defender id and the is_opportunity_attack flag as passed. (3) the resolve_move row also carries the result navigation.failure_reason (a held step shows FELT_LETHAL_FREE_SWING). Output keys per subject spec "id:lo-hi". Nothing else changed.

Non-flight free-swing trace (TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING, Scope 1). READ-ONLY: DRAFT for rpg-designer approval; NOT run, NOT smoked.

Run with the EVIDENCE sha's tree as cwd and on PYTHONPATH (detached worktree), same build and tick loop as defeat_trace2.py / arm_child_flight.py (tools.test_architecture.rpg_gate_run.build_kernel;
audit_mode and no_frame_pacing are checked). The end hash must equal <cell.json>'s final_hash (exit 3 otherwise: the trace then does not count).
  python free_swing_trace.py <world> <seed> <ticks> <cell.json> <subjects "id:t,id:t,..."> <out.json>
Every spy calls the real function with its own arguments and returns the real result unchanged; nothing writes to state. Raw inputs only: no class, no verdict.

Per subject S and death tick t, for each tick u in t-3..t (u = state.tick while tick_once runs; "start" = before it, "end" = after it):
  1. task: work_kind and payload at start of u (payload as stored, repr-safe).
  2. navigation.target at start and end of u; plus the LAST STAGED WRITE to it as of the end of u: the tick and the creating call stack (6 caller frames, file:function:line) of the last NavigationUpdate with
     target_set / target_clear / clear_target that was bound to an EntityUpdate for S (binding = first EntityUpdate built holding that navigation object). Staged means built, not necessarily applied: the applied value is
     the start/end target of the following tick.
  3. position at start and end of u; EVERY EntityUpdate built for S on u with new_position set (position change staged): new_position and the creating call stack; every MovementSystem.resolve_move call for S on u
     (target, mode, result new_position, caller stack); every MovementPhase._swap_updates that involves S; every positioning.get_bracketing_position call with S as the entity (ally, target, result, caller stack).
  4. engagement at start of u: LegalityServiceV2.get_engaged_hostiles(S) (read-only helper) and, separately, every alive entity at Manhattan distance 1 (ids only).
  5. decision: whether TacticalDecisionSystem.evaluate_entity_intent ran for S on u and on u-1, with its output (work_kind, action, reason, target_id, navigation.target_set).
  6. group: identity.group_id and, when state.groups holds it, that record's member ids; the bracketing/group-staged moves are the calls in item 3 and the resolve_move callers.
  7. opportunity-attack call on u: every outermost CombatResolutionSystem.resolve_attack / resolve_multi_attack / resolve_aoe_attack / resolve_skill_usage call with defender S and is_opportunity_attack=True:
     attackers, result damage_taken / hp_delta / outcome_kind, the subject's hp BEFORE the call (live state hp: the tick-start snapshot), is_lethal as passed, and the caller stack.
Output JSON: {meta, final_hash, cell_final_hash, match, subjects{"id:t": {ticks{u: {...}}}}}. A mismatch exits 3 and the file is written but must not be used.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import traceback
from pathlib import Path

WINDOW = 3
STACK_DEPTH = 6


def _stack(skip: int = 2) -> list:
    """Caller frames, innermost first, as 'path:function:line' (repo-relative), skipping this module's own frames and dataclass-generated ones."""
    out = []
    for fs in reversed(traceback.extract_stack()[:-skip]):
        if fs.filename.endswith("free_swing_trace.py") or fs.filename.startswith("<"):
            continue
        name = fs.filename
        cut = name.find("/src/")
        if cut >= 0:
            name = name[cut + 1:]
        out.append(f"{name}:{fs.name}:{fs.lineno}")
        if len(out) >= STACK_DEPTH:
            break
    return out


def _safe(v):
    try:
        json.dumps(v)
        return v
    except Exception:
        return repr(v)


def main(argv):
    world, seed, ticks, cell, subj_arg, out = argv[0], int(argv[1]), int(argv[2]), argv[3], argv[4], argv[5]
    pairs = []
    for p in subj_arg.split(","):
        sid, rng = p.split(":")
        lo, hi = (int(x) for x in rng.split("-")) if "-" in rng else (int(rng) - WINDOW, int(rng))
        pairs.append((int(sid), lo, hi))
    subjects = {s for s, _, _ in pairs}
    want_ticks = {u for _, lo, hi in pairs for u in range(lo, hi + 1)}

    from src.core.updates import EntityUpdate, NavigationUpdate
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.combat import CombatResolutionSystem as CRS
    from src.engine.legality import LegalityServiceV2
    from src.engine.movement import MovementSystem
    from src.engine.pipeline_phases.movement import MovementPhase
    from src.engine.tactical import TacticalDecisionSystem
    from tools.test_architecture.rpg_gate_run import build_kernel

    cur = [0]
    rec: dict = {}  # tick -> subject -> dict of lists

    def at(u: int, s: int) -> dict:
        return rec.setdefault(u, {}).setdefault(s, {"staged_position": [], "resolve_move": [], "swaps": [], "bracketing": [], "decisions": [], "attacks": []})

    # --- navigation target writes: NavigationUpdate origin, bound to an entity by the first EntityUpdate that holds it
    nav_origin: dict = {}   # id(nav) -> (nav, tick, stack, fields)
    last_nav_write: dict = {}  # subject -> {tick, stack, target_set, target_clear, clear_target}
    ni = NavigationUpdate.__init__

    def nav_init(self, *a, **kw):
        ni(self, *a, **kw)
        if kw.get("target_set") is not None or kw.get("target_clear") or kw.get("clear_target"):
            nav_origin[id(self)] = (self, cur[0], _stack(), {"target_set": _safe(kw.get("target_set")), "target_clear": bool(kw.get("target_clear")), "clear_target": bool(kw.get("clear_target"))})
    NavigationUpdate.__init__ = nav_init

    ei = EntityUpdate.__init__

    def ent_init(self, *a, **kw):
        ei(self, *a, **kw)
        try:
            eid = kw.get("entity_id", a[0] if a else None)
            if eid in subjects:
                nav = kw.get("navigation")
                if nav is not None and id(nav) in nav_origin:
                    _n, tk, stack, fields = nav_origin.pop(id(nav))
                    last_nav_write[eid] = {"tick": tk, "stack": stack, **fields}
                if kw.get("new_position") is not None and cur[0] in want_ticks:
                    at(cur[0], eid)["staged_position"].append({"new_position": _safe(list(kw["new_position"])), "stack": _stack()})
        except Exception as ex:  # logging only
            last_nav_write.setdefault("log_error", repr(ex))
    EntityUpdate.__init__ = ent_init

    # --- resolve_move / swap / bracketing
    rm_orig = MovementSystem.__dict__["resolve_move"]
    rm_fn = rm_orig.__func__

    def rm_spy(state, entity, target, *a, **kw):
        res = rm_fn(state, entity, target, *a, **kw)
        try:
            if entity.id in subjects and cur[0] in want_ticks:
                eu = res.get(entity.id) if isinstance(res, dict) else res
                at(cur[0], entity.id)["resolve_move"].append({"target": _safe(list(target) if target is not None else None), "mode": _safe(str(kw.get("mode"))),
                                                              "result_new_position": _safe(list(eu.new_position)) if eu is not None and getattr(eu, "new_position", None) else None,
                                                              "result_failure_reason": _safe(str(getattr(getattr(eu, "navigation", None), "failure_reason", None))), "stack": _stack()})
        except Exception as ex:
            at(cur[0], entity.id)["resolve_move"].append({"log_error": repr(ex)})
        return res
    MovementSystem.resolve_move = staticmethod(rm_spy)

    sw_orig = MovementPhase.__dict__["_swap_updates"]
    sw_fn = sw_orig.__func__

    def sw_spy(state, a, b, a_existing, b_existing):
        try:
            for who, other in ((a, b), (b, a)):
                if who.id in subjects and cur[0] in want_ticks:
                    at(cur[0], who.id)["swaps"].append({"with": other.id, "stack": _stack()})
        except Exception as ex:
            pass
        return sw_fn(state, a, b, a_existing, b_existing)
    MovementPhase._swap_updates = staticmethod(sw_spy)

    from src.engine import positioning
    pos_cls = [c for c in vars(positioning).values() if isinstance(c, type) and "get_bracketing_position" in c.__dict__][0]
    br_orig = pos_cls.__dict__["get_bracketing_position"]
    br_fn = br_orig.__func__

    def br_spy(entity, ally, target):
        res = br_fn(entity, ally, target)
        try:
            if entity.id in subjects and cur[0] in want_ticks:
                at(cur[0], entity.id)["bracketing"].append({"ally": ally.id, "target": target.id, "result": _safe(list(res)), "stack": _stack()})
        except Exception:
            pass
        return res
    pos_cls.get_bracketing_position = staticmethod(br_spy)

    # --- decisions
    od = TacticalDecisionSystem.evaluate_entity_intent

    def dspy(st, entity, *a, **kw):
        res = od(st, entity, *a, **kw)
        try:
            if entity.id in subjects and cur[0] in want_ticks | {u - 1 for u in want_ticks}:
                tk = getattr(res, "task", None)
                pl = (getattr(tk, "payload_set", None) or {}) if tk is not None else {}
                nav = getattr(res, "navigation", None)
                at(cur[0], entity.id)["decisions"].append({"work_kind": None if tk is None else _safe(str(tk.work_kind_set)), "action": _safe(pl.get("action")), "reason": _safe(pl.get("reason")),
                                                           "target_id": _safe(pl.get("target_id")), "nav_target_set": _safe(list(nav.target_set)) if nav is not None and nav.target_set is not None else None})
        except Exception as ex:
            at(cur[0], entity.id)["decisions"].append({"log_error": repr(ex)})
        return res
    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(dspy)

    # --- attack calls (outermost only); OA rows keep the defender's hp from the tick-start snapshot
    depth = [0]
    origs = {}
    hp_start: dict = {}

    def wrap(name):
        o = CRS.__dict__[name]
        fn = o.__func__
        origs[name] = o

        def spy(*a, **kw):
            outer = depth[0] == 0
            depth[0] += 1
            try:
                res = fn(*a, **kw)
            finally:
                depth[0] -= 1
            if outer:
                try:
                    att = a[0]
                    dfn = a[1] if len(a) > 1 else kw.get("defender")
                    atts = [x.id for x in att] if isinstance(att, (list, tuple, set)) else [att.id]
                    did = getattr(dfn, "id", None)
                    involved = [x for x in subjects if x in atts or x == did]
                    if involved and cur[0] in want_ticks:
                        row = {"fn": name, "attackers": atts, "defender": did, "is_opportunity_attack": bool(kw.get("is_opportunity_attack", False)), "is_lethal_arg": _safe(kw.get("is_lethal", True)),
                               "defender_hp_tick_start": hp_start.get(did), "result_damage_taken": _safe(getattr(res, "damage_taken", None)), "result_hp_delta": _safe(getattr(res, "hp_delta", None)),
                               "result_outcome_kind": _safe(str(getattr(res, "outcome_kind", None))), "stack": _stack()}
                        for x in involved:
                            at(cur[0], x)["attacks"].append(row)
                except Exception as ex:
                    pass
            return res
        setattr(CRS, name, staticmethod(spy))
    for n in ("resolve_attack", "resolve_multi_attack", "resolve_aoe_attack", "resolve_skill_usage"):
        if n in CRS.__dict__:
            wrap(n)

    run_id = f"rpgfst_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced")
        return 2
    try:
        for _ in range(ticks):
            st = kernel.state
            u = st.tick
            cur[0] = u
            if len(nav_origin) > 5000:
                nav_origin.clear()
            if u in want_ticks:
                for s in subjects:
                    e = st.entities.get(s)
                    if e is None:
                        continue
                    hp_start[s] = e.combat.hp
                    pos = e.navigation.position
                    adj = [o.id for o in st.entities.values() if o.id != s and o.combat.alive and abs(o.navigation.position[0] - pos[0]) + abs(o.navigation.position[1] - pos[1]) == 1]
                    try:
                        engaged = list(LegalityServiceV2.get_engaged_hostiles(e, st))
                    except Exception as ex:
                        engaged = f"log_error {ex!r}"
                    gid = e.identity.group_id
                    grp = st.groups.get(gid) if gid is not None else None
                    members = None
                    if grp is not None:
                        m = getattr(grp, "members", None) or getattr(grp, "member_ids", None)
                        members = _safe(sorted(m)) if m is not None else repr(grp)[:200]
                    p = e.task.payload or {}
                    d = at(u, s)
                    d["start"] = {"hp": e.combat.hp, "alive": bool(e.combat.alive), "position": list(pos), "nav_target": _safe(list(e.navigation.target) if e.navigation.target is not None else None),
                                  "task_work_kind": _safe(str(e.task.work_kind)), "task_payload": _safe({k: _safe(v) for k, v in p.items()}),
                                  "engaged_hostiles": _safe(engaged), "adjacent_alive_ids": adj, "group_id": gid, "group_members": members,
                                  "last_nav_write_staged_before_u": _safe(last_nav_write.get(s))}
            kernel.tick_once()
            if u in want_ticks:
                st2 = kernel.state
                for s in subjects:
                    e = st2.entities.get(s)
                    if e is None or u not in rec or s not in rec[u]:
                        continue
                    rec[u][s]["end"] = {"hp": e.combat.hp, "alive": bool(e.combat.alive), "position": list(e.navigation.position),
                                        "nav_target": _safe(list(e.navigation.target) if e.navigation.target is not None else None),
                                        "last_nav_write_staged_through_u": _safe(last_nav_write.get(s))}
        state = kernel.state
    finally:
        for n, o in origs.items():
            setattr(CRS, n, o)
        TacticalDecisionSystem.evaluate_entity_intent = od
        MovementSystem.resolve_move = rm_orig
        MovementPhase._swap_updates = sw_orig
        pos_cls.get_bracketing_position = br_orig
        NavigationUpdate.__init__ = ni
        EntityUpdate.__init__ = ei
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"]
    ok = final_hash == want
    res = {"meta": {"world": world, "seed": seed, "ticks": ticks, "cwd": os.getcwd(), "window": WINDOW, "pairs": pairs, "note": "windowed copy of 7c22df89"}, "final_hash": final_hash, "cell_final_hash": want, "match": ok,
           "subjects": {f"{s}:{lo}-{hi}": {str(u): rec.get(u, {}).get(s) for u in range(lo, hi + 1)} for s, lo, hi in pairs}}
    Path(out).write_text(json.dumps(res, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    print(("MATCH " if ok else "MISMATCH ") + final_hash[:12] + " vs cell " + want[:12])
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
