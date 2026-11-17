"""Read-only per-tick trace of selected subjects (default frontier s42 workers 2, 7, guard 10), both arm trees; wrappers record only.
Usage (cwd = tree root, PYTHONPATH=.): eng_trace_s42.py world seed ticks out.json from_tick id1,id2,... 
Per subject and tick (from_tick on): post-tick state (hp, hunger, debt, gold, last_meal_tick, task action/reason/target, project kind + objective target + way kind), and at its tactical decision the
hostiles in view (id, kind, task action/target, acting on the subject), the threatening/wary lists (tactical_avoid), need_first / need_yields / acting, hunt exemption (new arm only), which helper
returned a non-None update (avoid_what_can_eat_me / in_place_survival_update / pursue_objective / safety_retreat_warranted), the return's action/reason. Hunger arrivals (`_hunger_arrival`) with the values
shift_takeable and held_work_is_threatened read BEFORE the call, and EAT application: verify_action_legality, building_services.service_delta / service_building / admits_at results."""
import collections, json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out, from_tick = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
SUBJ = {int(x) for x in sys.argv[6].split(",")}
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_threat import hostile_acts_on, safety_retreat_warranted
from src.engine.work_shift import shift_takeable
from src.engine.work_wake import held_work_is_threatened
import src.engine.tactical as _tac
import src.engine.building_arrival as _barr
import src.engine.building_services as _bs
from src.engine.legality import LegalityServiceV2
from src.engine.serves import keeps_coin
from src.engine.spatial_query import SpatialQueryService
from tools.test_architecture.rpg_gate_run import build_kernel

_cur = [0]
DEC = {}; ARRIVE = []; LEG = []; SVC = []
_hood = {}; HELP = collections.defaultdict(list)
_ocls = _tac.classify_neighbours
def _cls(entity, neighbors, src, *a, **kw):
    hood = _ocls(entity, neighbors, src, *a, **kw)
    if entity.id in SUBJ:
        _hood[entity.id] = {"hostiles": [(h.id, str(getattr(h, "kind", "")), (h.task.payload or {}).get("action"), (h.task.payload or {}).get("target_id")) for h in hood.hostiles],
                            "threatening": [(h.id, str(getattr(h, "kind", ""))) for h in getattr(hood, "threatening", [])],
                            "wary": [(h.id, str(getattr(h, "kind", ""))) for h in getattr(hood, "wary", [])]}
    return hood
_tac.classify_neighbours = _cls
def wrap(name):
    orig = getattr(_tac, name)
    def f(*a, **kw):
        r = orig(*a, **kw)
        ent = next((x for x in a if hasattr(x, "id") and hasattr(x, "biological")), None)
        if ent is not None and ent.id in SUBJ:
            HELP[(_cur[0], ent.id)].append((name, r is not None and r is not False and not (isinstance(r, list) and not r)))
        return r
    setattr(_tac, name, f)
for n in ("avoid_what_can_eat_me", "in_place_survival_update", "pursue_objective", "safety_retreat_warranted"):
    if hasattr(_tac, n): wrap(n)
_oe = _tac.TacticalDecisionSystem.evaluate_entity_intent
def _eval(state, entity, *a, **kw):
    if entity.id in SUBJ: _hood.pop(entity.id, None)
    r = _oe(state, entity, *a, **kw)
    if entity.id in SUBJ and state.tick >= from_tick:
        hd = _hood.get(entity.id) or {"hostiles": [], "threatening": [], "wary": []}
        hs = perceived_hostiles(entity, state)
        acting = [hostile_acts_on(h, entity, state.tick) for h in hs]
        pr = need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt)
        pl = (r.task.payload_set if r.task is not None else None) or {}
        DEC[(_cur[0], entity.id)] = {"hostiles": hd["hostiles"], "threatening": hd["threatening"], "wary": hd["wary"], "perceived_hostiles": [h.id for h in hs],
                                      "acting_each": acting, "pressing": pr, "need_yields": any(acting), "need_first": bool(hs) and pr and not any(acting),
                                      "ret_action": pl.get("action"), "ret_reason": pl.get("reason"), "ret_target": pl.get("target_id"),
                                      "ret_nav": list(r.navigation.target_set) if (r.navigation is not None and r.navigation.target_set is not None) else None,
                                      "ret_noop": r.task is None and r.navigation is None and r.strategic is None and getattr(r, "interaction", None) is None,
                                      "helpers": [list(x) for x in HELP.get((_cur[0], entity.id), [])]}
    return r
_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

_oha = _barr._hunger_arrival
def _ha(state, entity, project, building_id):
    pre = None
    if entity.id in SUBJ:
        b = state.buildings.get(building_id)
        try: pre = {"hunger": entity.biological.hunger, "shift_takeable": shift_takeable(entity, state, b.position) if b is not None else None, "threatened": held_work_is_threatened(entity, state)}
        except Exception as ex: pre = {"err": type(ex).__name__}
    r = _oha(state, entity, project, building_id)
    if entity.id in SUBJ:
        p = (r.task.payload_set if r.task is not None else None) or {}
        ARRIVE.append({"t": state.tick, "eid": entity.id, "building": building_id, "pre": pre, "returned_action": p.get("action"), "ended": bool(r.strategic is not None and r.strategic.current_project_id_set == "")})
    return r
_barr._hunger_arrival = _ha
_ovl = LegalityServiceV2.verify_action_legality
def _vl(actor, action_kind, state):
    r = _ovl(actor, action_kind, state)
    if actor.id in SUBJ and action_kind in ("EAT", "WORK", "REST") and state.tick >= from_tick:
        LEG.append({"t": state.tick, "eid": actor.id, "action": action_kind, "legal": bool(r[0]), "reason": str(getattr(r[1], "value", r[1]))})
    return r
LegalityServiceV2.verify_action_legality = staticmethod(_vl)
_osd = _bs.service_delta
def _sd(context, entity, action, tick):
    r = _osd(context, entity, action, tick)
    if entity.id in SUBJ and action in ("EAT", "REST") and tick >= from_tick:
        b = None
        try: b = _bs.service_building(context, entity, action)
        except Exception: pass
        adm = None
        try: adm = _bs.admits_at(entity, b, action, context) if b is not None else None
        except Exception: pass
        SVC.append({"t": tick, "eid": entity.id, "action": action, "building": getattr(b, "id", None), "building_functional": getattr(b, "functional", None), "admits_at": adm, "delivered": r is not None})
    return r
_bs.service_delta = _sd

rid = f"s42_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
ROWS = collections.defaultdict(list)
PERS = {e.id for e in k.state.entities.values() if keeps_coin(e)}
ANIMALS = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values() if str(getattr(e, "kind", "")) in ("predator_hunter", "alpha", "wild_creature")}
ASUM = {i: {"kind": kd, "alive_ticks": 0, "death_tick": None, "attack_or_pursue_person_ticks": 0, "first_attack_person_tick": None, "near_ticks": 0, "targets": collections.Counter()} for i, kd in ANIMALS.items()}
NEAR = []   # per tick: animals within 12 tiles of any subject
for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    for aid, kd in ANIMALS.items():
        a = st.entities.get(aid); sm = ASUM[aid]
        if a is None or not a.combat.alive:
            if sm["death_tick"] is None and sm["alive_ticks"] > 0: sm["death_tick"] = t
            continue
        sm["alive_ticks"] += 1
        ap = a.task.payload or {}
        tgt = ap.get("target_id")
        if tgt in PERS and (ap.get("action") in ("ATTACK", "SKILL") or str(a.navigation.movement_mode) in ("MovementMode.PURSUE", "MovementMode.INTERCEPT")):
            sm["attack_or_pursue_person_ticks"] += 1; sm["targets"][tgt] += 1
            if sm["first_attack_person_tick"] is None: sm["first_attack_person_tick"] = t
        if t >= from_tick:
            ds = {}
            for sid in SUBJ:
                se = st.entities.get(sid)
                if se is not None and se.combat.alive:
                    ds[sid] = abs(a.navigation.position[0] - se.navigation.position[0]) + abs(a.navigation.position[1] - se.navigation.position[1])
            if ds and min(ds.values()) <= 12:
                sm["near_ticks"] += 1
                NEAR.append({"t": t, "id": aid, "kind": kd, "pos": list(a.navigation.position), "hp": a.combat.hp, "hunger": round(a.biological.hunger, 1), "task": [ap.get("action"), ap.get("reason"), tgt],
                             "mode": str(a.navigation.movement_mode), "dist": ds})
    if t < from_tick: continue
    for eid in SUBJ:
        e = st.entities.get(eid)
        if e is None or not e.combat.alive: continue
        pl = e.task.payload or {}
        cp = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
        ob = None
        if cp is not None:
            o = next((x for x in cp.objectives if x.id == e.strategic.current_objective_id), None)
            ob = None if o is None else [str(getattr(o.kind, "value", o.kind)), o.target, o.target_entity_id]
        d = DEC.get((t - 1, eid)) or DEC.get((t, eid))
        inn = SpatialQueryService.nearest_building(st, e.navigation.position, "inn")
        inn_pos = None if inn is None else [inn.position[0], inn.position[1]]
        inn_d = None if inn is None else abs(inn.position[0] - e.navigation.position[0]) + abs(inn.position[1] - e.navigation.position[1])
        ROWS[eid].append({"t": t, "hp": e.combat.hp, "hunger": round(e.biological.hunger, 1), "debt": round(e.biological.sleep_debt, 1), "gold": e.inventory.gold, "last_meal": e.biological.last_meal_tick,
                          "pos": list(e.navigation.position), "task": [pl.get("action"), pl.get("reason"), pl.get("target_id")], "mode": str(e.navigation.movement_mode), "inn_pos": inn_pos, "inn_dist": inn_d,
                          "proj": None if cp is None else str(getattr(cp.kind, "value", cp.kind)), "proj_status": None if cp is None else str(getattr(cp.status, "value", cp.status)), "obj": ob,
                          "dec": d if (t - 1, eid) in DEC or (t, eid) in DEC else None})
doc = {"world": world, "seed": seed, "ticks": ticks, "from_tick": from_tick, "hash": CanonicalStateHasher.get_hash(k.state), "rows": {str(a): b for a, b in ROWS.items()},
       "animals": {str(i): {**v, "targets": dict(v["targets"])} for i, v in ASUM.items()}, "animals_near_subjects": NEAR, "arrivals": ARRIVE, "legality": LEG, "service": SVC}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
