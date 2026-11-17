"""behavioral_5k alive curve: tests/regression/test_behavioral_5k.py::collect_behavioral_metrics unchanged; MetricsService.extract_metrics is wrapped only to record the alive count it already computes each 100 ticks."""
import json, sys, time
from pathlib import Path
out = sys.argv[1]
t0 = time.time()
from src.engine.metrics import MetricsService
orig = MetricsService.extract_metrics
alive = []
def wrapped(state, *a, **k):
    m = orig(state, *a, **k)
    alive.append(m.alive_entities)
    return m
MetricsService.extract_metrics = staticmethod(wrapped) if isinstance(MetricsService.__dict__.get("extract_metrics"), staticmethod) else wrapped
sys.path.insert(0, ".")
from tests.regression import test_behavioral_5k as b
res = b.collect_behavioral_metrics()
runs = sorted(Path("data/runs").glob("*/run_manifest.json"), key=lambda p: p.stat().st_mtime)
from tools.test_architecture.pinned_runner import classify_manifest
verdict = classify_manifest(json.loads(runs[-1].read_text())) if runs else None
Path(out).write_text(json.dumps({"summary": res, "alive_per_100": alive, "run_conditions_verdict": (verdict.verdict, verdict.differences) if verdict else None, "seconds": time.time() - t0}, sort_keys=True))
print(json.dumps({"n": len(alive), "verdict": verdict.verdict if verdict else None}))
