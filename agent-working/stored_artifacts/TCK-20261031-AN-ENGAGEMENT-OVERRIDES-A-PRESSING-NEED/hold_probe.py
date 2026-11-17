"""Ungated NO_RETREAT_DESTINATION (today AVOID_NO_ROUTE) hold counter (read-only; records only). Usage (cwd = tree, PYTHONPATH=.): hold_probe.py world seed ticks out.json
One row per hold RUN (consecutive ticks of the task reason AVOID_NO_ROUTE), recorded on its first tick: in a region or not, has a home region or not, Manhattan distance to the nearest
region boundary (distance to the clamp of the position into each region), distance to the nearest functional building and which side of the perceived threats it is on (behind = the building
is nearer the threats than the subject is), hp, hp ratio, the perceived hostiles' count, and after the run: death within 200 ticks of the hold start, the last attacker id and the death reason."""
import collections, json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_destinations import containing_region, _clamp_into
from tools.test_architecture.rpg_gate_run import build_kernel

rid = f"hold_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
regions = list(k.state.regions.values())
man1 = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
open_run = {}      # eid -> last tick seen
rows = []          # one dict per hold run
by_eid = collections.defaultdict(list)
hold_ticks = 0
reason_hist = collections.Counter()   # all avoid-verdict reasons seen, so a zero hold count is shown to come from a working scan
dead_tick = {}
for _ in range(ticks):
    k.tick_once(); st = k.state; t = st.tick
    for eid_ in list(by_eid):
        if eid_ not in dead_tick:
            e_ = st.entities.get(eid_)
            if e_ is None or not e_.combat.alive: dead_tick[eid_] = t
    for eid, e in st.entities.items():
        if not e.combat.alive:
            continue
        pl = e.task.payload or {}
        if pl.get("reason") in ("AVOID_NO_ROUTE", "AVOID_HOSTILE", "WATCH_HOSTILE", "KEEP_WALKING", "PANIC_RETREAT", "SAFETY_PRESSURE_RETREAT"): reason_hist[pl.get("reason")] += 1
        if pl.get("reason") != "AVOID_NO_ROUTE":
            continue
        hold_ticks += 1
        if open_run.get(eid) == t - 1:
            open_run[eid] = t
            by_eid[eid][-1]["len"] += 1
            continue
        open_run[eid] = t
        here = e.navigation.position
        hs = perceived_hostiles(e, st)
        reg = containing_region(st, here)
        home = st.regions.get(e.strategic.home_region_id) if e.strategic.home_region_id else None
        bd = None
        for rg in regions:
            c = _clamp_into(rg, (float(here[0]), float(here[1])))
            d = abs(c[0] - here[0]) + abs(c[1] - here[1])
            bd = d if bd is None else min(bd, d)
        blds = [b for b in st.buildings.values() if getattr(b, "functional", True)]
        nb = min(blds, key=lambda b: man1(b.position, here)) if blds else None
        side = None
        if nb is not None and hs:
            hx = sum(h.navigation.position[0] for h in hs) / len(hs); hy = sum(h.navigation.position[1] for h in hs) / len(hs)
            side = "behind_threat" if man1(nb.position, (hx, hy)) < man1(here, (hx, hy)) else "away_from_threat"
        row = {"tick": t, "eid": eid, "len": 1, "in_region": reg is not None, "has_home": home is not None, "dist_region_boundary": bd,
               "dist_nearest_building": man1(nb.position, here) if nb is not None else None, "building_kind": getattr(nb, "kind", None), "building_side": side,
               "hp": e.combat.hp, "hp_ratio": round(e.combat.hp / max(1, e.combat.max_hp), 3), "n_hostiles": len(hs), "last_attacker": e.combat.last_attacker_id,
               "hunger": round(e.biological.hunger, 1), "death_within_200": None, "death_reason": None, "killer": None}
        rows.append(row); by_eid[eid].append(row)
# death within 200t of each hold start (resolved from final state + recorded deaths)
deaths = {}
for eid, e in k.state.entities.items():
    if not e.combat.alive:
        deaths[eid] = (str(getattr(e.lifecycle, "death_reason", None)), e.combat.last_attacker_id)
for r in rows:
    d = deaths.get(r["eid"])
    r["died_eventually"] = d is not None
    dt = dead_tick.get(r["eid"])
    r["death_within_200"] = dt is not None and dt - r["tick"] <= 200
    r["death_tick"] = dt
    if d is not None:
        r["death_reason"], r["killer"] = d
h = CanonicalStateHasher.get_hash(k.state)
doc = {"world": world, "seed": seed, "ticks": ticks, "hash": h, "hold_ticks": hold_ticks, "avoid_reason_ticks": dict(reason_hist), "hold_runs": len(rows), "subjects": len({r["eid"] for r in rows}), "rows": rows}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
