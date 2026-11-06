"""[v2: adds the WAIT / NO_EAT stall measure for the conforming head; new arm only] Phase 1 probe for TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED (read-only; wrappers only record, they never change a result).

Usage (cwd = tree root, PYTHONPATH=.):  eng_probe.py world seed ticks out.json [--plain]
  --plain : run the same kernel with NO wrappers and write only the final hash (the unprobed run the probe hash is compared with).

Family tags per (tick, subject), one SURV-07 test for all of them: PRESSING = need_is_pressing(hunger, sleep_debt); PRESENT_THREAT = a perceived hostile one
tile away (decision 32) OR acting_threat_to. A tick is counted once in `any`; every tag it falls under is recorded (overlap matrix).
Tags: ENGAGEMENT_OVERRIDES, LOW_HP_RETREAT (PANIC_RETREAT reason, lane B's definition), LHR_HOLD (AVOID_NO_ROUTE hold = NO_RETREAT_DESTINATION),
LHR_CARRY_WALK (a REGROUP walk by a subject under attack at low hp), TOWN_RETURN, ESCALATED_NEED_SWITCH, FLEE_LINE, CAP_REFUSAL.
The skip counter wraps TacticalDecisionSystem.evaluate_entity_intent with its real signature (state, entity, ...): lane B's wrapper read entity=a[0], state=a[1],
so present_threat() raised before the counter was incremented and it recorded 0 skips.
"""
import collections, json, os, shutil, sys
from pathlib import Path

world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
PLAIN = "--plain" in sys.argv
from src.engine.checkpoint import CanonicalStateHasher
from tools.test_architecture.rpg_gate_run import build_kernel

rid = f"eng_{world}_{seed}_{os.getpid()}"
if PLAIN:
    k = build_kernel(world, seed, rid)
    for _ in range(ticks):
        k.tick_once()
    h = CanonicalStateHasher.get_hash(k.state)
    k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
    Path(out).write_text(json.dumps({"world": world, "seed": seed, "ticks": ticks, "hash": h}), encoding="utf-8")
    sys.exit(0)

from src.ai.goals import escalated_need_wins
from src.ai.goals.present_threat import acting_threat_to
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.need_pull import need_is_pressing, HUNGER_LINE, SLEEP_LINE
from src.engine.serves import keeps_coin
from src.engine.sleep_debt import COLLAPSE_FLAG
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_destinations import containing_region, _clamp_into
from src.engine.cognition import AppraisalSystem, SensoryFilter
from src.engine.domain_logic import SimulationDomainLogic
import src.engine.tactical as _tac
import src.engine.tactical_objective as _tobj
import src.engine.building_arrival as _barr
from src.engine.tactical_rest import eat_carried_update, in_danger
from src.engine.tactical_threat import hostile_acts_on
import src.systems.strategic_systems.intelligence as _intel

_EV = collections.defaultdict(set)      # (tick, eid) -> tags recorded by the wrappers during tick_once
_SKIP = collections.Counter()           # hostiles-present evaluate calls, by (pressing, adjacent, acting)
_SKIP_SUBJ = collections.defaultdict(set)
_CAP = []                               # (tick, eid, suspended_count)
_cur = [0]
_last_hood = {}
_last_hostiles = {}
_WAIT = collections.defaultdict(list)    # reason -> [(tick, eid)]
collapse_ticks = collections.defaultdict(list)
_orig_cls = _tac.classify_neighbours


def _cls(entity, neighbors, src, *a, **kw):
    hood = _orig_cls(entity, neighbors, src, *a, **kw)
    _last_hood[entity.id] = len(hood.hostiles)
    _last_hostiles[entity.id] = list(hood.hostiles)
    return hood


_tac.classify_neighbours = _cls
_orig_eval = _tac.TacticalDecisionSystem.evaluate_entity_intent


def man1(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def threat_split(e, st):
    """(adjacent hostile, acting hostile): the two halves of the present-threat test."""
    adj = any(man1(h.navigation.position, e.navigation.position) <= 1 for h in perceived_hostiles(e, st))
    return adj, bool(acting_threat_to(e, st))


def _eval(state, entity, *a, **kw):
    _last_hood.pop(entity.id, None)
    _SKIP[("evaluate_calls",)] += 1
    r = _orig_eval(state, entity, *a, **kw)
    n = _last_hood.get(entity.id)
    if n:   # reached the hostiles computation with hostiles present: the `if not hostiles:` arrival/pursuit block is skipped for this call
        pr = need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt)
        adj, act = threat_split(entity, state)
        _SKIP[(pr, adj, act)] += 1
        if pr:
            _SKIP_SUBJ[(pr, adj, act)].add(entity.id)
        if pr and not (adj or act):
            _EV[(_cur[0], entity.id)].add("SKIP_SITE")
        hs = _last_hostiles.get(entity.id) or []
        if hs and pr and not any(hostile_acts_on(h, entity, state.tick) for h in hs):      # the pressing-need path (need_first) was taken for this call
            project = entity.strategic.projects.get(entity.strategic.current_project_id) if entity.strategic.current_project_id else None
            serves = project is not None and str(getattr(project.status, "value", project.status)).upper() == "ACTIVE" and str(getattr(project.kind, "value", project.kind)).lower() in ("hunger", "fatigue")
            noop = r.task is None and r.navigation is None and r.strategic is None and getattr(r, "interaction", None) is None
            if not serves and noop:
                _WAIT["WAIT_NO_NEED_PROJECT"].append((_cur[0], entity.id))
            if eat_carried_update(entity, []) is not None and in_danger(entity, hs):
                _WAIT["NO_EAT_IN_PLACE"].append((_cur[0], entity.id))
    return r


_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

_orig_fw = _tobj._fatigue_arrival_waits
def _fw(state, entity, obj, resolve, hostiles):
    r = _orig_fw(state, entity, obj, resolve, hostiles)
    if r: _WAIT["WAIT_FATIGUE_ARRIVAL"].append((_cur[0], entity.id))
    return r
_tobj._fatigue_arrival_waits = _fw
_orig_hw = _barr.held_work_is_threatened
def _hw(entity, state, *a, **kw):
    r = _orig_hw(entity, state, *a, **kw)
    if r: _WAIT["WAIT_HELD_WORK"].append((_cur[0], entity.id))
    return r
_barr.held_work_is_threatened = _hw

_orig_switch = _intel.StrategicIntelligenceSystem.evaluate_project_switch


def _switch(entity, candidate_project, current_tick, state=None):
    r = _orig_switch(entity, candidate_project, current_tick, state=state)
    if r is None and escalated_need_wins(entity, candidate_project.kind):
        _EV[(_cur[0], entity.id)].add("ESCALATED_NEED_SWITCH")
    return r


_intel.StrategicIntelligenceSystem.evaluate_project_switch = staticmethod(_switch)
_orig_cap = _intel.has_project_capacity


def _capf(projects, max_active, *a, **kw):
    r = _orig_cap(projects, max_active, *a, **kw)
    if not r:
        fr = sys._getframe(1)
        if fr.f_code.co_filename.endswith("intelligence.py"):
            ent = fr.f_locals.get("entity")
            if ent is not None and "best_candidate" in fr.f_locals:   # the capacity gate that refuses the best candidate (intelligence.py:1768)
                n_susp = sum(1 for p in projects.values() if getattr(p.status, "value", p.status) == "SUSPENDED")
                _EV[(_cur[0], ent.id)].add("CAP_REFUSAL"); _CAP.append((_cur[0], ent.id, n_susp))
    return r


_intel.has_project_capacity = _capf

# CARRY by writer: who wrote a REGROUP walk. Record-only: the writer line in intelligence.py (town-carry branches) vs any other writer.
import src.core.updates as _upd
from src.core.movement_modes import MovementMode as _MM
_REG_WRITES = collections.Counter(); _REG_SUBJ = collections.defaultdict(set)
_orig_nav_init = _upd.NavigationUpdate.__init__


def _nav_init(self, *a, **kw):
    _orig_nav_init(self, *a, **kw)
    try:
        if getattr(self, "movement_mode_set", None) == _MM.REGROUP:
            f = sys._getframe(1)
            while f is not None and "/src/" not in f.f_code.co_filename or (f is not None and f.f_code.co_filename.endswith(("src/core/updates.py", "src/core/update_models/navigation.py"))):
                f = f.f_back
            if f is not None:
                key = f"{f.f_code.co_filename.split('/src/')[-1]}:{f.f_lineno}"
                eid_ = f.f_locals.get("e_id")
                if eid_ is None and f.f_locals.get("entity") is not None: eid_ = f.f_locals["entity"].id
                _REG_WRITES[key] += 1; _REG_SUBJ[key].add(eid_)
    except Exception:
        pass


_upd.NavigationUpdate.__init__ = _nav_init

k = build_kernel(world, seed, rid)
persons = {e.id for e in k.state.entities.values() if keeps_coin(e)}
kind_of = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values()}
tag_ticks = collections.Counter(); tag_subj = collections.defaultdict(set); tag_run = {}; tag_longest = collections.Counter()
overlap = collections.Counter(); any_ticks = 0
subj = {}            # eid -> per-subject record
role_ticks = collections.Counter()   # ENG ticks by role (leader/follower/none)
eng_followers = collections.defaultdict(int)
lhr_hold_rows = []   # per AVOID_NO_ROUTE hold tick (first tick of a run): region facts
lhr_hold_open = {}
carry = collections.Counter(); carry_subj = set()
collapse_prev = {}
regions = list(k.state.regions.values())


def rec(eid):
    return subj.setdefault(eid, {"person": eid in persons, "kind": kind_of.get(eid), "tags": set(), "starving_ticks": 0, "debt98_ticks": 0,
                                 "death": None, "collapses": 0, "eng_ticks": 0, "eng_follower_ticks": 0})


def region_facts(st, e, hostiles):
    here = e.navigation.position
    reg = containing_region(st, here)
    home = st.regions.get(e.strategic.home_region_id) if e.strategic.home_region_id else None
    bd = None
    for rg in regions:
        c = _clamp_into(rg, (float(here[0]), float(here[1])))
        d = abs(c[0] - here[0]) + abs(c[1] - here[1])
        bd = d if bd is None else min(bd, d)
    towns = [b for b in st.buildings.values() if getattr(b, "functional", True)]
    nb = min(towns, key=lambda b: man1(b.position, here)) if towns else None
    side = None
    if nb is not None and hostiles:
        hx = sum(h.navigation.position[0] for h in hostiles) / len(hostiles); hy = sum(h.navigation.position[1] for h in hostiles) / len(hostiles)
        side = "behind_threat" if man1(nb.position, (hx, hy)) < man1(here, (hx, hy)) else "away_from_threat"
    return {"in_region": reg is not None, "has_home": home is not None, "dist_region_boundary": bd,
            "dist_nearest_building": man1(nb.position, here) if nb is not None else None, "building_side": side}


last_pk_run = {}
KIND_ACC = collections.defaultdict(collections.Counter); last_meal_seen = {}
for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    for eid, e in st.entities.items():
        if eid not in subj and not (e.combat.alive and e.lifecycle.active):
            continue
        r = subj.get(eid)
        if not e.combat.alive:
            if r is not None and r["death"] is None:
                r["death"] = [t, str(getattr(e.lifecycle, "death_reason", None))]
            continue
        if not e.lifecycle.active:
            continue
        ev = _EV.pop((_cur[0], eid), set())
        pl = e.task.payload or {}
        act = pl.get("action")
        cpj = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
        pk = str(getattr(cpj.kind, "value", cpj.kind)).lower() if cpj is not None else None
        hunger, debt = e.biological.hunger, e.biological.sleep_debt
        pr = need_is_pressing(hunger, debt)
        kk = kind_of.get(eid)
        KIND_ACC[kk]["alive_ticks"] += 1
        if hunger >= HUNGER_LINE: KIND_ACC[kk]["starving_ticks"] += 1
        if pr: KIND_ACC[kk]["pressing_ticks"] += 1
        lm = e.biological.last_meal_tick
        if lm is not None and lm != last_meal_seen.get(eid, lm) : KIND_ACC[kk]["meals"] += 1
        last_meal_seen[eid] = lm
        tags = set(ev) - {"SKIP_SITE"}
        if hunger >= HUNGER_LINE or debt >= SLEEP_LINE or act == "ATTACK" or pr or tags:
            rr = rec(eid)
            if hunger >= HUNGER_LINE: rr["starving_ticks"] += 1
            if debt >= SLEEP_LINE: rr["debt98_ticks"] += 1
        c = bool(pl.get(COLLAPSE_FLAG))
        if c and not collapse_prev.get(eid):
            KIND_ACC[kind_of.get(eid)]["collapses"] += 1
            rec(eid)["collapses"] += 1
            collapse_ticks[eid].append(t)
        collapse_prev[eid] = c
        if pr or act == "ATTACK" or pl.get("reason") == "AVOID_NO_ROUTE" or e.navigation.movement_mode.name == "REGROUP":
            adj, acting = threat_split(e, st)
            pt = adj or acting
            if pr and not pt and (act == "ATTACK" or pk == "combat_engage" or "SKIP_SITE" in ev):
                tags.add("ENGAGEMENT_OVERRIDES")
            if pr and not pt and pl.get("reason") == "PANIC_RETREAT":
                tags.add("LOW_HP_RETREAT")
            if pr and pk == "town_return":
                tags.add("TOWN_RETURN")
            if pl.get("reason") == "AVOID_NO_ROUTE" and pr:   # NO_RETREAT_DESTINATION hold under a pressing need
                tags.add("LHR_HOLD")
                if eid not in lhr_hold_open or lhr_hold_open[eid] != t - 1:
                    hs = perceived_hostiles(e, st)
                    row = region_facts(st, e, hs); row.update({"tick": t, "eid": eid, "adjacent": adj, "acting": acting})
                    lhr_hold_rows.append(row)
                lhr_hold_open[eid] = t
            hp_ratio = e.combat.hp / max(1, e.combat.max_hp)
            if e.navigation.movement_mode.name == "REGROUP" and acting and hp_ratio < 0.5:
                tags.add("LHR_CARRY_WALK"); carry["hp<0.5"] += 1; carry_subj.add(eid)
                if hp_ratio < 0.35: carry["hp<0.35"] += 1
            if act == "ATTACK":
                try:
                    raw = SimulationDomainLogic.get_neighbor_view(st, e, radius=10.0)
                    nb = SensoryFilter.filter_saliency(e, raw, max_targets=5)
                    tr = SimulationDomainLogic.get_region_trauma(st, e.navigation.position)
                    if AppraisalSystem.evaluate_emotional_state(e, nb, region_trauma=tr, social_context=e.social).is_fleeing:
                        tags.add("FLEE_LINE")
                except Exception:
                    pass
            if "ENGAGEMENT_OVERRIDES" in tags:
                g = st.groups.get(e.identity.group_id) if e.identity.group_id is not None else None
                role = "none" if g is None else ("leader" if g.leader_id == eid else "follower")
                role_ticks[role] += 1
                rr = rec(eid); rr["eng_ticks"] += 1
                if role == "follower": rr["eng_follower_ticks"] += 1
        if tags:
            any_ticks += 1
            overlap[tuple(sorted(tags))] += 1
            rr = rec(eid)
            for g_ in tags:
                tag_ticks[g_] += 1; tag_subj[g_].add(eid); rr["tags"].add(g_)
                run = tag_run.get((g_, eid))
                tag_run[(g_, eid)] = (t, run[1] + 1 if run and run[0] == t - 1 else 1)
                tag_longest[g_] = max(tag_longest[g_], tag_run[(g_, eid)][1])

h = CanonicalStateHasher.get_hash(k.state)
for eid, r in subj.items():
    r["tags"] = sorted(r["tags"])
    e = k.state.entities.get(eid)
    if r["death"] is None and e is not None and not e.combat.alive:
        r["death"] = [k.state.tick, str(getattr(e.lifecycle, "death_reason", None))]
eng_ids = tag_subj["ENGAGEMENT_OVERRIDES"]

def _stretches(events, gap=12):
    by = collections.defaultdict(list)
    for t_, e_ in events: by[e_].append(t_)
    out = []
    for e_, ts in by.items():
        ts = sorted(set(ts)); start = prev = ts[0]
        for x in ts[1:] + [None]:
            if x is None or x - prev > gap:
                out.append((e_, start, prev)); start = x
            if x is not None: prev = x
    return out
wait_report = {}
for reason in ("WAIT_NO_NEED_PROJECT", "WAIT_FATIGUE_ARRIVAL", "WAIT_HELD_WORK", "NO_EAT_IN_PLACE"):
    st_ = _stretches(_WAIT.get(reason, []))
    caps = 0; dth = 0; col = 0; dth_subj = set(); col_subj = set()
    for e_, a_, b_ in st_:
        caps += sum(1 for (ct, ce, _n) in _CAP if ce == e_ and a_ <= ct <= b_)
        dtick = subj.get(e_, {}).get("death")
        if dtick and 0 <= dtick[0] - a_ <= 200: dth += 1; dth_subj.add(e_)
        if any(0 <= c_ - a_ <= 200 for c_ in collapse_ticks.get(e_, [])): col += 1; col_subj.add(e_)
    wait_report[reason] = {"events": len(_WAIT.get(reason, [])), "subjects": len({e for _, e in _WAIT.get(reason, [])}), "stretches": len(st_),
                           "longest_stretch_ticks": max([b - a + 1 for _, a, b in st_] or [0]), "cap_refusals_inside": caps,
                           "stretches_with_death_within_200": dth, "subjects_dead_within_200": len(dth_subj),
                           "stretches_with_collapse_within_200": col, "subjects_collapsed_within_200": len(col_subj)}
doc = {"world": world, "seed": seed, "ticks": ticks, "hash": h, "persons": len(persons),
       "tag_ticks": dict(tag_ticks), "tag_subjects": {a: len(b) for a, b in tag_subj.items()}, "tag_longest": dict(tag_longest), "any_tag_ticks": any_ticks,
       "overlap": {"+".join(a): b for a, b in overlap.items()},
       "skip_counter": {(k_[0] if len(k_) == 1 else "pressing=%s,adjacent=%s,acting=%s" % k_): v for k_, v in _SKIP.items()},
       "skip_subjects_pressing": {"pressing=%s,adjacent=%s,acting=%s" % k_: len(v) for k_, v in _SKIP_SUBJ.items()},
       "eng_role_ticks": dict(role_ticks),
       "eng_subjects": len(eng_ids), "eng_collapsed_subjects": sum(1 for i in eng_ids if subj[i]["collapses"] > 0),
       "eng_dead_subjects": sum(1 for i in eng_ids if subj[i]["death"]),
       "eng_deaths_by_cause": dict(collections.Counter(subj[i]["death"][1] for i in eng_ids if subj[i]["death"])),
       "cap_refusals": len(_CAP), "cap_suspended_counts": dict(collections.Counter(x[2] for x in _CAP)),
       "regroup_writers": {a: {"writes": b, "subjects": len(_REG_SUBJ[a])} for a, b in _REG_WRITES.items()},
       "wait_report": wait_report,
       "by_kind": {str(a): dict(b) for a, b in KIND_ACC.items()},
       "wait_by_kind": {r_: {str(kd): {"events": sum(1 for _, e_ in _WAIT.get(r_, []) if kind_of.get(e_) == kd), "subjects": len({e_ for _, e_ in _WAIT.get(r_, []) if kind_of.get(e_) == kd})} for kd in {kind_of.get(e_) for _, e_ in _WAIT.get(r_, [])}} for r_ in ("WAIT_NO_NEED_PROJECT", "WAIT_FATIGUE_ARRIVAL", "WAIT_HELD_WORK", "NO_EAT_IN_PLACE")},
       "lhr_carry_walk": {"ticks": dict(carry), "subjects": len(carry_subj)},
       "lhr_hold_rows": lhr_hold_rows[:400], "lhr_hold_row_count": len(lhr_hold_rows),
       "subjects": {str(a): b for a, b in subj.items()}}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
