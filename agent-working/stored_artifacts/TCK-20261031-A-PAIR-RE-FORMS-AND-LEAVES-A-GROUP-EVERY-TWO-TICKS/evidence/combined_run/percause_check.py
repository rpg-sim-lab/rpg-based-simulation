"""Per-cause death bar over rpg_measure arm_child results (same ruler as paired). rpg-planner-ubuntu, 2026-11-07.
Usage: python3 percause_check.py <cache root> <base sha12> <new sha12> [--ticks 5000] [--child 72320cac] [--worlds w ...] [--seeds 42 43 44 45 46]
Reads <cache>/results/<sha12>-<child>-<ticks>/<world>_<seed>.json ('final': {id: [alive, cause, kind]}). Missing cell -> exit 2 (REFUSED).
Tier 1 (STOP, exit 7), per world, for each cause in HAZARD, COMBAT, DEFEAT (the designer's bar, world_check.py): 5-seed rise >= max(2, ceil(10% of base total))
AND the cause rose in >= 3 of 5 seeds. Tier 2: total rose but missed Tier 1 -> list extra victims (id, kind; arm_child records no death tick).
Starvation gate (exit 9 if any to trace; rpg-designer 2026-11-07): EVERY STARVATION death on the new arm is listed, matched against the known entries
(--known world:seed:id, e.g. crowded_frontier:46:9 for e9). Unmatched ones (also marked arm-only when not STARVATION on base; the FED test applies to
those) get a traced re-run on the recorder harness that must reproduce the cell's final_hash before its V3 reading counts. A known entry that does not
die of STARVATION on the new arm is reported as ABSENT. All entities count (designer's bar); a people-only line (base keeps_coin at tick 0, from 'start'
rows [id, kind, keeps_coin, alive]) is printed for information only. Exit 7 Tier 1, else 9 starvations to trace, else 0; 2 REFUSED (missing cell)."""
import argparse, collections, json, math, sys
from pathlib import Path
CAUSES = ("HAZARD", "COMBAT", "DEFEAT")
ap = argparse.ArgumentParser(); ap.add_argument("cache"); ap.add_argument("base"); ap.add_argument("new")
ap.add_argument("--ticks", type=int, default=5000); ap.add_argument("--child", default="72320cac")
ap.add_argument("--worlds", nargs="+", default=["crowded_frontier", "frontier_living_world", "urban_political"])
ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
ap.add_argument("--known", nargs="*", default=["crowded_frontier:46:9"]); a = ap.parse_args()
known = {tuple(k.split(":")) for k in a.known}; seen_known = set()
def path(sha, w, s): return Path(a.cache) / "results" / f"{sha[:12]}-{a.child}-{a.ticks}" / f"{w}_{s}.json"
missing = [str(path(sha, w, s)) for sha in (a.base, a.new) for w in a.worlds for s in a.seeds if not path(sha, w, s).exists()]
if missing: print("REFUSED missing cells:", missing); sys.exit(2)
def deaths(doc, ids=None): return {i: v[1] for i, v in doc["final"].items() if not v[0] and (ids is None or i in ids)}
tier1 = False; starv = []
for w in a.worlds:
    runs = {s: (json.loads(path(a.base, w, s).read_text()), json.loads(path(a.new, w, s).read_text())) for s in a.seeds}
    print(f"WORLD {w} ({len(a.seeds)} seeds, {a.ticks}t, base {a.base[:12]} new {a.new[:12]})")
    for cause in CAUSES:
        bt = nt = 0; rising = []; per = {}
        for s, (b, n) in runs.items():
            nb = sum(1 for c in deaths(b).values() if c == cause); nn = sum(1 for c in deaths(n).values() if c == cause)
            bt += nb; nt += nn; per[s] = (nb, nn)
            if nn > nb: rising.append(s)
        th = max(2, math.ceil(0.10 * bt)); t1 = (nt - bt) >= th and len(rising) >= 3 and len(a.seeds) == 5; t2 = (not t1) and nt > bt
        print(f"  {cause}: base {bt} new {nt} rise {nt - bt} threshold {th} seeds rising {rising} per seed {per} -> {'TIER1_STOP' if t1 else 'TIER2_REVIEW' if t2 else 'no rise' if not rising else 'REPORT_ONLY'}")
        if t1 or t2:
            for s in rising:
                b, n = runs[s]; bd = deaths(b)
                print(f"    seed {s} extra {cause} victims (new arm, not {cause} on base): {[(i, n['final'][i][2]) for i, c in deaths(n).items() if c == cause and bd.get(i) != cause]}")
        tier1 = tier1 or t1
    for s, (b, n) in runs.items():
        bd = deaths(b); people = {str(r[0]) for r in b["start"] if r[2]}
        cb = collections.Counter(bd.values()); cn = collections.Counter(deaths(n).values())
        pb = len(deaths(b, people)); pn = len(deaths(n, people))
        print(f"  seed {s}: base {sum(cb.values())} {dict(sorted(cb.items()))} new {sum(cn.values())} {dict(sorted(cn.items()))}; people deaths base {pb} new {pn}; end hash base {b['final_hash'][:12]} new {n['final_hash'][:12]}")
        for i, c in deaths(n).items():
            if c != "STARVATION": continue
            key = (w, str(s), i)
            if key in known: seen_known.add(key); print(f"  KNOWN starvation present: {w} s{s} e{i}")
            else: starv.append((w, s, i, n["final"][i][2], "arm-only" if bd.get(i) != "STARVATION" else "also on base", n["final_hash"]))
for k in sorted(known - seen_known):
    if k[0] in a.worlds and int(k[1]) in a.seeds: print(f"  KNOWN starvation ABSENT on the new arm: {k[0]} s{k[1]} e{k[2]}")
print("STARVATION_GATE unmatched new-arm starvations to trace (world, seed, id, kind, base status, cell final_hash):", starv or "none")
print("TIER1_FIRED" if tier1 else "TIER1_NOT_FIRED")
sys.exit(7 if tier1 else 9 if starv else 0)
