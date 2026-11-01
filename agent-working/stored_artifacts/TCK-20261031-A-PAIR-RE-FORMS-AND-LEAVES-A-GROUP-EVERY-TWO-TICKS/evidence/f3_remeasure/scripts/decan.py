import json,sys,collections
f=sys.argv[1]; d=json.load(open(f)); L=d["lodged"]; rows=L.get("decision_rows",[])
print("hook cohesion",L.get("cohesion_hook"),"decision rows",len(rows),"leave rows",len(d.get("leave_rows",[])),"claim rows",len(d.get("claim_rows",[])))
if len(sys.argv)>2:
    e=int(sys.argv[2])
    print("== leaves of e%d:"%e)
    for r in d["leave_rows"]:
        if r["e"]==e: print("  ",r)
    print("== claims involving e%d (t>=1360):"%e)
    for r in d["claim_rows"]:
        if e in r["claimants"] and r["t"]>=1360: print("  ",r)
c=collections.Counter(); 
def changed(r):
    t=r.get("t10")
    if t is None: return "no_t10"
    if not t.get("alive"): return "dead"
    ch=[]
    if t["work"]!=r["work"] or t["reason"]!=r["reason"] or t["obj"]!=r["obj"]: ch.append("goal")
    if t["pos"]!=r["pos"]: ch.append("loc")
    return "+".join(ch) if ch else "same"
for r in rows:
    c[(r["phase"] if "phase" in r else "groups", r.get("kind"), "leader" if r.get("is_leader") else "other", "CHOSEN" if r.get("chosen_leader") else "-", "BOUND" if r.get("bound_holder") else "-", changed(r))]+=1
print("== counts by (phase, kind, role-before, chosen, bound, change within 10 ticks):")
for k,v in sorted(c.items(),key=lambda kv:-kv[1]): print(" ",v,k)
k2=collections.Counter(); 
for r in rows: k2[(r.get("kind"),changed(r))]+=1
print("== by kind x change:", dict(k2))
tot=collections.Counter(changed(r) for r in rows); print("== total split:",dict(tot))
chosen=[r for r in rows if r.get("chosen_leader") or r.get("bound_holder")]
print("== lodged stayers CHOSEN leader or BOUND holder:",len(chosen))
for r in chosen[:12]: print("  ",{k:r.get(k) for k in ("t","gid","m","kind","lodged_in","work","reason","t10")})
print("== DEFEAT deaths:")
for x in d.get("deaths_x",[]):
    if x["cause"]=="DEFEAT":
        e=x["e"]; t=x["t"]
        ll=L["by_entity_last_lodged"].get(str(e)); lv=L["by_entity_last_leave"].get(str(e))
        gs=[(f[1],f[0]) for f in d["forms"] if e in f[2] and f[0]<=t]
        gs=[(g,ft) for g,ft in gs if not any(x2[1]==g and x2[0]<t-50 for x2 in d["dis"])]
        print("  ",x,"last_lodged",ll,"last_leave",lv,"near_lodge50", (ll is not None and t-ll<=50) or (lv is not None and t-lv<=50),"groups_within50",gs[-3:])
