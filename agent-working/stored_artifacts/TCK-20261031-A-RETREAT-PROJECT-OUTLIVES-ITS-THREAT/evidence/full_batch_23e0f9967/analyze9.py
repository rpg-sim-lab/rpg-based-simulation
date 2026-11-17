"""Analysis of probe9 logs, both arms. Usage: analyze9.py <out9 dir> [tag=full]"""
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
def stale(R):
    held = collections.defaultdict(list)
    for r in R["rh"]: held[(r["e"], r["pr"])].append(r)
    out = {50: 0, 200: 0, 1000: 0}; nproj = 0
    for k, L in held.items():
        T = [r["t"] for r in L if r["acting"] or r["adj"]]; ref = max(T) if T else L[0]["t"]; span = L[-1]["t"] - ref
        for n in out:
            if span >= n: out[n] += 1
    return out
def nretreat(R):
    return len({(r["e"], r["pr"]) for r in R["pj"] if "combat_retreat" in r["pr"]})
def churn(R):
    ends = [r for r in R["end"]]; ad = R["adopt"]
    last_end = collections.defaultdict(list)
    for r in ends: last_end[r["e"]].append(r["t"])
    never = sum(1 for r in ad if not r["threat"])
    re60 = sum(1 for r in ad if any(0 <= r["t"] - te <= 60 for te in last_end[r["e"]]))
    re60_nothreat = sum(1 for r in ad if not r["threat"] and any(0 <= r["t"] - te <= 60 for te in last_end[r["e"]]))
    tc = [r for r in ends if r.get("ended_by") == "THREAT_CLEARED"]
    return dict(adopts=len(ad), never_threatened=never, readopt60=re60, readopt60_nothreat=re60_nothreat, ends=len(ends), threat_cleared=len(tc))
def deaths(R):
    c = collections.Counter(); ids = collections.defaultdict(list)
    for r in R["dead"]:
        if r["first"]: c[r["cause"]] += 1; ids[r["cause"]].append((r["e"], r["dtick"]))
    return c, ids
rows = []; tot = collections.defaultdict(lambda: collections.Counter())
print(f"# probe9 summary ({TAG})\n")
print("| world | seed | arm | retreat projects | stale50/200/1000 | adopts | never-threatened | re-adopt<=60t | re-adopt<=60t no threat | ends | THREAT_CLEARED | deaths | flights w/o present threat (A) | R3 max ticks | hash |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
H = {}; DC = {}; FD = {}
for w in W:
    for s in SEEDS:
        for a in ("base", "fix"):
            R = load(w, s, a)
            if R is None: continue
            st = stale(R); ch = churn(R); dc, ids = deaths(R)
            fl = R["flee_nopresent"]; r3 = (R["r3"][0]["ticks"] if R["r3"] else {})
            h = R["fin"][0]["state_hash"] if R["fin"] else None; H[(w, s, a)] = h; DC[(w, s, a)] = (dc, ids); FD[(w, s, a)] = R
            print(f"| {w} | {s} | {a} | {nretreat(R)} | {st[50]}/{st[200]}/{st[1000]} | {ch['adopts']} | {ch['never_threatened']} | {ch['readopt60']} | {ch['readopt60_nothreat']} | {ch['ends']} | {ch['threat_cleared']} | {sum(dc.values())} | {len(fl)} | {max(r3.values(), default=0)} | {(h or '')[:10]} |")
print("\n## Totals per arm\n")
for a in ("base", "fix"):
    keys = [k for k in FD if k[2] == a]
    sums = collections.Counter()
    for k in keys:
        R = FD[k]; st = stale(R); ch = churn(R)
        sums["runs"] += 1; sums["projects"] += nretreat(R)
        for n in st: sums[f"stale{n}"] += st[n]
        for kk, v in ch.items(): sums[kk] += v
        sums["deaths"] += sum(DC[k][0].values()); sums["flights_A"] += len(R["flee_nopresent"])
        sums["r3_gt200_entities"] += sum(1 for v in (R["r3"][0]["ticks"] if R["r3"] else {}).values() if v > 200)
    print(a, dict(sums))
print("\n## Hashes moved\n")
moved = [(w, s) for w in W for s in SEEDS if H.get((w, s, "base")) and H.get((w, s, "fix")) and H[(w, s, "base")] != H[(w, s, "fix")]]
print(f"{len(moved)} of {len([1 for w in W for s in SEEDS if (w,s,'base') in H and (w,s,'fix') in H])} runs moved:", moved)
print("\n## Deaths by cause per world and arm\n")
for w in W:
    for a in ("base", "fix"):
        c = collections.Counter()
        for s in SEEDS:
            if (w, s, a) in DC: c.update(DC[(w, s, a)][0])
        print(f"- {w} {a}: total {sum(c.values())} {dict(c)}")
print("\n## Per-run death delta by cause (fix - base), first-diff for changed runs\n")
for w in W:
    for s in SEEDS:
        if (w, s, "base") not in DC or (w, s, "fix") not in DC: continue
        b, f = DC[(w, s, "base")][0], DC[(w, s, "fix")][0]
        delta = {k: f.get(k, 0) - b.get(k, 0) for k in set(b) | set(f) if f.get(k, 0) != b.get(k, 0)}
        Rf, Rb = FD[(w, s, "fix")], FD[(w, s, "base")]
        tc = [r for r in Rf["end"] if r.get("ended_by") == "THREAT_CLEARED"]
        fl = Rf["flee_nopresent"]; flb = Rb["flee_nopresent"]
        first_tc = (tc[0]["e"], tc[0]["t"], tc[0]["pr"]) if tc else None
        first_fl = (flb[0]["e"], flb[0]["t"], round(flb[0]["hp"], 2), flb[0]["dist"]) if flb else None
        print(f"- {w} s{s}: death delta {delta or 'none'}; first THREAT_CLEARED end {first_tc}; base flights without present threat: {len(flb)} first {first_fl}")
