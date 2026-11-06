"""Flee / pursuit entity-ticks split by pressing y/n (read-only; records only). Usage (cwd = arm tree root, PYTHONPATH=.): mode_split.py world seed ticks out.json [victim ids]

Counts exactly what src/observability/run_ledger.py counts (entity-ticks whose movement_mode after the tick is in FLEE_MODES = {RETREAT} or PURSUIT_MODES = {PURSUE, INTERCEPT},
every living entity), and splits each tick by: need pressing (need_is_pressing(hunger, sleep_debt)), person (keeps_coin), kind, and membership of the given victim set.
Also records the alive population by kind at the end and the final state hash. The totals must equal the paired run's flee_ticks / pursuit_ticks (checked by the caller)."""
import collections, json, os, shutil, sys
from pathlib import Path

world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
victims = {int(x) for x in sys.argv[5].split(",")} if len(sys.argv) > 5 and sys.argv[5] else set()
from src.core.movement_modes import MovementMode
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.need_pull import need_is_pressing
from src.engine.serves import keeps_coin
from tools.test_architecture.rpg_gate_run import build_kernel

FLEE, PURSUIT = {MovementMode.RETREAT}, {MovementMode.PURSUE, MovementMode.INTERCEPT}
rid = f"modes_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
persons = {e.id for e in k.state.entities.values() if keeps_coin(e)}
ticks_by = collections.Counter()          # (mode, pressing, person, kind) -> entity-ticks
victim_ticks = collections.Counter()      # (mode, pressing) for victim ids
by_subject = collections.defaultdict(collections.Counter)   # eid -> (mode, pressing) -> ticks (only subjects with any mode tick)
for _ in range(ticks):
    k.tick_once(); st = k.state
    for eid, e in st.entities.items():
        if not e.combat.alive:
            continue
        m = e.navigation.movement_mode
        name = "flee" if m in FLEE else ("pursuit" if m in PURSUIT else None)
        if name is None:
            continue
        pr = bool(need_is_pressing(e.biological.hunger, e.biological.sleep_debt))
        ticks_by[(name, pr, eid in persons, str(e.kind))] += 1
        by_subject[eid][(name, pr)] += 1
        if eid in victims:
            victim_ticks[(name, pr)] += 1
alive = collections.Counter(str(e.kind) for e in k.state.entities.values() if e.combat.alive)
doc = {"world": world, "seed": seed, "ticks": ticks, "final_hash": CanonicalStateHasher.get_hash(k.state),
       "ticks_by": {"|".join(map(str, a)): b for a, b in ticks_by.items()},
       "victim_ticks": {"|".join(map(str, a)): b for a, b in victim_ticks.items()},
       "by_subject": {str(e): {"|".join(map(str, a)): b for a, b in c.items()} for e, c in by_subject.items()},
       "alive_by_kind": dict(alive)}
k.shutdown(); shutil.rmtree(Path("data") / "runs" / rid, ignore_errors=True)
Path(out).write_text(json.dumps(doc), encoding="utf-8")
