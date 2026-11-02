"""probe10 analysis, both arms. Usage: analyze10.py <out10 dir> [tag=full]. Extends analyze9 with first-diff classification, named entities, cap-exemption counts."""
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
    out = {50: 0, 200: 0, 1000: 0}
    for k, L in held.items():
        T = [r["t"] for r in L if r["acting"] or r["adj"]]; ref = max(T) if T else L[0]["t"]; span = L[-1]["t"] - ref
        for n in out:
            if span >= n: out[n] += 1
    return out
def nret(R): return len({(r["e"], r["pr"]) for r in R["pj"] if "combat_retreat" in r["pr"]})
def churn(R):
    last = collections.defaultdict(list)
    for r in R["end"]: last[r["e"]].append(r["t"])
    ad = R["adopt"]
    return dict(adopts=len(ad), never=sum(1 for r in ad if not r["threat"]), re60=sum(1 for r in ad if any(0 <= r["t"] - te <= 60 for te in last[r["e"]])),
                re60_nothreat=sum(1 for r in ad if not r["threat"] and any(0 <= r["t"] - te <= 60 for te in last[r["e"]])),
                ends=len(R["end"]), tc=sum(1 for r in R["end"] if r.get("ended_by") == "THREAT_CLEARED"))
def deaths(R):
    c = collections.Counter(); ids = {}
    for r in R["dead"]:
        if r["first"]: c[r["cause"]] += 1; ids[r["e"]] = (r["dtick"], r["cause"], r["attacker"])
    return c, ids
def cap_counts(R):
    gate = [r for r in R["gate"] if r["kind"] == "combat_retreat" and r["exempt"]]
    gate_full = [r for r in gate if r["live"] >= 3]
    kept = [r for r in R["capfull"] if r["hold_retreat"] and r["n"] > r["mx"]]
    return len(gate), len(gate_full), len(kept)
def first_diff(Rb, Rf):
    pb = [(r["t"], r["e"], r["a"], r["pr"]) for r in Rb["pj"]]; pf = [(r["t"], r["e"], r["a"], r["pr"]) for r in Rf["pj"]]
    i = next((i for i, (x, y) in enumerate(zip(pb, pf)) if x != y), None)
    if i is None: return None
    t, e = min(pb[i][0], pf[i][0]), pf[i][1]
    cands = []
    tf = pf[i]
    # classify against fix-arm events on the diverging entity at or just before the diff
    for r in Rf["end"]:
        if r["e"] == tf[1] and abs(r["t"] - tf[0]) <= 1: cands.append(f"retreat end {r.get('ended_by')} ({r['pr']}) t{r['t']}")
    if "combat_retreat" in tf[3] and tf[2]: cands.append(f"retreat adopted {tf[3]}")
    for r in Rf["gate"]:
        if r["e"] == tf[1] and r["kind"] == "combat_retreat" and r["exempt"] and r["live"] >= 3 and abs(r["t"] - tf[0]) <= 20: cands.append(f"cap-exempt retreat gate t{r['t']} live {r['live']}")
    for r in Rb["flee_nopresent"]:
        if r["e"] == tf[1] and abs(r["t"] - tf[0]) <= 20: cands.append(f"base flight w/o present threat t{r['t']}")
    return dict(base=pb[i], fix=pf[i], idx=i, cls=cands or ["other (neither a retreat end, a cap-exempt adoption nor a removed flight at that entity/tick)"])
print(f"# probe10 summary ({TAG})\n")
print("| world | seed | arm | retreat projects | stale50/200/1000 | adopts | never-threatened | re60 | re60 no threat | ends | THREAT_CLEARED | deaths | R3 max | cap-exempt gates (all/at>=3 live) | trim-kept samples | hash |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
F = {}; H = {}
for w in W:
    for s in SEEDS:
        for a in ("base", "fix"):
            R = load(w, s, a)
            if R is None: continue
            F[(w, s, a)] = R; st = stale(R); ch = churn(R); dc, _ = deaths(R); g, gf, kp = cap_counts(R)
            r3 = R["r3"][0]["ticks"] if R["r3"] else {}; h = R["fin"][0]["state_hash"] if R["fin"] else ""
            H[(w, s, a)] = h
            print(f"| {w} | {s} | {a} | {nret(R)} | {st[50]}/{st[200]}/{st[1000]} | {ch['adopts']} | {ch['never']} | {ch['re60']} | {ch['re60_nothreat']} | {ch['ends']} | {ch['tc']} | {sum(dc.values())} | {max(r3.values(), default=0)} | {g}/{gf} | {kp} | {h[:10]} |")
print("\n## Totals per arm\n")
for a in ("base", "fix"):
    t = collections.Counter()
    for k, R in F.items():
        if k[2] != a: continue
        t["runs"] += 1; t["projects"] += nret(R); st = stale(R)
        for n in st: t[f"stale{n}"] += st[n]
        for kk, v in churn(R).items(): t[kk] += v
        t["deaths"] += sum(deaths(R)[0].values()); g, gf, kp = cap_counts(R); t["capexempt_gate"] += g; t["capexempt_gate_ge3"] += gf; t["trim_kept_samples"] += kp
        t["flights_noPresent"] += len(R["flee_nopresent"])
        t["r3_gt200_entities"] += sum(1 for v in (R["r3"][0]["ticks"] if R["r3"] else {}).values() if v > 200)
    print(a, dict(t))
moved = [(w, s) for w in W for s in SEEDS if H.get((w, s, "base")) and H.get((w, s, "fix")) and H[(w, s, "base")] != H[(w, s, "fix")]]
print(f"\nHashes moved: {len(moved)} of 15: {moved}\n\n## Deaths by cause per world and arm\n")
for w in W:
    for a in ("base", "fix"):
        c = collections.Counter()
        for s in SEEDS:
            if (w, s, a) in F: c.update(deaths(F[(w, s, a)])[0])
        print(f"- {w} {a}: total {sum(c.values())} {dict(c)}")
print("\n## Per run: death delta by cause and FIRST DIFF (every run; rises marked RISE)\n")
for w in W:
    for s in SEEDS:
        if (w, s, "base") not in F or (w, s, "fix") not in F: continue
        Rb, Rf = F[(w, s, "base")], F[(w, s, "fix")]
        b, f = deaths(Rb)[0], deaths(Rf)[0]; delta = {k: f.get(k, 0) - b.get(k, 0) for k in set(b) | set(f) if f.get(k, 0) != b.get(k, 0)}
        rise = sum(f.values()) > sum(b.values())
        fd = first_diff(Rb, Rf)
        print(f"- {w} s{s}: deaths {sum(b.values())} -> {sum(f.values())} {delta or ''} {'**RISE**' if rise else ''}; first diff: {fd}")
        if rise:
            _, ib = deaths(Rb); _, if_ = deaths(Rf)
            print(f"    fix-only deaths: {sorted([(e, *v) for e, v in if_.items() if e not in ib], key=lambda x: x[1])}")
            print(f"    base-only deaths: {sorted([(e, *v) for e, v in ib.items() if e not in if_], key=lambda x: x[1])}")
print("\n## Named entities (fix vs base)\n")
for w, s, e in [("frontier_living_world", 46, 9), ("urban_political", 42, 18), ("frontier_living_world", 43, 19)]:
    for a in ("base", "fix"):
        R = F.get((w, s, a))
        if R is None: continue
        rets = sorted({(r["t"], r["pr"]) for r in R["pj"] if r["e"] == e and "combat_retreat" in r["pr"]})
        d = deaths(R)[1].get(e)
        ends = [(r["t"], r["pr"], r.get("ended_by"), r["status"]) for r in R["end"] if r["e"] == e]
        gates = [(r["t"], r["live"], r["exempt"]) for r in R["gate"] if r["e"] == e and r["kind"] == "combat_retreat"][:6]
        print(f"- {w} s{s} e{e} {a}: retreat projects {rets[:8]}{'...' if len(rets) > 8 else ''}; ends {ends[:6]}; first retreat gate calls (t, live, exempt) {gates}; death {d}")
