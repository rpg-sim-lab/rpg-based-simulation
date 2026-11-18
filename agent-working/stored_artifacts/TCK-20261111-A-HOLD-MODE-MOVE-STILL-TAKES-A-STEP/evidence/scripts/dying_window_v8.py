"""DYING-WINDOW spy v8 (rpg-implementer; DRAFT for rpg-designer approval; NOT run, NOT smoked). TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, stage-2 urban_political COMBAT/HAZARD Tier 2 read.
INPUTS ONLY, NO VERDICTS: this spy records what the subject, its neighbours and the engine's decision points did in the 60 ticks before each subject's fix-arm death; it classes nothing, ranks nothing and
computes no cause. A standalone file: it imports nothing from hold_spy_v7.py and shares none of its closures. Every wrapper calls the original with its own arguments and returns ITS result unchanged; the
tick loop only calls kernel.tick_once(); every scan only reads kernel.state. Same build as hold_spy_v7 (tools.test_architecture.rpg_gate_run.build_kernel, audit_mode / no_frame_pacing checked).
No rmtree anywhere: the kernel's data/runs/<run_id> directory is left in place (the driver names it; the owner decides its deletion).

Usage: python dying_window_v8.py <world> <seed> <ticks> <out.json> [PLAIN | <expected final_hash>]
  PLAIN = no wrapper, no scan (the plain twin; stores its hash). A hash given = exit 3 on a mismatch (the JSON is still written). Exit 4 = the spy recorded >=1 error (errors must be 0; every
  error record is kept, with its tick, where and repr). Exit 2 = bad build.
Env V8_SMOKE=1 swaps the subject table for the smoke's: subjects 15 and 17 in the window [60, 119] (any seed), so a 120-tick run exercises every recorded field; nothing else changes.

SUBJECTS (the fix-arm deaths of the Tier 2 read; entity -> fix death tick D; window = ticks D-60 .. D inclusive, the same ticks in both arms):
  s42: e15 (COMBAT, D=421), e17 (COMBAT, D=455)   s43: e12 (COMBAT, D=291), e9 (HAZARD, D=387)   s45: e15 (COMBAT, D=352, killer e3, 1-tick AFTER_KILL hold)
A subject that is dead (combat.alive False) or absent before a window tick gets a row with alive False and nothing else (its death record when it has one); the window never moves.

Tick labels: tick = kernel.state.tick before the tick_once call (the tick being run), as in v3-v7. Everything read from the state is read AFTER that tick_once (ent_init reads entity_id, navigation and task from the constructed object, not from the call arguments); every wrapper's record carries the tick being run.

PER SUBJECT, PER WINDOW TICK, one row:
  tick; alive; death_record (typed, when dead); movement_mode (stored, post-tick); hold_open (mode == HOLD); hold_entered_tick and hold_length_so_far (consecutive ticks in HOLD up to and including this one, counted
  from the first tick the spy saw HOLD for this subject: the spy scans the subject EVERY tick from tick 0, only the ROWS are windowed); hold_writer = the last EntityUpdate that wrote movement_mode HOLD for
  the subject: {tick, site (first frame outside dataclasses.py / core/updates.py), task_kind_set, label}; mode_writer = the last write of ANY movement_mode for the subject, same shape; hold_entry_label = the label
  of that HOLD write (typed waits: WATCH_HOSTILE / AVOID_NO_ROUTE / HOLD_CHOKEPOINT are named, others are reported as written); position; hp; hp_delta (vs the previous tick's post-state); task_kind; task_label;
  task_payload (scalars only); stored nav target; readiness; combat.last_attacker_id / last_hit_tick / last_hit_damage; engaged_hostiles (LegalityServiceV2.get_engaged_hostiles, the adjacency call v3-v7 use);
  near: every OTHER alive entity within Manhattan distance <= radius of the subject, radius = max(4, 1 + max combat.range among alive entities) per tick (recorded in each row as near_radius, with subject_range): id, kind, role, faction id string, range, task_payload scalars (they carry the attack target id), hp, position, distance, engaged (id in engaged_hostiles), movement_mode, nav target, task_kind,
  task_label, and that entity's own last_attacker_id / last_hit_tick (so a hit ON the subject is visible from either side); NO hostility verdict beyond the engine's own engaged list;
  decisions: tact = every TacticalDecisionSystem.evaluate_entity_intent call for the subject this tick (result None / task label / payload / work_kind_set / movement_mode_set / target_set), strat = every
  strategic evaluate_strategic_intent call (movement_mode_set / target_set / task work_kind_set); movement_target = the branch of the last MovementCandidateSelector.movement_target call (decision |
  target_set_no_move_task | stored_or_live); walks = every MovementSystem.resolve_move call for the subject this tick: effective mode argument, target, position before, stored target, engaged hostiles before,
  hp before, and the RESULT's every non-None field (new_position, and any refusal / blocked / reason field the EntityUpdate carries, repr truncated to 160 chars): a "walk refused with its reason" is shown
  exactly as the engine returned it, never re-derived; attacks = every CombatResolutionSystem.resolve_multi_attack call this tick with the subject as defender or among the attackers: attacker ids, defender id,
  is_opportunity_attack, is_lethal (the free swing is is_lethal=False), result_fields (every non-None field of the returned CombatUpdate, via fields_of: no guessed field names); damage_events = the per-tick hp drop plus the subject's last_attacker_id / last_hit_tick / last_hit_damage if last_hit_tick == this tick (the
  engine's own record of source and size); hazard = region at the subject's position (SpatialQueryService.get_region_at, the call WorldDynamicsSystem uses): region id, hazard_kind, hazard_level,
  calamity_intensity, suppression_active, active_modifiers (e.g. MIASMA x1.5 drain), EnvironmentService.calculate_hazard_drain(region, entity) (a pure read), the previous tick's region id and whether the subject's tile changed (a hazard tile entered
  = region id differs from the previous tick's or hazard_level/drain differs).

DEAD ROWS (v8 hash 3828af12; documented here after the set): a window tick on which the subject is dead or absent gets {tick, alive: False, present, death_record (typed, to_dict), attacks, walks, decisions {tact, strat,
movement_target} (each collected for (tick, subject) in that tick, which is the fatal tick for the tick-D row), position_last_alive and hp_last_alive (the previous alive scan's post-state)}; it carries no hold_open,
hold_writer, hp or near fields. Ordinary hits go through resolve_attack (combat.py), which this spy does NOT wrap, so a fatal blow is not expected to appear in attacks; the killer's position and range on the
subject's last alive row (engaged_hostiles and near) are the recorded inputs.

Output JSON: spy, world, seed, ticks, final_hash, match, errors (count) and error_records (all kept), subjects (the table used), rows {entity: [rows...]}, death_ticks_seen {entity: tick} (post-tick scan of every
subject, the whole run), counts (calls wrapped per kind, rows written)."""
from __future__ import annotations

import dataclasses
import json
import os
import sys
from collections import Counter

TYPED = {"WATCH_HOSTILE", "AVOID_NO_ROUTE", "HOLD_CHOKEPOINT"}
NEAR_R = 4
SUBJECTS = {42: {15: 421, 17: 455}, 43: {12: 291, 9: 387}, 45: {15: 352}}
WINDOW = 60


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    mode_arg = argv[4] if len(argv) > 4 else None
    plain = mode_arg == "PLAIN"
    want = None if plain else mode_arg
    from pathlib import Path

    from src.core.movement_modes import MovementMode
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    smoke = os.environ.get("V8_SMOKE") == "1"
    if smoke:
        windows = {15: (60, 119), 17: (60, 119)}
    else:
        windows = {e: (d - WINDOW, d) for e, d in SUBJECTS.get(seed, {}).items()}
    subj = set(windows)

    run_id = f"rpgdying_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD")
        return 2
    HOLD = MovementMode.HOLD
    cur = {"tick": 0}
    errors = []
    counts = Counter()
    rows = {e: [] for e in subj}
    tact, strat, walks, attacks, mt_branch = {}, {}, {}, {}, {}   # keyed (tick, eid)
    mode_writer, hold_writer = {}, {}                              # eid -> {tick, site, task_kind_set, label}
    hold_since = {}                                                # eid -> first tick seen in HOLD (consecutive)
    prev = {}                                                      # eid -> {hp, region, drain, level}
    death_ticks = {}

    def err(where, e=None):
        errors.append({"tick": cur["tick"], "where": where, "repr": repr(e)[:300] if e is not None else None})

    def val(x):
        return getattr(x, "value", str(x))

    def label_of(payload):
        if not payload:
            return None
        return payload.get("reason") or payload.get("action")

    def scal(v):
        return v if isinstance(v, (int, float, str, bool, type(None))) else str(v)[:160]

    def site():
        f = sys._getframe(2)
        while f is not None and (f.f_code.co_filename.endswith("dataclasses.py") or f.f_code.co_filename.endswith(os.path.join("core", "updates.py"))):
            f = f.f_back
        if f is None:
            return "unknown"
        return f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno}:{f.f_code.co_name}"

    def fields_of(obj):
        try:
            if dataclasses.is_dataclass(obj):
                return {f.name: repr(getattr(obj, f.name))[:160] for f in dataclasses.fields(obj) if getattr(obj, f.name) is not None}
            return {k: repr(v)[:160] for k, v in vars(obj).items() if v is not None}
        except Exception as e_:
            err("fields_of", e_)
            return {}

    if not plain:
        from src.core.updates import EntityUpdate
        from src.engine.candidate_selector import MovementCandidateSelector
        from src.engine.combat import CombatResolutionSystem
        from src.engine.legality import LegalityServiceV2
        from src.engine.movement import MovementSystem
        from src.engine.spatial_query import SpatialQueryService
        from src.engine.tactical import TacticalDecisionSystem
        from src.world.environment import EnvironmentService
        import src.systems.strategic_systems.intelligence as intel_mod

        in_window = lambda eid: eid in windows and windows[eid][0] <= cur["tick"] <= windows[eid][1]

        o_mt = MovementCandidateSelector.__dict__["movement_target"].__func__

        def mt_spy(*a, **kw):
            res = o_mt(*a, **kw)
            try:
                entity = a[0] if a else kw["entity"]
                if entity.id in subj:
                    ent_upd = a[1] if len(a) > 1 else kw.get("ent_upd")
                    nav = ent_upd.navigation if ent_upd else None
                    if nav is not None and nav.target_set is not None:
                        b = "decision" if (ent_upd.task is not None and ent_upd.task.work_kind_set == "ENTITY_MOVE") else "target_set_no_move_task"
                    else:
                        b = "stored_or_live"
                    mt_branch[(cur["tick"], entity.id)] = b
                    counts["movement_target"] += 1
            except Exception as e_:
                err("movement_target", e_)
            return res

        MovementCandidateSelector.movement_target = staticmethod(mt_spy)

        o_init = EntityUpdate.__init__

        def ent_init(self, *a, **kw):
            o_init(self, *a, **kw)
            try:
                eid = self.entity_id
                if eid in subj:
                    nav = self.navigation
                    ms = getattr(nav, "movement_mode_set", None) if nav is not None else None
                    if ms is not None:
                        task = self.task
                        ps = (getattr(task, "payload_set", None) or {}) if task is not None else {}
                        rec = {"tick": cur["tick"], "mode": val(ms), "site": site(), "task_kind_set": scal(getattr(task, "work_kind_set", None)) if task is not None else None, "label": label_of(ps)}
                        mode_writer[eid] = rec
                        if ms == HOLD:
                            hold_writer[eid] = rec
            except Exception as e_:
                err("entity_update_init", e_)

        EntityUpdate.__init__ = ent_init

        o_td = TacticalDecisionSystem.evaluate_entity_intent

        def td_spy(st, entity, *a, **kw):
            res = o_td(st, entity, *a, **kw)
            try:
                if entity.id in subj:
                    tk = getattr(res, "task", None)
                    pl = (getattr(tk, "payload_set", None) or {}) if tk is not None else {}
                    nav = getattr(res, "navigation", None)
                    tset = getattr(nav, "target_set", None) if nav is not None else None
                    mset = getattr(nav, "movement_mode_set", None) if nav is not None else None
                    tact.setdefault((cur["tick"], entity.id), []).append({
                        "result_none": res is None, "label": label_of(pl), "payload": {k: scal(v) for k, v in dict(pl).items()}, "work_kind_set": scal(getattr(tk, "work_kind_set", None)) if tk is not None else None,
                        "movement_mode_set": val(mset) if mset is not None else None, "target_set": list(tset) if tset is not None else None})
                    counts["tactical"] += 1
            except Exception as e_:
                err("tactical_wrap", e_)
            return res

        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(td_spy)

        sis_cls = [c_ for c_ in vars(intel_mod).values() if isinstance(c_, type) and "evaluate_strategic_intent" in c_.__dict__][0]
        so_fn = sis_cls.__dict__["evaluate_strategic_intent"].__func__

        def ss_spy(state_, entity, *a, **kw):
            res = so_fn(state_, entity, *a, **kw)
            try:
                if entity.id in subj:
                    nav = getattr(res, "navigation", None)
                    tk = getattr(res, "task", None)
                    tset = getattr(nav, "target_set", None) if nav is not None else None
                    mset = getattr(nav, "movement_mode_set", None) if nav is not None else None
                    strat.setdefault((cur["tick"], entity.id), []).append({
                        "result_none": res is None, "movement_mode_set": val(mset) if mset is not None else None, "target_set": list(tset) if tset is not None else None,
                        "work_kind_set": scal(getattr(tk, "work_kind_set", None)) if tk is not None else None})
                    counts["strategic"] += 1
            except Exception as e_:
                err("strategic_wrap", e_)
            return res

        sis_cls.evaluate_strategic_intent = staticmethod(ss_spy)

        o_rm = MovementSystem.__dict__["resolve_move"].__func__

        def rm_spy(state, entity, target, *a, **kw):
            pre = None
            try:
                if entity.id in subj:
                    pre = {"mode": val(kw.get("mode", a[0] if a else None)), "target": list(target) if target is not None else None, "position_before": list(entity.navigation.position),
                           "stored_target": list(entity.navigation.target) if entity.navigation.target is not None else None,
                           "engaged_before": list(LegalityServiceV2.get_engaged_hostiles(entity, state)), "hp_before": entity.combat.hp, "readiness": entity.combat.readiness}
            except Exception as e_:
                err("resolve_move_pre", e_)
            res = o_rm(state, entity, target, *a, **kw)
            try:
                if pre is not None:
                    eu = res.get(entity.id) if isinstance(res, dict) else res
                    pre["result_fields"] = fields_of(eu) if eu is not None else None
                    pre["result_none"] = eu is None
                    walks.setdefault((cur["tick"], entity.id), []).append(pre)
                    counts["resolve_move"] += 1
            except Exception as e_:
                err("resolve_move_post", e_)
            return res

        MovementSystem.resolve_move = staticmethod(rm_spy)

        o_oa = CombatResolutionSystem.__dict__["resolve_multi_attack"].__func__

        def oa_spy(*a, **kw):
            res = o_oa(*a, **kw)
            try:
                atks = a[0] if a else kw.get("attackers")
                dfd = a[1] if len(a) > 1 else kw.get("defender")
                aids = [getattr(x, "id", x) for x in (atks or [])]
                did = getattr(dfd, "id", None)
                if did in subj or any(x in subj for x in aids):
                    rec = {"attackers": aids, "defender": did, "is_opportunity_attack": bool(kw.get("is_opportunity_attack", a[3] if len(a) > 3 else False)),
                           "is_lethal": bool(kw.get("is_lethal", a[4] if len(a) > 4 else True)), "result_fields": fields_of(res) if res is not None else None}
                    for k in {did, *aids} & subj:
                        attacks.setdefault((cur["tick"], k), []).append(rec)
                    counts["resolve_multi_attack"] += 1
            except Exception as e_:
                err("resolve_multi_attack", e_)
            return res

        CombatResolutionSystem.resolve_multi_attack = staticmethod(oa_spy)

    def scan(state, t):
        engine_ok = True
        for eid in subj:
            e = state.entities.get(eid)
            lo, hi = windows[eid]
            win = lo <= t <= hi
            if e is None or not e.combat.alive:
                if e is not None and eid not in death_ticks:
                    death_ticks[eid] = t
                if win:
                    dr = getattr(getattr(e, "lifecycle", None), "death_record", None) if e is not None else None
                    pv0 = prev.get(eid)
                    rows[eid].append({"tick": t, "alive": False, "present": e is not None, "death_record": (dr.to_dict() if dr is not None and hasattr(dr, "to_dict") else (str(dr) if dr is not None else None)),
                                      "attacks": attacks.get((t, eid), []), "walks": walks.get((t, eid), []),
                                      "decisions": {"tact": tact.get((t, eid), []), "strat": strat.get((t, eid), []), "movement_target": mt_branch.get((t, eid))},
                                      "position_last_alive": pv0["position"] if pv0 else None, "hp_last_alive": pv0["hp"] if pv0 else None})
                continue
            m = e.navigation.movement_mode
            if m == HOLD:
                hold_since.setdefault(eid, t)
            else:
                hold_since.pop(eid, None)
            pos = tuple(e.navigation.position)
            region = SpatialQueryService.get_region_at(state, pos)
            drain = EnvironmentService.calculate_hazard_drain(region, e) if region is not None else None
            haz = {"region_id": getattr(region, "id", getattr(region, "region_id", None)) if region is not None else None,
                   "hazard_kind": scal(getattr(region, "hazard_kind", None)) if region is not None else None,
                   "hazard_level": scal(getattr(region, "hazard_level", None)) if region is not None else None,
                   "calamity_intensity": scal(getattr(region, "calamity_intensity", None)) if region is not None else None,
                   "suppression_active": scal(getattr(region, "suppression_active", None)) if region is not None else None,
                   "active_modifiers": sorted(str(x) for x in (getattr(region, "active_modifiers", None) or [])) if region is not None else None, "drain": drain}
            pv = prev.get(eid)
            haz["previous_region_id"] = pv["region_id"] if pv else None
            haz["entered_different_region_or_level"] = bool(pv and (pv["region_id"] != haz["region_id"] or pv["level"] != haz["hazard_level"] or pv["drain"] != drain))
            hp = e.combat.hp
            if win:
                engaged = list(LegalityServiceV2.get_engaged_hostiles(e, state))
                near = []
                radius = max(NEAR_R, 1 + max((o_.combat.range for o_ in state.entities.values() if o_.combat.alive), default=0))
                for oid, o in state.entities.items():
                    if oid == eid or not o.combat.alive:
                        continue
                    d = abs(o.navigation.position[0] - pos[0]) + abs(o.navigation.position[1] - pos[1])
                    if d <= radius:
                        try:
                            from src.content_semantics.faction import get_faction_id_str
                            fac = get_faction_id_str(o)
                        except Exception as e_:
                            fac = None
                            err("faction_id", e_)
                        near.append({"id": oid, "kind": o.kind, "role": int(o.identity.role), "faction": fac, "hp": o.combat.hp, "position": list(o.navigation.position), "distance": d,
                                     "engaged": oid in engaged, "movement_mode": val(o.navigation.movement_mode), "target": list(o.navigation.target) if o.navigation.target is not None else None,
                                     "task_kind": o.task.work_kind, "task_label": label_of(o.task.payload), "task_payload": {k: scal(v) for k, v in dict(o.task.payload or {}).items()}, "range": o.combat.range,
                                     "last_attacker_id": o.combat.last_attacker_id, "last_hit_tick": o.combat.last_hit_tick})
                hw, mw = hold_writer.get(eid), mode_writer.get(eid)
                hit_now = e.combat.last_hit_tick == t
                rows[eid].append({
                    "tick": t, "alive": True, "movement_mode": val(m), "hold_open": m == HOLD, "hold_entered_tick": hold_since.get(eid), "hold_length_so_far": (t - hold_since[eid] + 1) if eid in hold_since else 0,
                    "hold_writer": hw, "hold_entry_label": hw["label"] if hw else None, "mode_writer": mw, "position": list(pos), "hp": hp, "hp_delta": (hp - pv["hp"]) if pv else None,
                    "task_kind": e.task.work_kind, "task_label": label_of(e.task.payload), "task_payload": {k: scal(v) for k, v in dict(e.task.payload or {}).items()},
                    "stored_target": list(e.navigation.target) if e.navigation.target is not None else None, "readiness": e.combat.readiness,
                    "last_attacker_id": e.combat.last_attacker_id, "last_hit_tick": e.combat.last_hit_tick, "last_hit_damage": e.combat.last_hit_damage,
                    "engaged_hostiles": engaged, "near_radius": radius, "subject_range": e.combat.range, "near": near,
                    "decisions": {"tact": tact.get((t, eid), []), "strat": strat.get((t, eid), []), "movement_target": mt_branch.get((t, eid))},
                    "walks": walks.get((t, eid), []), "attacks": attacks.get((t, eid), []),
                    "damage_events": {"hp_drop": (pv["hp"] - hp) if pv and pv["hp"] > hp else 0, "hit_this_tick": hit_now,
                                      "source": e.combat.last_attacker_id if hit_now else None, "size": e.combat.last_hit_damage if hit_now else None},
                    "hazard": haz})
                counts["rows"] += 1
            prev[eid] = {"hp": hp, "region_id": haz["region_id"], "level": haz["hazard_level"], "drain": drain, "position": list(pos)}

    try:
        for _ in range(ticks):
            cur["tick"] = kernel.state.tick
            kernel.tick_once()
            if plain or not subj:
                continue
            try:
                scan(kernel.state, cur["tick"])
            except Exception as e_:
                err("scan", e_)
    finally:
        state = kernel.state
        kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    doc = {"spy": "dying_window_v8", "world": world, "seed": seed, "ticks": ticks, "plain": plain, "final_hash": final_hash, "match": (None if (plain or want is None) else final_hash == want),
           "hashseed": os.environ.get("PYTHONHASHSEED"), "smoke": smoke, "subjects": {str(e): list(w) for e, w in windows.items()}, "near_radius": NEAR_R,
           "errors": len(errors), "error_records": errors, "death_ticks_seen": {str(k): v for k, v in death_ticks.items()}, "counts": dict(counts),
           "rows": {str(e): r for e, r in rows.items()}}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"final_hash": final_hash, "match": doc["match"], "errors": len(errors), "rows": counts["rows"], "counts": dict(counts)}))
    if want is not None and final_hash != want:
        return 3
    if errors:
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
