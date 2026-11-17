import json,sys,collections
f=sys.argv[1]; R=[json.loads(l) for l in open(f)]
deaths={r["e"]:r for r in R if r["k"]=="death"}
tacs=[r for r in R if r["k"]=="tac"]; ticks={r["t"]:r for r in R if r["k"]=="tick" and r["det"]}
mk=[r for r in R if r["k"]=="mark"][0]
victims=sorted({e for r in R if r["k"]=="static" for e in map(int,r["ents"])})
BR=("5.2_bracket_if","5.2_bracket_pos","4.1_role_read","4.1_guard_pos","4.2_dist_check","5.3_vanguard_if_second")
def det(t,e):
    r=ticks.get(t); 
    if not r: return None
    return r["det"].get(str(e)) or r["det"].get(e)
for v in victims:
    D=deaths.get(v)
    if not D: print(f"== victim {v}: no death row in this run"); continue
    k=D["att"]; tD=D["t"]
    # first hit by the killer on v inside the window
    first=None; prev=None
    for t in sorted(ticks):
        x=det(t,v)
        if not x: continue
        key=(x["last_att"],x["last_hit_t"])
        if x["last_att"]==k and x["last_hit_t"] is not None and first is None: first=x["last_hit_t"]
    rng=None
    for t in sorted(ticks):
        x=det(t,v)
        if x and k in x["near10"]: rng=t; break
    gid=None
    print(f"== victim {v}: death t{tD} COMBAT killer {k} (hp {D['hp']} at {D['pos']}); killer's first hit on victim in the window: t{first}; killer first within Euclid 10 of victim: t{rng}")
    # who moved before the first hit: victim position series vs killer position at its traced calls
    vp=[(t,det(t,v)["pos"]) for t in sorted(ticks) if det(t,v) and (first is None or t<=first)]
    moves=[(t0,p0,t1,p1) for (t0,p0),(t1,p1) in zip(vp,vp[1:]) if p0!=p1]
    print("   victim position changes before/at contact (last 6):",moves[-6:])
    for r in sorted(tacs,key=lambda r:(r["t"],r["e"])):
        if r["e"] in (v,k) and (first is None or r["t"]<=first+1) :
            mh=[m for m,h in r["marks_hit"].items() if h and m in BR]
            print(f"   t{r['t']} e{r['e']} {'VICTIM' if r['e']==v else 'KILLER'} pos{r['pos']} grp{r['group']} hostiles{r['hostiles']} tgt{r['target']} ret{r.get('ret_line')}/{r.get('ret_reason')} role/group marks {mh} scores{r['scores']}")
    # group/role branch fired by either side at any traced call before first hit
    pre=[(r["t"],r["e"],r.get("ret_reason"),[m for m,h in r["marks_hit"].items() if h and m in BR]) for r in tacs if r["e"] in (v,k) and (first is None or r["t"]<first) and (r.get("ret_reason")=="BRACKETING" or any(h and m in BR for m,h in r["marks_hit"].items()))]
    print("   group/role branches fired by victim or killer BEFORE the first hit:",pre)
    post=[(r["t"],r["e"],r.get("ret_reason")) for r in tacs if r["e"] in (v,k) and first is not None and r["t"]>=first and (r.get("ret_reason")=="BRACKETING" or any(h and m in BR for m,h in r["marks_hit"].items()))]
    print("   ... at or after the first hit:",post)
print("control: marks hit anywhere",{m:c for m,c in collections.Counter(m for r in tacs for m,h in r["marks_hit"].items() if h).items()})
print("traced entities/calls:",len(tacs),"| hook control window",mk["control"])
