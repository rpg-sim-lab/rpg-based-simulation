"""One arm of the replay-digest byte comparison (TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK, AC2). cwd = the frozen tree.

Usage: python -B replay_digest_arm.py <world> <seed> <ticks> <out.json>
Builds the pinned kernel (tools.test_architecture.rpg_gate_run.build_kernel: PROD_SMALL, PinnedNormalGovernor, LocalSequentialExecutor, audit_mode, no frame pacing) with REPLAY ON (nothing here sets
no_replay), runs `ticks` ticks, takes the final proof hash with the real hasher, shuts the kernel down (which flushes the last chunk) and writes one JSON document. The run id is the same in every arm
(`rd_<world>_<seed>`) so any run-id text in the replay files is equal between arms. Reads only; the launcher moves the run directory out afterwards.
"""
import json
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.getcwd())  # the tree's own src/, never an installed copy
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import PROOF_DIGEST_SCHEME, CanonicalStateHasher  # noqa: E402
from tools.test_architecture.rpg_gate_run import build_kernel  # noqa: E402

run_id = f"rd_{world}_{seed}"
kernel = build_kernel(world, seed, run_id)
flags = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_replay": getattr(kernel, "_no_replay", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None)}
if flags["audit_mode"] is not True or flags["no_replay"]:
    raise RuntimeError(f"this arm needs audit_mode on and replay on: {flags}")
t0 = time.perf_counter()
for _ in range(ticks):
    kernel.tick_once()
loop_s = time.perf_counter() - t0
final_hash = CanonicalStateHasher.get_hash(kernel.state)
final_tick = kernel.state.tick
memo = getattr(kernel, "_canonical_memo", None)
memo_facts = None if memo is None else {"entries": len(memo), "hits": memo.hits, "misses": memo.misses}
kernel.shutdown()
doc = {"world": world, "seed": seed, "ticks": ticks, "final_tick": final_tick, "final_hash": final_hash, "scheme": PROOF_DIGEST_SCHEME, "run_id": run_id, "flags": flags,
       "hashseed": os.environ.get("PYTHONHASHSEED"), "loop_wall_s": loop_s, "memo": memo_facts, "cwd": os.getcwd()}
with open(out, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=1, sort_keys=True)
