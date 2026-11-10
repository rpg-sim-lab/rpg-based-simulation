"""The recorder the evidence runner builds and passes in (through ``state.feature_flags[SINK_KEY]``). It is held by no module-level global, stores nothing on state or the
update, and the pipeline never creates one: with the audit flag off no instance exists."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional

from src.engine.access_audit.observe import (
    diff_state,
    snapshot_state,
    snapshot_update,
    update_inplace,
    update_writes,
)


@dataclass
class StepObservation:
    """What one step did on one tick."""

    tick: int
    phase: str
    writes: FrozenSet[str]
    inplace_update_mutations: FrozenSet[str]
    hidden_state_mutations: FrozenSet[str]


@dataclass
class AccessAuditRecorder:
    """Collects one ``StepObservation`` per audited step."""

    observations: List[StepObservation] = field(default_factory=list)

    def before(self, state: Any, upd: Any) -> tuple:
        """Snapshot tick-start state and the input update before a step runs."""
        return snapshot_state(state), snapshot_update(upd)

    def after(self, phase: str, state: Any, upd: Any, result: Any, pre: tuple) -> None:
        """Observe one step after it ran (and before the pipeline's SHADOW branch discards anything)."""
        pre_state, pre_upd = pre
        self.observations.append(StepObservation(
            tick=int(getattr(state, "tick", -1)),
            phase=phase,
            writes=update_writes(upd, result),
            inplace_update_mutations=update_inplace(pre_upd, upd),
            hidden_state_mutations=diff_state(pre_state, snapshot_state(state)),
        ))

    def per_phase(self) -> Dict[str, Dict[str, Any]]:
        """Union over all ticks: per phase, the writes, in-place update mutations and hidden state mutations seen, with the tick count each phase ran."""
        out: Dict[str, Dict[str, Any]] = {}
        for ob in self.observations:
            rec = out.setdefault(ob.phase, {"ticks_run": 0, "writes": set(), "inplace_update_mutations": set(), "hidden_state_mutations": set()})
            rec["ticks_run"] += 1
            rec["writes"] |= ob.writes
            rec["inplace_update_mutations"] |= ob.inplace_update_mutations
            rec["hidden_state_mutations"] |= ob.hidden_state_mutations
        return {p: {k: (sorted(v) if isinstance(v, set) else v) for k, v in rec.items()} for p, rec in out.items()}

    def dump(self, path: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Write the per-phase union (and any ``extra`` facts) to ``path`` as JSON."""
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"per_phase": self.per_phase(), **(extra or {})}, fh, indent=1, sort_keys=True)
