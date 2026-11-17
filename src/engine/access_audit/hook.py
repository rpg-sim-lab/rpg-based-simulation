"""The single entry point the step-dispatch layer (``pipeline.run_phase``) calls. OFF path: ``audit_sink_for`` answers None and the pipeline calls ``phase_fn(upd)`` with no
other work, so no recorder object, no snapshot and no module-level state exists."""
from __future__ import annotations

from typing import Any, Callable, Optional

from src.domains.optimization.feature_flags import FeatureMode

AUDIT_FLAG = "ENABLE_ACCESS_AUDIT"
SINK_KEY = "ACCESS_AUDIT_SINK"  # the recorder, passed in by the evidence runner; read, never written, here


def audit_sink_for(state: Any, ff_manager: Any) -> Optional[Any]:
    """The recorder to use for this tick, or None. The flag is read through the pipeline's own FeatureFlagManager, so a rollout profile or a state flag turns it on the same way."""
    if ff_manager.get_flag_mode(AUDIT_FLAG) not in (FeatureMode.ON, FeatureMode.STRICT):
        return None
    return (getattr(state, "feature_flags", None) or {}).get(SINK_KEY)


def dispatch_phase(ff_manager: Any, phase_name: str, state: Any, upd: Any, phase_fn: Callable[[Any], Any]) -> Any:
    """What ``run_phase`` calls in place of ``phase_fn(upd)``: with the audit off (the default) it IS ``phase_fn(upd)``: no recorder, no snapshot, no module-level state."""
    sink = audit_sink_for(state, ff_manager)
    return phase_fn(upd) if sink is None else audited_phase_call(sink, phase_name, state, upd, phase_fn)


def audited_phase_call(sink: Any, phase_name: str, state: Any, upd: Any, phase_fn: Callable[[Any], Any]) -> Any:
    """Run ``phase_fn(upd)`` unchanged and record what it read-and-wrote around the call. The result is returned untouched."""
    pre = sink.before(state, upd)
    result = phase_fn(upd)
    sink.after(phase_name, state, upd, result, pre)
    return result
