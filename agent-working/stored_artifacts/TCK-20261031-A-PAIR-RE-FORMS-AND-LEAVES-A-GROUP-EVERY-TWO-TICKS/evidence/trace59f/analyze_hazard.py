import json, sys, collections
D, world, seed = sys.argv[1], sys.argv[2], sys.argv[3]; victims = [int(x) for x in sys.argv[4].split(",")]
def load(p):
    T = {}; Dd = {}; st = {}
    for l in open(p):
        r = json.loads(l)
        if r["k"] == "tick": T[r["t"]] = r
        elif r["k"] == "death": Dd[r["e"]] = r
        elif r["k"] == "static": st = r["ents"]
    return T, Dd, st
T, Dd, st = load(f"{D}/branch.jsonl")
rj = json.load(open(f"/data/vboxuser/Work/groups_base/out15/{world}_s{seed}_branch.json"))
print(f"## {world} s{seed} branch tree 59f0e78bd")
for e in victims:
    d = Dd[e]; dt = d["t"]
    print(f"\n### victim {e}: death t{dt} {d['cause']} hazard={d['hazard']} att={d['att']} pos={d['pos']}; spawn static row: {st.get(str(e)) or st.get(e)}")
    rows = {t: (T[t]["det"].get(str(e)) or T[t]["det"].get(e)) for t in range(max(1, dt - 60), dt + 1) if t in T}
    # hazard entry: first tick of the final contiguous hp-drain run to death
    hp = {t: r["hp"] for t, r in rows.items() if r}
    entry = dt
    for t in range(dt, max(1, dt - 60), -1):
        if t in hp and t - 1 in hp and hp[t - 1] > hp[t]: entry = t - 1
        elif t in hp and t - 1 in hp and hp[t - 1] == hp[t]: break
    # walk start: first tick of the contiguous ENTITY_MOVE run ending at entry
    ws = entry
    for t in range(entry, max(1, dt - 60), -1):
        r = rows.get(t - 1)
        if r and r["work"] == "ENTITY_MOVE": ws = t - 1
        else: break
    # group history in window
    gtick = [t for t, r in rows.items() if r and r["gid"] is not None and r["gid"] >= 0]
    last_grouped = max(gtick) if gtick else None
    print(f" hazard entry (first hp-draining tick) t{entry} at pos {rows[entry]['pos'] if rows.get(entry) else None}; contiguous ENTITY_MOVE walk starts t{ws}; last tick in a group t{last_grouped}; group ended {'BEFORE' if last_grouped is not None and last_grouped < ws else ('AFTER/DURING' if last_grouped is not None else 'n/a (never grouped in window)')} the walk start")
    tg = collections.OrderedDict()
    for t in range(max(1, dt - 50), dt + 1):
        r = rows.get(t)
        if r and r["grp"]: tg[t] = (r["grp"][0], r["grp"][1], r["grp"][2], r["grp"][3])
    sh = []; lastv = None
    for t, v in tg.items():
        if v != lastv: sh.append((t, v)); lastv = v
    print(" group rows prior 50 ticks (t: leader,holder,contract,shared_target), changes only:", sh)
    wr = [(t, rows[t]["work"], rows[t]["reason"], rows[t]["target_id"], rows[t]["nav"], rows[t]["pos"], rows[t]["hp"], rows[t]["proj"] and rows[t]["proj"][0]) for t in range(max(ws - 2, dt - 60), dt + 1) if rows.get(t)]
    cut = [wr[0]] + [x for i, x in enumerate(wr[1:], 1) if x[1:5] != wr[i - 1][1:5] or x[0] in (entry, dt)]
    for x in cut[:14]: print("   t%d work=%s reason=%s tgt=%s nav=%s pos=%s hp=%s proj=%s" % x)
    for f in rj["forms"]:
        if e in f[2] and dt - 110 <= f[0] <= dt:
            dd = [x for x in rj["dis"] if x[1] == f[1] and x[0] >= f[0]]
            print(f"  [group] formed t{f[0]} gid {f[1]} members {f[2]} contract {f[3]} holder {f[4]} leader {f[5]} -> {[(x[0], x[4], x[5]) for x in dd[:1]]}")
