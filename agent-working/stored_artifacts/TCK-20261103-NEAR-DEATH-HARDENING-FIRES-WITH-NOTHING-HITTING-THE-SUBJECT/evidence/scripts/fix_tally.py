"""Read-only: base vs fix cells (tools/rpg_measure/stats). usage: fix_tally.py <baseDir> <fixDir> [fix-cell-prefix-for-base]"""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from tools.rpg_measure import stats
bd, fd = Path(sys.argv[1]), Path(sys.argv[2]); bp = sys.argv[3] if len(sys.argv) > 3 else ""
W = "crowded_frontier"; seeds = [42,43,44,45,46]
b = [json.load(open(bd/f"{bp}{W}_{s}.json")) for s in seeds]; n = [json.load(open(fd/f"{W}_{s}.json")) for s in seeds]
ids = [sorted(stats.people_ids(x["start"])) for x in b]
pb = [stats.people_deaths(x, i) for x, i in zip(b, ids)]; pn = [stats.people_deaths(x, i) for x, i in zip(n, ids)]
d = [y-x for x, y in zip(pb, pn)]
for s, x, y in zip(seeds, b, n):
    cb, cn = stats.causes_by_kind(x), stats.causes_by_kind(y)
    ks = sorted(set(cb)|set(cn))
    cc=lambda c:{cs:sum(v for k,v in c.items() if k.split('|')[1]==cs) for cs in sorted({k.split('|')[1] for k in c})}
    tb_,tn_=cc(cb),cc(cn); print(f"s{s} per-cause totals B->F:", ", ".join(f"{c} {tb_.get(c,0)}->{tn_.get(c,0)}" for c in sorted(set(tb_)|set(tn_))))
    print(f"s{s} B {x['final_hash'][:10]} F {y['final_hash'][:10]} people {pb[seeds.index(s)]}->{pn[seeds.index(s)]} | moved:", ", ".join(f"{k} {cb[k]}->{cn[k]}" for k in ks if cb[k]!=cn[k]) or "none")
print("people deaths B", pb, "F", pn, "total", sum(pb), "->", sum(pn), f"delta {sum(d):+d} mean {stats.mean(d):.2f} SE {stats.standard_error(d):.2f} verdict '{stats.verdict(d)}'")
print("extinctions", stats.extinction_verdict(b, n))
tb = sum((stats.causes_by_kind(x) for x in b), Counter()); tn = sum((stats.causes_by_kind(x) for x in n), Counter())
bc = lambda c: dict(sorted(Counter({cs: sum(v for k,v in c.items() if k.split('|')[1]==cs) for cs in {k.split('|')[1] for k in c}}).items()))
print("per-cause B", bc(tb)); print("per-cause F", bc(tn))
ab = sum((stats.alive_by_kind(x) for x in b), Counter()); an = sum((stats.alive_by_kind(x) for x in n), Counter())
print("alive by kind (sum 5 seeds) B", dict(sorted(ab.items()))); print("                          F", dict(sorted(an.items())))
for s, x, y in zip(seeds, b, n):
    if s != 45: continue
    print(f"e31 s{s}: B {x['final'].get('31')} F {y['final'].get('31')}")
