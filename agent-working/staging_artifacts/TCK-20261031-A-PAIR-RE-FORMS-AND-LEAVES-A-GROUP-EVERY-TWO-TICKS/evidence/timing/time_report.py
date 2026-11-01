import json, glob, statistics, collections
W = ("crowded_frontier", "frontier_living_world", "urban_political")
O = "out_time"
sw = [tuple(map(int, l.split())) for l in open(f"{O}/swap.log") if len(l.split()) == 5]
def swap(ep0, ep1):
    rows = [r for r in sw if ep0 <= r[0] <= ep1]
    if len(rows) < 2: return None
    return dict(pswpin=rows[-1][1] - rows[0][1], pswpout=rows[-1][2] - rows[0][2], min_memavail_kB=min(r[3] for r in rows), min_swapfree_kB=min(r[4] for r in rows), samples=len(rows))
def load(w, t):
    runs = []
    for r in (1, 2, 3):
        d = json.load(open(f"{O}/{w}_r{r}_{t}.json")); ep = [int(x) for x in open(f"{O}/{w}_r{r}_{t}.done").read().split()]
        d["rep"] = r; d["swap"] = swap(*ep); runs.append(d)
    return runs
def spread(v): return (max(v) - min(v)) / statistics.median(v) * 100
print("METHOD: non-audit, pinned FULL (PinnedNormalGovernor), ConcurrentExecutionAdapter; s42, 2000 ticks, PROD_SMALL, cores 4-5. Production on this host is not measured by this method (smoke: frontier s42 base 600t default governor FULL 66 / MINIMAL 281 / OFF 253).")
hold = {}
for w in W:
    b = load(w, "base"); r = load(w, "branch"); print(f"\n=== {w}")
    for lab, runs in (("base c9b9a50f4", b), ("branch 59f0e78bd", r)):
        ts = [x["tick_sum_s"] for x in runs]
        print(f" {lab}: tick-sum s per run (rep1,2,3) {[round(x, 1) for x in ts]} median {statistics.median(ts):.1f} spread {spread(ts):.1f}% | hashes {[x['state_hash'][:12] for x in runs]} {'IDENTICAL' if len({x['state_hash'] for x in runs}) == 1 else 'DIFFERENT'} | policy {[x['policy_ticks'] for x in runs]} all_full {[x['all_full'] for x in runs]} | store {[x['store_records'] for x in runs]} ghosts {[x['ghost'] for x in runs]} overwrites {[x['overwrites'] for x in runs]} | executor {runs[0]['executor']} governor {runs[0]['governor']}")
        print(f"   swap per run (pswpin pages, pswpout pages, min MemAvailable kB): {[(x['swap']['pswpin'], x['swap']['pswpout'], x['swap']['min_memavail_kB']) if x['swap'] else None for x in runs]}")
    tb = [x["tick_sum_s"] for x in b]; tr = [x["tick_sum_s"] for x in r]
    mb, mr = statistics.median(tb), statistics.median(tr); rise = (mr - mb) / mb * 100
    resolved = rise > 5 and min(tr) > max(tb)
    print(f" total tick: median base {mb:.1f} s, branch {mr:.1f} s, rise {rise:+.1f}% ; ranges base [{min(tb):.1f},{max(tb):.1f}] branch [{min(tr):.1f},{max(tr):.1f}] -> {'RESOLVED rise >5%' if resolved else ('rise >5% but ranges overlap (unresolved)' if rise > 5 else 'no resolved rise >5%')}")
    base_total_ms = statistics.median([x["tick_mean_ms"] for x in b])
    ph = collections.defaultdict(lambda: ([], []))
    for x in b:
        for k, v in x["phase_median_ms"].items(): ph[k][0].append(v)
    for x in r:
        for k, v in x["phase_median_ms"].items(): ph[k][1].append(v)
    fire = []; rows = []
    for k, (vb, vr) in ph.items():
        if len(vb) < 3 or len(vr) < 3: continue
        mb_, mr_ = statistics.median(vb), statistics.median(vr); sp = max(max(vb) - min(vb), max(vr) - min(vr))
        beyond = abs(mr_ - mb_) - sp
        rows.append((abs(mr_ - mb_), k, mb_, mr_, sp, beyond))
        if beyond > 0.05 * base_total_ms: fire.append(k)
    print(f" phase medians (ms/tick, median of 3 per-run medians), top 8 by |branch-base|; base mean tick {base_total_ms:.1f} ms, 5% = {0.05 * base_total_ms:.2f} ms:")
    for d, k, mb_, mr_, sp, beyond in sorted(rows, reverse=True)[:8]: print(f"   {k}: base {mb_:.3f} branch {mr_:.3f} diff {mr_ - mb_:+.3f} spread {sp:.3f} beyond-spread {beyond:+.3f}")
    stores = max(x["store_records"] for x in r)
    hold[w] = dict(total=resolved, store=stores > 2000, phase=fire)
    print(f" HOLD RULE: total tick resolved rise>5%: {resolved}; store>2000: {stores > 2000} (max {stores}); phase median beyond spread by >5% of base total: {fire or 'none'}")
print("\nHOLD SUMMARY", hold)
