"""(v2: adds designer fields: per-person wait events, strategic-pass/score/cap records, first-hit after wait, wait share and need-met post-process; still record-only.)
Phase 2 trace of the urban s44 victims (read-only; wrappers only record, never change a result). Works on both arm trees (imports only what both have).

Usage (cwd = arm tree root, PYTHONPATH=.): eng_trace.py world seed ticks out.json id1,id2,...

Per tick it records the state hash (to find the first divergence between the arms) and a decision tuple per entity (to find which entity decides differently first).
For the listed victims it records, every tick they are alive: position, hp, hunger, sleep debt, the task action/reason/target after the tick, the project kind, and the ENG
branch view: whether hostiles were in sight at the tactical decision, whether the need was pressing, whether a hostile was acting on the subject, whether an adjacent hostile was
present, and what the tactical decision returned (EAT / REST / walk to a target / other). Deaths: tick, cause, killer id and the killer's task.
"""
import collections, json, os, shutil, sys
from pathlib import Path

world, seed, ticks, out, victims = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], {int(x) for x in sys.argv[5].split(",")}
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing
from src.engine.tactical_threat import hostile_acts_on
import src.engine.tactical as _tac
from src.engine.serves import keeps_coin
from src.engine.tactical_rest import eat_carried_update, in_danger
import src.systems.strategic_systems.intelligence as _intel
import src.ai.score_modifiers as _sm
from tools.test_architecture.rpg_gate_run import build_kernel

LOWHP = []; WAIT = []; PERSONS = set(); STRAT = {}; SCORE = {}; CAP = []
TACT = {}                # (tick, eid) -> tactical view recorded at the decision
_cur = [0]
_hood = {}
_orig_cls = _tac.classify_neighbours


def _cls(entity, neighbors, src, *a, **kw):
    hood = _orig_cls(entity, neighbors, src, *a, **kw)
    _hood[entity.id] = len(hood.hostiles)
    return hood


_tac.classify_neighbours = _cls
_orig_eval = _tac.TacticalDecisionSystem.evaluate_entity_intent


def _eval(state, entity, *a, **kw):
    _hood.pop(entity.id, None)
    r = _orig_eval(state, entity, *a, **kw)
    n = _hood.get(entity.id)
    if n and entity.id in PERSONS:
        hs0 = perceived_hostiles(entity, state)
        pr0 = need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt)
        if hs0 and pr0 and entity.combat.hp / max(1, entity.combat.max_hp) < 0.15 and not any(hostile_acts_on(h, entity, state.tick) for h in hs0):
            LOWHP.append((_cur[0], entity.id))     # hp<15%, pressing, hostiles in sight, none acting on it: need_first (:278) precedes the :469 hp<15% site
        if hs0 and pr0 and not any(hostile_acts_on(h, entity, state.tick) for h in hs0):
            project = entity.strategic.projects.get(entity.strategic.current_project_id) if entity.strategic.current_project_id else None
            serves = project is not None and str(getattr(project.status, "value", project.status)).upper() == "ACTIVE" and str(getattr(project.kind, "value", project.kind)).lower() in ("hunger", "fatigue")
            noop = r.task is None and r.navigation is None and r.strategic is None and getattr(r, "interaction", None) is None
            if not serves and noop:
                WAIT.append((_cur[0], entity.id))
    if n and entity.id in victims:
        hs = perceived_hostiles(entity, state)
        pr = need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt)
        adj = any(abs(h.navigation.position[0] - entity.navigation.position[0]) + abs(h.navigation.position[1] - entity.navigation.position[1]) <= 1 for h in hs)
        acting = any(hostile_acts_on(h, entity, state.tick) for h in hs)
        p = (r.task.payload_set if r.task is not None else None) or {}
        TACT[(_cur[0], entity.id)] = {"hostiles_in_sight": n, "pressing": pr, "adjacent": adj, "acting": acting,
                                      "ret_action": p.get("action"), "ret_reason": p.get("reason"), "ret_target": p.get("target_id"),
                                      "ret_nav": list(r.navigation.target_set) if (r.navigation is not None and r.navigation.target_set is not None) else None,
                                      "ret_strat_suspends": bool(r.strategic is not None and getattr(r.strategic, "projects_add_or_update", None))}
    return r


_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

_oes = _intel.StrategicIntelligenceSystem.evaluate_strategic_intent
def _es(state, entity, *a, **kw):
    if entity.id in PERSONS:
        STRAT[(_cur[0], entity.id)] = 1      # the strategic pass ran for this entity this tick (cadence passed)
    return _oes(state, entity, *a, **kw)
_intel.StrategicIntelligenceSystem.evaluate_strategic_intent = staticmethod(_es)
_oam = _sm.ScoreModifierSystem.apply_modifiers
def _am(entity, state, scores, *a, **kw):
    out = _oam(entity, state, scores, *a, **kw)
    if entity.id in PERSONS:
        ms = sorted(out, key=lambda x: (-x.utility, x.kind))
        best = next((g for g in ms if not (g.utility < 20.0 or (g.target_id is None and g.target_pos is None))), None)
        SCORE[(_cur[0], entity.id)] = {"top": [[str(getattr(g.kind, "value", g.kind)), round(g.utility, 1)] for g in ms[:4]],
                                       "best": [str(getattr(best.kind, "value", best.kind)), round(best.utility, 1)] if best is not None else None}
    return out
_sm.ScoreModifierSystem.apply_modifiers = staticmethod(_am)
_ocap = _intel.has_project_capacity
def _capf(projects, max_active, *a, **kw):
    r = _ocap(projects, max_active, *a, **kw)
    if not r:
        fr = sys._getframe(1)
        if fr.f_code.co_filename.endswith("intelligence.py"):
            ent = fr.f_locals.get("entity")
            if ent is not None and "best_candidate" in fr.f_locals:
                bc = fr.f_locals["best_candidate"]
                CAP.append((_cur[0], ent.id, str(getattr(bc.kind, "value", bc.kind))))
    return r
_intel.has_project_capacity = _capf

rid = f"trace_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
PERSONS.update(e.id for e in k.state.entities.values() if keeps_coin(e))
ALLROWS = collections.defaultdict(list)
hashes, decisions, rows, deaths = [], [], collections.defaultdict(list), {}
prev_dec = {}
for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    hashes.append(CanonicalStateHasher.get_hash(st)[:16])
    dec = {}
    for eid, e in st.entities.items():
        if not e.combat.alive:
            continue
        pl = e.task.payload or {}
        d = (pl.get("action"), pl.get("reason"), pl.get("target_id"), tuple(e.navigation.target) if e.navigation.target is not None else None)
        dec[eid] = d
    decisions.append(dec)
    for eid in PERSONS:
        e = st.entities.get(eid)
        if e is None or not e.combat.alive:
            continue
        pl = e.task.payload or {}
        ALLROWS[eid].append([t, round(e.biological.hunger, 1), round(e.biological.sleep_debt, 1), e.combat.hp, pl.get("action"), pl.get("target_id"), e.combat.last_attacker_id, e.combat.last_hit_tick])
    for eid in victims:
        e = st.entities.get(eid)
        if e is None:
            continue
        if not e.combat.alive:
            if eid not in deaths:
                kid = e.combat.last_attacker_id
                ke = st.entities.get(kid) if kid is not None else None
                kt = (ke.task.payload or {}) if ke is not None else {}
                dr = getattr(e.lifecycle, "death_record", None)
                deaths[eid] = {"tick": t, "cause": str(getattr(getattr(dr, "cause", None), "value", getattr(e.lifecycle, "death_reason", None))), "killer": kid,
                               "killer_kind": getattr(ke, "kind", None), "killer_task": [kt.get("action"), kt.get("reason"), kt.get("target_id")], "killer_pos": list(ke.navigation.position) if ke is not None else None,
                               "pos": list(e.navigation.position), "last_hit_tick": e.combat.last_hit_tick}
            continue
        pl = e.task.payload or {}
        cp = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
        row = {"t": t, "pos": [round(e.navigation.position[0], 1), round(e.navigation.position[1], 1)], "hp": e.combat.hp, "hunger": round(e.biological.hunger, 1),
               "debt": round(e.biological.sleep_debt, 1), "action": pl.get("action"), "reason": pl.get("reason"), "target": pl.get("target_id"),
               "proj": str(getattr(cp.kind, "value", cp.kind)) if cp is not None else None, "last_attacker": e.combat.last_attacker_id, "last_hit": e.combat.last_hit_tick}
        tv = TACT.get((t - 1, eid)) or TACT.get((t, eid))
        if tv:
            row["tact"] = tv
        rows[eid].append(row)
def _stretches(ts, gap=12):
    ts = sorted(set(ts)); out = []
    if not ts: return out
    a = p = ts[0]
    for x in ts[1:] + [None]:
        if x is None or x - p > gap:
            out.append((a, p)); a = x
        if x is not None: p = x
    return out
wait_by = collections.defaultdict(list)
for (t_, e_) in WAIT: wait_by[e_].append(t_)
wait_report = {}
for eid, ts in wait_by.items():
    rws = ALLROWS.get(eid, []); by_t = {r_[0]: r_ for r_ in rws}
    dtick = (deaths.get(eid) or {}).get("tick")
    stretches = []
    for a, b in _stretches(ts):
        r0 = by_t.get(a)
        # first hit after the wait began: first row with last_hit_tick >= a
        hit = next((r_ for r_ in rws if r_[0] >= a and r_[7] is not None and r_[7] >= a), None)
        attacker = hit[6] if hit else None
        pre = [r_ for r_ in rws if a - 40 <= r_[0] < a]
        fought_before = bool(attacker is not None and any((r_[5] == attacker) or (r_[6] == attacker and r_[7] is not None and r_[7] < a) for r_ in pre))
        met = next((r_[0] for r_ in rws if r_[0] > b and r0 is not None and (r_[1] <= r0[1] - 15 or r_[2] <= r0[2] - 15)), None)
        stretches.append({"start": a, "end": b, "hunger0": r0[1] if r0 else None, "debt0": r0[2] if r0 else None, "hp0": r0[3] if r0 else None,
                          "first_hit": {"tick": hit[7], "attacker": attacker} if hit else None, "fought_attacker_in_prior_40t": fought_before,
                          "strategic_pass_ticks": sum(1 for t_ in range(a, b + 1) if (t_, eid) in STRAT),
                          "cap_refusals": [c_ for c_ in CAP if c_[1] == eid and a <= c_[0] <= b],
                          "score_best": [SCORE[(t_, eid)]["best"] for t_ in range(a, min(b, a + 3) + 1) if (t_, eid) in SCORE][:4],
                          "need_met_tick_after": met})
    wait_report[str(eid)] = {"wait_ticks": len(set(ts)), "alive_ticks": len(rws), "share": round(len(set(ts)) / max(1, len(rws)), 4),
                             "death": deaths.get(eid), "stretches": stretches,
                             "end": "death" if dtick else "run_end", "unmet_after_last": (stretches[-1]["need_met_tick_after"] is None) if stretches else None}
lowhp_report = {}
lh_by = collections.defaultdict(list)
for (t_, e_) in LOWHP: lh_by[e_].append(t_)
for eid, ts in lh_by.items():
    rws = ALLROWS.get(eid, []); by_t = {r_[0]: r_ for r_ in rws}; t0 = min(ts); r0 = by_t.get(t0)
    d_ = (deaths.get(eid) or {}).get("tick")
    met = next((r_[0] for r_ in rws if r_[0] > t0 and r0 is not None and (r_[1] <= r0[1] - 15 or r_[2] <= r0[2] - 15)), None)
    lowhp_report[str(eid)] = {"ticks": len(set(ts)), "first": t0, "last": max(ts), "death_tick": d_, "death_within_200": bool(d_ and d_ - t0 <= 200),
                              "need_met_tick_after_first": met}
# why no need project, per victim wait tick: due? cap? best candidate?
why = {}
for eid in victims:
    w = sorted(set(t_ for (t_, e_) in WAIT if e_ == eid))
    why[str(eid)] = [{"t": t_, "strategic_pass_ran": (t_, eid) in STRAT or (t_ + 1, eid) in STRAT, "best": (SCORE.get((t_, eid)) or SCORE.get((t_ + 1, eid)) or {}).get("best"),
                      "top": (SCORE.get((t_, eid)) or SCORE.get((t_ + 1, eid)) or {}).get("top"), "cap_refused": [c_[2] for c_ in CAP if c_[1] == eid and c_[0] in (t_, t_ + 1)]} for t_ in w]
doc = {"lowhp_pressing_unacted": {"subjects": len(lowhp_report), "ticks": sum(v["ticks"] for v in lowhp_report.values()), "per_subject": lowhp_report}, "wait_report": wait_report, "wait_why_victims": why, "world": world, "seed": seed, "ticks": ticks, "final_hash": CanonicalStateHasher.get_hash(k.state), "hashes": hashes,
       "decisions_sample_len": len(decisions), "deaths": deaths, "rows": {str(a): b for a, b in rows.items()}}
# per-tick decision map is large: keep only the decision tuples as a compact list of dicts of changed entities vs the previous tick
changed = []
for i, dec in enumerate(decisions):
    prev = decisions[i - 1] if i else {}
    changed.append({str(e): list(d) for e, d in dec.items() if prev.get(e) != d})
doc["decision_changes"] = changed
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
