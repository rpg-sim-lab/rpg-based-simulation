"""[trace_lodge: trace_pair2 plus the F3 watch fields: lodged_in, is_lodged, last_attacker_id/last_hit_tick, the hazard on the tile, and who targets the watched entity this tick]
Read-only per-tick trace (scratch; wraps ApplyPath.apply_generation only). Usage: TR_OUT=<jsonl> WATCH=<comma ids> python trace_pair2.py <world> <seed> <ticks> <hash_until>
Every tick: new deaths (typed cause, hazard kind, last attacker, position), live groups [leader, holder, contract, members], and for each WATCH entity a detail row (position, hp, group, shared target,
contract, task, nav target, project, objective). Up to hash_until: per-entity per-key canonical hashes (first state diff). Tick 1 also writes a static row per watch entity (kind, role, faction, class).
cwd = tree, PYTHONPATH = tree."""
import hashlib, json, os, sys
sys.path.insert(0, ".")
from src.engine.apply import ApplyPath
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
        w({"k": "static", "ents": {eid: static(prior.entities[eid]) for eid in sorted(WATCH) if eid in prior.entities}})
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
    for eid in WATCH:
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
                    "targeted_by": sorted(oid for oid, oe in new.entities.items() if oid != eid and oe.combat.alive and oe.task.payload.get("target_id") == eid)[:8]}
    if T0 <= t <= T1 or ents is not None:
        w({"k": "tick", "t": t, "ent": ents, "groups": groups if T0 <= t <= T1 else {}, "det": det if T0 <= t <= T1 else {}})
    return new
ApplyPath.apply_generation = staticmethod(ag)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=True)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
w({"k": "fin", "hash": m["state_hash"], "elapsed": elapsed}); out.close(); print("TRACE_OK", m["state_hash"][:12])
