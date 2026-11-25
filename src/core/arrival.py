"""The STRUCTURAL adjacency rule of arrival: a body is ARRIVED at a point when its Manhattan distance to it is at most one tile (`ARRIVAL_DISTANCE`). It is not a balance value (nothing here is tuned, so it lives in core and not in
data/): it is the same adjacency the objective step has always used to tell a walk that is still en route from one that has arrived (`tactical_objective`: `_reach_location_step`, `_other_objective_step`, the fatigue arrival).

`has_arrived(position, target)` is pure and reads nothing else. Movement applies it to the walk's own NAV TARGET (the stored target the walk is moving to, `resolve_move`'s ``target_pos``), never to an objective: movement
does not see objectives. The strategic detour completion (`intelligence.py`, ``dist < 1.0``) is a DIFFERENT rule at exactly 1.0 (strictly less) and is deliberately left as it is."""
from __future__ import annotations

from typing import Tuple

ARRIVAL_DISTANCE: float = 1.0


def has_arrived(position: Tuple[float, float], target: Tuple[float, float]) -> bool:
    """True when ``position`` is within `ARRIVAL_DISTANCE` of ``target`` (Manhattan distance, boundary included)."""
    return abs(target[0] - position[0]) + abs(target[1] - position[1]) <= ARRIVAL_DISTANCE
