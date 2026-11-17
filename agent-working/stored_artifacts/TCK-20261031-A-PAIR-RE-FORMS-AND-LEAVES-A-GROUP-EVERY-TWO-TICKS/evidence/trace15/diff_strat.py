import json, os, sys
sys.path.insert(0, ".")
from src.engine.apply import ApplyPath
out = {}
_oa = ApplyPath.apply_generation
def ag(prior, update, *a, **k):
    new = _oa(prior, update, *a, **k)
    if new.tick in (12, 13):
        for e in (32, 33):
            out[f"{new.tick}:{e}"] = json.loads(json.dumps(new.entities[e].strategic.to_canonical_dict() if hasattr(new.entities[e].strategic, "to_canonical_dict") else new.entities[e].to_canonical_dict()["strategic"], default=str))
    return new
ApplyPath.apply_generation = staticmethod(ag)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
_run_engine("crowded_frontier", 42, 14, extra_flags=_load_profile_feature_flags(_resolve_profile("crowded_frontier")), audit_mode=True)
json.dump(out, open(os.environ["DS_OUT"], "w"))
