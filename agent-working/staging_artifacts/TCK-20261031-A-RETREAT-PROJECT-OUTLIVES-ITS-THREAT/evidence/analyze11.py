"""probe11 position counts (TCK-20261101-A-RETREAT-WALKS-TOWARD-THE-THREAT). Usage: analyze11.py <out dir> [tag=full]
Per COMBAT_RETREAT project (entity, project id) on each arm: distance to the nearest PERCEIVED hostile at adoption (first held tick), minimum over the walk, and at the last held tick; share with min < adoption.
Per death while holding a retreat: killer id, whether the killer was within 10 tiles at adoption (the threat present at adoption) or met en route, distance trend to the killer over the last 30 ticks.
Base arm: same subject's fate (death tick/cause) and its positions when it held a retreat."""
import json, sys, collections
D = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else "full"
W = ["urban_political", "crowded_frontier", "frontier_living_world"]; SEEDS = [42, 43, 44, 45, 46]
def load(w, s, a):
    R = collections.defaultdict(list)
    try:
        for l in open(f"{D}/{TAG}_{w}_s{s}_{a}.jsonl"):
            r = json.loads(l); R[r["k"]].append(r)
    except FileNotFoundError: return None
    return R
def walks(R):
    rh = collections.defaultdict(list)
    for r in R["rh"]: rh[(r["e"], r["pr"])].append(r)
    d2 = {(r["e"], r["t"]): r for r in R["rh2"]}
    out = []
    for (e, pr), L in sorted(rh.items()):
        L.sort(key=lambda r: r["t"]); ser = [d2.get((e, r["t"]), {}).get("dmin") for r in L]
        known = [x for x in ser if x is not None]
        a0 = ser[0]
        out.append(dict(e=e, pr=pr, t0=L[0]["t"], t1=L[-1]["t"], adopt=a0, mn=min(known) if known else None, end=ser[-1], p0=L[0]["p"], p1=L[-1]["p"],
                        closer=(a0 is not None and known and min(known) < a0), nh0=d2.get((e, L[0]["t"]), {}).get("nh", {})))
    return out
def deaths(R): return {r["e"]: r for r in R["dead"] if r["first"]}
print(f"# probe11 positions ({TAG})\n")
tot = collections.Counter(); rows = []
for w in W:
    for s in SEEDS:
        for a in ("base", "fix"):
            R = load(w, s, a)
            if R is None: continue
            ws = walks(R)
            for x in ws:
                tot[(a, "walks")] += 1
                if x["adopt"] is not None:
                    tot[(a, "walks_with_adopt_dist")] += 1
                    if x["closer"]: tot[(a, "min_lt_adopt")] += 1
            ds = deaths(R); d2 = collections.defaultdict(dict)
            for r in R["rh2"]: d2[r["e"]][r["t"]] = r
            for e, d in ds.items():
                if "combat_retreat" not in (d["pr"] or ""): continue
                tot[(a, "deaths_holding_retreat")] += 1
                w0 = next((x for x in ws if x["e"] == e and x["pr"] == d["pr"]), None)
                k = d["attacker"]; nh0 = w0["nh0"] if w0 else {}
                present0 = k is not None and str(k) in {str(i) for i, v in nh0.items() if v <= 10}
                tr = [(t, d2[e][t]["nh"].get(str(k), d2[e][t]["nh"].get(k))) for t in range(d["dtick"] - 30, d["dtick"] + 1) if t in d2[e]]
                tr = [(t, v) for t, v in tr if v is not None]
                trend = "closing" if len(tr) >= 2 and tr[-1][1] < tr[0][1] else ("opening" if len(tr) >= 2 and tr[-1][1] > tr[0][1] else "n/a")
                tot[(a, "killer_present_at_adoption" if present0 else "killer_met_en_route")] += 1
                tot[(a, f"trend_{trend}")] += 1
                rows.append((w, s, a, e, d["dtick"], d["cause"], k, "at-adoption" if present0 else "en-route", trend, tr[:1], tr[-1:]))
print("| arm | retreat walks | with an adoption distance | min distance < adoption distance | deaths holding a retreat | killer present at adoption | killer met en route | trend closing | opening | n/a |")
print("|---|---|---|---|---|---|---|---|---|---|")
for a in ("base", "fix"):
    g = lambda k: tot[(a, k)]
    print(f"| {a} | {g('walks')} | {g('walks_with_adopt_dist')} | {g('min_lt_adopt')} ({100*g('min_lt_adopt')/max(1,g('walks_with_adopt_dist')):.0f}%) | {g('deaths_holding_retreat')} | {g('killer_present_at_adoption')} | {g('killer_met_en_route')} | {g('trend_closing')} | {g('trend_opening')} | {g('trend_n/a')} |")
print("\n## Deaths while holding a retreat (world, seed, arm, entity, tick, cause, killer, killer at adoption/en route, trend over last 30t, first and last (tick, distance))\n")
for r in rows: print("-", *r)
print("\n## Fix-arm walks that got closer (min < adoption), with the base arm's fate for the same subject\n")
for w in W:
    for s in SEEDS:
        Rf, Rb = load(w, s, "fix"), load(w, s, "base")
        if Rf is None or Rb is None: continue
        db = deaths(Rb); bw = {(x["e"]): x for x in walks(Rb)}
        for x in walks(Rf):
            if x["closer"]:
                b = db.get(x["e"]); 
                print(f"- {w} s{s} e{x['e']} {x['pr']} t{x['t0']}-{x['t1']}: adoption dist {x['adopt']}, min {x['mn']}, end {x['end']}; pos {x['p0']} -> {x['p1']}; base fate: {('died t%s %s' % (b['dtick'], b['cause'])) if b else 'alive'}")
