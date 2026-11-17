"""One world cell: pinned kernel (rpg_gate_run.build_kernel), per-tick completions, deaths by cause, alive at checkpoints. Args: world seed ticks out.json. Read-only on the tree."""
import json, os, shutil, sys
from pathlib import Path
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from tools.test_architecture.pinned_runner import read_manifest, require_pinned
from tools.test_architecture.rpg_gate_run import build_kernel
run_id = f"nbe_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, run_id)
mp = Path("data/runs") / run_id / "run_manifest.json"
verdict = require_pinned(read_manifest(mp) if mp.exists() else {}, what="nobody-eats cell")
def snap(state):
    return {str(e.id): (e.combat.alive, e.biological.hunger, e.biological.sleep_debt) for e in state.entities.values()}
prev = snap(k.state)
eat = [0] * (ticks // 100 + 1); slp = [0] * (ticks // 100 + 1)
alive_at = {}
for t in range(1, ticks + 1):
    k.tick_once()
    cur = snap(k.state)
    b = (t - 1) // 100
    for i, (a, h, s) in cur.items():
        p = prev.get(i)
        if p and p[0] and a:
            if h < p[1]: eat[b] += 1
            if s < p[2]: slp[b] += 1
    prev = cur
    if t in (900, 1100, 1200, ticks):
        alive_at[t] = sum(1 for v in cur.values() if v[0])
def cause(e):
    if e.combat.alive: return None
    r = getattr(e.lifecycle, "death_record", None)
    if r is not None: return str(getattr(r.cause, "value", r.cause))
    return "legacy:" + str(getattr(e.lifecycle.passive_death_cause, "value", None) or e.lifecycle.death_reason or "unknown")
deaths = {}
for e in k.state.entities.values():
    c = cause(e)
    if c: deaths[c] = deaths.get(c, 0) + 1
doc = {"world": world, "seed": seed, "ticks": ticks, "pinned": verdict.verdict, "final_hash": CanonicalStateHasher.get_hash(k.state),
       "eat_per_100": eat[:ticks // 100], "sleep_per_100": slp[:ticks // 100], "alive_at": alive_at, "deaths_by_cause": deaths,
       "entities_total": len(k.state.entities)}
k.shutdown()
shutil.rmtree(Path("data/runs") / run_id, ignore_errors=True)
Path(out).write_text(json.dumps(doc, sort_keys=True))
print(json.dumps({"hash": doc["final_hash"], "pinned": doc["pinned"]}))
