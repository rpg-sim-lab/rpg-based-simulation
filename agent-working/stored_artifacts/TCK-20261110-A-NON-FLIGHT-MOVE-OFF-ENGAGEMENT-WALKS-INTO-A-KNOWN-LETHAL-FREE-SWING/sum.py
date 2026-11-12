import json,sys
def inner(st,n=2):
    f=[x for x in (st or []) if "dataclasses.py" not in x and "free_swing_trace" not in x and "core/updates.py:merge" not in x]
    return f[:n]
for fn in sys.argv[1:]:
    d=json.load(open(fn))
    for k,ticks in d["subjects"].items():
        t=int(k.split(":")[1]); print("=====",fn.split("/")[-1],k,"match",d["match"])
        for u in (t-1,t):
            r=ticks[str(u)]; s=r["start"]; e=r["end"]
            lw=s["last_nav_write_staged_before_u"] or {}
            print(f" u={u} hp {s['hp']}->{e['hp']} pos {s['position']}->{e['position']} navT {s['nav_target']}->{e['nav_target']} task {s['task_work_kind']} {s['task_payload']}")
            print(f"   engaged {s['engaged_hostiles']} adj {s['adjacent_alive_ids']} group {s['group_id']} {s['group_members']}")
            print(f"   last staged nav write before u: tick {lw.get('tick')} set={lw.get('target_set')} clear={lw.get('target_clear')}/{lw.get('clear_target')} via {inner(lw.get('stack'),2)}")
            print("   decisions", [ (x.get('work_kind'),x.get('action'),x.get('reason'),x.get('target_id'),x.get('nav_target_set')) for x in r['decisions']])
            seen=set()
            for x in []:
                key=tuple(inner(x["stack"],1))
                if key in seen: continue
                seen.add(key); print("   staged new_position",x["new_position"],"via",key)
            for x in r["resolve_move"]: print("   resolve_move target",x.get("target"),"mode",x.get("mode"),"->",x.get("result_new_position"),"called from",inner(x.get("stack"),1))
            for x in r["swaps"]: print("   swap with",x["with"],inner(x["stack"],1))
            for x in r["bracketing"]: print("   bracketing",x)
            for x in r["opp_calls"]: print("   OPP",x["fn"],"attackers",x["attackers"],"hp_before",x["hp_before_call"],"is_lethal_arg",x["is_lethal_arg"],"damage",x["result_damage_taken"],"hp_delta",x["result_hp_delta"],x["result_outcome_kind"],"from",inner(x["stack"],2))
