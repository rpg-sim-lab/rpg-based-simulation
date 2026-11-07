"""Read-only: hits on persons and the gap to the subject's next tactical decision (wrappers record only). Works on both arm trees.
Usage (cwd = tree root, PYTHONPATH=.): probe_gap.py world seed ticks out.json
For every person (keeps_coin): each hit (a new last_hit_tick with an attacker) -> hit tick, hp before, the first evaluate_entity_intent call at a LATER tick (the call in the hit's own tick runs before the hit applies),
the gap in ticks, hp lost between the hit and that decision, and which wake condition held at that decision (cadence slot / adjacency wake / need wake / none of these = other), computed with the scheduler's own predicates."""
import collections, json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.serves import keeps_coin
from src.engine.cadence import should_run
from src.engine.need_wake import NEED_WAKE_CADENCE
from src.engine.scheduler import DeterministicScheduler, ADJACENCY_WAKE_COOLDOWN
from src.engine.candidate_selector import MovementCandidateSelector
import src.engine.tactical as _tac
from tools.test_architecture.rpg_gate_run import build_kernel

DEC = collections.defaultdict(dict)    # eid -> {tick: wake_label}
_cur = [0]
_orig = _tac.TacticalDecisionSystem.evaluate_entity_intent
PERSONS = set()
def _eval(state, entity, *a, **kw):
    if entity.id in PERSONS:
        t = state.tick; wk = entity.task.work_kind
        labels = []
        if should_run(t, entity.id, NEED_WAKE_CADENCE): labels.append("cadence_slot")
        try:
            if (t + entity.id) % ADJACENCY_WAKE_COOLDOWN == 0 and not (wk == "ENTITY_ACT" and entity.task.payload) and MovementCandidateSelector.unengaged_adjacent_hostile(entity, state.entities):
                labels.append("adjacency_wake")
            if DeterministicScheduler._is_need_woken(entity, state, wk): labels.append("need_wake")
        except Exception:
            labels.append("probe_err")
        DEC[entity.id][t] = "+".join(labels) if labels else "other"
    return _orig(state, entity, *a, **kw)
_tac.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(_eval)

rid = f"gap_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
kind_of = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values()}
PERSONS.update(e.id for e in k.state.entities.values() if keeps_coin(e))
HP = collections.defaultdict(dict); hits = []; prev_hit = {}; prev_hp = {}
for _ in range(ticks):
    k.tick_once(); st = k.state; t = st.tick
    for eid in PERSONS:
        e = st.entities.get(eid)
        if e is None: continue
        HP[eid][t] = (e.combat.hp, e.combat.alive)
        lh = e.combat.last_hit_tick
        if lh is not None and lh != prev_hit.get(eid) and e.combat.last_attacker_id is not None:
            hits.append({"eid": eid, "kind": kind_of.get(eid), "hit_tick": lh, "seen_at": t, "attacker": e.combat.last_attacker_id, "hp_before": prev_hp.get(eid, e.combat.hp)})
        prev_hit[eid] = lh; prev_hp[eid] = e.combat.hp
rows = []
for h in hits:
    eid = h["eid"]; later = sorted(d for d in DEC[eid] if d > h["hit_tick"])
    d = later[0] if later else None
    hp_at = None
    if d is not None and d in HP[eid]: hp_at = HP[eid][d][0]
    died_before = None
    for tt in range(h["hit_tick"] + 1, (d if d is not None else ticks) + 1):
        if tt in HP[eid] and not HP[eid][tt][1]: died_before = tt; break
    rows.append({**h, "next_decision_tick": d, "gap": None if d is None else d - h["hit_tick"], "wake_at_next": None if d is None else DEC[eid][d],
                 "hp_lost_in_gap": None if hp_at is None else h["hp_before"] - hp_at, "died_before_next_decision_tick": died_before})
gaps = [r["gap"] for r in rows if r["gap"] is not None]
dist = collections.Counter(("1-2" if g <= 2 else "3-5" if g <= 5 else "6-10" if g <= 10 else ">10") for g in gaps)
wake = collections.Counter(r["wake_at_next"] for r in rows if r["gap"] is not None and r["gap"] > 2)
byk = collections.Counter(r["kind"] for r in rows if r["gap"] is None or r["gap"] > 2)
doc = {"world": world, "seed": seed, "ticks": ticks, "hash": CanonicalStateHasher.get_hash(k.state), "hits_on_persons": len(rows), "gap_distribution": dict(dist),
       "wake_ending_gaps_over_2": dict(wake), "hits_with_gap_over_2_by_kind": dict(byk), "no_later_decision": sum(1 for r in rows if r["gap"] is None),
       "hp_lost_in_gap_over_2_total": sum(r["hp_lost_in_gap"] or 0 for r in rows if (r["gap"] or 0) > 2), "hp_lost_in_gap_le_2_total": sum(r["hp_lost_in_gap"] or 0 for r in rows if r["gap"] is not None and r["gap"] <= 2),
       "died_before_next_decision": sum(1 for r in rows if r["died_before_next_decision_tick"] is not None), "rows": rows}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
