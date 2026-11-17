"""Starvation trace of one cell, same ruler as tools/rpg_measure/arm_child.py (rpg-planner-ubuntu, 2026-11-07).
Run exactly as paired.py runs arm_child: cwd = the arm's git-archive tree, PYTHONPATH = that tree, PYTHONHASHSEED=0.
Usage: python starv_trace.py <world> <seed> <ticks> <cell.json> <out.jsonl> <entity id> [<entity id> ...]
Same build (tools.test_architecture.rpg_gate_run.build_kernel, audit_mode and no_frame_pacing checked) and the same tick loop as arm_child; it only READS
state between ticks. Rows: per tick before the tick ("t": hunger, sleep debt, hp, pos, task work kind/reason/action/target, nav target, alive) for each
named entity; "meal" when an entity's hunger falls between consecutive ticks (the manual meal check); "death" with the typed cause; at the end every
"starvation_death_record" payload from the run's own event log (the V3 recorder: verdict, ways open/attempted, last_meal_tick) and the final_hash check.
The final_hash must equal <cell.json>'s final_hash (the arm_child result of the same world/seed/arm); otherwise exit 3 and the trace does not count.
Exit 0 match, 3 mismatch, 2 bad build."""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path

def row(e, t, st=None):
    p = e.task.payload or {}
    bio = e.biological
    return {"k": "t", "t": t, "e": e.id, "alive": e.combat.alive, "hunger": round(bio.hunger, 3), "sleep_debt": round(getattr(bio, "sleep_debt", 0.0) or 0.0, 3),
            "hp": e.combat.hp, "pos": list(e.navigation.position), "work": e.task.work_kind, "reason": p.get("reason"), "action": p.get("action"),
            "tid": p.get("target_id"), "nav": None if e.navigation.target is None else str(e.navigation.target)[:40], **_extra(e, st)}

def _extra(e, st):
    """Read-only additions (pass 2): group id, group shared target, last attacker and its position/task at this tick."""
    if st is None: return {}
    gid = getattr(e.identity, "group_id", None)
    g = None if gid is None else st.groups.get(gid)
    aid = getattr(e.combat, "last_attacker_id", None)
    a = None if aid is None else st.entities.get(aid)
    ap = None if a is None else (a.task.payload or {})
    return {"gid": gid, "gtarget": None if g is None else g.shared_target_id, "gleader": None if g is None else g.leader_id,
            "gsize": None if g is None else len(g.member_ids),
            "att": aid, "att_hit_t": getattr(e.combat, "last_hit_tick", None), "att_alive": None if a is None else a.combat.alive,
            "att_pos": None if a is None else list(a.navigation.position),
            "att_task": None if a is None else [a.task.work_kind, ap.get("action"), ap.get("reason"), ap.get("target_id")]}

def main(argv):
    world, seed, ticks, cell, out = argv[0], int(argv[1]), int(argv[2]), argv[3], argv[4]
    ids = [int(x) for x in argv[5:]]
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel
    run_id = f"rpgtrace_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD audit_mode/no_frame_pacing not forced"); return 2
    with open(out, "w", encoding="utf-8") as f:
        w = lambda d: f.write(json.dumps(d, sort_keys=True) + "\n")
        last = {}; last_dead = set()
        for _ in range(ticks):
            st = kernel.state
            for i in ids:
                e = st.entities.get(i)
                if e is None: continue
                r = row(e, st.tick, st); w(r)
                if i in last and r["hunger"] < last[i]["hunger"]: w({"k": "meal", "t": st.tick, "e": i, "from": last[i]["hunger"], "to": r["hunger"]})
                if i in last and last[i]["alive"] and not r["alive"]:
                    last_dead.add(i)
                    rec = getattr(e.lifecycle, "death_record", None)
                    w({"k": "death", "t": st.tick, "e": i, "cause": None if rec is None else str(getattr(rec.cause, "value", rec.cause))})
                last[i] = r
            kernel.tick_once()
        state = kernel.state
        kernel.shutdown()
        final_hash = CanonicalStateHasher.get_hash(state)
        run_dir = Path("data") / "runs" / run_id
        ev = run_dir / "simulation_events.jsonl"
        v3_ids = set()
        if ev.exists():
            for line in ev.read_text(encoding="utf-8", errors="ignore").splitlines():
                if '"starvation_death_record"' in line:
                    pl = json.loads(line)["payload"]; v3_ids.add(pl.get("entity_id")); w({"k": "v3", **pl})
        for i in ids:
            e = state.entities.get(i)
            rec = None if e is None else getattr(e.lifecycle, "death_record", None)
            cause = None if rec is None else str(getattr(rec.cause, "value", rec.cause))
            if e is not None and not e.combat.alive and i not in last_dead: w({"k": "death", "t": state.tick, "e": i, "cause": cause, "note": "died on the last tick"})
            if cause == "STARVATION" and i not in v3_ids: w({"k": "v3_missing", "e": i}); print(f"V3_RECORD_MISSING e{i}: starved but the recorder wrote no starvation_death_record")
        want = json.loads(Path(cell).read_text(encoding="utf-8"))["final_hash"]
        ok = final_hash == want
        w({"k": "final", "final_hash": final_hash, "cell_final_hash": want, "match": ok})
    shutil.rmtree(run_dir, ignore_errors=True)
    print(("MATCH " if ok else "MISMATCH ") + final_hash[:12] + " vs cell " + want[:12])
    return 0 if ok else 3

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
