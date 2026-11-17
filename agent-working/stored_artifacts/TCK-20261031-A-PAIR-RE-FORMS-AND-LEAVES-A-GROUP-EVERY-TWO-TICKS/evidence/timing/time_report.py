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
    bar = 0.05 * base_total_ms
    def outside(vb, vr):
        m = statistics.median(vr)
        return max(0.0, m - max(vb), min(vb) - m)
    ruled = {}
    # RULED PHASE TEST (rpg-planner's ruling, staging rpg_designer_ruling_2026-10-31.md): groups and cooperation phases only; the branch's median sits OUTSIDE BASE's spread
    # [min, max of base's per-run values] by more than 5% of base's median TOTAL tick (ms/tick).
    rows_r = [("cooperation (kernel phase, per-run median ms/tick)", [x["phase_median_ms"]["cooperation"] for x in b], [x["phase_median_ms"]["cooperation"] for x in r]),
              ("groups phase (GroupPhase.resolve wall, per-run mean ms/tick = group_phase_ms_total / 2000)", [x["group_phase_ms_total"] / x["tick_calls"] for x in b], [x["group_phase_ms_total"] / x["tick_calls"] for x in r])]
    print(f" RULED PHASE TEST: bar = 5% of base median total tick {base_total_ms:.1f} ms = {bar:.2f} ms/tick; distance of the branch median outside base's [min,max]:")
    for name, vb, vr in rows_r:
        d = outside(vb, vr); ruled[name.split(" ")[0]] = d > bar
        print(f"   {name}: base runs {[round(v, 3) for v in vb]} median {statistics.median(vb):.3f} ; branch runs {[round(v, 3) for v in vr]} median {statistics.median(vr):.3f} ; spread of base [{min(vb):.3f}, {max(vb):.3f}] ; distance outside {d:.3f} -> {'EXCEEDS the bar' if d > bar else 'within the bar'}")
    ph = collections.defaultdict(lambda: ([], []))
    for x in b:
        for k, v in x["phase_median_ms"].items(): ph[k][0].append(v)
    for x in r:
        for k, v in x["phase_median_ms"].items(): ph[k][1].append(v)
    rows = []
    for k, (vb, vr) in ph.items():
        if len(vb) < 3 or len(vr) < 3: continue
        rows.append((abs(statistics.median(vr) - statistics.median(vb)), k, statistics.median(vb), statistics.median(vr), outside(vb, vr)))
    print(f" OTHER PHASES (not under the ruled test; reported as differences only, no pass/fail), top 6 by |branch-base| median, with the distance outside base's [min,max]:")
    for d, k, mb_, mr_, o in sorted(rows, reverse=True)[:6]: print(f"   {k}: base {mb_:.3f} branch {mr_:.3f} diff {mr_ - mb_:+.3f} ms/tick, outside base spread by {o:.3f}")
    # PAIRWISE (same rep): branch vs base total tick-sum
    pairs = [(y - x) / x * 100 for x, y in zip(tb, tr)]
    print(f" pairwise by rep (branch vs base, same rep): {[round(p, 1) for p in pairs]}% ; branch slower in {sum(1 for p in pairs if p > 0)} of 3 pairs")
    stores = max(x["store_records"] for x in r)
    hold[w] = dict(total=resolved, store=stores > 2000, ruled_phase=[k for k, v in ruled.items() if v])
    slower = sum(1 for p in pairs if p > 0)
    note = f" (rise over 5 percent on medians but the ranges overlap by {max(tb) - min(tr):.1f} s, resting on one base run of {max(tb):.1f} s: UNRESOLVED, not within noise: the branch was slower in {slower} of 3 pairs)" if (rise > 5 and not resolved) else ""
    print(f" HOLD RULE (as ruled): total tick resolved rise>5%: {resolved}{note}; store>2000: {stores > 2000} (max {stores}); ruled phases (groups, cooperation) outside base spread by >5% of base total: {hold[w]['ruled_phase'] or 'none'}")
print("\nHOLD SUMMARY", hold)
