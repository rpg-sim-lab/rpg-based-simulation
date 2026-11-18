"""Child-side shims for the trigger-neutrality arms (M1 risen origin, rulings of 2026-11-18): count the rise trigger's firings, and in the OFF arm make it never fire.

The ruled trigger is ``src.world.risen.rise_triggers_phase``; the name the scheduler actually CALLS is ``src.engine.phase_graph.rise_triggers_phase`` (imported there by name, called in
``PhaseDependencyGraph.should_run_phase``), so that attribute is the patch target. Nothing in src is edited: the shim is installed in the child process only and restored at exit.

``ON`` calls the real trigger, counts each True and counts an EXTRA phase run when the phase would not have run without that firing (evaluated by asking ``should_run_phase`` again
with the trigger held False). ``OFF`` returns False and counts nothing (0 firings, 0 extra runs by construction), and also replaces ``RisenService.process_rises`` with the identity on the
update, so the rise is off as well as the trigger. Both are test-time rebindings of module attributes; none changes a source file.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.engine import phase_graph
from src.engine.phase_graph import PhaseDependencyGraph
from src.world import risen
from src.world.risen import RisenService


class _RiseChanceCatalog:
    """The warmed catalog with every risen profile's chance forced (0.0 for the neutrality arms, 1.0 for the positive control)."""

    def __init__(self, real: Any, chance: float) -> None:
        self._real, self._chance = real, chance

    def get_risen_profile(self, profile_id: str) -> Any:
        return self._real.get_risen_profile(profile_id).model_copy(update={"rise_chance_per_check": self._chance})

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


class TriggerShim:
    """``install(mode)`` patches the scheduler's trigger name (and in OFF the rise itself); ``restore()`` undoes. ``counts()`` reports firings, extra phase runs and the first firing tick."""

    def __init__(self) -> None:
        self.firings = 0
        self.extra_runs = 0
        self.first_firing_tick: Optional[int] = None
        self._probing = False
        self._saved: List[tuple] = []

    def install(self, mode: str, chance: float = 0.0) -> "TriggerShim":
        if mode not in ("on", "off"):
            raise ValueError(f"trigger mode {mode!r}")
        real = phase_graph.rise_triggers_phase
        shim = self

        def counting(phase_name, state, cadence):
            if shim._probing:
                return False
            fired = real(phase_name, state, cadence)
            if fired:
                shim.firings += 1
                shim.first_firing_tick = state.tick if shim.first_firing_tick is None else shim.first_firing_tick
                shim._probing = True
                try:
                    needed = PhaseDependencyGraph.should_run_phase(phase_name, state, shim._update, cadence)
                finally:
                    shim._probing = False
                if not needed:
                    shim.extra_runs += 1
            return fired

        def off(phase_name, state, cadence):
            return False

        self._update = None
        original_should_run = PhaseDependencyGraph.__dict__["should_run_phase"]

        def should_run_phase(phase_name, state, update, cadence=None):
            shim._update = update
            return original_should_run.__func__(phase_name, state, update, cadence)

        self._swap(phase_graph, "rise_triggers_phase", counting if mode == "on" else off)
        self._swap(PhaseDependencyGraph, "should_run_phase", staticmethod(should_run_phase))
        self._swap(risen, "get_catalog", lambda: _RiseChanceCatalog(_real_catalog(), chance))
        if mode == "off":
            self._swap(RisenService, "process_rises", staticmethod(lambda state, update, cadence=None: update))
        return self

    def _swap(self, owner: Any, name: str, replacement: Any) -> None:
        self._saved.append((owner, name, owner.__dict__[name] if isinstance(owner, type) else getattr(owner, name)))
        setattr(owner, name, replacement)

    def restore(self) -> None:
        for owner, name, original in reversed(self._saved):
            setattr(owner, name, original)
        self._saved.clear()

    def counts(self) -> Dict[str, Any]:
        return {"firings": self.firings, "extra_phase_runs": self.extra_runs, "first_firing_tick": self.first_firing_tick}


_CATALOG = None


def _real_catalog() -> Any:
    global _CATALOG
    if _CATALOG is None:
        from src.engine.behavior_consumers import get_catalog
        _CATALOG = get_catalog()
    return _CATALOG
