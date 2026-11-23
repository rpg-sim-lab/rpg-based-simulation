"""The navigation experience memory (the #996 rework, TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON; design: docs/plans/systemic_world/experience_memory_design.md sections 2.2, 3, 5).

A subject that gave up reaching a place remembers WHY (a cause and the evidence of it), for WHAT it was moving (the purpose of the target) and from WHERE, and reconsiders the place by that reason. This module holds the
typed vocabulary shared by the producer (movement's give-up record) and the memory (the subject's own `MemoryModel.navigation`): the causes, the ring evidence mapped from legality's refusal codes, the status of a
record, and the reason it was reviewed. No kind, role, faction or name is read anywhere in it."""
from __future__ import annotations

from enum import Enum
from typing import Iterable, Tuple

from src.core.enums import ReasonCode


class NavCause(str, Enum):
    """Why the subject could not get there. Slice 1 writes the first two."""
    OSCILLATION = "oscillation"      # a way-round tile existed, but the bounded count passed `wayround_limit` with no net progress
    RING_BLOCKED = "ring_blocked"    # the ONE-RING check (the sidestep plus the 4 orthogonal neighbours) found no legal tile; not a route search
    UNCLASSIFIED = "unclassified"    # reserved; slice 1 writes none


class RingEvidence(str, Enum):
    """From the `ReasonCode` each ring tile was refused with (`LegalityServiceV2.verify_movement_legality`)."""
    BODIES = "bodies"                # the tile is occupied, or claimed by another mover this tick
    STATIC = "static"                # terrain, a building or the world's bounds
    OTHER = "other"                  # any other refusal (exhaustion, a blocking status); rare: the oscillation branch follows a step that already passed these


class NavExperienceStatus(str, Enum):
    ACTIVE = "active"
    REVIEWED = "reviewed"


class ReviewReason(str, Enum):
    DUE_TICK = "due_tick"
    APPROACH_CHANGED = "approach_changed"
    NEED_SEVERE = "need_severe"
    TARGET_ACCEPTED = "target_accepted"   # the subject holds an accepted target at the anchor with the record's purpose


_BODY_CODES = frozenset({ReasonCode.OCCUPANCY_VIOLATION, ReasonCode.IDEMPOTENCY_VIOLATION})
_OTHER_CODES = frozenset({ReasonCode.ACTION_EXHAUSTION, ReasonCode.ATTACKER_STATUS_BLOCKED, ReasonCode.INSUFFICIENT_READINESS})


def ring_evidence_of(refusals: Iterable[ReasonCode]) -> Tuple[RingEvidence, ...]:
    """The distinct evidence of the ring tiles' refusal codes, in a fixed order (BODIES, STATIC, OTHER): an occupancy or idempotency refusal is BODIES, a readiness or status refusal is OTHER, every other refusal
    (the static obstruction reasons of `verify_occupancy`) is STATIC. A tile that was not refused contributes nothing. Pure."""
    seen = set()
    for code in refusals:
        if code == ReasonCode.LEGAL:
            continue
        seen.add(RingEvidence.BODIES if code in _BODY_CODES else RingEvidence.OTHER if code in _OTHER_CODES else RingEvidence.STATIC)
    return tuple(e for e in (RingEvidence.BODIES, RingEvidence.STATIC, RingEvidence.OTHER) if e in seen)
