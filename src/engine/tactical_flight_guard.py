"""A flight weighs the free swing it would take (TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE, divergence 2.202).

Leaving melee gives every engaged hostile a free swing (COMB-009). A subject does not flee into a blow it has felt and knows will finish it: when the last
blow it took, from a hostile still engaged with it, is at least its remaining health, the flight is withheld and the subject answers that hostile instead
(CONFLICT-04). It knows only what it has felt: no hostile's stats, and a hostile that has not hit it is not assumed lethal.

A pure builder: reads the entity and the decision's already-chosen update, writes nothing.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.hostility import source_identity
from src.engine.legality import LegalityServiceV2
from src.engine.movement import is_evasive_flight, live_action_style
from src.engine.tactical_hold import held_swing_update

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


class FlightSite(str, Enum):
    """The tactical emission a flight came from. A label for the caller and for counting; never stored in state. Two sites share PANIC_RETREAT."""
    PANIC_RETREAT = "PANIC_RETREAT"
    SAFETY_PRESSURE_RETREAT = "SAFETY_PRESSURE_RETREAT"
    LOW_HP_RETREAT = "LOW_HP_RETREAT"
    LEASH_RETURN = "LEASH_RETURN"
    AVOID_HOSTILE = "AVOID_HOSTILE"
    FLEE_THREAT = "FLEE_THREAT"


def _flight_reason(entity: "EntityState", update: EntityUpdate) -> Optional[str]:
    """The ``reason`` of the flight the update issues, when it issues one from ``FLIGHT_REASONS`` and steps off the subject's tile; None otherwise.
    A flight held on the subject's own tile gives no free swing."""
    task = update.task
    if task is None or task.payload_set is None:
        return None
    target = task.payload_set.get("target_position")
    if target is not None and tuple(target) == tuple(entity.navigation.position):
        return None
    reason = task.payload_set.get("reason")
    return reason if reason in MovementCandidateSelector.FLIGHT_REASONS else None


def _felt_lethal_attacker(state: "AuthoritativeState", entity: "EntityState") -> Optional["EntityState"]:
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


def flight_weighs_free_swing(
    state: "AuthoritativeState", entity: "EntityState", update: Optional[EntityUpdate], site: FlightSite,
) -> Optional[EntityUpdate]:
    """``update`` unchanged, or the engagement response when ``update`` is a flight into a free swing the subject knows is lethal.

    Response toward the felt attacker, in CONFLICT-04's own order and never falling through: ATTACK when legal at full readiness, else the held swing
    (HOLD_BETWEEN_BLOWS), else hold on the subject's own tile in RETREAT mode with no task (the LOW-HP shape). An evasive retreat is unaffected: the free
    swing cannot reach it (movement.py).
    """
    if update is None or _flight_reason(entity, update) is None:
        return update
    if is_evasive_flight(MovementMode.RETREAT, live_action_style(entity, state)):
        return update
    attacker = _felt_lethal_attacker(state, entity)
    if attacker is None:
        return update
    carried: Dict[str, Any] = {"stale_ticks": 0, "recent_positions": [], "target_identity_source": source_identity(entity)[1]}
    if entity.combat.readiness >= 100.0 and LegalityServiceV2.verify_attack_legality(entity, attacker, state)[0]:
        return EntityUpdate(
            entity_id=entity.id,
            strategic=update.strategic,
            navigation=NavigationUpdate(target_clear=True),
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": attacker.id, **carried}),
        )
    held = held_swing_update(state, entity, attacker, update.strategic, carried)
    if held is not None:
        return held
    return EntityUpdate(
        entity_id=entity.id,
        strategic=update.strategic,
        navigation=NavigationUpdate(target_set=entity.navigation.position, movement_mode_set=MovementMode.RETREAT),
    )
