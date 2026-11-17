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
import collections as _col
E["hard_law"] = {}
from src.engine.kernel import Kernel as _K
_orig_hl = _K._run_hard_law_checks
def _hl(self, dirty_set):
    try: return _orig_hl(self, dirty_set)
    finally:
        vs = getattr(self._status, "hard_law_violations", None) or []
        E["hard_law"] = dict(_col.Counter(str(getattr(v, "law_id", v)) for v in vs))
_K._run_hard_law_checks = _hl
# --- cross-lane row (F3 lodgers): prepared, inactive until an entity exposes `lodged_in` (field name read from F3's branch once it is available; set LODGED_FIELD to override) ---
_LODGED = os.environ.get("LODGED_FIELD", "lodged_in")
E["lodged"] = dict(field_found=None, lodger_ticks=0, leaves=[], enters=[], group_decision_lodged=0, group_decision_ticks=0, by_entity_last_lodged={}, by_entity_last_leave={})
_lodged_state = {}
def _lodged_value(e):
    for comp in ("lifecycle", "biological", "identity", "navigation", "strategic", "task", "interaction", "social", "combat"):
        c = getattr(e, comp, None)
        if c is not None and hasattr(c, _LODGED): return getattr(c, _LODGED)
    return getattr(e, _LODGED, None) if hasattr(e, _LODGED) else None
def _lodged_probe(state):
    """Called once per tick on the post-apply state."""
    L = E["lodged"]
    for eid, e in state.entities.items():
        v = _lodged_value(e)
        if L["field_found"] is None and (hasattr(e, _LODGED) or any(hasattr(getattr(e, c, None), _LODGED) for c in ("lifecycle", "biological", "identity", "navigation", "strategic", "task", "interaction", "social", "combat"))): L["field_found"] = True
        was = _lodged_state.get(eid)
        if v is not None:
            L["lodger_ticks"] += 1; L["by_entity_last_lodged"][eid] = state.tick
            if was is None: L["enters"].append([state.tick, eid])
        elif was is not None:
            L["leaves"].append([state.tick, eid]); L["by_entity_last_leave"][eid] = state.tick
        _lodged_state[eid] = v
def _lodged_at_group_decision(state):
    L = E["lodged"]; L["group_decision_ticks"] += 1
    for g in state.groups.values():
        if g.dissolution_tick is None:
            for m in g.member_ids:
                e = state.entities.get(m)
                if e is not None and _lodged_value(e) is not None: L["group_decision_lodged"] += 1
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
    _lodged_at_group_decision(state)
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
    _lodged_probe(new)
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
E["lodged"]["by_entity_last_lodged"] = {str(k): v for k, v in E["lodged"]["by_entity_last_lodged"].items()}; E["lodged"]["by_entity_last_leave"] = {str(k): v for k, v in E["lodged"]["by_entity_last_leave"].items()}
with open(os.environ["M15_OUT"], "w") as fh: fh.write(json.dumps(E, default=str, separators=(",", ":")))
print("M15_OK")
