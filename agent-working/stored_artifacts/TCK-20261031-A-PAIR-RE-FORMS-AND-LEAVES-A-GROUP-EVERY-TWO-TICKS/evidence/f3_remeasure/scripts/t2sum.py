import json,sys
R=[json.loads(l) for l in open(sys.argv[1])]
deaths={r["e"]:r for r in R if r["k"]=="death"}
tacs=[r for r in R if r["k"]=="tac"]; ticks={r["t"]:r for r in R if r["k"]=="tick" and r["det"]}
WINS=[]
for p in sys.argv[2].split(";"):
    rg,v=p.split(":"); a,b=rg.split("-"); WINS.append((int(a),int(b),int(v)))
def det(t,e):
    r=ticks.get(t); return None if not r else (r["det"].get(str(e)) or r["det"].get(e))
def fired(r):
    why=[]
    if r.get("ret_reason")=="BRACKETING": why.append("BRACKETING returned")
    mh=r["marks_hit"]
    for m in ("5.2_bracket_pos","4.1_role_read","4.1_guard_pos","4.2_dist_check"):
        if mh.get(m): why.append(m)
    gb=[v[1] for v in (r["scores"] or {}).values() if v[1]!=1.0]
    if gb: why.append("group_bias!=1: "+str(gb))
    return why
for a,b,v in WINS:
    D=deaths.get(v)
    if not D: print(f"victim {v}: no death in window"); continue
    k=D["att"]; tD=D["t"]
    ser=[(t,det(t,v)) for t in sorted(ticks) if a<=t<=b and det(t,v)]
    first=None; prev=None
    for t,x in ser:
        key=(x["last_att"],x["last_hit_t"])
        if key!=prev and x["last_att"]==k and x["last_hit_t"] is not None and x["last_hit_t"]>=a: first=x["last_hit_t"]; break
        prev=key
    rng=next((t for t,x in ser if k in x["near10"]),None)
    gk=next((x["gid"] for t,x in ser),None)
    vt=[r for r in tacs if r["e"]==v and a<=r["t"]<=(first or tD)]; kt=[r for r in tacs if r["e"]==k and a<=r["t"]<=(first or tD)]
    vlast=vt[-1] if vt else None; klast=kt[-1] if kt else None
    f_v=[(r["t"],fired(r)) for r in vt if fired(r)]; f_k=[(r["t"],fired(r)) for r in kt if fired(r)]
    print(f"== victim {v} (death t{tD}, killer {k}): first hit by killer inside window: t{first}; killer in Euclid-10 of victim from t{rng}; victim group at window start {gk}")
    print("   victim last traced pick before contact:", None if not vlast else (vlast['t'], 'tgt',vlast['target'], 'ret',vlast.get('ret_line'),vlast.get('ret_reason'), 'tuple', (vlast['scores'] or {}).get(str(vlast['target']))))
    print("   killer last traced pick before contact:", None if not klast else (klast['t'], 'tgt',klast['target'], 'ret',klast.get('ret_line'),klast.get('ret_reason'), 'tuple', (klast['scores'] or {}).get(str(klast['target']))))
    print("   group/role branch FIRED (returned/entered body/group_bias!=1) before contact: victim",f_v,"killer",f_k)
    print("   traced calls before contact: victim",len(vt),"killer",len(kt))
