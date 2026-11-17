"""Stored-target FIX spy (TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE, divergence 2.206, shape (iii)). READ-ONLY: DRAFT for rpg-designer approval; NOT run, NOT smoked.

Runs on BOTH arms: the base tree (main at dispatch, gate predicate ``engaged_adjacent_hostile``) and the fix tree (``adjacent_perceived_hostile``). The predicate is looked up by name,
newest first. Run with the tree under test as cwd and on PYTHONPATH, same build and tick loop as held_step_spy.py / stored_target_spy.py (tools.test_architecture.rpg_gate_run.build_kernel;
audit_mode and no_frame_pacing are checked).
  python stored_target_fix_spy.py <world> <seed> <ticks> <out.json> [<plain_cell.json>]
When <plain_cell.json> (the plain, un-spied cell's result with "final_hash") is given, the run's end hash is compared with it; a mismatch exits 3 and the cell is void.
Revisions vs ab5f08fb (rpg-designer 2026-11-12): (1) a hold is counted only when a pre-gate target exists and differs from the position (nav.target_set if set else entity.navigation.target; movement.py:236); (2) on the base arm the per-pair filter also needs is_engaged; (3) the branch is kept per hold tick, with counts per 20+ run and totals; (4) a zero tactical or strategic decision count prints "decision hook missed" and marks those figures untrusted; (5) each pair is watched one tick past its last hold so the hit window [first, last+1] is true.
Every wrapper calls the real function with its own arguments and returns the real result unchanged; nothing writes to state; every helper it calls is a read. All "tick" figures below are the loop
tick taken before each ``tick_once`` (state.tick is not visible inside ``movement_target``); rows that have a state also carry state.tick.

What it records (counts are uncapped; row lists are capped and the totals stated):
  1. GATE HOLDS. A gate hold is a tick on which ``movement_target`` returns None because the gate predicate holds (the subject is not an action holder, no decision this tick, not a decided flight, the predicate true),
     counted per (subject, hostile) for each adjacent perceived hostile (on the base arm: the engaged ones the old predicate saw). Consecutive ticks form a run; gap-joined runs (a gap of at most 2 ticks) are reported
     separately and labelled. Every run of 20+ ticks is recorded with the hits the hostile landed on the subject in the run (from last_attacker_id/last_hit_tick, read after each tick). FREEZE BAR flags:
     ``freeze_stop_ge50_no_hit`` (a run of 50+ ticks in which that hostile landed no hit on the subject) and ``freeze_stop_held_at_last_tick`` (a run still in force at the last tick). Run-length distribution included.
  2. move_ends_here True calls, distinct (tick, subject), and for each the brain decisions (tactical ``evaluate_entity_intent`` or strategic ``evaluate_strategic_intent`` called for that subject) within 2 ticks after it.
  3. Brain decisions per run: distinct (tick, subject) calls of each decision function.
  4. UNDECIDED STEPS: ``resolve_move`` calls from the movement phase (a movement_target record from the same tick with the same target and a mode passed) with the branch not "decision", a Legality-engaged hostile and a new
     position: count, distinct (tick, subject), opportunity-attack damage taken, deaths within 10 ticks. Rows capped at 400. caller=other (the second caller, src/engine/domain/movement_actions.py:27) is reported separately, never summed.
  5. S1 pin figures: ``resolve_move`` results carrying FELT_LETHAL_FREE_SWING per entity (distinct ticks), runs of 50+ ticks, the first 40 held rows with hp, and deaths with causes/ticks, so the S1 stop rules can be applied
     (record every pin of 50+; STOP on 500+, still held at the last tick, or an hp fall or a death in [first, last+1]).
  6. Exception counters mt_exceptions, rm_exceptions, ex_exceptions (every wrapper); the first 5 reprs are kept; any non-zero count prints "counts untrusted".
Meta: arm (which predicate name was found), occupancy_snapshot_present (first resolve_move call).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def _runs(ticks, join_gap=0):
    out, prev, start, length = [], None, None, 0
    for t in sorted(set(ticks)):
        if prev is not None and t <= prev + 1 + join_gap:
            length += t - prev
        else:
            if prev is not None:
                out.append((start, prev, length))
            start, length = t, 1
        prev = t
    if prev is not None:
        out.append((start, prev, length))
    return out


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    cell = argv[4] if len(argv) > 4 else None
    from src.engine.candidate_selector import MovementCandidateSelector as MCS
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.hostility import is_engaged, perceived_hostile
    from src.engine.legality import LegalityServiceV2
    from src.engine.movement import MovementSystem
    from src.engine.tactical import TacticalDecisionSystem
    from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
    from tools.rpg_measure.arm_child import _cause
    from tools.test_architecture.rpg_gate_run import build_kernel

    arm_name = "adjacent_perceived_hostile" if hasattr(MCS, "adjacent_perceived_hostile") else "engaged_adjacent_hostile"
    pred = getattr(MCS, arm_name)

    cur = [-1]
    exc = {"mt": 0, "rm": 0, "ex": 0}
    reprs: list = []
    last_mt: dict = {}
    hold_ticks: dict = {}        # (subject, hostile) -> set of ticks
    decision_ticks: dict = {"tactical": set(), "strategic": set()}
    ends: set = set()
    hit_ticks: dict = {}         # (subject, attacker) -> set of hit ticks
    watch_now: set = set()
    prev_watch: set = set()
    hold_branch: dict = {}       # (subject, hostile) -> {tick: branch}
    undecided: dict = {"other": [], "movement_phase": []}
    undecided_cnt = {"movement_phase": 0, "other": 0}
    undecided_dist = {"movement_phase": set(), "other": set()}
    oa_damage = {"movement_phase": 0, "other": 0}
    undecided_events: list = []
    held_felt: dict = {}
    held_rows: list = []
    first_call = [True]
    occ = [None]

    def note(kind, e):
        exc[kind] += 1
        if len(reprs) < 5:
            reprs.append(f"{kind}:{e!r}"[:200])

    real_mt = MCS.__dict__["movement_target"].__func__
    real_rm = MovementSystem.__dict__["resolve_move"].__func__
    real_end = MCS.__dict__["move_ends_here"].__func__
    real_tac = TacticalDecisionSystem.__dict__["evaluate_entity_intent"].__func__
    real_str = StrategicIntelligenceSystem.__dict__["evaluate_strategic_intent"].__func__

    def mt_spy(entity, ent_upd, entities, index=None):
        res = real_mt(entity, ent_upd, entities, index)
        try:
            nav = ent_upd.navigation if ent_upd else None
            if nav and nav.target_set is not None and ent_upd and ent_upd.task is not None and ent_upd.task.work_kind_set == "ENTITY_MOVE":
                branch = "decision"
            elif nav and nav.target_set is not None:
                branch = "target_set_no_move_task"
            elif MCS.holds_action_task(entity):
                branch = "action_holder"
            else:
                branch = "stored_or_live"
            last_mt[entity.id] = (cur[0], branch, res)
            pre = nav.target_set if (nav and nav.target_set is not None) else entity.navigation.target  # the pre-gate target, the test of movement.py:236
            has_pre_target = bool(pre) and entity.navigation.position != pre
            if res is None and has_pre_target and branch in ("stored_or_live", "target_set_no_move_task") and not MCS.is_decided_flight(entity) and pred(entity, entities, index):
                idx = index if index is not None else MCS.position_index(entities)
                x, y = int(entity.navigation.position[0]), int(entity.navigation.position[1])
                for tile in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    for oid in idx.get(tile, ()):
                        o = entities.get(oid)
                        if o is not None and o.id != entity.id and perceived_hostile(entity, o) and (arm_name == "adjacent_perceived_hostile" or is_engaged(entity, o)):
                            hold_ticks.setdefault((entity.id, oid), set()).add(cur[0])
                            hold_branch.setdefault((entity.id, oid), {})[cur[0]] = branch
                            watch_now.add((entity.id, oid))
        except Exception as e:  # logging only, but counted
            note("mt", e)
        return res

    def end_spy(entity, entities, index=None):
        res = real_end(entity, entities, index)
        try:
            if res:
                ends.add((cur[0], entity.id))
        except Exception as e:
            note("ex", e)
        return res

    def tac_spy(st, entity, *a, **k):
        try:
            decision_ticks["tactical"].add((cur[0], entity.id))
        except Exception as e:
            note("ex", e)
        return real_tac(st, entity, *a, **k)

    def str_spy(st, entity, *a, **k):
        try:
            decision_ticks["strategic"].add((cur[0], entity.id))
        except Exception as e:
            note("ex", e)
        return real_str(st, entity, *a, **k)

    def rm_spy(state, entity, target, *a, **kw):
        res = real_rm(state, entity, target, *a, **kw)
        try:
            if first_call[0]:
                first_call[0] = False
                occ[0] = getattr(state, "occupancy_snapshot", None) is not None
            rec = last_mt.pop(entity.id, None)
            if rec is not None and rec[0] == cur[0] and rec[2] is not None and tuple(rec[2]) == tuple(target) and "mode" in kw:
                branch, caller = rec[1], "movement_phase"
            else:
                branch, caller = "no_movement_target_this_tick", "other"
            upd = res.get(entity.id) if isinstance(res, dict) else res
            nav = getattr(upd, "navigation", None)
            reason = getattr(nav, "failure_reason", None)
            tick = int(getattr(state, "tick", -1))
            if reason is not None and getattr(reason, "value", reason) == "FELT_LETHAL_FREE_SWING":
                held_felt.setdefault(entity.id, []).append(cur[0])
                if len(held_rows) < 40:
                    c = entity.combat
                    held_rows.append({"loop_tick": cur[0], "tick": tick, "subject": entity.id, "hp": c.hp, "last_attacker_id": c.last_attacker_id, "last_hit_damage": getattr(c, "last_hit_damage", None)})
            engaged = LegalityServiceV2.get_engaged_hostiles(entity, state)
            new_pos = getattr(upd, "new_position", None)
            if engaged and branch != "decision" and new_pos is not None:
                ccom = getattr(upd, "combat", None)
                dmg = getattr(ccom, "damage_taken", 0) if ccom is not None else 0
                undecided_cnt[caller] += 1
                undecided_dist[caller].add((cur[0], entity.id))
                oa_damage[caller] += dmg
                undecided_events.append((cur[0], entity.id, caller))
                if len(undecided[caller]) < 400:
                    undecided[caller].append({"loop_tick": cur[0], "tick": tick, "subject": entity.id, "branch": branch, "hp": entity.combat.hp, "oa_damage_taken": dmg,
                                              "engaged": list(engaged), "new_position": new_pos})
        except Exception as e:
            note("rm", e)
        return res

    MCS.movement_target = staticmethod(mt_spy)
    MCS.move_ends_here = staticmethod(end_spy)
    MovementSystem.resolve_move = staticmethod(rm_spy)
    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(tac_spy)
    StrategicIntelligenceSystem.evaluate_strategic_intent = staticmethod(str_spy)
    run_id = f"rpgsfx_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced")
        return 2
    try:
        for _ in range(ticks):
            cur[0] = int(kernel.state.tick)
            prev_watch = set(watch_now)
            watch_now.clear()
            kernel.tick_once()
            try:
                st = kernel.state
                for sid, aid in (watch_now | prev_watch):
                    s = st.entities.get(sid)
                    if s is not None and s.combat.last_attacker_id == aid and s.combat.last_hit_tick is not None:
                        hit_ticks.setdefault((sid, aid), set()).add(int(s.combat.last_hit_tick))
            except Exception as e:
                note("ex", e)
        state = kernel.state
    finally:
        MCS.movement_target = staticmethod(real_mt)
        MCS.move_ends_here = staticmethod(real_end)
        MovementSystem.resolve_move = staticmethod(real_rm)
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(real_tac)
        StrategicIntelligenceSystem.evaluate_strategic_intent = staticmethod(real_str)
    kernel.shutdown()
    last_tick = cur[0]
    final_hash = CanonicalStateHasher.get_hash(state)
    want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"] if cell else None
    ok = None if want is None else final_hash == want

    # gate-hold runs
    runs_all, ge20, dist = [], [], {}
    for (sid, hid), ts in hold_ticks.items():
        hits = hit_ticks.get((sid, hid), set())
        for start, end, length in _runs(ts):
            runs_all.append(length)
            dist[length] = dist.get(length, 0) + 1
            if length >= 20:
                n_hits = sum(1 for h in hits if start <= h <= end + 1)  # the pair is watched for one tick after its last hold, so this window is true
                bc = {}
                for tt, bb in hold_branch.get((sid, hid), {}).items():
                    if start <= tt <= end:
                        bc[bb] = bc.get(bb, 0) + 1
                ge20.append({"subject": sid, "hostile": hid, "first_tick": start, "last_tick": end, "ticks": length, "hits_landed_by_that_hostile": n_hits,
                             "hit_window": "[first_tick, last_tick + 1]", "branch_counts": bc, "held_at_last_tick": end >= last_tick - 1})
    branch_totals: dict = {}
    for bm in hold_branch.values():
        for bb in bm.values():
            branch_totals[bb] = branch_totals.get(bb, 0) + 1
    gap_runs = []
    for (sid, hid), ts in hold_ticks.items():
        for start, end, length in _runs(ts, join_gap=2):
            if length >= 20:
                gap_runs.append({"subject": sid, "hostile": hid, "first_tick": start, "last_tick": end, "span_ticks_gap_joined": length})
    stop_no_hit = [r for r in ge20 if r["ticks"] >= 50 and r["hits_landed_by_that_hostile"] == 0]
    stop_last = [r for r in ge20 if r["held_at_last_tick"]]

    # move_ends_here followed by a decision within 2 ticks
    dec_all = decision_ticks["tactical"] | decision_ticks["strategic"]
    ends_with_decision = sum(1 for (t, sid) in ends if any((t + d, sid) in dec_all for d in (0, 1, 2)))

    # S1 pins
    deaths = {}
    for e in state.entities.values():
        if not e.combat.alive:
            rec = getattr(e.lifecycle, "death_record", None)
            deaths[str(e.id)] = [None if rec is None else rec.tick, _cause(e), e.kind]
    pins = []
    for eid, ts in held_felt.items():
        for start, end, length in _runs(ts):
            if length >= 50:
                pins.append({"entity": eid, "first_tick": start, "last_tick": end, "ticks": length})
    death_ticks = {int(k): v[0] for k, v in deaths.items() if v[0] is not None}
    died10 = sum(1 for (t, sid, c) in undecided_events if sid in death_ticks and t <= death_ticks[sid] <= t + 10)

    hook_missed = len(decision_ticks["tactical"]) == 0 or len(decision_ticks["strategic"]) == 0
    res = {"meta": {"world": world, "seed": seed, "ticks": ticks, "cwd": os.getcwd(), "arm_predicate": arm_name, "occupancy_snapshot_present": occ[0]},
           "final_hash": final_hash, "cell_final_hash": want, "match": ok,
           "exceptions": {"mt": exc["mt"], "rm": exc["rm"], "ex": exc["ex"], "first5": reprs},
           "gate_holds": {"branch_totals": branch_totals, "pairs": len(hold_ticks), "hold_ticks_total": sum(len(v) for v in hold_ticks.values()), "runs_total": len(runs_all),
                          "run_length_distribution": {str(k): v for k, v in sorted(dist.items())}, "runs_ge_20": ge20, "gap_joined_runs_ge_20_gap_le_2_span": gap_runs,
                          "freeze_stop_ge50_no_hit": stop_no_hit, "freeze_stop_held_at_last_tick": stop_last},
           "decision_hook_missed": hook_missed,
           "move_ends_here": {"true_distinct_tick_subject": len(ends), "with_a_brain_decision_within_2_ticks": ends_with_decision, "untrusted": hook_missed},
           "brain_decisions": {"untrusted": hook_missed, "tactical_distinct_tick_subject": len(decision_ticks["tactical"]), "strategic_distinct_tick_subject": len(decision_ticks["strategic"])},
           "undecided_steps": {c: {"calls": undecided_cnt[c], "distinct_tick_subject": len(undecided_dist[c]), "oa_damage_taken": oa_damage[c], "rows_kept": len(undecided[c]), "rows": undecided[c]} for c in ("movement_phase", "other")},
           "undecided_steps_died_within_10_ticks_all_callers_not_summed_across_callers_see_rows": died10,
           "s1_pins": {"held_calls_by_entity_distinct_ticks": {str(k): len(set(v)) for k, v in held_felt.items()}, "runs_ge_50": pins, "held_rows_first_40": held_rows},
           "death": deaths}
    Path(out).write_text(json.dumps(res, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    bad = exc["mt"] or exc["rm"] or exc["ex"]
    print(("MATCH " if ok else ("NOCELL " if ok is None else "MISMATCH ")) + final_hash[:12] + (f" vs cell {want[:12]}" if want else "")
          + f" holds={sum(len(v) for v in hold_ticks.values())} stop_no_hit={len(stop_no_hit)} stop_last={len(stop_last)} ends={len(ends)} exc={exc['mt']}/{exc['rm']}/{exc['ex']}" + (" counts untrusted" if bad else "") + (" decision hook missed (move_ends_here-within-2 and decisions-per-run untrusted)" if hook_missed else ""))
    return 3 if ok is False else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
