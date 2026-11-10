"""The recorder the evidence runner builds and passes in (through ``state.feature_flags[SINK_KEY]``). It is held by no module-level global, stores nothing on state or the
update, and the pipeline never creates one: with the audit flag off no instance exists."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from src.engine.access_audit.observe import (
    TIMELINE_SAMPLE_EVERY,
    diff_state,
    entity_fanout,
    sample_mutable_timeline_elements,
    snapshot_globals,
    snapshot_state,
    snapshot_update,
    split_tiers,
    update_identity_only,
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
    promote: FrozenSet[str] = frozenset()  # Tier 2 hits: fields to promote to the content-hashed watch list
    global_changes: FrozenSet[str] = frozenset()
    identity_only: FrozenSet[str] = frozenset()  # A3: object replaced, value equal
    unsafe_equality: FrozenSet[str] = frozenset()
    created_entries: int = 0  # cross-entity proxy (a)
    fanout: Dict[str, int] = field(default_factory=dict)  # cross-entity proxy (b): distinct entity ids written per bucket


@dataclass
class AccessAuditRecorder:
    """Collects one ``StepObservation`` per audited step."""

    observations: List[StepObservation] = field(default_factory=list)
    timeline_samples: List[int] = field(default_factory=list)  # ticks at which a content sample was taken
    sampled_timeline_edits: List[Dict[str, Any]] = field(default_factory=list)  # findings: a mutable timeline element whose content differs from its first-seen digest
    _baseline: Dict[int, Tuple[Any, Any, int]] = field(default_factory=dict, repr=False)  # element id -> (entity id, first-seen digest, first-seen tick); dropped on eviction

    def before(self, state: Any, upd: Any) -> tuple:
        """Snapshot tick-start state and the input update before a step runs."""
        self._maybe_sample(state)
        return snapshot_state(state), snapshot_update(upd), snapshot_globals()

    def _maybe_sample(self, state: Any) -> None:
        """Once per ``TIMELINE_SAMPLE_EVERY`` ticks: compare each mutable timeline element's content digest with the one taken the first time it was seen (keyed by id while it stays in the deque; evicted ones are dropped). A difference is a finding naming the entity, the element and the tick window; the sample does not name the step."""
        tick = int(getattr(state, "tick", -1))
        if tick % TIMELINE_SAMPLE_EVERY or (self.timeline_samples and self.timeline_samples[-1] == tick):
            return
        now = sample_mutable_timeline_elements(state)
        self._baseline = {k: v for k, v in self._baseline.items() if k in now}
        for key, (e_id, type_name, idx, dig) in now.items():
            first = self._baseline.setdefault(key, (e_id, dig, tick))
            if first[1] != dig:
                self.sampled_timeline_edits.append({"entity": e_id, "element": type_name, "index": idx, "first_seen_tick": first[2], "sample_tick": tick})
                self._baseline[key] = (e_id, dig, tick)
        self.timeline_samples.append(tick)

    def after(self, phase: str, state: Any, upd: Any, result: Any, pre: tuple) -> None:
        """Observe one step after it ran (and before the pipeline's SHADOW branch discards anything)."""
        pre_state, pre_upd, pre_globals = pre
        hidden = diff_state(pre_state, snapshot_state(state))
        post_globals = snapshot_globals()
        same, unsafe = update_identity_only(upd, result)
        created, fanout = entity_fanout(upd, result)
        self.observations.append(StepObservation(
            tick=int(getattr(state, "tick", -1)),
            phase=phase,
            writes=update_writes(upd, result),
            inplace_update_mutations=update_inplace(pre_upd, upd),
            hidden_state_mutations=hidden,
            promote=split_tiers(hidden)[1],
            global_changes=frozenset(k for k in pre_globals.keys() | post_globals.keys() if pre_globals.get(k) != post_globals.get(k)),
            identity_only=same,
            unsafe_equality=unsafe,
            created_entries=created,
            fanout=fanout,
        ))

    def per_phase(self) -> Dict[str, Dict[str, Any]]:
        """Union over all ticks per phase, plus per-field tick counters: ``hidden_ticks``, ``global_ticks``, ``created_entries`` (ticks, max) and ``fanout_max`` per bucket."""
        out: Dict[str, Dict[str, Any]] = {}
        for ob in self.observations:
            _fold(out.setdefault(ob.phase, _empty_record()), ob)
        return {p: {k: (sorted(v) if isinstance(v, set) else v) for k, v in rec.items()} for p, rec in out.items()}

    def dump(self, path: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Write the per-phase union (and any ``extra`` facts) to ``path`` as JSON."""
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"per_phase": self.per_phase(), "timeline_content_sampled": {"every_ticks": TIMELINE_SAMPLE_EVERY, "samples": len(self.timeline_samples), "findings": self.sampled_timeline_edits}, **(extra or {})}, fh, indent=1, sort_keys=True)


def _empty_record() -> Dict[str, Any]:
    return {"ticks_run": 0, "writes": set(), "inplace_update_mutations": set(), "hidden_state_mutations": set(), "promote": set(), "identity_only": set(),
            "unsafe_equality": set(), "hidden_ticks": {}, "global_ticks": {}, "created_entries_ticks": 0, "created_entries_max": 0, "fanout_max": {}}


def _count(counter: Dict[str, int], keys: Any) -> None:
    for key in keys:
        counter[key] = counter.get(key, 0) + 1


def _fold(rec: Dict[str, Any], ob: StepObservation) -> None:
    """Add one step observation to its phase record."""
    rec["ticks_run"] += 1
    for key in ("writes", "inplace_update_mutations", "hidden_state_mutations", "promote", "identity_only", "unsafe_equality"):
        rec[key] |= getattr(ob, key)
    _count(rec["hidden_ticks"], ob.hidden_state_mutations)
    _count(rec["global_ticks"], ob.global_changes)
    if ob.created_entries:
        rec["created_entries_ticks"] += 1
        rec["created_entries_max"] = max(rec["created_entries_max"], ob.created_entries)
    for bucket, n in ob.fanout.items():
        rec["fanout_max"][bucket] = max(rec["fanout_max"].get(bucket, 0), n)
