"""Outside-follower count (designer's definition): per tick, per live group whose LEADER is lodged, per member NOT lodged (and alive): count conditions separately.
c_building_tile: nav target or task target_position == the leader's building tile (the leader's position);  c_reach_orth: == the leader tile + one of the leave offsets (the first-choice leave tiles);
c_ring: == a tile of the wider leave ring (2 <= Manhattan <= radius);  c_target_id: task target_id == leader id;  c_reason: reason contains REGROUP or FOLLOW.
Denominator: outside-member ticks with a lodged leader. Pure function over (state, lodged_fn, offsets, radius, acc)."""
import collections

def _tile(p):
    return None if p is None else (int(p[0]), int(p[1]))

def reach_sets(offsets, radius):
    orth = set(offsets)
    ring = {(dx, dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1) if 2 <= abs(dx) + abs(dy) <= radius}
    return orth, ring

def new_acc():
    return dict(denominator=0, c_building_tile=0, c_reach_orth=0, c_ring=0, c_target_id=0, c_reason=0, any=0, reasons=collections.Counter(), examples=[])

def count(state, lodged_fn, offsets, radius, acc):
    orth, ring = reach_sets(offsets, radius)
    for g in state.groups.values():
        if g.dissolution_tick is not None: continue
        leader = state.entities.get(g.leader_id)
        if leader is None or lodged_fn(leader) is None: continue
        lt = _tile(leader.navigation.position)
        for m in g.member_ids:
            if m == g.leader_id: continue
            e = state.entities.get(m)
            if e is None or not e.combat.alive or lodged_fn(e) is not None: continue
            acc["denominator"] += 1
            p = e.task.payload or {}
            tg = [_tile(e.navigation.target), _tile(p.get("target_position"))]
            tg = [x for x in tg if x is not None]
            rel = [(x[0] - lt[0], x[1] - lt[1]) for x in tg]
            c1 = any(x == lt for x in tg); c2 = any(r in orth for r in rel); c3 = any(r in ring for r in rel)
            c4 = p.get("target_id") == g.leader_id; reason = p.get("reason"); c5 = reason is not None and ("REGROUP" in str(reason) or "FOLLOW" in str(reason))
            acc["reasons"][str(reason)] += 1
            for k, v in (("c_building_tile", c1), ("c_reach_orth", c2), ("c_ring", c3), ("c_target_id", c4), ("c_reason", c5)):
                if v: acc[k] += 1
            if c1 or c2 or c3 or c4 or c5:
                acc["any"] += 1
                if len(acc["examples"]) < 20: acc["examples"].append([state.tick, g.id, g.leader_id, m, tg, p.get("target_id"), reason])
