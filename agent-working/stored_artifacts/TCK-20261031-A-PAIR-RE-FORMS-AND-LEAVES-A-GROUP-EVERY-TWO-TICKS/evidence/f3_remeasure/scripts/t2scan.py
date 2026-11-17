import json,sys
f=sys.argv[1]; R=[json.loads(l) for l in open(f)]
deaths={r["e"]:r for r in R if r["k"]=="death"}
ticks={r["t"]:r for r in R if r["k"]=="tick" and r["det"]}
tacs=[r for r in R if r["k"]=="tac"]
WINS=[]
for p in sys.argv[2].split(";"):
    rg,v=p.split(":"); a,b=rg.split("-"); WINS.append((int(a),int(b),int(v)))
def det(t,e):
    r=ticks.get(t); return None if not r else (r["det"].get(str(e)) or r["det"].get(e))
for a,b,v in WINS:
    D=deaths.get(v); ser=[(t,det(t,v)) for t in sorted(ticks) if a<=t<=b and det(t,v)]
    if not ser: continue
    hits=[]; prev=None
    for t,x in ser:
        key=(x["last_att"],x["last_hit_t"])
        if key!=prev and x["last_att"] is not None and x["last_hit_t"] is not None and x["last_hit_t"]>=a: hits.append((x["last_hit_t"],x["last_att"]))
        prev=key
    atk=sorted({h[1] for h in hits})
    print(f"== victim {v} death t{D['t'] if D else None} killer {D['att'] if D else None}; hits (tick, attacker) in window: {hits}")
    for k in atk:
        t_in=next((t for t,x in ser if k in x["near10"]),None)
        fh=min(h[0] for h in hits if h[1]==k)
        # victim position at t_in and 6 ticks earlier; attacker position at its traced calls near t_in
        pin=det(t_in,v)["pos"] if t_in else None
        e6=det(t_in-6,v)["pos"] if t_in and det(t_in-6,v) else None
        akpos=[(r["t"],r["pos"]) for r in tacs if r["e"]==k and t_in is not None and t_in-6<=r["t"]<=t_in+6]
        moved_v = (e6 is not None and pin is not None and e6!=pin)
        print(f"   attacker {k}: first within Euclid 10 of victim at t{t_in}; first hit t{fh}; victim pos t{(t_in or 0)-6}->t{t_in}: {e6}->{pin} ({'victim moved' if moved_v else 'victim still'}); attacker traced positions near entry: {akpos}")
