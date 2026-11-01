"""Read-only trace (scratch; wraps GroupSystem.update_groups and ApplyPath.apply_generation, never alters args/results).
Usage: TRACE_OUT=<jsonl> python trace_contract.py <world> <seed> <ticks>  (cwd = a commit tree, PYTHONPATH = that tree).
Entities PAIR=(19,33), window T0..T1. Per tick at update_groups: id(state), state.tick, id(current_update); groups touching the pair; for each member the records
of ids starting cnt_recruit_<a>_<b>_ / cnt_recruit_<b>_<a>_ in state.entities[m].strategic.contracts (status, expiry or 'absent'/list of ids); the pending update's
strategic.contracts_add_or_update / contracts_remove for each member; the REPLICA of the dissolution lookup (which branch would answer: leader_up add_or_update vs leader.strategic.contracts);
the REPLICA of the formation read (entity_a = lowest id of the pair, its own contracts). Outputs of the real call: groups_add rows and dissolution rows for groups holding the pair.
At apply_generation: contract ids of each member before and after (prior vs new), to catch remove/re-add."""
import json, os, sys
sys.path.insert(0, "."); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
A, B = (int(x) for x in os.environ.get("PAIR","19,33").split(",")); T0, T1 = (int(x) for x in os.environ.get("WIN","90,116").split(","))
PFX = (f"cnt_recruit_{A}_{B}_", f"cnt_recruit_{B}_{A}_")
rows = []
def recs(e):
    if e is None: return "no_entity"
    return {k: [str(getattr(c.status, "value", c.status)), c.expiry_tick, c.source_id, c.target_id] for k, c in e.strategic.contracts.items() if k.startswith(PFX)}
def upd_all(cu, m):
    if cu is None or m not in cu.entity_updates: return None
    u = cu.entity_updates[m]; out = {}
    import dataclasses
    for f in dataclasses.fields(u):
        v = getattr(u, f.name)
        if v in (None, (), [], {}, False) or f.name == "entity_id": continue
        if f.name == "strategic":
            sv = {g.name: len(getattr(v, g.name)) if hasattr(getattr(v, g.name), "__len__") else str(getattr(v, g.name)) for g in dataclasses.fields(v) if getattr(v, g.name) not in (None, (), [], {}, False)}
            if sv: out["strategic"] = sv
        else: out[f.name] = str(v)[:80]
    return out
def upd_view(cu, m):
    if cu is None or m not in cu.entity_updates: return None
    s = cu.entity_updates[m].strategic
    if s is None: return None
    return {"add_or_update": [[c.id, str(getattr(c.status, "value", c.status)), c.expiry_tick] for c in s.contracts_add_or_update if c.id.startswith(PFX)],
            "remove": [i for i in s.contracts_remove if i.startswith(PFX)]}
from src.systems.world_systems.groups import GroupSystem
from src.engine.apply import ApplyPath
ou = GroupSystem.update_groups
def ug(state, *a, **k):
    cu = a[0] if a else k.get("current_update")
    t = state.tick
    r = ou(state, *a, **k)
    if T0 <= t <= T1:
        row = {"tick": t, "next_group_id": getattr(state, "next_group_id", None), "groups_taken_ge": sorted(i for i in state.groups if i >= 10000)[-4:], "id_state": id(state), "id_cu": id(cu), "groups": [], "members": {}, "formation_replica": None, "forms": [], "dis": []}
        for gid, g in state.groups.items():
            if A in g.member_ids and B in g.member_ids:
                ld = state.entities.get(g.leader_id)
                lu = upd_view(cu, g.leader_id)
                # replica of groups.py:159-166 lookup
                if g.contract_id:
                    in_up = None
                    if cu and g.leader_id in cu.entity_updates and cu.entity_updates[g.leader_id].strategic:
                        in_up = next((c for c in cu.entity_updates[g.leader_id].strategic.contracts_add_or_update if c.id == g.contract_id), None)
                    in_ld = ld.strategic.contracts.get(g.contract_id) if ld else None
                    branch = "leader_up.contracts_add_or_update" if in_up else ("leader.strategic.contracts" if in_ld else "none(contract absent)")
                    ans = in_up or in_ld
                    rep = {"branch": branch, "status": None if ans is None else str(getattr(ans.status, "value", ans.status)), "expiry": None if ans is None else ans.expiry_tick}
                else: rep = None
                row["groups"].append({"gid": gid, "leader": g.leader_id, "contract_id": g.contract_id, "members": sorted(g.member_ids), "dissolution_tick": g.dissolution_tick, "last_leadership_check_tick": g.last_leadership_check_tick, "last_updated_tick": g.last_updated_tick, "roles": {str(k): v for k, v in g.roles.items()}, "dissolution_read_replica": rep})
        for m in (A, B):
            row["members"][m] = {"contracts_in_state": recs(state.entities.get(m)), "pending_update": upd_view(cu, m), "pending_all_fields": upd_all(cu, m), "blockers": None if state.entities.get(m) is None else len(state.entities[m].strategic.blockers), "group_id": None if m not in state.entities else state.entities[m].identity.group_id}
        ea = state.entities.get(A)
        row["formation_replica"] = {"entity_a": A, "entity_a_contracts": recs(ea), "ungrouped_a": ea is not None and ea.identity.group_id is None, "ungrouped_b": state.entities.get(B) is not None and state.entities[B].identity.group_id is None}
        for g in getattr(r, "groups_add", ()):
            if A in g.member_ids and B in g.member_ids: row["forms"].append([g.id, g.leader_id, g.contract_id, sorted(g.member_ids)])
        for g in r.groups_add_or_update:
            if g.dissolution_tick == t and A in g.member_ids and B in g.member_ids: row["dis"].append([g.id, sorted(g.member_ids)])
        rows.append(row)
    return r
GroupSystem.update_groups = staticmethod(ug)
oa = ApplyPath.apply_generation
def ag(prior, update, *a, **k):
    new = oa(prior, update, *a, **k)
    if T0 <= prior.tick <= T1:
        rows.append({"apply": True, "prior_tick": prior.tick, "new_tick": new.tick, "prior": {m: sorted(recs(prior.entities.get(m))) if isinstance(recs(prior.entities.get(m)), dict) else recs(prior.entities.get(m)) for m in (A, B)},
                     "new": {m: sorted(recs(new.entities.get(m))) if isinstance(recs(new.entities.get(m)), dict) else recs(new.entities.get(m)) for m in (A, B)}})
    return new
ApplyPath.apply_generation = staticmethod(ag)
from src.systems.social_systems.party_lifecycle import PartyLifecycleService as PLS
ocl = PLS.check_leadership
def cl(group, members, tick, *a, **k):
    res = ocl(group, members, tick, *a, **k)
    if T0 <= tick <= T1 and A in group.member_ids and B in group.member_ids:
        rows.append({"election_check": True, "tick": tick, "gid": group.id, "leader_in": group.leader_id, "last_leadership_check_tick": group.last_leadership_check_tick,
                     "sociability": {str(e.id): e.identity.personality.sociability for e in members if e.id in group.member_ids},
                     "leader_out": None if res[0] is None else res[0].leader_id, "event": None if res[1] is None else type(res[1]).__name__})
    return res
PLS.check_leadership = staticmethod(cl)
from src.engine.pipeline_phases.groups import GroupPhase as GP
ogr = GP.resolve
def gr(state, update, *a, **k):
    res = ogr(state, update, *a, **k)
    if T0 <= state.tick <= T1:
        for g in res.groups_add_or_update:
            old = state.groups.get(g.id)
            if old is not None and A in g.member_ids and B in g.member_ids and (old.leader_id != g.leader_id or g.dissolution_tick is not None):
                rows.append({"group_phase_resolve_row": True, "tick": state.tick, "gid": g.id, "leader_before": old.leader_id, "leader_after": g.leader_id, "dissolution_tick": g.dissolution_tick})
    return res
GP.resolve = staticmethod(gr)
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile(world))
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
with open(os.environ["TRACE_OUT"], "w") as fh:
    for r in rows: fh.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
print("TRACE_OK rows", len(rows), "elapsed", elapsed)
