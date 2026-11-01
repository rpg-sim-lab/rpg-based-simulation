"""World-level death check for the paired runs (designer's bar). Usage: world_check.py <world> [out15 dir]
For each cause in HAZARD, COMBAT, DEFEAT, over the world's 5 seeds (branch vs base, same seeds):
  Tier 1 (STOP): total rise >= max(2, ceil(10% of base total)) AND rise in >= 3 of 5 seeds.
  Tier 2 (victim review): any other rise > 0 (no stop); lists the extra victims = on the branch and absent on base for that cause, per seed, with their groups
      (formation tick, dissolution tick/reason, contract, whether it re-formed the same members within 50 ticks before) and re-formation after death within 50 ticks;
      the outcome field is left 'NOT SHOWN' for the trace.
  Reported only: an all-cause rise with no cause in either tier; every per-pair rise with victim ids.
Exit code 7 if Tier 1 fires for any cause, else 0."""
import json, math, sys, collections
CAUSES = ("HAZARD", "COMBAT", "DEFEAT")
world = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else "/data/vboxuser/Work/groups_base/out15"
SEEDS = (42, 43, 44, 45, 46)
def load(lab, seed):
    try: return json.load(open(f"{D}/{world}_s{seed}_{lab}.json"))
    except FileNotFoundError: return None
runs = {s: (load("base", s), load("branch", s)) for s in SEEDS}
avail = [s for s in SEEDS if all(runs[s])]
print(f"WORLD {world}: seeds with both runs: {avail}")
tier1 = False
for cause in CAUSES:
    bt = br = 0; rising = []; per = {}
    for s in avail:
        b, r = runs[s]
        nb = sum(1 for x in b["deaths"] if x[2] == cause); nr = sum(1 for x in r["deaths"] if x[2] == cause)
        bt += nb; br += nr; per[s] = (nb, nr)
        if nr > nb: rising.append(s)
    thresh = max(2, math.ceil(0.10 * bt))
    t1 = (br - bt) >= thresh and len(rising) >= 3 and len(avail) == 5
    t2 = (not t1) and (br > bt or bool(rising))
    print(f"  {cause}: base total {bt}, branch total {br}, rise {br - bt}, threshold {thresh}, seeds rising {rising} (per seed base,branch {per}) -> {'TIER1_STOP' if t1 else ('TIER2_REVIEW' if t2 else 'no rise')}")
    tier1 = tier1 or t1
    if t1 or t2:
        for s in rising:
            b, r = runs[s]
            bs = {(x[1], x[2]) for x in b["deaths"]}
            extra = [x for x in r["deaths"] if x[2] == cause and (x[1], x[2]) not in bs]
            for x in extra:
                t, e = x[0], x[1]
                gs = []
                for f in r["forms"]:
                    if e in f[2]:
                        d = [y for y in r["dis"] if y[1] == f[1] and y[0] >= f[0]]
                        dd = d[0] if d else None
                        prev = [y for y in r["dis"] if y[2] == f[2] and 0 <= f[0] - y[0] <= 50]
                        if f[0] <= t + 0 and f[0] >= t - 50 or (dd and dd[0] >= t - 50 and f[0] <= t):
                            gs.append({"gid": f[1], "formed": f[0], "members": f[2], "contract": f[3], "holder": f[4], "dissolved": None if not dd else [dd[0], dd[4], dd[5]], "reform_of_same_members_within_50": bool(prev), "prior_contract": [y[3] for y in prev]})
                after = [f for f in r["forms"] if e in f[2] and 0 < f[0] - t <= 50]
                print(f"    seed {s} extra {cause} victim {e} died t{t}; groups within 50 ticks before death: {json.dumps(gs)}; group formed within 50 ticks after death: {len(after)}; OUTCOME: NOT SHOWN (needs the trace)")
print("  all-cause per pair:")
for s in avail:
    b, r = runs[s]; cb = collections.Counter(x[2] for x in b["deaths"]); cr = collections.Counter(x[2] for x in r["deaths"])
    rises = {c: (cb.get(c, 0), cr[c]) for c in cr if cr[c] > cb.get(c, 0)}
    bs = {(x[1], x[2]) for x in b["deaths"]}
    print(f"    seed {s}: base {sum(cb.values())} {dict(cb)} branch {sum(cr.values())} {dict(cr)} rises {rises} extra victims {[(x[0], x[1], x[2]) for x in r['deaths'] if (x[1], x[2]) not in bs and x[2] in rises][:20]}")
print("TIER1_FIRED" if tier1 else "TIER1_NOT_FIRED")
sys.exit(7 if tier1 else 0)
