"""Stage-2 per-cell / per-world stop checker (read-only; reads the v5 spy JSONs). Exit codes: 0 ok, 20 = a stop tripped in a FIX-arm cell ((i), (ii) or an exception counter non-empty),
21 = a world-level stop tripped ((iii) the death bar, (iv) live-SLEEP collapse steps, or extinction; halts the set, goes to the designer for the Tier 2 read), 2 = bad input.
Every number used is printed. Readings follow the designer's ruling on 521cb8e0:
  (i)  per 50+ episode with no hit row in the hold: a qualifying run = >=50 CONSECUTIVE kept trace rows with an adjacent hostile and NO fresh wait decision AND not action_live (a live self-decided action task: ENTITY_ACT, truthy payload, action not a typed-wait label; such rows break a run and are reported as "acting under a stored HOLD", total and longest run, and do not stop). typed_wait/kill/other candidate -> STOP.
       collapse candidate whose qualifying run includes a tick AFTER task_end_tick -> STOP; a collapse candidate whose runs lie wholly inside the live sleep (task_end_tick None or every run tick <= it)
       is printed as "OWNER-LIST (i) collapse-asleep" and the run continues.
  (ii) last-tick HOLD entities: wait/kill: lag = last tick - the LAST walk decision tick (from the kept trace if the episode has one, else the spy's own list); STOP if a walk decision exists and lag > 1.
       collapse (REVISED, designer ruling): stale ONLY if is_asleep is False at the last tick AND the last SLEEP ended more than 1 tick earlier; asleep means not stale. Both fields are printed per holder, with where the
       'last SLEEP ended' tick came from: the kept trace (last row whose task_action is SLEEP, +1) for a >=50-row episode, else last_tick_hold_entities (task_end_tick, the entering task's end, with task_label/is_asleep).
       Report-only line: 'collapse-class ticks awake under HOLD' = trace rows of 50+ collapse-class episodes with a live non-SLEEP action task under the stored HOLD (the kept traces only).
  (iv) world(): collapse live-SLEEP steps on 5-seed sums: fix sum - base sum >= max(2, ceil(10% of base sum)) AND up in >=3 of 5 seeds. Per-seed values printed.
  (iii) world(): per cause, the same bar on dead_by_cause. Extinction on 5-seed sums by role: base sum >= 1 and fix sum 0 -> STOP; per-seed losses are disclosed only.
  stage2_check.py cell <fix.json> <base.json>
  stage2_check.py world <outdir> <world>
"""
import json, math, sys

def load(p):
    return json.load(open(p))

def clean(d):
    return d["exceptions"] == {} and d["v4"]["v4_exceptions"] == {} and d.get("v5", {}).get("v5_exceptions") == {}

def qualifying_runs(tr):
    """Runs of consecutive trace rows with an adjacent hostile, no fresh wait decision and no live action task; returns [(first_t, last_t, length)] of length >= 50."""
    runs, cur = [], None
    for r in tr:
        has_wait = any(x["kind"] == "wait" for x in r.get("tact", []))
        if r["adj"] and not has_wait and not r.get("action_live", False):
            if cur is None:
                cur = [r["t"], r["t"], 1]
            else:
                cur[1] = r["t"]; cur[2] += 1
        else:
            if cur is not None and cur[2] >= 50:
                runs.append(tuple(cur))
            cur = None
    if cur is not None and cur[2] >= 50:
        runs.append(tuple(cur))
    return runs

def acting_stats(tr):
    """Rows where the subject holds a live self-decided action task under a stored HOLD: (total, longest consecutive run)."""
    tot = best = run = 0
    for r in tr:
        if r.get("action_live", False):
            tot += 1; run += 1; best = max(best, run)
        else:
            run = 0
    return tot, best

def cell(fixp, basep):
    f, b = load(fixp), load(basep)
    fv, bv = f["v4"], b["v4"]
    trip = []
    print(f"cell {fixp.split('/')[-1]} counters clean: fix={clean(f)} base={clean(b)}")
    if not (clean(f) and clean(b)):
        trip.append("EXCEPTIONS (the arm is void)")
    # (i)
    for e in fv["episodes_50plus_verdicts"]:
        v5 = (e["VERDICT"].get("V5") or {})
        a_tot, a_best = acting_stats(e["trace"])
        if a_tot:
            print(f"  acting_under_stored_hold e{e['entity']} {e['cls']} {e['entry_label']} t{e['start_tick']}-{e['end_tick']}: total {a_tot} longest run {a_best} of {len(e['trace'])} rows")
        if v5.get("any_hit_row") or e["VERDICT"].get("any_hit_during_hold"):
            continue
        runs = qualifying_runs(e["trace"])
        if not runs:
            continue
        te = e["task_end_tick"]
        after = [r for r in runs if te is not None and r[1] > te]
        tag = f"e{e['entity']} {e['cls']} {e['entry_label']} t{e['start_tick']}-{e['end_tick']} runs={runs} task_end_tick={te}"
        if e["cls"] == "collapse" and not after:
            print(f"  OWNER-LIST (i) collapse-asleep: {tag}")
        else:
            print(f"  (i) STOP candidate: {tag}")
            trip.append(f"(i) e{e['entity']} {e['cls']}")
    rw = f["v5"]["rechosen_wait_summary_50plus"]
    print(f"  re-chosen waits in 50+ episodes (reported): {rw}")
    # (ii)
    t_end = f["ticks"]
    by_ent = {e["entity"]: e for e in fv["episodes_50plus_verdicts"] if e["ended"] == "still_hold_at_end"}
    for x in fv["last_tick_hold_entities"]:
        te = x["task_end_tick"]
        if x["episode_class"] == "collapse":
            ep = by_ent.get(x["entity"])
            if ep is not None:
                sl = [r["t"] for r in ep["trace"] if r.get("task_action") == "SLEEP"]
                ended, src = ((sl[-1] + 1) if sl else te), "trace (last SLEEP row + 1)"
            else:
                ended, src = te, "last_tick_hold_entities.task_end_tick (the entering task's end)"
            stale = (not x["is_asleep"]) and ended is not None and (t_end - ended) > 1
            print(f"  (ii) last-tick HOLD e{x['entity']} collapse is_asleep={x['is_asleep']} task_label={x['task_label']} last_SLEEP_ended={ended} [{src}] lag={(t_end - ended) if ended is not None else None} stale={stale}")
        else:
            ep = by_ent.get(x["entity"])
            if ep is not None:
                walks = [r["t"] for r in ep["trace"] if any(y["kind"] == "walk" for y in r.get("tact", [])) or any(y["kind"] == "walk" for y in r.get("strat", []))]
            else:
                walks = list(x["walk_decision_ticks_since_task_end"])
            lag = (t_end - walks[-1]) if walks else None
            stale = bool(walks) and lag > 1
            print(f"  (ii) last-tick HOLD e{x['entity']} {x['episode_class']} last_walk_tick={(walks[-1] if walks else None)} lag={lag} stale={stale} (source={'trace' if ep is not None else 'spy list'})")
        if stale:
            trip.append(f"(ii) e{x['entity']}")
    awake_ticks = 0
    for e in fv["episodes_50plus_verdicts"]:
        if e["cls"] == "collapse":
            awake_ticks += sum(1 for r in e["trace"] if r.get("action_live") and r.get("task_action") != "SLEEP")
    print(f"  collapse-class ticks awake under HOLD (report-only; kept traces of 50+ collapse episodes): {awake_ticks}")
    live = lambda d: d["counts_by_class_and_label"].get("class:collapse", {}).get("hold_steps_hold_task_live", 0)
    print(f"  (iv) [world-level] collapse live-SLEEP steps fix={live(f)} base={live(b)}")
    print(f"  collapse 1-tick lag episodes fix={f['v5']['collapse_lag_1tick_count']} base={b['v5']['collapse_lag_1tick_count']}; AVOID_NO_ROUTE eps hit while holding fix={f['v5']['avoid_no_route_episodes_hit_while_holding']}/{f['v5']['avoid_no_route_episodes']} base={b['v5']['avoid_no_route_episodes_hit_while_holding']}/{b['v5']['avoid_no_route_episodes']}")
    print(f"  whole-run OA (multi/OA path only) fix={fv['whole_run_combat_multi_or_oa_path_only']} base={bv['whole_run_combat_multi_or_oa_path_only']}")
    print("  TRIPPED: " + ("; ".join(trip) if trip else "none"))
    return 20 if trip else 0

def bar_rows(rows):
    fs, bs = sum(r[1] for r in rows), sum(r[2] for r in rows)
    up = sum(1 for r in rows if r[1] > r[2])
    bar = max(2, math.ceil(0.10 * bs))
    return fs, bs, up, bar, ((fs - bs) >= bar and up >= 3)

def world(outdir, w):
    seeds = [42, 43, 44, 45, 46]
    causes, live, roles = {}, [], {}
    for s in seeds:
        F, B = load(f"{outdir}/fix_{w}_s{s}_v7.json"), load(f"{outdir}/base_{w}_s{s}_v7.json")
        f, b = F["v4"]["end_census"], B["v4"]["end_census"]
        for c in set(f["dead_by_cause"]) | set(b["dead_by_cause"]):
            causes.setdefault(c, []).append((s, f["dead_by_cause"].get(c, 0), b["dead_by_cause"].get(c, 0)))
        lv = lambda d: d["counts_by_class_and_label"].get("class:collapse", {}).get("hold_steps_hold_task_live", 0)
        live.append((s, lv(F), lv(B)))
        for role in set(f["alive_by_role"]) | set(b["alive_by_role"]) | set(f["total_by_role"]):
            roles.setdefault(role, []).append((s, f["alive_by_role"].get(role, 0), b["alive_by_role"].get(role, 0)))
    trip = []
    a_sum = a_max = aw_sum = 0
    for s in seeds:
        for e in load(f"{outdir}/fix_{w}_s{s}_v7.json")["v4"]["episodes_50plus_verdicts"]:
            t_, b_ = acting_stats(e["trace"]); a_sum += t_; a_max = max(a_max, b_)
            if e["cls"] == "collapse":
                aw_sum += sum(1 for r in e["trace"] if r.get("action_live") and r.get("task_action") != "SLEEP")
    print(f"world {w}: collapse-class ticks awake under HOLD (report-only, fix kept traces): {aw_sum}")
    print(f"world {w}: acting_under_stored_hold in fix 50+ episodes: total rows {a_sum}, longest single run {a_max}")
    print(f"world {w}: bar = fix sum - base sum >= max(2, ceil(10% of base sum)) AND up in >=3 of 5 seeds")
    fs, bs, up, bar, t1 = bar_rows(live)
    print(f"  (iv) collapse live-SLEEP steps: fix sum {fs} base sum {bs} diff {fs-bs} bar {bar} up_in_seeds {up}/5 per-seed(seed,fix,base) {live} TIER={t1}")
    if t1:
        trip.append("(iv)")
    for c, rows in sorted(causes.items()):
        fs, bs, up, bar, t1 = bar_rows(rows)
        print(f"  (iii) cause {c}: fix sum {fs} base sum {bs} diff {fs-bs} bar {bar} up_in_seeds {up}/5 per-seed {rows} TIER1={t1}")
        if t1:
            trip.append(f"(iii) {c}")
    for role, rows in sorted(roles.items()):
        fs, bs = sum(r[1] for r in rows), sum(r[2] for r in rows)
        loss = [(r[0], r[2], r[1]) for r in rows if r[2] > 0 and r[1] == 0]
        ext = bs >= 1 and fs == 0
        print(f"  extinction role {role}: alive 5-seed sum fix {fs} base {bs} STOP={ext}; per-seed losses (disclosed only) (seed,base,fix) {loss}")
        if ext:
            trip.append(f"(iii) extinction role {role}")
    print("  TRIPPED: " + ("; ".join(trip) if trip else "none"))
    return 21 if trip else 0

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "cell":
        sys.exit(cell(a[1], a[2]))
    if len(a) == 3 and a[0] == "world":
        sys.exit(world(a[1], a[2]))
    print(__doc__); sys.exit(2)
