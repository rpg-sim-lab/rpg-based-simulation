"""Probe B2 (read-only, both arm trees; wrappers record only): per-subject rows for worker/blacksmith/guard/raider at starving-line ticks (hunger >= HUNGER_LINE).
Per subject: starving ticks, first starving tick, death, kind; action|reason, project kind, objective naming a living target, ways in reach, inn in reach/distance, gold, hostile in view,
current gate wait; goal scores (latest evaluation: winner > runner-up kinds, with the evaluation's age); work-shift state at the nearest work building (offers work, can pay, serves, shift_takeable,
held_work_is_threatened); and the hunger-arrival decisions (`building_arrival._hunger_arrival`): what was dispatched and, for a building that offers work, why a shift was not started.
Usage (cwd = tree root, PYTHONPATH=.): probe_ab2.py world seed ticks out.json"""
import collections, json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing, HUNGER_LINE
from src.ai.goals.scorers_support import perceived_hostiles
from src.ai.goals.ways import ways_in_reach, inn_in_reach
from src.engine.tactical_threat import hostile_acts_on
from src.engine.building_services import offers_work
from src.engine.serves import serves
from src.engine.work_shift import _can_pay_shift, shift_takeable, nearest_work
from src.engine.work_wake import held_work_is_threatened
import src.engine.tactical as _tac
import src.engine.building_arrival as _barr
import src.ai.score_modifiers as _sm
from tools.test_architecture.rpg_gate_run import build_kernel

_cur = [0]
WAITSET = set(); _hood = {}
_orig_cls = _tac.classify_neighbours
def _cls(entity, neighbors, src, *a, **kw):
    hood = _orig_cls(entity, neighbors, src, *a, **kw); _hood[entity.id] = len(hood.hostiles); return hood
_tac.classify_neighbours = _cls
_orig_eval = _tac.TacticalDecisionSystem.evaluate_entity_intent
def _eval(state, entity, *a, **kw):
    _hood.pop(entity.id, None)
    r = _orig_eval(state, entity, *a, **kw)
    if _hood.get(entity.id) and need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt):
        hs = perceived_hostiles(entity, state)
        if hs and not any(hostile_acts_on(h, entity, state.tick) for h in hs):
            p = entity.strategic.projects.get(entity.strategic.current_project_id) if entity.strategic.current_project_id else None
            serves_need = p is not None and str(getattr(p.status, "value", p.status)).upper() == "ACTIVE" and str(getattr(p.kind, "value", p.kind)).lower() in ("hunger", "fatigue")
            noop = r.task is None and r.navigation is None and r.strategic is None and getattr(r, "interaction", None) is None
            if not serves_need and noop: WAITSET.add((_cur[0], entity.id))
    return r
_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

SCORES = {}   # eid -> (tick, [(kind, utility)...top3])
_oam = _sm.ScoreModifierSystem.apply_modifiers
def _am(entity, state, scores, *a, **kw):
    out_ = _oam(entity, state, scores, *a, **kw)
    ms = sorted(out_, key=lambda x: (-x.utility, x.kind))
    SCORES[entity.id] = (_cur[0], [(str(getattr(g.kind, "value", g.kind)), round(g.utility, 1)) for g in ms[:3]])
    return out_
_sm.ScoreModifierSystem.apply_modifiers = staticmethod(_am)

ARR = collections.defaultdict(collections.Counter)    # eid -> counter of hunger-arrival outcomes
_oha = _barr._hunger_arrival
def _ha(state, entity, project, building_id):
    r = _oha(state, entity, project, building_id)
    b = state.buildings.get(building_id)
    pl = (r.task.payload_set if r.task is not None else None) or {}
    act = pl.get("action") or ("ENDED" if (r.strategic is not None and r.strategic.current_project_id_set == "") else "NOOP")
    key = f"{getattr(b,'kind',None)}|{act}"
    if act in ("ENDED", "NOOP") and b is not None and offers_work(b):
        try:
            tk = shift_takeable(entity, state, b.position); th = held_work_is_threatened(entity, state)
            key += f"|offers_work,takeable={tk},threatened={th},can_pay={_can_pay_shift(state, b)},hunger<20={entity.biological.hunger < 20.0}"
        except Exception as ex:
            key += f"|probe_err={type(ex).__name__}"
    ARR[entity.id][key] += 1
    return r
_barr._hunger_arrival = _ha

rid = f"ab2_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
kind_of = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values()}
PEOPLE = {"worker", "blacksmith", "guard", "raider"}
S = {}
def rec(eid):
    return S.setdefault(eid, {"kind": kind_of.get(eid), "starving_ticks": 0, "first": None, "death": None, "action_reason": collections.Counter(), "project_kind": collections.Counter(),
                              "need_objective": collections.Counter(), "ways": collections.Counter(), "inn_dist": collections.Counter(), "gold": collections.Counter(),
                              "hostile_in_view": collections.Counter(), "gate_wait": 0, "score_pair": collections.Counter(), "score_age": collections.Counter(),
                              "work_state": collections.Counter(), "meals": 0, "ate_ticks": []})
meal_prev = {}
for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    for eid, e in st.entities.items():
        kk = kind_of.get(eid)
        if kk not in PEOPLE: continue
        if not e.combat.alive:
            if eid in S and S[eid]["death"] is None: S[eid]["death"] = [t, str(getattr(e.lifecycle, "death_reason", None))]
            continue
        lm = e.biological.last_meal_tick
        if lm is not None and lm != meal_prev.get(eid, lm) and eid in S:
            S[eid]["meals"] += 1; S[eid]["ate_ticks"].append(t)
        meal_prev[eid] = lm
        if e.biological.hunger < HUNGER_LINE: continue
        r = rec(eid); r["starving_ticks"] += 1
        if r["first"] is None: r["first"] = t
        pl = e.task.payload or {}
        r["action_reason"][f"{pl.get('action')}|{pl.get('reason')}"] += 1
        cp = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
        pk = str(getattr(cp.kind, "value", cp.kind)).lower() if cp is not None else "none"
        r["project_kind"][pk] += 1
        if cp is not None and pk in ("hunger", "fatigue"):
            ob = next((o for o in cp.objectives if o.id == e.strategic.current_objective_id), None)
            r["need_objective"]["living_target" if (ob is not None and ob.target_entity_id is not None) else "place_or_other"] += 1
        try: r["ways"]["+".join(sorted(w.value for w in ways_in_reach(e, st))) or "NO_WAY"] += 1
        except Exception: r["ways"]["ERR"] += 1
        inn = inn_in_reach(e, st)
        d = None if inn is None else abs(inn.position[0] - e.navigation.position[0]) + abs(inn.position[1] - e.navigation.position[1])
        r["inn_dist"]["none" if d is None else "<=5" if d <= 5 else "<=20" if d <= 20 else ">20"] += 1
        r["gold"]["0" if e.inventory.gold <= 0 else "<10" if e.inventory.gold < 10 else ">=10"] += 1
        r["hostile_in_view"]["yes" if perceived_hostiles(e, st) else "no"] += 1
        if (t, eid) in WAITSET: r["gate_wait"] += 1
        sc = SCORES.get(eid)
        if sc:
            tops = sc[1]
            r["score_pair"][f"{tops[0][0]}>{tops[1][0] if len(tops) > 1 else '-'}"] += 1
            age = t - sc[0]; r["score_age"]["<=1" if age <= 1 else "<=10" if age <= 10 else ">10"] += 1
        try:
            nw = nearest_work(st, e)
            if nw is None: r["work_state"]["no_work_building_open (none offers work that can pay and serves)"] += 1
            else:
                tk = shift_takeable(e, st, nw.position); th = held_work_is_threatened(e, st)
                r["work_state"][f"nearest_work_open|takeable={tk}|threatened={th}"] += 1
        except Exception as ex:
            r["work_state"][f"err_{type(ex).__name__}"] += 1
h = CanonicalStateHasher.get_hash(k.state)
for eid, r in S.items():
    if r["death"] is None:
        e = k.state.entities.get(eid)
        if e is not None and not e.combat.alive: r["death"] = [k.state.tick, str(getattr(e.lifecycle, "death_reason", None))]
    for key_ in ("action_reason", "project_kind", "need_objective", "ways", "inn_dist", "gold", "hostile_in_view", "score_pair", "score_age", "work_state"):
        r[key_] = dict(r[key_].most_common(8))
    r["arrival"] = dict(ARR.get(eid, {}))
    r["ate_ticks"] = r["ate_ticks"][:10]
doc = {"world": world, "seed": seed, "ticks": ticks, "hash": h, "subjects": {str(a): b for a, b in S.items()},
       "arrival_all_people": {kind_of.get(a, "?") + "|" + key_: n for a, c in ARR.items() if kind_of.get(a) in PEOPLE for key_, n in c.items()}}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
