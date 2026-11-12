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

    swing = last_hit_damage if last_attacker_id is engaged else 0 (the sum over engaged hostiles of what the subject has felt from each is only ever the
    last attacker's); lethal = swing > 0 and swing >= hp.
    """
    combat = entity.combat
    swing = combat.last_hit_damage
    if combat.last_attacker_id is None or not swing or swing < combat.hp:
        return None
    if combat.last_attacker_id not in LegalityServiceV2.get_engaged_hostiles(entity, state):
        return None
    attacker = state.entities.get(combat.last_attacker_id)
    return attacker if attacker is not None and attacker.combat.alive else None
