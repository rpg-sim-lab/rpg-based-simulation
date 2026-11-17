"""[trace_lodge: trace_pair2 plus the F3 watch fields: lodged_in, is_lodged, last_attacker_id/last_hit_tick, the hazard on the tile, and who targets the watched entity this tick]
Read-only per-tick trace (scratch; wraps ApplyPath.apply_generation only). Usage: TR_OUT=<jsonl> WATCH=<comma ids> python trace_pair2.py <world> <seed> <ticks> <hash_until>
Every tick: new deaths (typed cause, hazard kind, last attacker, position), live groups [leader, holder, contract, members], and for each WATCH entity a detail row (position, hp, group, shared target,
contract, task, nav target, project, objective). Up to hash_until: per-entity per-key canonical hashes (first state diff). Tick 1 also writes a static row per watch entity (kind, role, faction, class).
cwd = tree, PYTHONPATH = tree."""
import hashlib, json, os, sys
sys.path.insert(0, ".")
from src.engine.apply import ApplyPath
from src.engine.tactical import TacticalDecisionSystem
TENT = set()
WINS = []  # (t0, t1, victim id): env WINS="a-b:e;c-d:f"
for _p in os.environ.get("WINS", "").split(";"):
    if _p:
        _r, _v = _p.split(":"); _a, _b = _r.split("-"); WINS.append((int(_a), int(_b), int(_v)))
def active(t):
    return {v for a, b, v in WINS if a <= t <= b}
_TAC = TacticalDecisionSystem.evaluate_entity_intent
_CODE = getattr(_TAC, "__code__", None) or getattr(getattr(_TAC, "__func__", None), "__code__", None)
_src_lines = open("src/engine/tactical.py").read().splitlines()
def _ln(text):
    return next((i + 1 for i, l in enumerate(_src_lines) if text in l), None)
MARK = {"4.1_if_group_and_not_hostiles": _ln("if group and not hostiles:"), "4.1_role_read": _ln("role = group.roles.get(entity.id)"), "4.1_guard_pos": _ln("guard_pos = PositioningService.find_guard_position(entity, leader, None, state)"),
        "4.2_if_group": _ln("# 4.2 Cohesion Check") + 1, "4.2_dist_check": _ln("if dist_sq > group.cohesion_radius**2:"), "4_target_selection_group_line": _ln("# 4. Target Selection with Focus Fire") + 1, "5.2_bracket_if": _ln('if role == "VANGUARD" and group:'), "5.2_bracket_pos": _ln("bracket_pos = PositioningService.get_bracketing_position"), "5.3_vanguard_if_second": 766, "sort": _ln("hostiles.sort(key=target_score)"), "target_pick": _ln("target = legal_attack_targets[0] if legal_attack_targets else hostiles[0]")}

import src.engine.lodging as _LG
LEAVES = []; CLAIMS = []
_orig_il = _LG._is_leaving
def _il(state, entity, upd):
    r = _orig_il(state, entity, upd)
    if r and entity.id in active(state.tick):
        task = upd.task if upd is not None else None
        wk = task.work_kind_set if task is not None and task.work_kind_set is not None else entity.task.work_kind
        pl = task.payload_set if task is not None and task.payload_set is not None else entity.task.payload
        LEAVES.append({"k": "leave", "t": state.tick, "e": entity.id, "work": wk, "reason": (pl or {}).get("reason"), "action": (pl or {}).get("action"), "obj": entity.strategic.current_objective_id})
    return r
_LG._is_leaving = _il
_orig_sb = _LG._settle_building
def _sb(state, building_id, claimants, refined, drops):
    r = _orig_sb(state, building_id, claimants, refined, drops)
    if any(c in active(state.tick) for c in claimants):
        b = state.buildings.get(building_id)
        CLAIMS.append({"k": "claim", "t": state.tick, "bld": building_id, "beds": getattr(b, "beds", None), "held": len(_LG.lodgers_of(state, building_id)), "claimants": list(claimants),
                       "granted": [c for c in claimants if refined.get(c) is not None and refined[c].navigation is not None and refined[c].navigation.lodged_in_set is not None]})
    return r
_LG._settle_building = _sb
TACROWS = []
NEARW = int(os.environ.get("NEAR", "0"))  # entity id whose Euclid radius-10 neighbours are traced too (the killer is unknown in advance)
CT0, CT1 = [int(x) for x in os.environ.get("CTRLWIN", "0,-1").split(",")]
CTRL = {"calls": 0, "marks": {k: 0 for k in MARK}, "grouped_no_hostile_calls": 0}
CALLS = {}
def _gt(frame, event, arg):
    if event != "call" or frame.f_code is not _CODE: return None
    ent = frame.f_locals.get("entity"); st = frame.f_locals.get("state")
    if ent is None or st is None: return None
    near = False
    act = active(st.tick)
    for v in act:
        w0 = st.entities.get(v)
        if w0 is not None and ((ent.navigation.position[0] - w0.navigation.position[0]) ** 2 + (ent.navigation.position[1] - w0.navigation.position[1]) ** 2) <= 100:
            near = True
    if act and (ent.id in act or near):
        CALLS[(st.tick, ent.id)] = CALLS.get((st.tick, ent.id), 0) + 1
        rec = {"k": "tac", "t": st.tick, "e": ent.id, "near": bool(near and ent.id not in act), "lines": set(), "pos": list(ent.navigation.position)}
    elif CT0 <= st.tick <= CT1:
        crec = {"lines": set()}
        def _clt(fr, ev, ar):
            if ev == "line": crec["lines"].add(fr.f_lineno)
            elif ev == "return":
                CTRL["calls"] += 1
                for k, v in MARK.items():
                    if v in crec["lines"]: CTRL["marks"][k] += 1
                if MARK["4.1_role_read"] in crec["lines"] or MARK["4.2_dist_check"] in crec["lines"]: CTRL["grouped_no_hostile_calls"] += 1
            return _clt
        return _clt
    else:
        return None
    def _lt(fr, ev, ar):
        if ev == "line": rec["lines"].add(fr.f_lineno)
        elif ev == "return":
            L = fr.f_locals; rec["ret_line"] = fr.f_lineno
            try:
                rec["ret_reason"] = None if ar is None else (ar.task.payload_set or {}).get("reason") if ar.task is not None else None
                rec["ret_work"] = None if ar is None or ar.task is None else ar.task.work_kind_set
            except Exception as ex: rec["ret_err"] = repr(ex)[:80]
            hs = L.get("hostiles"); ts = L.get("target_score"); g = L.get("group"); tg = L.get("target")
            rec["group"] = None if g is None else [g.id, g.leader_id, g.shared_target_id, g.roles.get(ent.id), sorted(g.member_ids)]
            rec["hostiles"] = None if hs is None else [h.id for h in hs]
            rec["target"] = None if tg is None else tg.id
            rec["scores"] = None
            if hs is not None and ts is not None:
                try: rec["scores"] = {h.id: [round(x, 3) if isinstance(x, float) else x for x in ts(h)] for h in hs}
                except Exception as ex: rec["scores_err"] = repr(ex)[:80]
            rec["lines"] = sorted(rec["lines"]); rec["marks_hit"] = {k: (v in rec["lines"]) for k, v in MARK.items()}
            TACROWS.append(rec)
        return _lt
    return _lt
import threading
threading.settrace(_gt)
sys.settrace(_gt)
from src.core.lodging_rules import is_lodged
T0, T1 = [int(x) for x in os.environ.get('TWIN', '0,10**9').split(',')] if os.environ.get('TWIN') else (0, 10**9)
world, seed, ticks, until = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
WATCH = {int(x) for x in os.environ.get("WATCH", "").split(",") if x}
out = open(os.environ["TR_OUT"], "w")
def w(r): out.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
def h(o): return hashlib.md5(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()[:8]
_oa = ApplyPath.apply_generation
def static(e):
    i = e.identity
    return {"kind": str(getattr(e, "kind", None)), "role": str(getattr(i, "role", None)), "faction": str(getattr(i, "faction", None)), "class_id": str(getattr(i, "class_id", None)), "name": str(getattr(i, "name", None)), "pos0": list(e.navigation.position)}
def ag(prior, update, *a, **k):
    if prior.tick <= 1:
        w({"k": "static", "ents": {eid: static(prior.entities[eid]) for eid in sorted({v for _, _, v in WINS}) if eid in prior.entities}})
    new = _oa(prior, update, *a, **k)
    t = new.tick
    for eid, ne in new.entities.items():
        dr = ne.lifecycle.death_record
        if dr is not None and (prior.entities.get(eid) is None or prior.entities[eid].lifecycle.death_record is None):
            w({"k": "death", "t": t, "e": eid, "cause": dr.cause.value, "hazard": dr.hazard_kind, "att": dr.last_attacker_id, "pos": list(ne.navigation.position), "hp": ne.combat.hp})
    ents = None
    if t <= until:
        ents = {eid: {key: h(v) for key, v in ne.to_canonical_dict().items()} for eid, ne in new.entities.items()}
    groups = {gid: [g.leader_id, getattr(g, "contract_holder_id", None), g.contract_id, sorted(g.member_ids)] for gid, g in new.groups.items() if g.dissolution_tick is None}
    det = {}
    for eid in active(t):
        ne = new.entities.get(eid)
        if ne is None: continue
        st = ne.strategic; proj = st.projects.get(st.current_project_id) if st.current_project_id else None
        gid = ne.identity.group_id; g = new.groups.get(gid) if gid is not None and gid >= 0 else None
        c = None
        if g is not None and g.contract_id:
            hold = new.entities.get(getattr(g, "contract_holder_id", None) if getattr(g, "contract_holder_id", None) is not None else g.leader_id)
            cc = hold.strategic.contracts.get(g.contract_id) if hold else None
            if cc is not None: c = [g.contract_id, str(getattr(cc.status, "value", cc.status)), cc.expiry_tick]
        p = ne.task.payload
        det[eid] = {"pos": [round(x, 2) for x in ne.navigation.position], "hp": ne.combat.hp, "alive": ne.combat.alive, "gid": gid,
                    "grp": None if g is None else [g.leader_id, getattr(g, "contract_holder_id", None), g.contract_id, g.shared_target_id, sorted(g.member_ids), g.dissolution_tick],
                    "contract": c, "work": ne.task.work_kind, "reason": p.get("reason"), "target_id": p.get("target_id"), "tpos": str(p.get("target_position"))[:30],
                    "nav": None if ne.navigation.target is None else str(ne.navigation.target)[:30],
                    "proj": None if proj is None else [str(getattr(proj, "kind", ""))[:24], str(getattr(proj, "status", ""))[:12]], "obj": st.current_objective_id,
                    "lodged_in": getattr(ne.navigation, "lodged_in", None), "is_lodged": bool(is_lodged(ne)), "last_att": ne.combat.last_attacker_id, "last_hit_t": ne.combat.last_hit_tick,
                    "dist30": None if 30 not in new.entities else abs(ne.navigation.position[0] - new.entities[30].navigation.position[0]) + abs(ne.navigation.position[1] - new.entities[30].navigation.position[1]), "trust": (None if g is None else (lambda b, th, lid: {"leader": lid, "bond_sentiment": None if b is None else b.sentiment, "trust_history": th.get(lid), "from": "bonds" if b is not None else ("trust_history" if lid in th else "default_0.5"),
            "trust_value": ((b.sentiment + 1.0) / 2.0) if b is not None else th.get(lid, 0.5), "tactical_role": ne.combat.tactical_role, "shared_target": g.shared_target_id,
            "bias_formula": (lambda tv: (1.0 if tv < 0.2 else (1.0 - tv) * (0.5 if ne.combat.tactical_role == "VANGUARD" else 1.0)))(((b.sentiment + 1.0) / 2.0) if b is not None else th.get(lid, 0.5))})(ne.social.bonds.get(g.leader_id), ne.social.trust_history, g.leader_id)), "near10": sorted(oid for oid, oe in new.entities.items() if oid != eid and oe.combat.alive and (oe.navigation.position[0] - ne.navigation.position[0]) ** 2 + (oe.navigation.position[1] - ne.navigation.position[1]) ** 2 <= 100)[:12], "targeted_by": sorted(oid for oid, oe in new.entities.items() if oid != eid and oe.combat.alive and oe.task.payload.get("target_id") == eid)[:8]}
    if active(t) or ents is not None:
        w({"k": "tick", "t": t, "ent": ents, "groups": groups if active(t) else {}, "det": det if active(t) else {}})
    return new
ApplyPath.apply_generation = staticmethod(ag)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=True)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
[w(r) for r in TACROWS + LEAVES + CLAIMS]; w({"k": "mark", "marks": MARK, "code_found": _CODE is not None, "control": CTRL, "calls": {f"{k[0]}:{k[1]}": v for k, v in CALLS.items()}})
w({"k": "fin", "hash": m["state_hash"], "elapsed": elapsed}); out.close(); print("TRACE_OK", m["state_hash"][:12])

