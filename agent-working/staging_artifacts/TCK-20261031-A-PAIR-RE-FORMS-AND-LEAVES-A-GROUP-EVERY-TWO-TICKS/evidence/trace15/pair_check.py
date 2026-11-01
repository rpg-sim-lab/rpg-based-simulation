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

# lag STOP: any FULFILLED end of a bound group whose dissolution tick is after the contract's true expiry (branch only)
ran = set(r.get("phase_ran", [])); ended = r.get("ended_log", [])
late = []
for x in r["dis"]:
    if x[4] == "BINDING_CONTRACT_NOT_ACTIVE" and x[5] == "FULFILLED" and len(x) > 8 and x[8] is not None and x[0] > x[8]:
        rel = [(e[0], e[2]) for e in ended if e[1] == x[1] and x[8] <= e[0] <= x[0]]
        late.append(dict(tick=x[0], group=x[1], members=x[2], contract=x[3], expiry=x[8], lag=x[0] - x[8], phase_ran_on_expiry_tick=(x[8] in ran), relevant_set_by_tick=rel))
fulf = [x for x in r["dis"] if x[4] == "BINDING_CONTRACT_NOT_ACTIVE" and x[5] == "FULFILLED"]
skipped = [t for t in range(1, r["ticks_run"] + 1) if t not in ran]
exp_on_skipped = [x for x in fulf if len(x) > 8 and x[8] in set(skipped)]
print("PHASE contracts-phase ticks run", len(ran), "skipped", len(skipped), "| FULFILLED ends", len(fulf), "whose true expiry fell on a skipped tick", len(exp_on_skipped), "| late (lag>0)", len(late))
if late:
    print("LAG_STOP", json.dumps(late[:20])); sys.exit(8)
