"""The hostile whose last felt blow would finish a subject (divergence 2.202, reused by 2.204).

Lives in a neutral module because both the flight guard (``tactical_flight_guard``) and the movement step (``movement.resolve_move``) ask it, and the guard imports movement.
Reads the entity and the state, writes nothing.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.engine.legality import LegalityServiceV2

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def felt_lethal_attacker(state: "AuthoritativeState", entity: "EntityState") -> Optional["EntityState"]:
    """The hostile whose last felt blow would finish the subject, if that hostile is engaged with it now; else None.

    swing = the sum of the shares of the last hit's attackers that are engaged with the subject now and alive (a group hit has several; every other hit has one,
    holding the whole blow); lethal = swing > 0 and swing >= hp. The hostile returned is the first such attacker in attacker-list order (divergence 2.204).
    """
    combat = entity.combat
    shares = tuple(zip(combat.last_hit_attackers, combat.last_hit_damages))
    if not shares:
        return None
    engaged = LegalityServiceV2.get_engaged_hostiles(entity, state)
    swing = 0
    first: Optional["EntityState"] = None
    for attacker_id, share in shares:
        if attacker_id not in engaged:
            continue
        attacker = state.entities.get(attacker_id)
        if attacker is None or not attacker.combat.alive:
            continue
        swing += share
        if first is None:
            first = attacker
    return first if swing > 0 and swing >= combat.hp else None
