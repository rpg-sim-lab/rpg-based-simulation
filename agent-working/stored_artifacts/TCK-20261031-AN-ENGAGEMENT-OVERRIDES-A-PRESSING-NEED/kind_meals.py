"""Per-kind meals / starving-line ticks / pressing ticks / collapses (read-only; works on both arm trees, no hooks). Same definitions as eng_probe_v2.py's by_kind.
Usage (cwd = tree root, PYTHONPATH=.): kind_meals.py world seed ticks out.json"""
import collections, json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing, HUNGER_LINE
from src.engine.sleep_debt import COLLAPSE_FLAG
from tools.test_architecture.rpg_gate_run import build_kernel
rid = f"km_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
kind_of = {e.id: str(getattr(e, "kind", "")) for e in k.state.entities.values()}
ACC = collections.defaultdict(collections.Counter); seen = {}; cprev = {}
for _ in range(ticks):
    k.tick_once(); st = k.state
    for eid, e in st.entities.items():
        if not e.combat.alive or not e.lifecycle.active:
            continue
        kk = kind_of.get(eid); pl = e.task.payload or {}
        hunger, debt = e.biological.hunger, e.biological.sleep_debt
        ACC[kk]["alive_ticks"] += 1
        if hunger >= HUNGER_LINE: ACC[kk]["starving_ticks"] += 1
        if need_is_pressing(hunger, debt): ACC[kk]["pressing_ticks"] += 1
        lm = e.biological.last_meal_tick
        if lm is not None and lm != seen.get(eid, lm): ACC[kk]["meals"] += 1
        seen[eid] = lm
        c = bool(pl.get(COLLAPSE_FLAG))
        if c and not cprev.get(eid): ACC[kk]["collapses"] += 1
        cprev[eid] = c
h = CanonicalStateHasher.get_hash(k.state)
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps({"world": world, "seed": seed, "ticks": ticks, "hash": h, "by_kind": {a: dict(b) for a, b in ACC.items()}}), encoding="utf-8")
