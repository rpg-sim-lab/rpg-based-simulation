"""Retention trace + width probe (scratch, read-only; pushable). Usage: PROBE_OUT=<jsonl> python probe6.py <world> <seed> <ticks>   (cwd = a commit tree, PYTHONPATH = that tree)
Runs the engine the way tools/evaluate_simq.py -> calibrate_simq does for an anchored key: tools.calibrate_simq._run_engine(world, seed, ticks, extra_flags=<profile flags of the same name>, audit_mode=True), without the quality-report replay.
Records (all read-only):
  pj  per entity, on change of (alive, current project id): tick, entity, alive, project id
  rh  per tick, per ALIVE entity whose current project id contains 'combat_retreat': hp, max hp, acting_threat_to (src/ai/goals/present_threat.py), adj (a perceived hostile orthogonally adjacent, decision 32), perceived count
  sel per strategic goal-selection call (ScoreModifierSystem.apply_modifiers) for an entity holding a retreat project: top-3 modified scores, the best_candidate the intelligence.py:1586-1593 filter yields (utility >= 20 and a target) or None, the head committed intention (kind, status)
  sw  per evaluate_project_switch call where the current project is a retreat project: candidate, candidate score, current score, lock_until, retention margin inputs, returned switch
  dead per DEAD entity (at its first dead tick, every 250 ticks, and at the last tick): current project id and the ids/kinds/status of its ACTIVE projects
  fin the final state_hash from run_manifest.json"""
import json, os, sys, shutil
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w")
def log(**r): OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from src.ai.goals.present_threat import acting_threat_to
from src.ai.goals.present_threat import present_threat_to   # exists on both arms
retreat_threat_present = present_threat_to
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.legality import LegalityServiceV2
from src.ai.score_modifiers import ScoreModifierSystem as SM
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem as SI
from src.systems.world_systems.groups import GroupSystem
def holds_retreat(e): return "combat_retreat" in (e.strategic.current_project_id or "")
om = SM.apply_modifiers
import src.systems.strategic_systems.intelligence as I
cur = {"t": None, "e": None}
def am(entity, state, scores):
    res = om(entity, state, scores)
    cur["t"], cur["e"] = state.tick, entity.id
    if holds_retreat(entity):
        ms = sorted(res, key=lambda x: (-x.utility, x.kind))
        best = next((g for g in ms if not (g.utility < 20.0 or (g.target_id is None and g.target_pos is None))), None)
        ci = entity.strategic.committed_intentions
        ex = next((p for p in entity.strategic.projects.values() if best and p.kind == best.kind), None)
        log(k="ex", t=state.tick, e=entity.id, best_kind=str(best.kind) if best else None, existing=[ex.id, str(ex.status)] if ex else None,
            n_active=sum(1 for p in entity.strategic.projects.values() if "ACTIVE" in str(p.status)), max_active=entity.strategic.profile.max_active_projects)
        log(k="sel", t=state.tick, e=entity.id, top=[[str(g.kind), round(g.utility, 3), g.target_id] for g in ms[:3]],
            best=[str(best.kind), round(best.utility, 3), best.target_id] if best else None,
            ci=[ci[0].goal_kind, ci[0].status] if ci else None)
    return res

from src.ai.goals.scorers import CombatRetreatScorer, RecoverScorer
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.cognition import SensoryFilter, AppraisalSystem
_crs = CombatRetreatScorer.score
def _crs_log(self, entity, state):
    res = _crs(self, entity, state)
    if res.utility > 0 and not holds_retreat(entity):
        try:
            rn = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
            nb = SensoryFilter.filter_saliency(entity, rn, max_targets=5)
            em = AppraisalSystem.evaluate_emotional_state(entity, nb, region_trauma=SimulationDomainLogic.get_region_trauma(state, entity.navigation.position), social_context=entity.social)
            rc = RecoverScorer().score(entity, state)
            st = getattr(entity, "stamina", None)
            log(k="adopt", t=state.tick, e=entity.id, hp=entity.combat.hp / max(1, entity.combat.max_hp),
                stam=(st.current / st.max_stamina if st is not None and st.max_stamina > 0 else None), panic=em.panic_level, fleeing=bool(em.is_fleeing),
                bravery=entity.identity.personality.bravery, retreat_u=res.utility, recover_u=rc.utility, threat=bool(retreat_threat_present(entity, state)),
                acting=bool(acting_threat_to(entity, state)))
        except Exception as ex:
            log(k="adopt_err", t=state.tick, e=entity.id, err=str(ex))
    return res
CombatRetreatScorer.score = _crs_log

# R3: ticks with hp < 0.5, no present threat, and no RECOVER/REST/FATIGUE project current (per entity), sampled in update_groups below.
r3 = {}
# Tactical flight counter: a PANIC_RETREAT issued while present_threat_to is False (option A would remove it).
from src.engine.tactical import TacticalDecisionSystem as TDS
_tdi = TDS.evaluate_entity_intent
def _tdi_log(state, entity, *a, **k):
    res = _tdi(state, entity, *a, **k)
    try:
        t = getattr(res, "task", None)
        if t is not None and t.payload_set and t.payload_set.get("reason") == "PANIC_RETREAT" and not present_threat_to(entity, state):
            hs = perceived_hostiles(entity, state); ex, ey = entity.navigation.position
            dmin = min((abs(h.navigation.position[0] - ex) + abs(h.navigation.position[1] - ey) for h in hs), default=None)
            log(k="flee_nopresent", t=state.tick, e=entity.id, hp=entity.combat.hp / max(1, entity.combat.max_hp), dist=dmin, n_hostiles=len(hs))
    except Exception as ex_:
        log(k="flee_err", t=state.tick, err=str(ex_))
    return res
TDS.evaluate_entity_intent = staticmethod(_tdi_log)
SM.apply_modifiers = staticmethod(am)
oe = SI.evaluate_project_switch
def ev(entity, candidate_project, current_tick, state=None):
    res = oe(entity, candidate_project, current_tick, state=state)
    cur = entity.strategic.projects.get(entity.strategic.current_project_id)
    if cur is not None and "combat_retreat" in cur.id:
        p = entity.strategic.profile
        log(k="sw", t=current_tick, e=entity.id, cand=candidate_project.id, cand_score=candidate_project.score, cur=cur.id, cur_status=str(cur.status), cur_score=cur.score,
            lock_until=cur.lock_until_tick, resist=p.interruption_resistance, mult=p.resistance_multiplier, switched=bool(res),
            set=(res.current_project_id_set if res else None))
    return res
SI.evaluate_project_switch = staticmethod(ev)
_hc, _en, _rs = I.has_project_capacity, I.escalated_need_wins, SI.resume_project
from src.core.strategic import is_live_project
def hc(projects, max_active):
    r = _hc(projects, max_active)
    if cur["e"] is not None and any("combat_retreat" in pid for pid, p in projects.items() if "ACTIVE" in str(p.status)): log(k="cap", t=cur["t"], e=cur["e"], has_capacity=bool(r), live=sum(1 for p in projects.values() if is_live_project(p)), max=max_active)
    return r
def en(entity, kind):
    r = _en(entity, kind)
    if holds_retreat(entity): log(k="esc", t=cur["t"], e=entity.id, kind=str(kind), escalated=bool(r))
    return r
def rs(entity, pid):
    r = _rs(entity, pid)
    if holds_retreat(entity): log(k="res", t=cur["t"], e=entity.id, pid=pid, resumed=bool(r))
    return r
I.has_project_capacity, I.escalated_need_wins = hc, en
SI.resume_project = staticmethod(rs)
prev = {}
og = GroupSystem.update_groups
def ug(state, current_update=None):
    t = state.tick
    for eid in sorted(state.entities):
        e = state.entities[eid]; st = e.strategic; pr = st.current_project_id or ""
        key = (bool(e.combat.alive), pr)
        if prev.get(eid) != key:
            old_pr = prev[eid][1] if eid in prev else ""
            if "combat_retreat" in old_pr:
                op = st.projects.get(old_pr)
                log(k="end", t=t, e=eid, pr=old_pr, alive=key[0], status=str(op.status) if op else None, ended_by=(op.ended_by.value if op is not None and op.ended_by is not None else None))
            prev[eid] = key; log(k="pj", t=t, e=eid, a=key[0], pr=pr)
        if e.combat.alive and e.combat.hp / max(1, e.combat.max_hp) < 0.5:
            cur_p = st.projects.get(st.current_project_id) if st.current_project_id else None
            ck = str(getattr(cur_p.kind, "value", cur_p.kind)) if cur_p is not None else None
            if ck not in ("recover", "rest", "fatigue") and not present_threat_to(e, state):
                r3[eid] = r3.get(eid, 0) + 1
        if e.combat.alive and t % 20 == 0:
            live = [p for p in st.projects.values() if is_live_project(p)]
            mx = st.profile.max_active_projects
            if len(live) >= mx:
                sus = [p for p in live if "SUSPENDED" in str(p.status)]
                log(k="capfull", t=t, e=eid, n=len(live), mx=mx, hold_retreat=("combat_retreat" in pr), susp=[[p.id, str(p.kind), t - p.created_tick] for p in sus])
        if e.combat.alive and "combat_retreat" in pr and (prev.get(("susp", eid)) is None or t % 100 == 0):
            prev[("susp", eid)] = t
            log(k="live", t=t, e=eid, pr=pr, live=[[p.id, str(p.kind), str(p.status), t - p.created_tick] for p in st.projects.values() if is_live_project(p)])
        if e.combat.alive and "combat_retreat" in pr:
            hs = perceived_hostiles(e, state)
            adj = any(LegalityServiceV2.is_adjacent(e.navigation.position, h.navigation.position) for h in hs)
            log(k="rh", t=t, e=eid, pr=pr, hp=e.combat.hp, mh=e.combat.max_hp, acting=bool(acting_threat_to(e, state)), adj=bool(adj), perc=len(hs), p=e.navigation.position, wk=e.task.work_kind, act=(e.task.payload.get("action") if e.task.payload else None))
        if not e.combat.alive:
            first = prev.get(("dead", eid)) is None
            if first or t % 250 == 249 or t == ticks - 1:
                prev[("dead", eid)] = t
                act = [[pid, str(p.kind), str(p.status)] for pid, p in st.projects.items() if "ACTIVE" in str(p.status)]
                dr = getattr(e.lifecycle, "death_record", None)
                log(k="dead", t=t, e=eid, pr=pr, active=act, first=first, cause=(dr.cause.value if dr else None), dtick=(dr.tick if dr else None), attacker=(dr.last_attacker_id if dr else None))
    return og(state, current_update)
GroupSystem.update_groups = staticmethod(ug)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile(world))
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
log(k="r3", ticks=r3)
log(k="fin", state_hash=m["state_hash"], ticks=m["ticks_completed"], run_id=run_id, elapsed=elapsed, flags=flags)
OUT.close()
shutil.rmtree(run_dir)   # this run's own scratch run directory (about 100 MB); the manifest hash is kept in the log
