"""Cross-lane row for F3 lodgers (prepared; usable once an entity exposes `lodged_in`, see m15.py). Usage: lodger_check.py <world> [out15 dir]
Per world, base vs arm over the 5 seeds: lodger-ticks (entity-ticks with lodged_in set), enters, leaves, group members lodged at a group decision (summed over ticks), and for every
branch-only victim (by cause) whether it was lodged or had left a bed within 50 ticks before its death -> STOP line for rpg-planner (exit 9). Reports numbers; the sort is rpg-planner's."""
import json, sys
W = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else "/data/vboxuser/Work/groups_base/out15"
stop = False
for s in (42, 43, 44, 45, 46):
    try: b = json.load(open(f"{D}/{W}_s{s}_base.json")); r = json.load(open(f"{D}/{W}_s{s}_branch.json"))
    except FileNotFoundError: continue
    lb, lr = b.get("lodged", {}), r.get("lodged", {})
    print(f"seed {s}: field_found base {lb.get('field_found')} arm {lr.get('field_found')} | lodger-ticks {lb.get('lodger_ticks')} -> {lr.get('lodger_ticks')} | enters {len(lb.get('enters', []))} -> {len(lr.get('enters', []))} | leaves {len(lb.get('leaves', []))} -> {len(lr.get('leaves', []))} | group members lodged at a group decision {lb.get('group_decision_lodged')} -> {lr.get('group_decision_lodged')} (over {lr.get('group_decision_ticks')} ticks)")
    bs = {(x[1], x[2]) for x in b["deaths"]}
    for x in r["deaths"]:
        if (x[1], x[2]) in bs: continue
        t, e = x[0], str(x[1])
        ll, lv = lr.get("by_entity_last_lodged", {}).get(e), lr.get("by_entity_last_leave", {}).get(e)
        near = (ll is not None and t - ll <= 50) or (lv is not None and t - lv <= 50)
        if near: stop = True
        print(f"   extra victim {e} ({x[2]}, t{t}): last lodged tick {ll}, last bed-leave tick {lv} -> {'STOP: lodged or left a bed within 50 ticks' if near else 'not lodged within 50 ticks'}")
print("LODGER_STOP" if stop else "LODGER_NO_STOP"); sys.exit(9 if stop else 0)
