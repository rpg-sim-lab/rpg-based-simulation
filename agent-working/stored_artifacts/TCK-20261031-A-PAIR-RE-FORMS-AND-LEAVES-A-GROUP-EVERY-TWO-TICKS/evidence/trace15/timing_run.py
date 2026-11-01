"""NON-AUDIT timing run (scratch; wrappers only). Usage: TIM_OUT=<json> python timing_run.py <world> <seed> <ticks>  (cwd = tree, PYTHONPATH = tree)
probe_groups2.install() supplies the whole-tick sum (Kernel.tick_once), store counts, ghosts and overwrites; on top, per tick: the kernel's per-phase costs (Kernel._phase_costs) and the replay policy
(richness, allowed, name). Runs with audit_mode=False. A run whose policy leaves FULL on any tick is flagged invalid (not replaced)."""
import json, os, sys, statistics, collections
sys.path.insert(0, "."); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_groups2 as P
P.install()
from src.engine.kernel import Kernel
_pin = os.environ.get("PIN", "")
if _pin:
    from tests.helpers.kernel_pinning import PinnedNormalGovernor
    _oinit = Kernel.__init__
    def _init(self, *a, **k):
        if k.get("governor") is None: k["governor"] = PinnedNormalGovernor()
        if _pin == "gov+seq" and k.get("executor") is None:
            from src.engine.executor import LocalSequentialExecutor
            k["executor"] = LocalSequentialExecutor()
        return _oinit(self, *a, **k)
    Kernel.__init__ = _init
_inner = Kernel.tick_once
executor_seen = set(); governor_seen = set(); phase_lists = collections.defaultdict(list); policy_ticks = collections.Counter(); policy_changes = []; last = [None]
def _tk(self, *a, **k):
    r = _inner(self, *a, **k)
    executor_seen.add(type(getattr(self, "_executor", None)).__name__); governor_seen.add(type(getattr(self, "_governor", None)).__name__)
    for name, ms in dict(getattr(self, "_phase_costs", {}) or {}).items(): phase_lists[name].append(ms)
    pol = getattr(self, "_current_policy", None)
    cur = [str(getattr(pol, "replay_richness", None)), str(getattr(pol, "replay_allowed", None)), str(getattr(pol, "name", None) or getattr(self, "_current_mode", None))]
    policy_ticks["/".join(cur)] += 1
    if last[0] != cur: policy_changes.append([getattr(getattr(self, "_state", None), "tick", None), last[0], cur]); last[0] = cur
    return r
Kernel.tick_once = _tk
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=False)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
S = P.S
full = all(k.startswith("FULL") or "RichnessLevel.FULL" in k or k.split("/")[0].endswith("FULL") for k in policy_ticks)
out = dict(world=world, seed=seed, ticks=ticks, state_hash=m["state_hash"], elapsed_s=elapsed, tick_sum_s=S["tick_ms"] / 1000.0, tick_calls=S["tick_calls"],
           tick_mean_ms=S["tick_ms"] / max(S["tick_calls"], 1), phase_median_ms={k: statistics.median(v) for k, v in phase_lists.items()}, phase_mean_ms={k: sum(v) / len(v) for k, v in phase_lists.items()},
           group_phase_ms_total=S["phase_ms"], coop_ms_total=S["coop_ms"], work_phase=S["work_phase"], work_coop=S["work_coop"], work_relevant=S["work_relevant"], phase_calls=S["phase_calls"], coop_calls=S["coop_calls"], store_records=S["end_groups"], store_dissolved=S["end_dissolved"], ghost=len(S["ghost_any"]), overwrites=S["pre_loose"],
           policy_ticks=dict(policy_ticks), policy_changes=policy_changes[:20], all_full=full, pin=_pin or None, executor=sorted(executor_seen), governor=sorted(governor_seen))
open(os.environ["TIM_OUT"], "w").write(json.dumps(out, default=str)); print("TIM_OK", out["state_hash"][:12], round(out["tick_sum_s"], 1), "s", "policy", dict(policy_ticks))
