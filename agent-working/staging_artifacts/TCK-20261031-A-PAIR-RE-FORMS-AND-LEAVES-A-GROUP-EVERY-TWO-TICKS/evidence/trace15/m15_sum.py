import json, sys, collections, statistics
def load(p): return json.load(open(p))
def pct(v, q):
    if not v: return None
    v = sorted(v); return v[min(len(v) - 1, int(q * (len(v) - 1) + 0.5))]
def summ(d, has_typed):
    forms = d["forms"]; dis = d["dis"]
    last_form = {}
    # lifetime: pair each dissolution with the formation of the same id at or before it (ids are unique on the branch; on base the last formation of that id)
    byid = collections.defaultdict(list)
    for f in forms: byid[f[1]].append(f)
    life = []
    for x in dis:
        fs = [f for f in byid.get(x[1], []) if f[0] <= x[0]]
        if fs: life.append(x[0] - fs[-1][0])
    out = dict(formations=len(forms), dissolutions=len(dis), life_p50=pct(life, .5), life_p90=pct(life, .9), n_life=len(life))
    if has_typed:
        out["by_reason"] = dict(collections.Counter(x[4] or "None" for x in dis))
        out["not_active_status"] = dict(collections.Counter(x[5] for x in dis if x[4] == "BINDING_CONTRACT_NOT_ACTIVE"))
    # re-forms by the same members after a dissolution within N ticks, split by binding contract
    last_dis = {}  # members tuple -> list of (tick, contract)
    rf = {10: [0, 0], 50: [0, 0]}
    events = sorted([(x[0], 0, x) for x in dis] + [(f[0], 1, f) for f in forms], key=lambda e: (e[0], e[1]))
    for t, kind, row in events:
        key = tuple(row[2])
        if kind == 0: last_dis[key] = (t, row[3])
        else:
            if key in last_dis:
                td, c = last_dis[key]
                for N in (10, 50):
                    if 0 <= t - td <= N: rf[N][0 if row[3] == c else 1] += 1
    out["reform_same_contract_10_50"] = [rf[10][0], rf[50][0]]; out["reform_diff_contract_10_50"] = [rf[10][1], rf[50][1]]
    out["lag_nonzero"] = sum(1 for g, a, b in d["lag"] if b - a > 0); out["lag_max"] = max([b - a for g, a, b in d["lag"]], default=0)
    out["overdue_group_ticks"] = d["overdue_ticks"]; out["overdue_not_relevant"] = d["overdue_not_relevant"]; out["ended_seen_by_state_view"] = d["ended_seen"]
    out["full_scan_ticks"] = d["full_scan_ticks"]
    mb = collections.Counter(); 
    for t, gid, ld, ho, dr, hd in d["mbt"]:
        for c in set(dr.values()): mb[("holder_dropped:" if hd else "other_dropped:") + c] += 1
    out["mbt"] = dict(mb)
    out["deaths"] = len(d["deaths"]); out["deaths_by_cause"] = dict(collections.Counter(x[2] for x in d["deaths"]))
    out["active_recruit_pairs"] = d["active_pairs"]
    return out
if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = load(p); pr = {}
        for l in open(p.replace(".json", ".jsonl")):
            pr = json.loads(l)
        probe = pr.get("probe", {})
        s = summ(d, "branch" in p)
        s.update(file=p.split("/")[-1], hash=d["state_hash"][:12], elapsed_s=round(d["elapsed"]), overwrites_loose=probe.get("pre_loose"), ghost=probe.get("ghost_any"), tick_ms_mean=round(probe.get("tick_ms", 0) / max(probe.get("tick_calls", 1), 1), 2), store_records=probe.get("end_groups"), store_dissolved=probe.get("end_dissolved"))
        print(json.dumps(s))
