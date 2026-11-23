"""Region-contained tactical destinations for retreat and stalemate-break wandering.

Pure functions: they read the state and the entity and return a destination or ``None``.
They never mutate state; the caller turns the result into a ``NavigationUpdate``.

Governing Rules (docs/world_rules/space-environment/): MOV-01 (a destination must be valid),
LOC-01 / LOC-03 (containment is a real relationship, an entity outside every region is outside
the declared spatial model), MOV-03 (holding position is a legitimate outcome).

Retreat and wander are different semantics and deliberately do not share a derivation.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from src.core.enums import Domain
from src.platform.rng import DeterministicRNG
from src.strategy.destination_suppression import propose_target

if TYPE_CHECKING:
    from src.core.navigation_purpose import TargetPurpose
    from src.core.state import AuthoritativeState, EntityState, RegionState

Position = Tuple[float, float]

# One perception radius (get_neighbor_view radius in TacticalDecisionSystem): a retreating entity
# aims for the point that far beyond itself along the away-vector, so it keeps clear of the
# threat horizon it is reacting to.
RETREAT_STEP = 10.0
# Half-width of the square a stalemate-breaking entity wanders within.
WANDER_RADIUS = 5.0
_EPSILON = 1e-9


def _manhattan(a: Position, b: Position) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def containing_region(state: "AuthoritativeState", pos: Position) -> Optional["RegionState"]:
    """The region whose bounds contain ``pos``, or None.

    Strict bounds only. ``RegionService.find_region_at`` falls back to the nearest region centre,
    which would call a point outside every region "inside" one; that is exactly the defect here.
    Iterates in sorted id order so overlapping bounds resolve the same way every run.
    """
    px, py = pos
    for region_id in sorted(state.regions):
        region = state.regions[region_id]
        xmin, ymin, xmax, ymax = region.bounds
        if xmin <= px <= xmax and ymin <= py <= ymax:
            return region
    return None


def _clamp_into(region: "RegionState", pos: Position) -> Position:
    xmin, ymin, xmax, ymax = region.bounds
    return (min(max(pos[0], float(xmin)), float(xmax)), min(max(pos[1], float(ymin)), float(ymax)))


def _away_destination(
    region: "RegionState", here: Position, threat_positions: list[Position], step: float = RETREAT_STEP
) -> Optional[Position]:
    """The point one ``step`` (RETREAT_STEP unless the suppression fallback halves it) directly away from the threats, clamped into ``region``.

    None when the threats give no direction (they cancel out) or the clamped point is no farther from the
    nearest threat than the entity already is (cornered).
    """
    away_x = sum(here[0] - p[0] for p in threat_positions)
    away_y = sum(here[1] - p[1] for p in threat_positions)
    norm = math.hypot(away_x, away_y)
    if norm <= _EPSILON:
        return None
    candidate = _clamp_into(
        region, (here[0] + away_x / norm * step, here[1] + away_y / norm * step)
    )
    nearest_now = min(_manhattan(here, p) for p in threat_positions)
    nearest_then = min(_manhattan(candidate, p) for p in threat_positions)
    return candidate if nearest_then > nearest_now + _EPSILON else None


def wander_destination(state: "AuthoritativeState", entity: "EntityState") -> Optional[Position]:
    """A seeded, nearby, region-contained point for a stalemate-breaking entity, or None.

    None when the entity is itself outside every region: there is no region to stay inside, so
    the caller holds position rather than inventing a destination.
    """
    here: Position = entity.navigation.position
    region = containing_region(state, here)
    if region is None:
        return None
    rng = DeterministicRNG(state.seed)
    dx = (rng.get_float(Domain.TACTICAL, state.tick, entity.id, 0) * 2.0 - 1.0) * WANDER_RADIUS
    dy = (rng.get_float(Domain.TACTICAL, state.tick, entity.id, 1) * 2.0 - 1.0) * WANDER_RADIUS
    return _clamp_into(region, (here[0] + dx, here[1] + dy))


def retreat_destination(
    state: "AuthoritativeState",
    entity: "EntityState",
    threats: Iterable["EntityState"],
    purpose: "TargetPurpose",
) -> Optional[Position]:
    """Where a retreating entity should head, or None when no valid destination exists. The candidates in a fixed order, each through `propose_target` (F2 v2.2a D2, class F: a destination near a suppressed
    give-up anchor is refused): (1) away from the perceived threats, clamped to stay inside the entity's current region (uses only the threats the caller already perceives and the entity's own position);
    (2) the same direction at half the distance, clamped into the region as today; (3) the entity's own ``strategic.home_region_id`` region centre, when set and present. None when no candidate exists (no
    threat vector, cornered, no home) or every one is refused: the caller holds position (MOV-03), never a sentinel coordinate. With no suppression this is exactly the old derivation (the half-distance point is tried only
    when the full-distance point exists and is refused)."""
    here: Position = entity.navigation.position
    region = containing_region(state, here)
    threat_positions = sorted(t.navigation.position for t in threats)
    if region is not None and threat_positions:
        away = _away_destination(region, here, threat_positions)
        if away is not None:
            if propose_target(entity, away, state.tick, purpose) is not None:
                return away
            half = _away_destination(region, here, threat_positions, RETREAT_STEP / 2.0)  # (2) only when (1) exists and is refused: an unrefused derivation is the old one
            if half is not None and propose_target(entity, half, state.tick, purpose) is not None:
                return half
    home_id = entity.strategic.home_region_id
    home = state.regions.get(home_id) if home_id else None
    return propose_target(entity, home.center, state.tick, purpose) if home is not None else None
