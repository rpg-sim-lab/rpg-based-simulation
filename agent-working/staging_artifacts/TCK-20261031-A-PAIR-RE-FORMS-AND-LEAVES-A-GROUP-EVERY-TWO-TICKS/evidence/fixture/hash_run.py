"""Read-only: run a world and print the final state hash (no wrappers). Usage: python hash_run.py <world> <seed> <ticks>  (cwd = tree, PYTHONPATH = tree)"""
import json, os, sys
sys.path.insert(0, ".")
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=True)
print("HASH", world, seed, ticks, json.load(open(os.path.join(run_dir, "run_manifest.json")))["state_hash"][:16])
