"""Read-only count of live bound groups whose binding contract has ended, and the lag in ticks (scratch; wraps GroupSystem.update_groups only).
Usage: LAG_OUT=<json> python lag_run.py <world> <seed> <ticks>   (cwd = a tree with the binding, PYTHONPATH = that tree)
Per tick, before the real call: for each LIVE group with contract_holder_id, ask the real GroupSystem._binding_end on the start-of-tick state (no same-tick
pending update, so a same-tick write is not counted as overdue). After the real call: did the result dissolve it this tick? Per group record first tick
the binding was seen ended and the tick it was dissolved; lag = dissolved tick - first ended tick. Also: was the group in the relevant set, was the tick a full scan."""
import json, os, sys
sys.path.insert(0, ".")
from src.systems.world_systems.groups import GroupSystem
from src.core.dirty import get_relevant_group_ids
ou = GroupSystem.update_groups
reasons = {}; first_ended = {}; dissolved = {}; seen_live = set(); stats = dict(ticks=0, full_scan_ticks=0, relevant_all_ticks=0, overdue_group_ticks=0, overdue_not_relevant_ticks=0, bound_live_group_ticks=0)
def ug(state, *a, **k):
    cu = a[0] if a else k.get("current_update")
    rel = get_relevant_group_ids(state, cu)
    fs = bool(cu is not None and cu.force_full_scan) or getattr(state, "_force_full_scan", False)
    stats["ticks"] += 1; stats["full_scan_ticks"] += int(fs); stats["relevant_all_ticks"] += int(len(rel) >= len(state.groups) and len(state.groups) > 0)
    ended_now = {}
    alive = lambda i: i in state.entities and state.entities[i].combat.alive
    active = lambda i: i in state.entities and state.entities[i].lifecycle.active
    for gid, g in state.groups.items():
        if g.dissolution_tick is not None or g.contract_holder_id is None: continue
        stats["bound_live_group_ticks"] += 1; seen_live.add(gid)
        e = GroupSystem._binding_end(state, g, None, alive, active)
        if e is not None:
            ended_now[gid] = e[0].value
            first_ended.setdefault(gid, state.tick)
            stats["overdue_group_ticks"] += 0
    r = ou(state, *a, **k)
    done = {row.id for row in r.groups_add_or_update if row.dissolution_tick == state.tick}
    for row in r.groups_add_or_update:
        if row.dissolution_tick == state.tick and row.contract_holder_id is not None:
            k = row.dissolution_reason.value if row.dissolution_reason else 'None'
            reasons[k] = reasons.get(k, 0) + 1
            st = row.dissolution_contract_status.value if row.dissolution_contract_status else None
            if st: reasons['status:' + st] = reasons.get('status:' + st, 0) + 1
            rel_in = row.id in rel; reasons['dissolved_in_relevant_set' if (rel_in or fs) else 'dissolved_NOT_in_relevant_set'] = reasons.get('dissolved_in_relevant_set' if (rel_in or fs) else 'dissolved_NOT_in_relevant_set', 0) + 1
    for gid in ended_now:
        if gid not in done:
            stats["overdue_group_ticks"] += 1
            if gid not in rel and not fs: stats["overdue_not_relevant_ticks"] += 1
        else: dissolved.setdefault(gid, state.tick)
    return r
GroupSystem.update_groups = staticmethod(ug)
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile(world))
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
lags = {str(g): [first_ended[g], dissolved.get(g)] for g in first_ended}
never = [g for g in first_ended if g not in dissolved]
lag_vals = [d - f for g, (f, d) in ((g, (first_ended[g], dissolved[g])) for g in dissolved)]
out = dict(world=world, seed=seed, ticks=ticks, elapsed=elapsed, stats=stats, bound_groups_seen_live=len(seen_live), groups_with_ended_binding=len(first_ended),
           dissolved_with_lag=len(dissolved), lag_ticks_max=max(lag_vals) if lag_vals else None, lag_nonzero=sum(1 for v in lag_vals if v > 0), never_dissolved=never[:20], n_never=len(never), dissolution_reasons=reasons, lags_sample=dict(list(lags.items())[:20]))
open(os.environ["LAG_OUT"], "w").write(json.dumps(out, indent=1))
print("LAG_OK", json.dumps({k: out[k] for k in ("stats","dissolution_reasons","bound_groups_seen_live","groups_with_ended_binding","lag_ticks_max","lag_nonzero","n_never")}))
