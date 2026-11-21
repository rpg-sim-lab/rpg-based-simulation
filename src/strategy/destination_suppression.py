"""Destination suppression (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; rpg-designer FINAL v2.1): READ-ONLY helpers over a subject's ACCESS blockers.

A way-round give-up files an ACCESS blocker ``blocker_access_<x>_<y>`` for the anchor tile (the strategic pass's consume step); while that blocker is suppressed no writer may re-target a tile within
Chebyshev 1 of its anchor. Everything here is pure: it reads the entity and a tick and returns a value; nothing is written, there is no RNG, and every comparison is on integer tiles by the id, never
by the subject text."""
from __future__ import annotations

import re
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


def destination_suppressed(entity: EntityState, pos: Tuple[float, float], tick: int) -> Optional[BlockerState]:
    """The active, suppressed ACCESS blocker that forbids ``pos`` as a destination, or None. A blocker forbids a tile when it is an unresolved ``blocker_access_<x>_<y>`` blocker of the subject, the
    tile is within Chebyshev 1 of its anchor (``int`` tiles; the +-1 covers the task layer's one-tile jitter of the objective's target), and ``tick`` is before its ``suppression_until_tick``. The
    blocker with the lowest id wins when several apply, so the answer does not depend on dict order."""
    tx, ty = int(pos[0]), int(pos[1])
    hit: Optional[BlockerState] = None
    for blocker in entity.strategic.blockers.values():
        tile = access_blocker_tile(blocker)
        if tile is None or blocker.resolved or tick >= blocker.suppression_until_tick:
            continue
        if max(abs(tx - tile[0]), abs(ty - tile[1])) <= 1 and (hit is None or blocker.id < hit.id):
            hit = blocker
    return hit


def destination_open(entity: EntityState, pos: Tuple[float, float], tick: int) -> bool:
    """True when no suppressed give-up ACCESS blocker forbids ``pos`` as a destination (the guard of every target writer)."""
    return destination_suppressed(entity, pos, tick) is None

