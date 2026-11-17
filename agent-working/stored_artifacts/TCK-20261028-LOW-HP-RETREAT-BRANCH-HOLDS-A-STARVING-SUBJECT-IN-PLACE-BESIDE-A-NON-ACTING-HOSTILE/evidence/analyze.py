import json,sys,collections
sys.path.insert(0,'.')
from tools.rpg_measure import stats
R="/mnt/data2/rpg-measure/lowhp/results/"; BASEC="/mnt/data2/rpg-measure/results/e755dc3d1ff2-72320cac-5000/"
CAUSES=["COMBAT","DEFEAT","HAZARD","STARVATION"]
def load(p): return json.load(open(p))
def causes(run,ids):
    c=collections.Counter()
    for i in ids:
        alive,cause,kind=run["final"][str(i)]
        if not alive: c[cause if cause in CAUSES else "other:"+str(cause)]+=1
    return c
def alive_by_kind(run,ids):
    c=collections.Counter()
    for i in ids:
        alive,cause,kind=run["final"][str(i)]
        if alive: c[kind]+=1
    return c
def report(world,seeds,basef,fixf,label):
    print(f"## {label}")
    tb=collections.Counter(); tn=collections.Counter(); ab=collections.Counter(); an=collections.Counter(); up=0
    for s in seeds:
        b=load(basef(s)); n=load(fixf(s)); ids=stats.people_ids(b["start"])
        cb,cn=causes(b,ids),causes(n,ids)
        db,dn=sum(cb.values()),sum(cn.values()); up+= dn>db
        print(f"s{s}: base {dict(cb)} total {db} | fix {dict(cn)} total {dn} | hash equal {b['final_hash']==n['final_hash']}")
        tb+=cb; tn+=cn; ab+=alive_by_kind(b,ids); an+=alive_by_kind(n,ids)
    print("TOTAL base",dict(tb),sum(tb.values()),"| fix",dict(tn),sum(tn.values()),"| seeds up",up,"of",len(seeds))
    print("alive by role base",dict(ab),"| fix",dict(an))
if __name__=="__main__":
    seeds=[42,43,44,45,46]
    report("crowded_frontier",seeds,lambda s:(R+"base_plain_crowded_frontier_42.json") if s==42 else BASEC+f"crowded_frontier_{s}.json",lambda s:R+f"fix_crowded_frontier_{s}.json","crowded_frontier (base s42 = our spot-check cell; s43-46 = lane C e755dc3d1)")
    try: report("frontier_living_world",[43],lambda s:R+"base_frontier_living_world_43.json",lambda s:R+"fix_frontier_living_world_43.json","frontier_living_world s43 (one-seed read)")
    except FileNotFoundError as e: print("pending",e)
    for s in seeds:
        n=load(R+f"fix_crowded_frontier_{s}.json"); print(f"counts s{s}",n["lowhp_counts"])
