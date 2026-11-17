"""Per-pass group visit counter for step (a) (scratch; wrappers only, nothing is moved past a guard). Definitions fixed before any result is read (rpg-planner):
A visit = one entry into a pass's loop body, counted BEFORE any dissolved-skip guard, per pass: update_groups (the relevant-id loop), election, defection, cohesion.
live_at_start = live groups of state at the start of the phase (GroupPhase.resolve for the first three passes, CooperationPhase.execute for cohesion).
excess = visits - live_at_start, split by what the wrapper SAW (not by subtraction): (A) a dissolved id read from the store and skipped at the guard; (B) an id created this tick
(typed: in this tick's groups_add) that is not in the store yet; anything else is RESIDUAL. A dissolved id visited again later than its dissolve tick + 1 is flagged LATE.
Also: store records scanned per tick (the filter's own scan), summed; the old store counters stay in the probe."""
import collections
V = dict(ticks=0, live_sum=0, store_sum=0, groups_remove_ticks=0, scanned=0, passes={}, late=[], residual=[], live_last=None, visits_last_tick={})
for name in ("update_groups", "election", "defection", "cohesion"):
    V["passes"][name] = dict(visits=0, excess=0, A=0, B=0, residual=0, A_rows=[])
_cur = {}
def _classify(pass_name, ids, state, live_start, created):
    P = V["passes"][pass_name]; P["visits"] += len(ids)
    for i in ids:
        if i in live_start: continue
        P["excess"] += 1
        rec = state.groups.get(i)
        if rec is not None and rec.dissolution_tick is not None:
            P["A"] += 1
            if len(P["A_rows"]) < 40: P["A_rows"].append([state.tick, i, rec.dissolution_tick])
            if state.tick > rec.dissolution_tick + 1: V["late"].append([pass_name, state.tick, i, rec.dissolution_tick])
        elif rec is None and i in created:
            P["B"] += 1
        else:
            P["residual"] += 1; V["residual"].append([pass_name, state.tick, i, None if rec is None else rec.dissolution_tick])
def install():
    import src.core.dirty as dirty
    import src.engine.pipeline_phases.groups as pg
    import src.domains.cooperation.phase as cp
    from src.core.group_record import is_live_group
    from src.engine.pipeline_phases.groups import GroupPhase
    from src.systems.world_systems.groups import GroupSystem
    from src.domains.cooperation.phase import CooperationPhase
    # the filter's own scan
    def count_scan(orig):
        def w(groups): V["scanned"] += len(groups); return orig(groups)
        return w
    dirty.live_group_ids = count_scan(dirty.live_group_ids); dirty.live_group_items = count_scan(dirty.live_group_items)
    pg.live_group_ids = count_scan(pg.live_group_ids); cp.live_group_items = count_scan(cp.live_group_items)
    # groups phase entry: live at start, created / dissolved rows
    ores = GroupPhase.resolve
    def res(state, update, *a, **k):
        live = {g_id for g_id, g in state.groups.items() if is_live_group(g)}
        V["ticks"] += 1; V["live_sum"] += len(live); V["store_sum"] += len(state.groups); V["live_last"] = len(live)
        if update.groups_remove: V["groups_remove_ticks"] += 1
        _cur.clear(); _cur.update(state=state, live=live, created=set(), views=0)
        return ores(state, update, *a, **k)
    GroupPhase.resolve = staticmethod(res)
    oug = GroupSystem.update_groups
    def ug(state, *a, **k):
        r = oug(state, *a, **k)
        if _cur.get("state") is state: _cur["created"] = {g.id for g in r.groups_add}
        return r
    GroupSystem.update_groups = staticmethod(ug)
    # update_groups pass: the relevant ids it iterates (imported inside update_groups at each call)
    org = dirty.get_relevant_group_ids
    def rel(state, update):
        ids = org(state, update)
        if _cur.get("state") is state:
            live = _cur["live"]
            P = V["passes"]["update_groups"]; P["visits"] += len(ids)
            for i in ids:
                if i in live: continue
                P["excess"] += 1; rec = state.groups.get(i)
                if rec is not None and rec.dissolution_tick is not None:
                    P["A"] += 1
                    if len(P["A_rows"]) < 40: P["A_rows"].append([state.tick, i, rec.dissolution_tick])
                    if state.tick > rec.dissolution_tick + 1: V["late"].append(["update_groups", state.tick, i, rec.dissolution_tick])
                else:
                    P["residual"] += 1; V["residual"].append(["update_groups", state.tick, i, None if rec is None else rec.dissolution_tick])
        return ids
    dirty.get_relevant_group_ids = rel
    # election and defection passes: the ids of sorted(all_relevant_group_ids) = live store ids + the view's ids (the view is built twice per resolve)
    ogv = GroupPhase._group_view
    def gv(viewable_adds, rows):
        view = ogv(viewable_adds, rows)
        if "state" in _cur:
            _cur["views"] += 1; name = "election" if _cur["views"] == 1 else "defection"
            ids = _cur["live"] | set(view.keys())
            _classify(name, ids, _cur["state"], _cur["live"], _cur["created"])
        return view
    GroupPhase._group_view = staticmethod(gv)
    # cohesion pass: the cooperation phase's live view
    oex = CooperationPhase.execute
    def ex(state, update, *a, **k):
        _cur["coop_state"] = state; _cur["coop_live"] = {g_id for g_id, g in state.groups.items() if is_live_group(g)}
        return oex(state, update, *a, **k)
    CooperationPhase.execute = staticmethod(ex)
    oli = cp.live_group_items
    def li(groups):
        items = oli(groups)
        st = _cur.get("coop_state")
        if st is not None and st.groups is groups:
            _classify("cohesion", [i for i, _g in items], st, _cur["coop_live"], set())
        return items
    cp.live_group_items = li
def report():
    out = dict(V); out["live_per_tick_mean"] = V["live_sum"] / max(V["ticks"], 1); out["scanned_per_tick_mean"] = V["scanned"] / max(V["ticks"], 1)
    return out
