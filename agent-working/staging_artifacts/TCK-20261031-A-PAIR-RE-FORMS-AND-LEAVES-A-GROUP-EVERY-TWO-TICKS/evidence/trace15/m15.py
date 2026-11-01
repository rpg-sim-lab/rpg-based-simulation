"""Measurement wrapper for the 15 paired runs (scratch, read-only; wrappers only, no src edits). Runs profile_run.py's instrument (NOPROF=1) and layers on top:
formations with their binding contract; every dissolution (from the apply diff, so the defection pass is included) with typed reason and status when the tree has them;
live bound groups whose contract has ended (lag); MEMBERS_BELOW_TWO split by cause with a holder-dropped flag; deaths with typed cause and victim id; ACTIVE recruit
contracts per pair at t500/1000/2000. Usage: PROBE_OUT=<jsonl> M15_OUT=<json> NOPROF=1 python m15.py <world> <seed> <ticks>  (cwd = tree, PYTHONPATH = tree)."""
import os, sys, json
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile_run.py")).read()
_head, _tail = _src.split("world, seed, ticks = sys.argv[1]", 1)
exec(compile(_head, "profile_run_head", "exec"))
from src.systems.world_systems.groups import GroupSystem as _GS
from src.engine.apply import ApplyPath as _AP
import src.core.dirty as _dirty
E = dict(forms=[], dis=[], pending_ended={}, first_ended={}, lag=[], overdue_ticks=0, overdue_not_relevant=0, ended_seen=0, mbt=[], deaths=[], active_pairs={}, full_scan_ticks=0, ticks=0)
_has_binding = hasattr(_GS, "_binding_end")
E["phase_ran"] = []; E["ended_log"] = []; E["formation_pick"] = []
from src.engine.pipeline import AuthoritativeApplyPipeline as _AAP
_orc = _AAP._resolve_contract_expirations
def _rc(state, update, *a, **k):
    E["phase_ran"].append(state.tick)
    return _orc(state, update, *a, **k)
_AAP._resolve_contract_expirations = staticmethod(_rc)
if _has_binding:
    _ogf = _GS._gather_formation
    def _gf(state, id_a, already_forming):
        members, best = _ogf(state, id_a, already_forming)
        if len(members) >= 2:
            ea = state.entities[id_a]
            qual = [c for c in sorted(ea.strategic.contracts) if _GS._formation_partner(state, ea, ea.strategic.contracts[c], already_forming) is not None]
            E["formation_pick"].append([state.tick, id_a, len(qual), qual[0] if qual else None, best])
        return members, best
    _GS._gather_formation = staticmethod(_gf)
_inner_ug = _GS.update_groups
def _ug2(state, *a, **k):
    cu = a[0] if a else k.get("current_update")
    E["ticks"] += 1
    fs = bool(cu is not None and cu.force_full_scan) or getattr(state, "_force_full_scan", False)
    E["full_scan_ticks"] += int(fs)
    if _has_binding:
        rel = _dirty.get_relevant_group_ids(state, cu)
        alive = lambda i: i in state.entities and state.entities[i].combat.alive
        active = lambda i: i in state.entities and state.entities[i].lifecycle.active
        ended = {}
        for gid, g in state.groups.items():
            if g.dissolution_tick is None and g.contract_holder_id is not None:
                e = _GS._binding_end(state, g, cu, alive, active)  # with the same-tick update, so a status write landing on the expiry tick is seen
                if e is not None:
                    ended[gid] = (e[0].value, gid in rel or fs); E["ended_log"].append([state.tick, gid, bool(gid in rel or fs)])
        E["pending_ended"][state.tick] = ended
    r = _inner_ug(state, *a, **k)
    for g in P.CUR["form"]:
        E["forms"].append([state.tick, g.id, sorted(g.member_ids), g.contract_id, getattr(g, "contract_holder_id", None), g.leader_id])
    return r
_GS.update_groups = staticmethod(_ug2)
_inner_ag = _AP.apply_generation
def _classify_mbt(prior, new, old):
    dropped = {}
    for m in sorted(old.member_ids):
        if m == old.leader_id: continue
        pe = prior.entities.get(m); ne = new.entities.get(m)
        dead = ne is None or not ne.combat.alive or not ne.lifecycle.active
        far = False
        pos_e = ne if ne is not None else pe  # the member loop reads the same-tick (post-move) position
        if pos_e is not None:
            dx = pos_e.navigation.position[0] - old.anchor[0]; dy = pos_e.navigation.position[1] - old.anchor[1]
            far = dx * dx + dy * dy > (old.cohesion_radius * 2) ** 2
        dropped[m] = "dead_or_inactive" if dead else ("distance" if far else "other")
    return dropped
def _ag2(prior, update, *a, **k):
    new = _inner_ag(prior, update, *a, **k)
    t = prior.tick
    dissolved_now = {}
    for gid, g in new.groups.items():
        old = prior.groups.get(gid)
        if g.dissolution_tick is not None and old is not None and old.dissolution_tick is None and g.dissolution_tick == t:
            reason = getattr(g, "dissolution_reason", None); status = getattr(g, "dissolution_contract_status", None)
            _ho = prior.entities.get(getattr(old, "contract_holder_id", None) if getattr(old, "contract_holder_id", None) is not None else old.leader_id)
            _hc = _ho.strategic.contracts.get(old.contract_id) if _ho is not None else None
            E["dis"].append([t, gid, sorted(old.member_ids), old.contract_id, reason.value if reason else None, status.value if status else None, old.leader_id, getattr(old, "contract_holder_id", None), None if _hc is None else _hc.expiry_tick])
            dissolved_now[gid] = True
            if reason is not None and reason.value == "MEMBERS_BELOW_TWO":
                d = _classify_mbt(prior, new, old)
                E["mbt"].append([t, gid, old.leader_id, getattr(old, "contract_holder_id", None), d, getattr(old, "contract_holder_id", None) in d])
    if _has_binding:
        for gid, (why, in_rel) in E["pending_ended"].pop(t, {}).items():
            E["ended_seen"] += 1
            E["first_ended"].setdefault(gid, t)
            if gid not in dissolved_now:
                E["overdue_ticks"] += 1
                if not in_rel: E["overdue_not_relevant"] += 1
        for gid in list(E["first_ended"]):
            if gid in dissolved_now:
                E["lag"].append([gid, E["first_ended"].pop(gid), t])
    for eid, ne in new.entities.items():
        dr = ne.lifecycle.death_record
        if dr is not None and (prior.entities.get(eid) is None or prior.entities[eid].lifecycle.death_record is None):
            E["deaths"].append([new.tick, eid, dr.cause.value])
    if new.tick in (500, 1000, 2000):
        seen = {}
        for e in new.entities.values():
            for cid, c in e.strategic.contracts.items(): seen[cid] = c
        import collections
        pairs = collections.Counter((min(c.source_id, c.target_id), max(c.source_id, c.target_id)) for c in seen.values()
                                    if str(getattr(c.status, "value", c.status)) == "ACTIVE" and "recruit" in str(getattr(c.kind, "value", c.kind)).lower())
        E["active_pairs"][str(new.tick)] = [len(pairs), max(pairs.values()) if pairs else 0, sum(pairs.values()), sum(1 for v in pairs.values() if v > 1)]
    return new
_AP.apply_generation = staticmethod(_ag2)
exec(compile("world, seed, ticks = sys.argv[1]" + _tail, "profile_run_tail", "exec"))
E["pending_ended"] = {}
E["state_hash"] = m["state_hash"]; E["elapsed"] = elapsed; E["world"] = world; E["seed"] = seed; E["ticks_run"] = ticks; E["dis_probe"] = X["dis"]; E["dis_other"] = X["dis_other"]
E["first_ended"] = {str(k): v for k, v in E["first_ended"].items()}
with open(os.environ["M15_OUT"], "w") as fh: fh.write(json.dumps(E, default=str, separators=(",", ":")))
print("M15_OK")
