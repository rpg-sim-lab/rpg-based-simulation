"""Read-only per-tick trace for the crowded_frontier s42 pair (scratch; wraps ApplyPath.apply_generation only). Usage: TR_OUT=<jsonl> python trace_pair.py <world> <seed> <ticks> <detail_until>
Per tick <= detail_until: per entity a hash of each top-level key of its canonical dict (field-level first-diff), the live groups, and for the watch entities a detail row (position, hp, group, task, nav target, project).
Every tick: new deaths (typed cause). Final: run hash. cwd = tree, PYTHONPATH = tree."""
import hashlib, json, os, sys
sys.path.insert(0, ".")
from src.engine.apply import ApplyPath
WATCH = {3, 5, 11, 32, 25, 14, 36, 16, 1, 8, 4, 31, 23, 10, 19, 33}
world, seed, ticks, until = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
out = open(os.environ["TR_OUT"], "w")
def w(r): out.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
def h(o): return hashlib.md5(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()[:8]
_oa = ApplyPath.apply_generation
def ag(prior, update, *a, **k):
    new = _oa(prior, update, *a, **k)
    t = new.tick
    for eid, ne in new.entities.items():
        dr = ne.lifecycle.death_record
        if dr is not None and (prior.entities.get(eid) is None or prior.entities[eid].lifecycle.death_record is None):
            w({"k": "death", "t": t, "e": eid, "cause": dr.cause.value, "hazard": dr.hazard_kind, "att": dr.last_attacker_id, "pos": list(ne.navigation.position), "hp": ne.combat.hp})
    if t <= until:
        ents = {}
        for eid, ne in new.entities.items():
            cd = ne.to_canonical_dict()
            ents[eid] = {key: h(v) for key, v in cd.items()}
        groups = {}
        for gid, g in new.groups.items():
            if g.dissolution_tick is None:
                groups[gid] = [g.leader_id, getattr(g, "contract_holder_id", None), g.contract_id, sorted(g.member_ids), g.last_leadership_check_tick]
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
                if cc is not None: c = [g.contract_id, str(getattr(cc.status, "value", cc.status)), cc.expiry_tick, getattr(cc, "created_tick", None)]
            det[eid] = {"pos": [round(x, 2) for x in ne.navigation.position], "hp": ne.combat.hp, "alive": ne.combat.alive, "gid": gid,
                        "grp": None if g is None else [g.leader_id, getattr(g, "contract_holder_id", None), g.contract_id, g.shared_target_id, sorted(g.member_ids)],
                        "contract": c, "work": ne.task.work_kind, "payload": {kk: str(vv)[:40] for kk, vv in list(ne.task.payload.items())[:4]},
                        "nav": None if ne.navigation.target is None else str(ne.navigation.target)[:40],
                        "proj": None if proj is None else [str(getattr(proj, "kind", ""))[:30], str(getattr(proj, "status", ""))[:20], str(getattr(proj, "target_id", None)), str(getattr(proj, "target_position", None))[:30]],
                        "obj": st.current_objective_id}
        w({"k": "tick", "t": t, "ent": ents, "groups": groups, "det": det})
    return new
ApplyPath.apply_generation = staticmethod(ag)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=True)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
w({"k": "fin", "hash": m["state_hash"], "elapsed": elapsed}); out.close(); print("TRACE_OK", m["state_hash"][:12])
