"""Decisions 44 to 49 in the tactical pass: who a creature treats as a target, who it avoids, and a carcass its hunger goal points at.

Pure builders of ``EntityUpdate`` and a classifier; they read the acting entity and what it perceives and write nothing.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

from src.core.movement_modes import MovementMode
from src.core.navigation_purpose import TargetPurpose, purpose_of, ungated_purpose
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.appraisal import WARY_DISTANCE, Relation
from src.engine.hostility import ATTACK_RELATIONS, relation
from src.engine.tactical_destinations import retreat_destination
from src.engine.tile_distance import manhattan_tile_distance

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


class Neighbourhood(NamedTuple):
    """The perceived neighbours of one entity by how it regards them: attack targets, creatures coming for it, and creatures it is wary of."""

    hostiles: List["EntityState"]
    threatening: List["EntityState"]
    wary: List["EntityState"]
    hostile_identity_sources: Dict[int, str]


def classify_neighbours(entity: "EntityState", neighbors: Sequence["EntityState"], source: Tuple[str, str], night: bool = False, tick: Optional[int] = None) -> Neighbourhood:
    """Sorts ``neighbors`` by ``hostility.relation``: FACTION_HOSTILE and PREDATION are attack targets; THREATENING and WARY are avoided and
    never enter the hostile list (a plant-eater must never treat a wolf as an engagement target)."""
    hood = Neighbourhood([], [], [], {})
    for n in neighbors:
        rel = relation(entity, n, source, night=night, tick=tick)
        if rel in ATTACK_RELATIONS:
            hood.hostiles.append(n)
            hood.hostile_identity_sources[n.id] = source[1]
        elif rel is Relation.THREATENING:
            hood.threatening.append(n)
        elif rel is Relation.WARY:
            hood.wary.append(n)
    return hood


def _flight_update(entity: "EntityState", where: Tuple[float, float], reason: str, strat_up: Any, navigation: NavigationUpdate) -> EntityUpdate:
    """The flight update around a ready navigation update: the move task to ``where`` with its ``reason``, and the strategic update the caller carries."""
    return EntityUpdate(
        entity_id=entity.id, strategic=strat_up, navigation=navigation,
        task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": where, "reason": reason}),
    )


def _retreat(entity: "EntityState", where: Tuple[float, float], reason: str, strat_up: Any, purpose: TargetPurpose) -> EntityUpdate:
    """The flight update to a tile that came through the gate. ``purpose`` is the caller's bound name (the gate's argument), stored with the target as gated."""
    return _flight_update(entity, where, reason, strat_up, NavigationUpdate(target_set=where, movement_mode_set=MovementMode.RETREAT, target_purpose_set=purpose, target_gated_set=True))


def _retreat_hold(entity: "EntityState", reason: str, strat_up: Any) -> EntityUpdate:
    """The flight update with no tile to flee to: the subject holds its own tile (a by-value write that skipped the gate, stored with `ungated_purpose` and as NOT gated)."""
    where = entity.navigation.position
    return _flight_update(entity, where, reason, strat_up, NavigationUpdate(target_set=where, movement_mode_set=MovementMode.RETREAT, target_purpose_set=ungated_purpose(entity, MovementMode.RETREAT), target_gated_set=False))


def avoid_what_can_eat_me(
    state: "AuthoritativeState", entity: "EntityState", hood: Neighbourhood, strat_up: Any
) -> Optional[EntityUpdate]:
    """A creature with no attack target flees what is coming for it (THREATENING: a decided flight, ``FLEE_THREAT``) and keeps its distance
    from what could eat it and it cannot overcome (WARY within ``WARY_DISTANCE``: ``KEEP_DISTANCE``, not a flight); otherwise None."""
    if hood.hostiles:
        return None
    if hood.threatening:
        purpose = purpose_of(entity, None, MovementMode.RETREAT)
        away = retreat_destination(state, entity, hood.threatening, purpose)
        if away is None:
            return _retreat_hold(entity, "FLEE_THREAT", strat_up)
        return _retreat(entity, away, "FLEE_THREAT", strat_up, purpose)
    near = [w for w in hood.wary if manhattan_tile_distance(entity.navigation.position, w.navigation.position) <= WARY_DISTANCE]
    purpose = purpose_of(entity, None, MovementMode.RETREAT)
    distant = retreat_destination(state, entity, near, purpose) if near else None
    return _retreat(entity, distant, "KEEP_DISTANCE", strat_up, purpose) if distant is not None else None


def eat_at_hunger_corpse(entity: "EntityState", state: "AuthoritativeState", project: Any, objective: Any) -> Optional[EntityUpdate]:
    """Arrived at a carcass the hunger goal pointed at: eat where it lies (the corpse id rides in the payload), else None. A hunger objective that
    names a node, a building or a creature is not about a carcass."""
    if getattr(project, "kind", "") != "hunger" or objective.target_entity_id is not None or objective.target is None:
        return None
    try:
        corpse = state.corpses.get(int(objective.target))
    except ValueError:
        return None
    if corpse is None:
        return None
    return EntityUpdate(entity_id=entity.id, task=TaskUpdate(
        work_kind_set="ENTITY_ACT", payload_set={"action": "EAT", "reason": "EAT_AT_CORPSE", "corpse_id": corpse.id}))
