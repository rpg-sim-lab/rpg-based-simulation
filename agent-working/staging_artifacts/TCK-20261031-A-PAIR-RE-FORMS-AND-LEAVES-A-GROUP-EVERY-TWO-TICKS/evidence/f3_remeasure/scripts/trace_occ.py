"""Occupancy / retreat probe (read-only; wrappers only): urban s42 arm. Usage: TR_OUT=<jsonl> python trace_occ.py urban_political 42 <ticks>
Per tick t in OCC_WIN (default 1677-1686): the 8 neighbours of each centre in CENTRES ([41,30], [41,31]): occupant ids (living, int tile), static obstruction (src.engine.legality.static_obstruction),
LegalityServiceV2.verify_occupancy(tile, state, ignore_entity_id=23) (the legality the move used) -> free flag; every entity's position; details for the occupants and the watched entities.
Every call of tactical_hold.retreat_destination (the AVOID_NO_ROUTE source) for an entity within Euclid 6 of [41,30] in 1670-1686: threats, containing region and bounds, the _away_destination candidate and distances, home_region_id/centre, returned value.
History 1650-1686 of every entity within Manhattan 4 of [41,30]: position, task work/reason/target, nav target, group id and role, whether it is a member of 10047. cwd = tree, PYTHONPATH = tree."""
import json, os, sys
from types import SimpleNamespace as _NS
sys.path.insert(0, ".")
from src.engine.apply import ApplyPath
from src.engine.legality import LegalityServiceV2, static_obstruction
import src.engine.tactical_hold as TH
import src.engine.tactical_destinations as TD
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
W0, W1 = [int(x) for x in os.environ.get("OCC_WIN", "1677,1686").split(",")]
H0 = int(os.environ.get("HIST_FROM", "1650"))
CENTRES = [(41, 30), (41, 31)]
out = open(os.environ["TR_OUT"], "w")
def w(r): out.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
_RET = TH.retreat_destination
def _ret(state, entity, threats):
    res = _RET(state, entity, threats)
    if 1670 <= state.tick <= W1:
        here = entity.navigation.position
        if (here[0] - 41) ** 2 + (here[1] - 30) ** 2 <= 36:
            thr = list(threats); tp = sorted(t.navigation.position for t in thr)
            region = TD.containing_region(state, here)
            away = None if (region is None or not tp) else TD._away_destination(region, here, tp)
            home = state.regions.get(entity.strategic.home_region_id) if entity.strategic.home_region_id else None
            ax = sum(here[0] - p[0] for p in tp); ay = sum(here[1] - p[1] for p in tp)
            w({"k": "retreat", "t": state.tick, "e": entity.id, "pos": list(here), "threats": [[t.id, list(t.navigation.position)] for t in thr], "region": None if region is None else region.id,
               "bounds": None if region is None else list(region.bounds), "away_vec": [ax, ay], "away_candidate": away, "home_region_id": entity.strategic.home_region_id, "home_center": None if home is None else list(home.center),
               "returned": res})
    if entity.id == 23 and 1677 <= state.tick <= W1:
        props = entity.identity.properties or {}; here = entity.navigation.position
        region = TD.containing_region(state, here); home = state.regions.get(entity.strategic.home_region_id) if entity.strategic.home_region_id else None
        def at(p):  # retreat_destination reads only navigation.position and strategic.home_region_id of the entity (+ state.regions): a stand-in with another position, same threats
            stand = _NS(id=entity.id, navigation=_NS(position=p), strategic=_NS(home_region_id=entity.strategic.home_region_id))
            return _RET(state, stand, list(threats))
        w({"k": "e23_retreat", "t": state.tick, "pos": list(here), "posture": props.get("last_combat_posture"), "posture_target": props.get("last_combat_posture_target"), "region": None if region is None else [region.id, list(region.bounds)],
           "home_region_id": entity.strategic.home_region_id, "home_region_exists": home is not None, "returned_actual": res, "at_41_30": at((41.0, 30.0)), "at_41_31": at((41.0, 31.0)), "threats": [[t.id, list(t.navigation.position)] for t in threats]})
    return res
TH.retreat_destination = _ret
_oa = ApplyPath.apply_generation
import inspect, dataclasses
from src.core.updates import EntityUpdate, StateUpdate
CUR = [0]
WRITERS = []
def _sig(u):
    return None if u is None else {"new_position": u.new_position, "moved": u.moved_this_tick, "nav_target": None if u.navigation is None else str(u.navigation.target_set)[:30], "mode": None if u.navigation is None else str(getattr(u.navigation, "movement_mode_set", None)), "reason": None if u.task is None or u.task.payload_set is None else u.task.payload_set.get("reason"), "work": None if u.task is None else u.task.work_kind_set}
def _wrap_phase(owner, name):
    fn = owner.__dict__[name]; raw = fn.__func__ if isinstance(fn, (staticmethod, classmethod)) else fn
    def wrapped(*a, **k):
        res = raw(*a, **k)
        if 1677 <= CUR[0] <= W1 + 1 and isinstance(res, StateUpdate):
            before = next((x for x in list(a) + list(k.values()) if isinstance(x, StateUpdate)), None)
            b = _sig(before.entity_updates.get(23)) if before is not None else None; c = _sig(res.entity_updates.get(23))
            if b != c: WRITERS.append({"k": "writer_phase", "t": CUR[0], "fn": f"{owner.__name__}.{name}", "e23_before": b, "e23_after": c})
        return res
    setattr(owner, name, staticmethod(wrapped))
from src.engine.pipeline import AuthoritativeApplyPipeline as _AAP
import src.engine.pipeline_phases.movement as _MV, src.engine.pipeline_phases.occupancy as _OC
for _own in (_AAP, _MV.MovementPhase, _OC.OccupancyPhase):
    for _n, _v in list(_own.__dict__.items()):
        if isinstance(_v, staticmethod) and not _n.startswith("__") and _n not in ("run_phase",):
            try: _wrap_phase(_own, _n)
            except Exception: pass
_om = EntityUpdate.merge
def _merge(self, other):
    res = _om(self, other)
    if self.entity_id == 23 and 1677 <= CUR[0] <= W1 + 1 and other is not None and getattr(other, "new_position", None) is not None and res.new_position != self.new_position:
        WRITERS.append({"k": "writer_merge", "t": CUR[0], "self_pos": self.new_position, "other_pos": other.new_position, "other_reason": None if other.task is None or other.task.payload_set is None else other.task.payload_set.get("reason"),
                        "stack": [f"{f.filename.split('/src/')[-1]}:{f.function}" for f in inspect.stack()[1:9]]})
    return res
EntityUpdate.merge = _merge
def occ(new, centre):
    rows = {}
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0: continue
            tile = (centre[0] + dx, centre[1] + dy)
            who = sorted(eid for eid, e in new.entities.items() if e.combat.alive and (int(e.navigation.position[0]), int(e.navigation.position[1])) == tile)
            try: so = static_obstruction(tile, new)
            except Exception as ex: so = "ERR " + repr(ex)[:40]
            try: ok, why = LegalityServiceV2.verify_occupancy((float(tile[0]), float(tile[1])), new, ignore_entity_id=23)
            except Exception as ex: ok, why = None, "ERR " + repr(ex)[:40]
            rows[f"{tile[0]},{tile[1]}"] = {"occ": who, "static": None if so is None else str(so), "free": ok, "why": str(why)}
    return rows
def ent_row(new, eid):
    e = new.entities.get(eid)
    if e is None: return None
    p = e.task.payload or {}; g = new.groups.get(e.identity.group_id) if e.identity.group_id is not None and e.identity.group_id >= 0 else None
    return {"pos": [round(x, 2) for x in e.navigation.position], "alive": e.combat.alive, "hp": e.combat.hp, "gid": e.identity.group_id, "role": None if g is None else g.roles.get(eid), "in10047": bool(g is not None and g.id == 10047),
            "work": e.task.work_kind, "action": p.get("action"), "reason": p.get("reason"), "tid": p.get("target_id"), "tpos": str(p.get("target_position"))[:24], "nav": None if e.navigation.target is None else str(e.navigation.target)[:24], "lodged_in": getattr(e.navigation, "lodged_in", None)}
def ag(prior, update, *a, **k):
    if 1677 <= prior.tick <= W1 + 1:
        u23 = update.entity_updates.get(23)
        w({"k": "upd", "t": prior.tick, "u23": None if u23 is None else {"nav": repr(u23.navigation)[:400], "new_position": u23.new_position, "moved": u23.moved_this_tick, "task": repr(u23.task)[:400], "combat": repr(getattr(u23, "combat", None))[:300]},
           "to_tiles": [[eid, u.new_position] for eid, u in update.entity_updates.items() if u.new_position is not None and (int(u.new_position[0]), int(u.new_position[1])) in ((41, 30), (41, 31), (40, 30), (40, 31))],
           "rejections": {kk: vv for kk, vv in (getattr(update, "rejections_delta", {}) or {}).items()}})
    CUR[0] = prior.tick
    if 1677 <= prior.tick <= W1:
        e17 = prior.entities.get(17); e23 = prior.entities.get(23)
        if e17 is not None and e23 is not None:
            def at(p):
                stand = _NS(id=23, navigation=_NS(position=p), strategic=_NS(home_region_id=e23.strategic.home_region_id))
                return _RET(prior, stand, [e17])
            w({"k": "retreat_e17", "t": prior.tick, "e23_actual": list(e23.navigation.position), "e17_actual": list(e17.navigation.position), "at_actual": at(e23.navigation.position), "at_41_30": at((41.0, 30.0)), "at_41_31": at((41.0, 31.0))})
    new = _oa(prior, update, *a, **k); t = new.tick
    if W0 <= t <= W1:
        w({"k": "occ", "t": t, "centres": {f"{c[0]},{c[1]}": occ(new, c) for c in CENTRES}, "positions": {eid: [round(e.navigation.position[0], 1), round(e.navigation.position[1], 1)] for eid, e in new.entities.items() if e.combat.alive}})
    if H0 <= t <= W1:
        near = [eid for eid, e in new.entities.items() if abs(e.navigation.position[0] - 41) + abs(e.navigation.position[1] - 30) <= 4]
        w({"k": "hist", "t": t, "ents": {eid: ent_row(new, eid) for eid in sorted(set(near) | {23, 24, 17})}})
    for eid, ne in new.entities.items():
        dr = ne.lifecycle.death_record
        if dr is not None and (prior.entities.get(eid) is None or prior.entities[eid].lifecycle.death_record is None):
            w({"k": "death", "t": t, "e": eid, "cause": dr.cause.value, "att": dr.last_attacker_id, "pos": list(ne.navigation.position)})
    return new
ApplyPath.apply_generation = staticmethod(ag)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=True)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
[w(x) for x in WRITERS]; w({"k": "fin", "hash": m["state_hash"], "elapsed": elapsed}); out.close(); print("OCC_OK", m["state_hash"][:12])
