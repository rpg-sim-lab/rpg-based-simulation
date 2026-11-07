"""Read-only probe A (wild_creature collapses) and B (people's starving share). Works on both arm trees; wrappers only record, results are never changed.
Usage (cwd = tree root, PYTHONPATH=.): probe_ab.py world seed ticks out.json

A: for wild_creature: per collapse the prior 200 ticks of the sleep-debt path (ticks with a pressing debt, ticks a perceived hostile made a present threat (`in_danger`) and by which
AGENCY-07 term, whether that hostile acted on the subject, whether the hostile was on the gate-wait condition itself (hostiles in sight, need pressing, none acting, no need project, no-op result)),
forage availability and what a creature does when both needs press.
B: for worker/blacksmith/guard/raider: at each starving-line tick (hunger >= HUNGER_LINE): what it was doing, whether a way was open (`ways_in_reach`), gold, distance to the inn, hostile in view,
time already starving, pressing->first-meal durations and the never-eat share; income: positive gold deltas, WORK ticks, corpses created, deaths by kind."""
import collections, json, os, shutil, sys
from pathlib import Path

world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing, HUNGER_LINE, SLEEP_LINE, ESCALATION_ONSET
from src.engine.sleep_debt import COLLAPSE_FLAG
from src.engine.serves import keeps_coin
from src.ai.goals.scorers_support import perceived_hostiles
from src.ai.goals.ways import ways_in_reach, inn_in_reach
from src.ai.goals.opening_steps import _forage_step
from src.engine.tactical_threat import hostile_acts_on, present_threat_terms
from src.core.state import EntityState
import src.engine.tactical as _tac
from tools.test_architecture.rpg_gate_run import build_kernel

WAITSET = set()        # (tick, eid): the gate-wait condition held for this subject at its tactical decision (same definition as eng_trace_v2)
_cur = [0]
_orig_eval = _tac.TacticalDecisionSystem.evaluate_entity_intent
try:
    from src.engine.tactical_rest import eat_carried_update  # noqa: F401  (import check only)
except Exception:
    pass
_hood = {}
_orig_cls = _tac.classify_neighbours


def _cls(entity, neighbors, src, *a, **kw):
    hood = _orig_cls(entity, neighbors, src, *a, **kw)
    _hood[entity.id] = len(hood.hostiles)
    return hood


_tac.classify_neighbours = _cls


def _eval(state, entity, *a, **kw):
    _hood.pop(entity.id, None)
    r = _orig_eval(state, entity, *a, **kw)
    if _hood.get(entity.id) and need_is_pressing(entity.biological.hunger, entity.biological.sleep_debt):
        hs = perceived_hostiles(entity, state)
        if hs and not any(hostile_acts_on(h, entity, state.tick) for h in hs):
            project = entity.strategic.projects.get(entity.strategic.current_project_id) if entity.strategic.current_project_id else None
            serves = project is not None and str(getattr(project.status, "value", project.status)).upper() == "ACTIVE" and str(getattr(project.kind, "value", project.kind)).lower() in ("hunger", "fatigue")
            noop = r.task is None and r.navigation is None and r.strategic is None and getattr(r, "interaction", None) is None
            if not serves and noop:
                WAITSET.add((_cur[0], entity.id))
    return r


_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

rid = f"ab_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
kind_of = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values()}
PEOPLE = {"worker", "blacksmith", "guard", "raider"}
persons = {e.id for e in k.state.entities.values() if keeps_coin(e)}
DEBT_ON = ESCALATION_ONSET * SLEEP_LINE
HUN_ON = ESCALATION_ONSET * HUNGER_LINE

# ---- A ----
win = collections.defaultdict(collections.deque)           # wild eid -> last 200 rows (t, pressing_debt, in_danger, terms, any_acting, any_hostile_on_wait, my_action)
collapses_A = []
cprev = {}
A_forage = collections.Counter()
A_both = collections.Counter()                              # when hunger and debt both press: what the creature does
A_actions = collections.Counter()
A_node_samples = []
# ---- B ----
B = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))   # kind -> metric -> counter
first_starve = {}; press_start = {}; ep_durations = collections.defaultdict(list); ep_open = {}
meal_prev = {}; gold_prev = {}
income = collections.defaultdict(collections.Counter)
corpse_seen = set(); deaths_by = collections.Counter(); dead_seen = set()
subj_starve = collections.defaultdict(int)

for _ in range(ticks):
    _cur[0] = k.state.tick
    k.tick_once(); st = k.state; t = st.tick
    if t % 20 == 0:
        A_node_samples.append(sum(1 for n in st.resource_nodes.values() if n.remaining_charges > 0 and n.cooldown_remaining <= 0 and n.yields_item))
    for cid in st.corpses:
        if cid not in corpse_seen:
            corpse_seen.add(cid); income["world"]["corpses_created"] += 1
    for eid, e in st.entities.items():
        kk = kind_of.get(eid)
        if not e.combat.alive:
            if eid not in dead_seen:
                dead_seen.add(eid); deaths_by[f"{kk}|{str(getattr(e.lifecycle,'death_reason',None))}"] += 1
                if eid in ep_open:
                    ep_durations[kk].append(("never", t - ep_open.pop(eid)))
            continue
        if not e.lifecycle.active:
            continue
        pl = e.task.payload or {}
        hunger, debt = e.biological.hunger, e.biological.sleep_debt
        lm = e.biological.last_meal_tick
        ate = lm is not None and lm != meal_prev.get(eid, lm)
        meal_prev[eid] = lm
        if kk in PEOPLE:
            gold = e.inventory.gold
            if eid in gold_prev and gold > gold_prev[eid]:
                income[kk]["gold_gain_events"] += 1; income[kk]["gold_gained"] += gold - gold_prev[eid]
            gold_prev[eid] = gold
            if pl.get("action") == "WORK":
                income[kk]["work_ticks"] += 1
            if hunger >= HUN_ON and eid not in ep_open:
                ep_open[eid] = t
            if ate and eid in ep_open:
                ep_durations[kk].append(("ate", t - ep_open.pop(eid)))
            if hunger < HUN_ON * 0.5 and eid in ep_open:
                ep_open.pop(eid)
            if hunger >= HUNGER_LINE:
                if eid not in first_starve: first_starve[eid] = t
                age = t - first_starve[eid]
                bucket = "<100" if age < 100 else "<500" if age < 500 else "<1000" if age < 1000 else ">=1000"
                b = B[kk]
                b["n_ticks"]["starving"] += 1; b["age_bucket"][bucket] += 1
                b["action_reason"][f"{pl.get('action')}|{pl.get('reason')}"] += 1
                cp = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
                pk = str(getattr(cp.kind, "value", cp.kind)).lower() if cp is not None else "none"
                b["project_kind"][pk] += 1
                if cp is not None and pk in ("hunger", "fatigue"):
                    ob = next((o for o in cp.objectives if o.id == e.strategic.current_objective_id), None)
                    b["need_objective"][("living_target" if (ob is not None and ob.target_entity_id is not None) else "place_or_other")] += 1
                try:
                    ways = tuple(sorted(w.value for w in ways_in_reach(e, st)))
                except Exception:
                    ways = ("ERR",)
                b["ways"]["+".join(ways) if ways else "NO_WAY"] += 1
                inn = inn_in_reach(e, st)
                b["inn_in_reach"]["yes" if inn is not None else "no"] += 1
                if inn is not None:
                    d = abs(inn.position[0] - e.navigation.position[0]) + abs(inn.position[1] - e.navigation.position[1])
                    b["inn_dist"]["<=5" if d <= 5 else "<=20" if d <= 20 else ">20"] += 1
                b["gold"]["0" if e.inventory.gold <= 0 else "<10" if e.inventory.gold < 10 else ">=10"] += 1
                hs = perceived_hostiles(e, st)
                b["hostile_in_view"]["yes" if hs else "no"] += 1
                if (t, eid) in WAITSET: b["gate_wait"]["yes"] += 1
                subj_starve[eid] += 1
        if kk == "wild_creature":
            pd = debt >= DEBT_ON
            ph = hunger >= HUN_ON
            hs = perceived_hostiles(e, st) if (pd or ph) else []
            terms = [x.name for x in present_threat_terms(e, hs)] if hs else []
            acting = any(hostile_acts_on(h, e, t) for h in hs) if hs else False
            hw = any((t, h.id) in WAITSET or (t - 1, h.id) in WAITSET for h in hs) if hs else False
            win[eid].append((t, pd, bool(terms), tuple(terms), acting, hw, pl.get("action")))
            if len(win[eid]) > 200: win[eid].popleft()
            if pd and ph:
                A_both[f"{pl.get('action')}|{pl.get('reason')}"] += 1
            if ph:
                try: A_forage["forage_open" if _forage_step(e, st).available else "forage_closed"] += 1
                except Exception: A_forage["err"] += 1
            if pd: A_actions[f"{pl.get('action')}|{pl.get('reason')}"] += 1
            c = bool(pl.get(COLLAPSE_FLAG))
            if c and not cprev.get(eid):
                rows = list(win[eid])
                pdt = [r_ for r_ in rows if r_[1]]
                collapses_A.append({"t": t, "eid": eid, "debt": round(debt, 1), "hunger": round(hunger, 1),
                                    "window_ticks": len(rows), "pressing_debt_ticks": len(pdt),
                                    "in_danger_ticks_while_pressing": sum(1 for r_ in pdt if r_[2]),
                                    "term_ticks": dict(collections.Counter(x for r_ in pdt for x in r_[3])),
                                    "hostile_acting_ticks": sum(1 for r_ in pdt if r_[2] and r_[4]),
                                    "hostile_on_gate_wait_ticks": sum(1 for r_ in pdt if r_[2] and r_[5]),
                                    "my_actions_while_pressing": dict(collections.Counter(r_[6] for r_ in pdt))})
            cprev[eid] = c

# open episodes at end -> never ate
for eid, t0 in ep_open.items():
    ep_durations[kind_of.get(eid)].append(("never_by_end", ticks - t0))
h = CanonicalStateHasher.get_hash(k.state)
by_subject_starve = collections.defaultdict(list)
for eid, n in subj_starve.items(): by_subject_starve[kind_of.get(eid)].append(n)
doc = {"world": world, "seed": seed, "ticks": ticks, "hash": h,
       "A": {"collapses": collapses_A, "forage_when_hunger_pressing": dict(A_forage), "when_both_press": dict(A_both), "actions_while_debt_pressing": dict(A_actions),
             "food_nodes_available_sampled_every_20t": {"n": len(A_node_samples), "mean": round(sum(A_node_samples) / max(1, len(A_node_samples)), 2), "min": min(A_node_samples or [0]), "max": max(A_node_samples or [0])}},
       "B": {kk: {m: dict(c) for m, c in v.items()} for kk, v in B.items()},
       "B_episodes": {kk: {"ate": [d for s, d in v if s == "ate"], "never": [d for s, d in v if s != "ate"]} for kk, v in ep_durations.items()},
       "B_subject_starving_ticks": {kk: sorted(v, reverse=True) for kk, v in by_subject_starve.items()},
       "income": {kk: dict(c) for kk, c in income.items()}, "deaths_by": dict(deaths_by)}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
