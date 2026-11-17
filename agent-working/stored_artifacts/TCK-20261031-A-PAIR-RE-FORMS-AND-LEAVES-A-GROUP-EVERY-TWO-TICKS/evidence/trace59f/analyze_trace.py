import json, sys
D = sys.argv[1]; world, seed = sys.argv[2], sys.argv[3]; victims = [int(x) for x in sys.argv[4].split(",")]
def load(p):
    T = {}; Dd = {}; st = {}
    for l in open(p):
        r = json.loads(l)
        if r["k"] == "tick": T[r["t"]] = r
        elif r["k"] == "death": Dd[r["e"]] = r
        elif r["k"] == "static": st = r["ents"]
    return T, Dd, st
B = load(f"{D}/base.jsonl"); R = load(f"{D}/branch.jsonl")
O15 = "/data/vboxuser/Work/groups_base/out15"
bj = json.load(open(f"{O15}/{world}_s{seed}_base.json")); rj = json.load(open(f"{O15}/{world}_s{seed}_branch.json"))
def first_diff():
    for t in sorted(B[0]):
        if t not in R[0] or B[0][t]["ent"] is None: break
        be, re_ = B[0][t]["ent"], R[0][t]["ent"]
        ds = [(e, [k for k in be[e] if be[e][k] != re_[e].get(k)]) for e in be if be[e] != re_.get(e)]
        if ds: return t, ds[:6]
    return None, []
t, ds = first_diff(); print("FIRST STATE DIFF (any key):", t, ds)
def nonlabel():
    for t in sorted(B[0]):
        if B[0][t]["ent"] is None: break
        be, re_ = B[0][t]["ent"], R[0][t]["ent"]
        for e in be:
            ks = [k for k in be[e] if k not in ("identity", "group_id", "strategic") and be[e][k] != re_[e].get(k)]
            if ks: return t, e, ks
    return None
print("FIRST DIFF outside identity/group_id/strategic:", nonlabel())
print("STATIC (spawn) rows for watch entities, branch:", {e: v for e, v in list(R[2].items())[:30]})
def story(lab, T, Dd, rows_j, e, back=60):
    d = Dd.get(e); print(f"\n== entity {e} on {lab}: death {({k:d[k] for k in ('t','cause','hazard','att','pos','hp')} if d else None)}")
    dt = d["t"] if d else 2000
    last = None; lasthp = None
    for t in range(max(1, dt - back), min(2000, dt + 1) + 1):
        r = T[t]["det"].get(e) if e in T[t]["det"] else T[t]["det"].get(str(e))
        if not r: continue
        g = r["grp"]
        sig = (r["gid"], None if g is None else (g[0], g[1], g[2], g[3]), r["work"], r["reason"], r["target_id"], r["proj"] and r["proj"][0], r["alive"])
        hpmark = "" if lasthp is None or r["hp"] == lasthp else f" hp {lasthp}->{r['hp']}"
        if sig != last or t in (dt - 1, dt) or hpmark and abs((lasthp or 0) - r["hp"]) >= 8:
            print(f" t{t}(-{dt-t}) pos={tuple(r['pos'])} hp={r['hp']}{hpmark} gid={r['gid']} grp[leader,holder,contract,shared]={None if g is None else g[:4]} work={r['work']} reason={r['reason']} tgt={r['target_id']} proj={r['proj'] and r['proj'][0]}")
            last = sig
        lasthp = r["hp"]
    fs = [f for f in rows_j["forms"] if e in f[2] and dt - 110 <= f[0] <= dt]
    for f in fs:
        dd = [x for x in rows_j["dis"] if x[1] == f[1] and x[0] >= f[0]]
        print(f"  [group] formed t{f[0]} gid {f[1]} members {f[2]} contract {f[3]} holder {f[4]} leader {f[5]} -> dissolved {[(x[0], x[4], x[5]) for x in dd[:1]]}")
for e in victims:
    for lab, T, Dd, st in (("branch", R[0], R[1], R[2]), ("base", B[0], B[1], B[2])):
        story(lab, T, Dd, rj if lab == "branch" else bj, e)
