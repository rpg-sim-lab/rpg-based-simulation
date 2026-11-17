"""Read-only per-tick trace of one creature (default frontier s42 predator_hunter 45) on both arm trees; wrappers record only.
Usage (cwd = tree root, PYTHONPATH=.): eng_trace_p45.py world seed ticks out.json entity_id
Per tick: hp, hunger, sleep debt, position, movement mode, task (action, reason, target), current project (id, kind, status, cleared_since, objective kind/target/target_position), present_threat_to + terms,
retreat_outcome of a current COMBAT_RETREAT project (when the module has it), whether a tactical decision ran this tick (evaluate_entity_intent called) and which scheduler wake predicates held, the helper
that returned a non-None update in that decision and its return (action/reason/nav). Events: every hit (new last_hit_tick): tick, attacker id/kind/group, hp before/after; every change of the project set
(all projects with kind/status/objectives); has_project_capacity refusals (best_candidate kind); the whole-run list of 45's wake predicates."""
import collections, json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out, EID = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
from src.engine.checkpoint import CanonicalStateHasher
from src.ai.goals.present_threat import present_threat_to
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_threat import present_threat_terms
from src.engine.cadence import should_run
from src.engine.need_wake import NEED_WAKE_CADENCE
from src.engine.scheduler import DeterministicScheduler, ADJACENCY_WAKE_COOLDOWN
from src.engine.candidate_selector import MovementCandidateSelector
import src.engine.tactical as _tac
import src.systems.strategic_systems.intelligence as _intel
try:
    from src.systems.strategic_systems.entity_target_objective import retreat_outcome
except Exception:
    retreat_outcome = None
from tools.test_architecture.rpg_gate_run import build_kernel

_cur = [0]
DEC = {}; HELP = collections.defaultdict(list); CAP = []
def wrap(name):
    orig = getattr(_tac, name, None)
    if orig is None: return
    def f(*a, **kw):
        r = orig(*a, **kw)
        ent = next((x for x in a if hasattr(x, "id") and hasattr(x, "biological")), None)
        if ent is not None and ent.id == EID:
            HELP[_cur[0]].append((name, r is not None and r is not False and not (isinstance(r, list) and not r)))
        return r
    setattr(_tac, name, f)
for n in ("avoid_what_can_eat_me", "in_place_survival_update", "pursue_objective", "safety_retreat_warranted"): wrap(n)
_oe = _tac.TacticalDecisionSystem.evaluate_entity_intent
def _eval(state, entity, *a, **kw):
    r = _oe(state, entity, *a, **kw)
    if entity.id == EID:
        t = state.tick; wk = entity.task.work_kind; labels = []
        if should_run(t, entity.id, NEED_WAKE_CADENCE): labels.append("cadence_slot")
        try:
            if (t + entity.id) % ADJACENCY_WAKE_COOLDOWN == 0 and not (wk == "ENTITY_ACT" and entity.task.payload) and MovementCandidateSelector.unengaged_adjacent_hostile(entity, state.entities): labels.append("adjacency_wake")
            if DeterministicScheduler._is_need_woken(entity, state, wk): labels.append("need_wake")
        except Exception: labels.append("probe_err")
        pl = (r.task.payload_set if r.task is not None else None) or {}
        DEC[_cur[0]] = {"wake": "+".join(labels) or "other", "ret_action": pl.get("action"), "ret_reason": pl.get("reason"),
                        "ret_nav": list(r.navigation.target_set) if (r.navigation is not None and r.navigation.target_set is not None) else None,
                        "ret_strategic": None if r.strategic is None else {"set_proj": r.strategic.current_project_id_set, "n_proj_upd": len(r.strategic.projects_add_or_update or [])},
                        "helpers": [list(x) for x in HELP.get(_cur[0], [])]}
    return r
_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)
_ocap = _intel.has_project_capacity
def _capf(projects, max_active, *a, **kw):
    r = _ocap(projects, max_active, *a, **kw)
    if not r:
        fr = sys._getframe(1)
        if fr.f_code.co_filename.endswith("intelligence.py"):
            ent = fr.f_locals.get("entity")
            if ent is not None and ent.id == EID and "best_candidate" in fr.f_locals:
                bc = fr.f_locals["best_candidate"]; CAP.append({"t": _cur[0], "best": str(getattr(bc.kind, "value", bc.kind))})
    return r
_intel.has_project_capacity = _capf

rid = f"p45_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
kind_of = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values()}
ROWS = []; HITS = []; PROJ = []; prev_hit = None; prev_hp = None; prev_proj_sig = None; first_wound = None
for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    e = st.entities.get(EID)
    if e is None: break
    if not e.combat.alive:
        ROWS.append({"t": t, "dead": True}); break
    pl = e.task.payload or {}
    cp = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
    ob = None
    if cp is not None:
        o = next((x for x in cp.objectives if x.id == e.strategic.current_objective_id), None)
        ob = None if o is None else [str(getattr(o.kind, "value", o.kind)), o.target, o.target_entity_id, list(o.target_position) if o.target_position else None]
    try:
        hs = perceived_hostiles(e, st); pt = present_threat_to(e, st); terms = [x.name for x in present_threat_terms(e, hs)] if hs else []
    except Exception: hs, pt, terms = [], None, ["err"]
    ro = None
    if retreat_outcome is not None and cp is not None and str(getattr(cp.kind, "value", cp.kind)).lower() == "combat_retreat":
        try:
            o = next((x for x in cp.objectives if x.id == e.strategic.current_objective_id), None)
            r_ = retreat_outcome(e, st, cp, o) if o is not None else None
            ro = None if r_ is None else [str(r_.objective), str(r_.project)]
        except Exception as ex: ro = ["err", type(ex).__name__]
    ROWS.append({"t": t, "hp": e.combat.hp, "hunger": round(e.biological.hunger, 1), "debt": round(e.biological.sleep_debt, 1), "pos": list(e.navigation.position), "mode": str(e.navigation.movement_mode).replace("MovementMode.", ""),
                 "task": [pl.get("action"), pl.get("reason"), pl.get("target_id")], "proj": None if cp is None else [cp.id, str(getattr(cp.kind, "value", cp.kind)), str(getattr(cp.status, "value", cp.status)), getattr(cp, "cleared_since", None)], "obj": ob,
                 "present_threat": pt, "terms": terms, "hostiles": [h.id for h in hs], "retreat_outcome": ro, "dec": DEC.get(t - 1) or DEC.get(t)})
    lh = e.combat.last_hit_tick
    if lh is not None and lh != prev_hit:
        a = st.entities.get(e.combat.last_attacker_id)
        HITS.append({"hit_tick": lh, "seen_at": t, "attacker": e.combat.last_attacker_id, "attacker_kind": kind_of.get(e.combat.last_attacker_id), "attacker_group": None if a is None else a.identity.group_id, "hp_before": prev_hp, "hp_after": e.combat.hp})
        if first_wound is None: first_wound = lh
    prev_hit = lh; prev_hp = e.combat.hp
    sig = tuple(sorted((p.id, str(getattr(p.status, "value", p.status))) for p in e.strategic.projects.values())) + (e.strategic.current_project_id,)
    if sig != prev_proj_sig:
        PROJ.append({"t": t, "current": e.strategic.current_project_id, "projects": [{"id": p.id, "kind": str(getattr(p.kind, "value", p.kind)), "status": str(getattr(p.status, "value", p.status)), "cleared_since": getattr(p, "cleared_since", None),
                      "objectives": [[str(getattr(o.kind, "value", o.kind)), o.target, o.target_entity_id, list(o.target_position) if o.target_position else None, str(getattr(o.status, "value", o.status))] for o in p.objectives]} for p in e.strategic.projects.values()]})
        prev_proj_sig = sig
doc = {"world": world, "seed": seed, "ticks": ticks, "entity": EID, "hash": CanonicalStateHasher.get_hash(k.state), "first_wound": first_wound, "hits": HITS, "project_changes": PROJ, "cap_refusals": CAP, "rows": ROWS}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
