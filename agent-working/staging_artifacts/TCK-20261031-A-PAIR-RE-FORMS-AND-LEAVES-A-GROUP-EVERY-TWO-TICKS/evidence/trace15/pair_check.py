"""After a pair: compare deaths by cause (branch vs base). Exit 7 on any rise in any cause. Prints victims and the first diff. Usage: pair_check.py <base.json> <branch.json>"""
import json, sys, collections
b = json.load(open(sys.argv[1])); r = json.load(open(sys.argv[2]))
cb = collections.Counter(x[2] for x in b["deaths"]); cr = collections.Counter(x[2] for x in r["deaths"])
rise = {c: (cb.get(c, 0), cr[c]) for c in cr if cr[c] > cb.get(c, 0)}
sb = {(x[1], x[2]) for x in b["deaths"]}; sr = {(x[1], x[2]) for x in r["deaths"]}
only_r = sorted([x for x in r["deaths"] if (x[1], x[2]) not in sb]); only_b = sorted([x for x in b["deaths"] if (x[1], x[2]) not in sr])
first = min([x[0] for x in only_r] + [x[0] for x in only_b], default=None)  # first tick of a victim present in only one run
zip_first = next(((i, x, y) for i, (x, y) in enumerate(zip(b["deaths"], r["deaths"])) if x != y), None)  # first position where the two ordered death lists differ
print("PAIR", r["world"], r["seed"], "base_deaths", sum(cb.values()), dict(cb), "branch_deaths", sum(cr.values()), dict(cr), "first_victim_set_diff_tick", first, "first_ordered_list_diff", zip_first)
if rise:
    print("PER_PAIR_RISE", json.dumps(rise), "branch_only_victims", [(x[0], x[1], x[2]) for x in only_r][:30], "base_only_victims", [(x[0], x[1], x[2]) for x in only_b][:30])
