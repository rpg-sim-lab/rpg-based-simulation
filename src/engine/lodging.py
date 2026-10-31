"""Lodging: a subject served a bed at a building lodges INSIDE it (F3, divergence 2.155; Bible 04 section 1, local_world_interaction_contract 2.1).

While a subject lodges it stands on no tile: ``navigation.lodged_in`` is the building's id, its ``position`` is the building's own tile, and it is in no occupancy map, spatial
index or perception, so no one outside can reach or see it, and it sees no one outside. The building lodges at most its content-declared ``beds``; the count of lodgers is
DERIVED from the entities (never stored on the building), so there is one source of truth. ``lodged_in`` is set and cleared only by the apply path (a NavigationUpdate).

This module holds the pure predicates every consumer reads (`is_lodged`, `lodgers_of`, `has_free_bed`), the claim a bed service makes, the bed grant (`grant_beds`) and where a
leaver steps out (`leave_tile`). It writes no state.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

Tile = Tuple[int, int]

# The orthogonal reach tiles beside a building tile, in the fixed order of ``service_reach._REACH_OFFSETS`` without (0, 0): a leaver takes the first free one.
LEAVE_OFFSETS: Tuple[Tile, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))
LEAVE_RING_RADIUS = 3  # then the nearest free walkable tile within this many tiles, by a fixed ring order


def is_lodged(entity: Any) -> bool:
    """True while ``entity`` lodges in a building. The one predicate every spatial index, perception and targeting filter reads."""
    return entity.navigation.lodged_in is not None


def lodgers_of(state: Any, building_id: int) -> Tuple[int, ...]:
    """The ids of the living entities lodged in ``building_id``, ascending. Derived from the entities; a worker packet without entities answers ()."""
    entities = getattr(state, "entities", None) or {}
    return tuple(sorted(e_id for e_id, e in entities.items() if e.navigation.lodged_in == building_id and e.combat.alive))


def lodges(building: Any) -> bool:
    """True when ``building`` lodges anyone at all (content ``beds`` > 0). Zero or absent: its rest is served on the reach tile exactly as before."""
    return int(getattr(building, "beds", 0) or 0) > 0


def has_free_bed(state: Any, building: Any, entity: Any = None) -> bool:
    """True when ``building`` can take one more lodger: it has no beds declared (main's behaviour, nothing to count), or a bed is free, or ``entity`` already holds one."""
    if not lodges(building):
        return True
    held = lodgers_of(state, building.id)
    return (entity is not None and entity.id in held) or len(held) < int(building.beds)
