"""Death-STOP bar (rpg-designer standing bar via rpg-planner, 2026-11-01). Usage: analyze12.py <out dir> [tag=full]
Reads probe10/probe11 logs (needs no new probe fields). For each (world, cause) among HAZARD, COMBAT, DEFEAT: the per-seed base and fix counts, the 5-seed totals,
TIER 1 (STOP) = total rises by >= max(2, ceil(10% of base total)) AND rises in >= 3 of 5 seeds; TIER 2 = any smaller rise (extra victims listed with path + mechanism test);
REPORTED ONLY = per-pair rises, an all-cause rise with no cause in either tier.
Mechanism test (Tier 2 victim): within 200t of death the victim held a retreat project adopted (pj row, alive, combat_retreat) or completed (end row ended_by THREAT_CLEARED) on the fix arm. Pass -> STOP with the chain; fail -> divergence, reported."""
import json, sys, math, collections
D = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else "full"
W = ["urban_political", "crowded_frontier", "frontier_living_world"]; SEEDS = [42, 43, 44, 45, 46]; CAUSES = ["HAZARD", "COMBAT", "DEFEAT"]
def load(w, s, a):
    R = collections.defaultdict(list)
    try:
        for l in open(f"{D}/{TAG}_{w}_s{s}_{a}.jsonl"):
            r = json.loads(l); R[r["k"]].append(r)
    except FileNotFoundError: return None
    return R
def deaths(R): return {r["e"]: r for r in R["dead"] if r["first"]}
def path(R, e, dt, span=60):
    pj = [(r["t"], r["pr"] or "-") for r in R["pj"] if r["e"] == e and dt - span <= r["t"] <= dt + 1]
    return pj
def mech(R, e, dt):
    ad = [(r["t"], r["pr"]) for r in R["pj"] if r["e"] == e and r["a"] and "combat_retreat" in (r["pr"] or "") and dt - 200 <= r["t"] <= dt]
    tc = [(r["t"], r["pr"]) for r in R["end"] if r["e"] == e and r.get("ended_by") == "THREAT_CLEARED" and dt - 200 <= r["t"] <= dt]
    return ad, tc
def dt_line(R, e):
    x = next((r for r in R["dtask"] if r["e"] == e), None)
    if x is None: return "no dtask record (old log)"
    en = x["entry"] or {}
    return (f"at death task {x['task']} mode {x['mode']} reason {x['reason']} action {x['action']} project {x['project']}; entry tick t{en.get('t')} pos {en.get('pos')} move {en.get('work_kind')} reason {en.get('reason')} mode {en.get('mode')} project {en.get('project')} writer {x['entry_writer'] or 'project/other (no tactical reason)'}")
def outcome(R, e, d):
    """Final tier-2 wording: PASS only if a CAUSAL step of the death path, within 200t of death, is a retreat adopted or completed (THREAT_CLEARED) under the new rules; merely holding one is not enough.
    PASS: the entry move into the death tile (last position change) was a project-driven move (no tactical reason) made while the retreat project was current, or the first post-clear choice after a THREAT_CLEARED was that move's project. A tactical-reason entry move (retreat_destination never reads the retreat project) or a retreat merely current at death is FAIL.
    NOT SHOWN only when the logs cannot tell whether the retreat selected the path (no death-path record); a retreat in the window that did not select the entry move is FAIL (trajectory, as #769). FAIL: none in the window."""
    ad, tc = mech(R, e, d["dtick"]); x = next((r for r in R["dtask"] if r["e"] == e), None); en = (x or {}).get("entry") or {}
    # designer ruling 2026-11-01 (e34/e8): retreat_destination() never reads the retreat project, so an entry move with a tactical reason (PANIC_RETREAT, REGROUP, ...) is tactical flight, the same on both arms, even while a retreat project is current; and a retreat merely current at death is holding, not selecting.
    if "combat_retreat" in (en.get("project") or "") and not en.get("reason"): return f"PASS: retreat {en['project']} was current on a project-driven entry move (no tactical reason) into the death tile at t{en['t']} -> STOP to the designer with this chain"
    for tcr in reversed(tc):   # completion is causal too: the first post-clear choice is the project on the entry move into the death tile
        nxt = next((r for r in sorted(R["pj"], key=lambda r: r["t"]) if r["e"] == e and r["t"] >= tcr[0] and r["a"] and r["pr"] and "combat_retreat" not in r["pr"]), None)
        if nxt is not None and en.get("project") == nxt["pr"]:
            return f"PASS: THREAT_CLEARED of {tcr[1]} at t{tcr[0]}; first post-clear choice {nxt['pr']} (t{nxt['t']}, {'resumed' if int(nxt['pr'].rsplit('_', 1)[-1]) < tcr[0] else 'adopted'}) was the project on the entry move into the death tile at t{en.get('t')} -> STOP to the designer with this chain"
    if ad or tc:
        if x is None or not en:   # the logs cannot tell whether the retreat selected the path
            return f"NOT SHOWN: retreat adopted {ad[:3]} / THREAT_CLEARED {tc[:3]} within 200t, and no death-path record (task, entry move) to tell whether it selected the walk -> rows to the designer"
        return f"FAIL: retreat adopted {ad[:3]} / THREAT_CLEARED {tc[:3]} within 200t, but the entry move into the death tile (t{en.get('t')}, project {en.get('project')}, reason {en.get('reason')}) and the death task were not selected by it: trajectory only (it changed who fought or where), divergence, reported"
    return "FAIL: no retreat adopted or completed within 200t -> divergence, reported"
def first_diff(Rb, Rf):
    pb = [(r["t"], r["e"], r["a"], r["pr"]) for r in Rb["pj"]]; pf = [(r["t"], r["e"], r["a"], r["pr"]) for r in Rf["pj"]]
    i = next((i for i, (x, y) in enumerate(zip(pb, pf)) if x != y), None)
    return None if i is None else dict(base=pb[i], fix=pf[i])
R = {(w, s, a): load(w, s, a) for w in W for s in SEEDS for a in ("base", "fix")}
def cnt(w, s, a, c):
    x = R[(w, s, a)]
    return None if x is None else sum(1 for r in deaths(x).values() if r["cause"] == c)
print(f"# Death bar ({TAG})\n\n## Per world and cause, per seed (base/fix), totals, tier\n")
print("| world | cause | " + " | ".join(f"s{s}" for s in SEEDS) + " | base total | fix total | threshold | seeds rising | tier |\n|" + "---|" * (len(SEEDS) + 7))
tier1, tier2 = [], []
for w in W:
    for c in CAUSES:
        pairs = [(cnt(w, s, "base", c), cnt(w, s, "fix", c)) for s in SEEDS]
        if any(b is None or f is None for b, f in pairs): print(f"| {w} | {c} | incomplete |"); continue
        bt, ft = sum(b for b, _ in pairs), sum(f for _, f in pairs); th = max(2, math.ceil(0.10 * bt)); ris = sum(1 for b, f in pairs if f > b)
        t = "TIER 1 STOP" if (ft - bt >= th and ris >= 3) else ("TIER 2" if ft > bt else "-")
        if t == "TIER 1 STOP": tier1.append((w, c))
        elif t == "TIER 2": tier2.append((w, c))
        print(f"| {w} | {c} | " + " | ".join(f"{b}/{f}" for b, f in pairs) + f" | {bt} | {ft} | +{th} | {ris} | {t} |")
allc = {}
for w in W:
    bt = sum((cnt(w, s, "base", c) or 0) for s in SEEDS for c in CAUSES); ft = sum((cnt(w, s, "fix", c) or 0) for s in SEEDS for c in CAUSES)
    print(f"\n- {w} all three causes: base {bt}, fix {ft}" + (" (RISE)" if ft > bt else ""))
    if ft > bt and not any(k[0] == w for k in tier1 + tier2): print("  all-cause rise with no cause in either tier: reported only")
print(f"\nTIER 1 STOPs: {tier1 or 'none'}\nTIER 2 pairs: {tier2 or 'none'}")
print("\n## Tier 2 / Tier 1 extra victims (fix-arm death of this cause, entity not dead of this cause on base): first diff, path, mechanism test\n")
for w, c in tier1 + tier2:
    for s in SEEDS:
        Rb, Rf = R[(w, s, "base")], R[(w, s, "fix")]
        if cnt(w, s, "fix", c) <= cnt(w, s, "base", c): continue
        db, df = deaths(Rb), deaths(Rf)
        print(f"- {w} {c} s{s}: base {cnt(w, s, 'base', c)} fix {cnt(w, s, 'fix', c)}; run first diff {first_diff(Rb, Rf)}")
        for e, d in sorted(df.items(), key=lambda x: x[1]["dtick"]):
            if d["cause"] != c or (e in db and db[e]["cause"] == c): continue
            ad, tc = mech(Rf, e, d["dtick"]); held = "combat_retreat" in (d["pr"] or "")
            verdict = outcome(Rf, e, d)
            b = db.get(e)
            print(f"    - e{e} died t{d['dtick']} {c} attacker {d['attacker']}; holding retreat at death: {held}; retreats adopted in window {ad[:4]}; THREAT_CLEARED in window {tc[:4]}; OUTCOME {verdict}")
            print(f"      death detail: {dt_line(Rf, e)}")
            print(f"      base fate: {('died t%s %s attacker %s' % (b['dtick'], b['cause'], b['attacker'])) if b else 'alive at end'}; fix project path last 60t: {path(Rf, e, d['dtick'])[-8:]}; base path: {path(Rb, e, d['dtick'])[-8:]}")

print("\n## Tactical chase into drain terrain (HAZARD victims, all fix-arm HAZARD deaths): entry writer counts, so the older INTERCEPTING/BRACKETING defect is not counted against retention\n")
for w in W:
    for a in ("base", "fix"):
        c = collections.Counter()
        for s in SEEDS:
            Rx = R[(w, s, a)]
            if Rx is None: continue
            for e, d in deaths(Rx).items():
                if d["cause"] != "HAZARD": continue
                x = next((r for r in Rx["dtask"] if r["e"] == e), None)
                c[(x["entry"] or {}).get("reason") if x else "no-record"] += 1
        print(f"- {w} {a}: HAZARD deaths by entry-move reason {dict(c)}")
print("\n## Reported only: per-seed rises inside a (world, cause) whose 5-seed total did not rise (victim ids; no PASS/FAIL/NOT SHOWN review)\n")
for w in W:
    for c in CAUSES:
        if (w, c) in tier1 + tier2: continue
        for s in SEEDS:
            if R[(w, s, "base")] is None or R[(w, s, "fix")] is None or cnt(w, s, "fix", c) <= cnt(w, s, "base", c): continue
            db, df = deaths(R[(w, s, "base")]), deaths(R[(w, s, "fix")])
            ids = sorted((e, d["dtick"]) for e, d in df.items() if d["cause"] == c and not (e in db and db[e]["cause"] == c))
            print(f"- {w} {c} s{s}: base {cnt(w, s, 'base', c)} -> fix {cnt(w, s, 'fix', c)}; fix-only victims (entity, tick) {ids}")
