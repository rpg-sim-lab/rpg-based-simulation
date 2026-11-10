"""Hardening DEFEAT trace, v2 (rpg-implementer-3, DRAFT for rpg-designer approval; NOT run, NOT smoked). Records EVERY PERSON in one pass so the subject set (fix-arm DEFEAT deaths that are not base-arm DEFEAT deaths,
plus scout 17 on s43) can be chosen afterwards from the two arms' files by defeat_rows2.py. Read-only: same build (tools.test_architecture.rpg_gate_run.build_kernel; audit_mode / no_frame_pacing checked)
and tick loop as arm_child; run with the ARM'S tree as cwd and PYTHONPATH. End hash must equal <cell.json>'s final_hash (exit 3 otherwise: the trace then does not count).
  python defeat_trace2.py <world> <seed> <ticks> <cell.json> <out.json>
Spies (each passes its arguments through and returns the original result unchanged):
  A. CombatResolutionSystem.resolve_attack / resolve_multi_attack / resolve_aoe_attack / resolve_skill_usage, outermost call only (as in defeat_trace.py a06a17d0): per call {tick, fn, attackers, defender,
     opp, lethal, res_hp_delta, res_damage_taken, res_outcome_kind, res_attacker_id}. Same-tick identical resolve_attack rows are real second calls whose damage is not applied: the damage of a hit is NEVER summed from here.
  B. TacticalDecisionSystem.evaluate_entity_intent: per decision (person, tick) the staged (work_kind, action, reason, target_id).
  C. NearDeathHardeningPhase.apply (as hard_count.py 3929aa5a; on base trees too): a GRANT = output trace holds NEAR_DEATH_HARDENING and input did not. Row: tick, entity, hp / max_hp BEFORE the grant, projected hp,
     the INPUT update's hp_delta, damage_taken, hazard_damage, attacker_id, hit_tick_set, outcome_kind, max_hp_delta, permanent_max_hp_bonus_delta, tile, in-town flag. Source class (same rule as hard_count): hp_delta<0 and
     (damage_taken>0 or attacker_id) -> hit; hp_delta<0 and hazard_damage>0 -> hazard; hp_delta==1 on a town tile -> town heal; hp_delta==0 -> zero; other >=0 -> other heal. Amount = +5 (the phase's own constant) shown NEXT TO the observed change: the OUTPUT update's permanent_max_hp_bonus_delta / max_hp_delta, and (post-hoc) rows[tick+1].max_hp minus the max_hp before the grant, so a cap or clamp shows.
Per tick, BEFORE the tick, for every PERSON (not wild) including dead ones: [hp, max_hp, alive, work_kind, action, reason, target_id, last_hit_tick, last_attacker_id, lodged, pos].
Output JSON: {meta, final_hash, cell_final_hash, match, rows{tick:{id:[...]}}, decisions{"id|tick":[...]}, grants[...], calls[person defenders only], deaths{id:{kind,cause,tick,last_attacker_id,alive}}}.
No verdict is written. defeat_rows2.py (separate, post-hoc, reads the two arms' output files only) builds the table rows."""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path

def main(argv):
    world, seed, ticks, cell, out = argv[0], int(argv[1]), int(argv[2]), argv[3], argv[4]
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.combat import CombatResolutionSystem as CRS
    from src.engine.hostility import is_wild_creature
    from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase
    from src.engine.tactical import TacticalDecisionSystem
    from tools.rpg_measure.arm_child import _cause
    from tools.test_architecture.rpg_gate_run import build_kernel
    run_id = f"rpgdef2_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced"); return 2
    calls = []; depth = [0]; origs = {}; cur = [0]
    def wrap(name):
        o = CRS.__dict__[name]; fn = o.__func__; origs[name] = o
        def spy(*a, **kw):
            outer = depth[0] == 0
            depth[0] += 1
            try:
                res = fn(*a, **kw)
            finally:
                depth[0] -= 1
            if outer:
                try:
                    st = a[2] if len(a) > 2 else kw.get("state")
                    att = a[0]; dfn = a[1] if len(a) > 1 else kw.get("defender")
                    atts = [x.id for x in att] if isinstance(att, (list, tuple, set)) else [att.id]
                    row = {"tick": (getattr(st, "tick", None) if getattr(st, "tick", None) is not None else cur[0]), "fn": name, "attackers": atts, "defender": getattr(dfn, "id", None),
                           "opp": bool(kw.get("is_opportunity_attack", False)), "lethal": kw.get("is_lethal", True)}
                    for k in ("hp_delta", "damage_taken", "outcome_kind", "attacker_id"):
                        if hasattr(res, k): row["res_" + k] = getattr(res, k)
                    calls.append(row)
                except Exception as ex:  # a logging failure must not change the run
                    calls.append({"fn": name, "log_error": repr(ex)})
            return res
        setattr(CRS, name, staticmethod(spy))
    for n in ("resolve_attack", "resolve_multi_attack", "resolve_aoe_attack", "resolve_skill_usage"):
        if n in CRS.__dict__: wrap(n)
    dec_out = {}
    od = TacticalDecisionSystem.evaluate_entity_intent
    def dspy(st, entity, *a, **kw):
        res = od(st, entity, *a, **kw)
        try:
            tk = getattr(res, "task", None); pl = (getattr(tk, "payload_set", None) or {}) if tk is not None else {}
            dec_out[f"{entity.id}|{st.tick}"] = [None if tk is None else tk.work_kind_set, pl.get("action"), pl.get("reason"), pl.get("target_id")]
        except Exception as ex:  # logging only
            dec_out[f"{entity.id}|{st.tick}"] = ["log_error", repr(ex), None, None]
        return res
    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(dspy)
    grants = []
    oap = NearDeathHardeningPhase.apply
    def gspy(state, update):
        res = oap(state, update)
        try:
            for eid, eu in res.entity_updates.items():
                c = eu.combat
                if c is None or "NEAR_DEATH_HARDENING" not in c.trace: continue
                cin = update.entity_updates[eid].combat if eid in update.entity_updates else None
                if cin is not None and "NEAR_DEATH_HARDENING" in cin.trace: continue
                e = state.entities[eid]; pos = e.navigation.position; tile = (int(pos[0]), int(pos[1]))
                grants.append({"tick": state.tick, "e": eid, "kind": e.kind, "hp": e.combat.hp, "max_hp": e.combat.max_hp, "proj": c.trace.get("NEAR_DEATH_PROJECTED_HP"),
                               "hp_delta": cin.hp_delta, "damage_taken": cin.damage_taken, "hazard_damage": cin.hazard_damage, "attacker_id": cin.attacker_id, "hit_tick_set": cin.hit_tick_set,
                               "outcome": cin.outcome_kind, "max_hp_delta_in": cin.max_hp_delta, "perm_in": cin.permanent_max_hp_bonus_delta, "town_tile": tile in state.town_tiles, "perm_out": c.permanent_max_hp_bonus_delta, "max_hp_delta_out": c.max_hp_delta})
        except Exception as ex:
            grants.append({"log_error": repr(ex), "tick": state.tick})
        return res
    NearDeathHardeningPhase.apply = staticmethod(gspy)
    rows = {}; wild = {}
    try:
        for _ in range(ticks):
            st = kernel.state; r = {}; cur[0] = st.tick
            for e in st.entities.values():
                if e.id not in wild: wild[e.id] = bool(is_wild_creature(e))
                if wild[e.id]: continue
                p = e.task.payload or {}
                r[e.id] = [e.combat.hp, e.combat.max_hp, bool(e.combat.alive), e.task.work_kind, p.get("action"), p.get("reason"), p.get("target_id"),
                           e.combat.last_hit_tick, e.combat.last_attacker_id, e.navigation.lodged_in is not None, list(e.navigation.position)]
            rows[st.tick] = r
            kernel.tick_once()
        state = kernel.state
    finally:
        for n, o in origs.items(): setattr(CRS, n, o)
        TacticalDecisionSystem.evaluate_entity_intent = od
        NearDeathHardeningPhase.apply = oap
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"]
    ok = final_hash == want
    deaths = {}
    for e in state.entities.values():
        if wild.get(e.id, True): continue
        rec = getattr(e.lifecycle, "death_record", None)
        deaths[str(e.id)] = {"kind": e.kind, "alive": bool(e.combat.alive), "cause": None if e.combat.alive else _cause(e),
                             "tick": None if rec is None else rec.tick, "last_attacker_id": None if rec is None else rec.last_attacker_id}
    pcalls = [c for c in calls if str(c.get("defender")) in deaths]
    res = {"meta": {"world": world, "seed": seed, "ticks": ticks, "cwd": os.getcwd()}, "final_hash": final_hash, "cell_final_hash": want, "match": ok,
           "rows": {str(k): {str(i): v for i, v in r.items()} for k, r in rows.items()}, "decisions": {k: v for k, v in dec_out.items() if k.split("|")[0] in deaths},
           "grants": [g for g in grants if str(g.get("e")) in deaths or "log_error" in g], "calls": pcalls, "deaths": deaths}
    Path(out).write_text(json.dumps(res, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    print(("MATCH " if ok else "MISMATCH ") + final_hash[:12] + " vs cell " + want[:12])
    return 0 if ok else 3

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
