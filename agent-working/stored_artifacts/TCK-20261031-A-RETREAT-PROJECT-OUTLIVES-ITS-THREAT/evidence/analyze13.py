"""Flight check (option A) for the Tier-2 victims. Usage: analyze13.py <probe12 out dir> [tag=flight]
Victims: (world, seed, entity, death tick). For each: every `fl` row (an is_fleeing tick) within 200t before death: perceived count, present count, whether the base flight test (perceived) and the fix test (present) would be entered (hold_per/hold_pre), the decision taken.
A tick DIFFERS when perceived_threats and present_threats disagree about having a threat (base would be in the flight branch, fix is not). Same answer on every flight-relevant tick -> FAIL (flight check). Any DIFFER tick -> rows go to the designer (may PASS)."""
import json, sys, collections
D = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else "flight"
V = [("urban_political", 42, 14, 466), ("urban_political", 46, 3, 277), ("urban_political", 46, 13, 627), ("urban_political", 45, 16, 474),
     ("crowded_frontier", 43, 13, 370), ("crowded_frontier", 43, 32, 538), ("crowded_frontier", 43, 5, 542), ("crowded_frontier", 43, 8, 555),
     ("crowded_frontier", 43, 2, 1310), ("crowded_frontier", 43, 6, 1315), ("crowded_frontier", 43, 4, 1361)]
R = {}
def load(w, s):
    if (w, s) in R: return R[(w, s)]
    X = collections.defaultdict(list)
    try:
        for l in open(f"{D}/{TAG}_{w}_s{s}_fix.jsonl"):
            r = json.loads(l); X[r["k"]].append(r)
    except FileNotFoundError: X = None
    R[(w, s)] = X; return X
for w, s, e, dt in V:
    X = load(w, s)
    if X is None: print(f"- {w} s{s} e{e} t{dt}: no probe12 log"); continue
    fl = [r for r in X["fl"] if r["e"] == e and dt - 200 <= r["t"] <= dt]
    diff = [r for r in fl if r["differ"]]; chg = [r for r in diff if r["hold_per"] != r["hold_pre"]]
    print(f"- {w} s{s} e{e} died t{dt}: flee ticks in the 200t window {len(fl)}; perceived-vs-present disagree on {len(diff)}; base flight branch entered but fix not (hold_per true, hold_pre false) on {len(chg)} -> {'DIFFERS: rows to the designer' if diff else 'SAME on every flight-relevant tick: FAIL (flight check)'}")
    for r in (diff[:12]):
        print(f"    t{r['t']} hp {r['hp']:.2f} perceived {r['per']} present {r['pre']} hold_per {r['hold_per']} hold_pre {r['hold_pre']} dest_per {r['dest_per']} dest_pre {r['dest_pre']} taken {r['taken']}")
    if len(diff) > 12: print(f"    ... {len(diff) - 12} more")
print("\nErrors:", {k: sum(1 for x in X["fl_err"]) for k, X in ((k, v) for k, v in R.items()) if X})
