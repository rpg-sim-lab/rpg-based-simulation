"""Stored-target step spy (spec: rpg-designer 2026-11-12, option (b): run on current main; two possible gaps, target-naming (is_engaged) and perceived_hostile vs the catalog _is_engagement_hostile)
 (TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE, widened 2026-11-11). READ-ONLY: DRAFT for rpg-designer approval; NOT run, NOT smoked.

Question it answers with raw facts, no classing: on a tick where a subject that Legality calls engaged (a living, active, catalog-hostile entity orthogonally adjacent) takes a step on a target no decision set this tick,
which branch of MovementCandidateSelector.movement_target gave the target, and what are the inputs of its CONFLICT-04 gate (hostility.is_engaged in each direction, perceived_hostile in each direction,
holds_action_task, is_decided_flight, engaged_adjacent_hostile)?

Run with the tree under test as cwd and on PYTHONPATH, same build and tick loop as held_step_spy.py (tools.test_architecture.rpg_gate_run.build_kernel; audit_mode and no_frame_pacing are checked).
  python stored_target_spy.py <world> <seed> <ticks> <out.json> [<plain_cell.json>]
Two wrappers, each calls the real function with its own arguments and returns the real result unchanged; nothing writes to state, and every helper it calls is a read:
  - MovementCandidateSelector.movement_target: remembers, per entity id, (tick, the branch the real code took, the target it returned). The branch is recomputed from the same public helpers the real code uses.
  - MovementSystem.resolve_move: after the real call, if LegalityServiceV2.get_engaged_hostiles(subject) is non-empty and the remembered branch is not "decision", the call is recorded.
Callers: a row is labelled caller=movement_phase only when the remembered movement_target record is from the same tick, its target equals resolve_move's target and a mode was passed; otherwise branch=no_movement_target_this_tick and caller=other (MovementSystem.resolve_move has a second caller, src/engine/domain/movement_actions.py:27, no mode).
Branches: "decision" (nav.target_set together with an ENTITY_MOVE task update this tick), "target_set_no_move_task" (nav.target_set without one), "action_holder" (holds_action_task; returns None, so it never reaches resolve_move),
"stored_or_live" (the stored navigation target, live-refreshed for a tracking move).
Each recorded row: tick, subject, mode, hp, task work_kind and payload, branch, the step result (new_position or failure_reason), and per engaged hostile h: h's task payload target_id, subject's payload target_id,
is_engaged(subject,h), is_engaged(h,subject), perceived_hostile(subject,h), perceived_hostile(h,subject); plus holds_action_task, is_decided_flight and engaged_adjacent_hostile for the subject.
Output JSON: {meta, final_hash, cell_final_hash, match, calls_total, rows_total, rows (first 400), by_branch{branch: n}, by_flags{"<took_step>|<branch>|<engaged_adjacent_hostile>|<any is_engaged>": n}, by_mode{mode: n},
step_ticks_by_entity{id: [distinct ticks of a recorded call that returned a new_position]}}.
When <plain_cell.json> (the plain, un-spied cell's result with "final_hash") is given, the run's end hash is compared with it; a mismatch exits 3 and the file must not be used.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    cell = argv[4] if len(argv) > 4 else None
    from src.engine.candidate_selector import MovementCandidateSelector as MCS
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.hostility import is_engaged, perceived_hostile
    from src.engine.legality import LegalityServiceV2
    from src.engine.movement import MovementSystem
    from tools.test_architecture.rpg_gate_run import build_kernel

    last_branch: dict = {}
    rows: list = []
    counters = {"calls": 0, "rows": 0, "gate_none_engaged_adjacent_calls": 0, "mt_exceptions": 0, "rm_exceptions": 0}
    exc_reprs: list = []
    first_call = [True]
    occ_present = [None]
    distinct_rows: set = set()
    distinct_steps: set = set()
    gate_none_loop_ticks: set = set()
    events: list = []
    cur_tick = [-1]
    by_branch: dict = {}
    by_flags: dict = {}
    by_mode: dict = {}
    step_ticks: dict = {}

    real_mt = MCS.__dict__["movement_target"].__func__
    real_rm = MovementSystem.__dict__["resolve_move"].__func__

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
            last_branch[entity.id] = (cur_tick[0], branch, res)
            if res is None and branch != "action_holder" and MCS.engaged_adjacent_hostile(entity, entities, index) and not MCS.is_decided_flight(entity):
                counters["gate_none_engaged_adjacent_calls"] += 1
                gate_none_loop_ticks.add((cur_tick[0], entity.id))
        except Exception as exc:  # logging only, but counted
            counters["mt_exceptions"] += 1
            if len(exc_reprs) < 5:
                exc_reprs.append("mt:" + repr(exc)[:200])
        return res

    def rm_spy(state, entity, target, *a, **kw):
        res = real_rm(state, entity, target, *a, **kw)
        try:
            counters["calls"] += 1
            rec = last_branch.pop(entity.id, None)
            if rec is not None and rec[0] == cur_tick[0] and rec[2] is not None and tuple(rec[2]) == tuple(target) and "mode" in kw:
                branch, caller = rec[1], "movement_phase"
            else:
                branch, caller = "no_movement_target_this_tick", "other"
            if first_call[0]:
                first_call[0] = False
                occ_present[0] = getattr(state, "occupancy_snapshot", None) is not None
            engaged = LegalityServiceV2.get_engaged_hostiles(entity, state)
            if engaged and branch != "decision":
                upd = res.get(entity.id) if isinstance(res, dict) else res
                new_pos = getattr(upd, "new_position", None)
                nav = getattr(upd, "navigation", None)
                reason = getattr(nav, "failure_reason", None)
                tick = int(getattr(state, "tick", -1))
                mode = kw.get("mode")
                hostiles = []
                any_eng = False
                for hid in engaged:
                    h = state.entities.get(hid)
                    if h is None:
                        continue
                    e_fwd = entity.task.payload.get("target_id") == h.id
                    e_rev = h.task.payload.get("target_id") == entity.id
                    any_eng = any_eng or is_engaged(entity, h)
                    hostiles.append({"id": hid, "hostile_payload_target_id": h.task.payload.get("target_id"), "subject_payload_target_id": entity.task.payload.get("target_id"),
                                     "subject_names_h": e_fwd, "h_names_subject": e_rev, "is_engaged": is_engaged(entity, h), "is_engaged_h_subject": is_engaged(h, entity),
                                     "perceived_hostile_subject_h": perceived_hostile(entity, h), "perceived_hostile_h_subject": perceived_hostile(h, entity),
                                     "engagement_hostile_subject_h": LegalityServiceV2._is_engagement_hostile(entity, h)})
                eah = MCS.engaged_adjacent_hostile(entity, state.entities)
                took = new_pos is not None
                key = f"{int(took)}|{branch}|{int(eah)}|{int(any_eng)}"
                by_flags[key] = by_flags.get(key, 0) + 1
                by_branch[branch] = by_branch.get(branch, 0) + 1
                mname = "DEFAULT(WANDER)" if mode is None else str(getattr(mode, "name", mode))
                by_mode[mname] = by_mode.get(mname, 0) + 1
                counters["rows"] += 1
                if took:
                    step_ticks.setdefault(entity.id, set()).add(tick)
                ccom = getattr(upd, "combat", None)
                oa_damage = getattr(ccom, "damage_taken", 0) if ccom is not None else 0
                events.append((tick, entity.id))
                distinct_rows.add((tick, entity.id))
                if took:
                    distinct_steps.add((tick, entity.id))
                if len(rows) < 400:
                    rows.append({"tick": tick, "subject": entity.id, "kind": entity.kind, "caller": caller, "mode": mname, "hp": entity.combat.hp, "target": target,
                                 "target_source": "target_set_this_tick" if branch == "target_set_no_move_task" else "stored_or_live",
                                 "stepped": took, "oa_damage_taken": oa_damage, "task_work_kind": entity.task.work_kind,
                                 "task_payload": {k: repr(v)[:60] for k, v in entity.task.payload.items()}, "branch": branch,
                                 "new_position": new_pos, "failure_reason": str(getattr(reason, "value", reason)) if reason is not None else None,
                                 "holds_action_task": MCS.holds_action_task(entity), "is_decided_flight": MCS.is_decided_flight(entity),
                                 "engaged_adjacent_hostile": eah, "legality_engaged": list(engaged), "hostiles": hostiles})
        except Exception as exc:  # logging only, but counted
            counters["rm_exceptions"] += 1
            if len(exc_reprs) < 5:
                exc_reprs.append("rm:" + repr(exc)[:200])
        return res

    MCS.movement_target = staticmethod(mt_spy)
    MovementSystem.resolve_move = staticmethod(rm_spy)
    run_id = f"rpgstt_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced")
        return 2
    try:
        for _ in range(ticks):
            cur_tick[0] = int(kernel.state.tick)
            kernel.tick_once()
        state = kernel.state
    finally:
        MCS.movement_target = staticmethod(real_mt)
        MovementSystem.resolve_move = staticmethod(real_rm)
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"] if cell else None
    ok = None if want is None else final_hash == want
    death_tick = {}
    for e in state.entities.values():
        if not e.combat.alive:
            rec = getattr(e.lifecycle, "death_record", None)
            if rec is not None and rec.tick is not None:
                death_tick[e.id] = int(rec.tick)
    died_same = sum(1 for t, i in events if death_tick.get(i) == t)
    died_10 = sum(1 for t, i in events if i in death_tick and t <= death_tick[i] <= t + 10)
    for r in rows:
        dt = death_tick.get(r["subject"])
        r["died_this_tick"] = dt == r["tick"]
        r["died_within_10_ticks"] = dt is not None and r["tick"] <= dt <= r["tick"] + 10
    res = {"meta": {"world": world, "seed": seed, "ticks": ticks, "cwd": os.getcwd(), "occupancy_snapshot_present": occ_present[0]}, "final_hash": final_hash, "cell_final_hash": want, "match": ok,
           "calls_total": counters["calls"], "rows_total": counters["rows"], "rows_distinct_tick_subject": len(distinct_rows), "stepped_distinct_tick_subject": len(distinct_steps), "mt_exceptions": counters["mt_exceptions"], "rm_exceptions": counters["rm_exceptions"], "exception_reprs_first5": exc_reprs, "rows_kept": len(rows), "events_died_same_tick": died_same, "events_died_within_10": died_10,
           "gate_none_engaged_adjacent_calls": counters["gate_none_engaged_adjacent_calls"], "gate_none_engaged_adjacent_distinct_loop_tick_subject": len(gate_none_loop_ticks), "rows": rows, "by_branch": by_branch, "by_flags": by_flags, "by_mode": by_mode,
           "step_ticks_by_entity": {str(k): sorted(v) for k, v in step_ticks.items()}}
    Path(out).write_text(json.dumps(res, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    print(("MATCH " if ok else ("NOCELL " if ok is None else "MISMATCH ")) + final_hash[:12] + (f" vs cell {want[:12]}" if want else "") + f" calls={counters['calls']} rows={counters['rows']} mt_exc={counters['mt_exceptions']} rm_exc={counters['rm_exceptions']}" + (" counts untrusted" if counters["mt_exceptions"] or counters["rm_exceptions"] else ""))
    return 3 if ok is False else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
