# Compliance IDs: STRAT-295
"""The stay-or-leave rule of a lodger (F3, divergence 2.155), kept in core so the decision layers (systems) and the apply layers (engine) read one definition.

A lodger holds its bed only while it uses it: it STAYS while its task is a rest, a sleep or a meal, and LEAVES when anything else (including no task) is decided."""
from __future__ import annotations

from typing import Any, Optional

SLEEP_ACTIONS = frozenset({"SLEEP", "REST"})  # the actions that put a subject to sleep; each is held until the debt is below the wake line


def keeps_lodging(work_kind: Optional[str], payload: Any) -> bool:
    """True when a lodger's resulting task keeps it indoors: it is still resting or sleeping, or it is eating (only EAT was ruled, scope 7). Anything else, including no task at all
    (the held rest ended this tick), means it leaves: a lodger holds a bed only while it uses it, so the bed is free the tick its rest ends and no lodger can be stranded
    awake indoors waiting for a decision (risk R5). The brain then decides from the reach tile, where the building's services are still in reach."""
    action = (payload or {}).get("action") if isinstance(payload, dict) else None
    if not action:
        return False
    return action in SLEEP_ACTIONS or action == "EAT"


def is_lodged_stayer(entity: Any) -> bool:
    """True for a lodger whose held rest or meal goes on: it has no movement intent (F3, divergence 2.155). A decision pass reads this and writes no walk target for it; it never writes `lodged_in`.
    A lodger whose rest has ended is not a stayer: it decides again and leaves through `place_leavers`."""
    return entity.navigation.lodged_in is not None and keeps_lodging(entity.task.work_kind, entity.task.payload)


def is_lodged(entity: Any) -> bool:
    """True while ``entity`` lodges in a building. The one predicate every spatial index, perception and targeting filter reads."""
    return entity.navigation.lodged_in is not None


def outside_entity(entity: Any) -> Any:
    """``entity`` as seen from outside: None when it is absent or lodged (nobody outside can reach, ask or see a lodger)."""
    return None if entity is None or is_lodged(entity) else entity


def lodged_in_field(entity: Any) -> dict:
    """The read-model field of a lodger: ``{"lodged_in": building id}`` while lodged, else nothing (a subject that never lodged keeps its form)."""
    return {"lodged_in": entity.navigation.lodged_in} if is_lodged(entity) else {}
