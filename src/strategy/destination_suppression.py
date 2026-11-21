"""Destination suppression (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; rpg-designer FINAL v2.1): READ-ONLY helpers over a subject's ACCESS blockers.

A way-round give-up files an ACCESS blocker ``blocker_access_<x>_<y>`` for the anchor tile (the strategic pass's consume step); while that blocker is suppressed no writer may re-target a tile within
Chebyshev 1 of its anchor. Everything here is pure: it reads the entity and a tick and returns a value; nothing is written, there is no RNG, and every comparison is on integer tiles by the id, never
by the subject text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from src.core.state import EntityState
from src.core.strategic import BlockerState

ACCESS_BLOCKER_ID_PREFIX = "blocker_access_"
_ACCESS_ID = re.compile(r"^blocker_access_(-?\d+)_(-?\d+)$")


def access_blocker_id(tile: Tuple[float, float]) -> str:
    """The id of the ACCESS blocker for ``tile`` (integer tile), the one `infer_blockers` files for a navigation failure: ``blocker_access_<x>_<y>``."""
    return f"{ACCESS_BLOCKER_ID_PREFIX}{int(tile[0])}_{int(tile[1])}"


def access_subject(tile: Tuple[float, float]) -> str:
    """The subject text of an ACCESS blocker for ``tile`` in the format `infer_blockers` already writes (``f"{target_pos}"`` on float coordinates, e.g. ``"(9.0, 5.0)"``), so every existing reader of an
    ACCESS blocker's subject (resolution, detour, ResolveBlockerScorer, score modifiers) behaves as it does today. Normalising the format is another ticket's job (the material/partner subject ticket)."""
    return f"{(float(tile[0]), float(tile[1]))}"


def access_blocker_tile(blocker: BlockerState) -> Optional[Tuple[int, int]]:
    """The integer tile an ACCESS blocker names by its id, or None when it is not a ``blocker_access_<x>_<y>`` blocker (the congestion blocker, a material blocker)."""
    if blocker.kind != "access":
        return None
    m = _ACCESS_ID.match(blocker.id)
    return (int(m.group(1)), int(m.group(2))) if m else None


@dataclass(frozen=True, slots=True)
class SuppressionHit:
    """Why a tile is forbidden as a destination: the ACCESS blocker id of the anchor, the anchor tile, how long (``suppressed_until``, None while only PENDING), whether the forbidding record is a
    still-unconsumed give-up record (``pending``, v2.1c) or a filed blocker, and the blocker's ``failure_count`` (0 while pending)."""
    blocker_id: str
    anchor: Tuple[int, int]
    suppressed_until: Optional[int]
    pending: bool
    failure_count: int


def destination_suppressed(entity: EntityState, pos: Tuple[float, float], tick: int) -> Optional[SuppressionHit]:
    """The reason ``pos`` is forbidden as a destination for this subject at ``tick``, or None. Two sources, both within Chebyshev 1 of an anchor (integer tiles; the +-1 covers the task layer's one-tile
    jitter of the objective's target): (1) an unresolved ``blocker_access_<x>_<y>`` ACCESS blocker of the subject with ``tick`` before its ``suppression_until_tick``; (2) v2.1c, the subject's own PENDING
    give-up records (``navigation.giveup_records``, held until the strategic pass consumes them), so a target cannot be re-set to the anchor between the give-up and the filing. A filed blocker wins over
    a pending record, and the lowest blocker id wins among blockers, so the answer does not depend on dict order."""
    tx, ty = int(pos[0]), int(pos[1])
    hit: Optional[SuppressionHit] = None
    for blocker in entity.strategic.blockers.values():
        tile = access_blocker_tile(blocker)
        if tile is None or blocker.resolved or tick >= blocker.suppression_until_tick:
            continue
        if max(abs(tx - tile[0]), abs(ty - tile[1])) <= 1 and (hit is None or blocker.id < hit.blocker_id):
            hit = SuppressionHit(blocker.id, tile, blocker.suppression_until_tick, False, blocker.failure_count)
    if hit is not None:
        return hit
    for record in entity.navigation.giveup_records:
        anchor = (int(record.anchor[0]), int(record.anchor[1]))
        if max(abs(tx - anchor[0]), abs(ty - anchor[1])) <= 1:
            return SuppressionHit(access_blocker_id(anchor), anchor, None, True, 0)
    return None


def destination_open(entity: EntityState, pos: Tuple[float, float], tick: int) -> bool:
    """True when no suppressed give-up ACCESS blocker forbids ``pos`` as a destination (the guard of every target writer)."""
    return destination_suppressed(entity, pos, tick) is None

