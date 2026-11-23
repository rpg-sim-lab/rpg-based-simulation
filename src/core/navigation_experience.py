"""The navigation experience memory (the #996 rework, TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON; design: docs/plans/systemic_world/experience_memory_design.md sections 2.2, 3, 5).

A subject that gave up reaching a place remembers WHY (a cause and the evidence of it), for WHAT it was moving (the purpose of the target) and from WHERE, and reconsiders the place by that reason. This module holds the
typed vocabulary shared by the producer (movement's give-up record) and the memory (the subject's own `MemoryModel.navigation`): the causes, the ring evidence mapped from legality's refusal codes, the status of a
record, and the reason it was reviewed. No kind, role, faction or name is read anywhere in it."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Dict, FrozenSet, Iterable, Optional, Tuple

from src.core.enums import ReasonCode
from src.core.navigation_purpose import TargetPurpose


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


class NeedService(str, Enum):
    """A need a place can answer: a food tile (EAT) or a bed tile (REST), by the building kinds the existing service table declares."""
    EAT = "EAT"
    REST = "REST"


class NavExperienceStatus(str, Enum):
    """Whether a record still refuses its approach (ACTIVE) or has been reviewed."""
    ACTIVE = "active"
    REVIEWED = "reviewed"


class ReviewReason(str, Enum):
    """Why a record was reviewed (the first due rule that held)."""
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


# --- the record and the memory (design section 2.2) ------------------------------------------------------------------------------------------------------------------------------------------------------

def experience_id_of(anchor: Tuple[int, int], purpose: TargetPurpose) -> str:
    """The id of the one live record for (anchor, purpose): ``nx_<x>_<y>_<project_kind>_<movement_mode>``, built from integer tiles and `.value` strings only (no name, no kind of body)."""
    return f"nx_{int(anchor[0])}_{int(anchor[1])}_{purpose.project_kind}_{purpose.movement_mode}"


@dataclass(frozen=True, slots=True)
class NavigationExperience:
    """One failed approach the subject remembers, scoped to the purpose it moved with. Written only by the subject's strategic consume step (`consume_giveup_records`), never by the gate."""
    experience_id: str
    anchor: Tuple[int, int]
    purpose: TargetPurpose
    cause: NavCause
    ring_evidence: Tuple[RingEvidence, ...]    # sorted, distinct; () for OSCILLATION
    from_position: Tuple[int, int]
    target_tile: Tuple[int, int]
    need_services: FrozenSet[NeedService]      # the needs the building in reach of the anchor serves (the existing `SERVICE_KINDS` lookup); empty = not a food or bed tile
    project_id: str                            # "" when none
    observed_tick: int
    cycle: int                                 # identity and history only; never enters a due rule
    next_review_tick: Optional[int]            # None when the due rule is trigger-only
    status: NavExperienceStatus
    reviewed_tick: Optional[int]
    review_reason: Optional[ReviewReason]
    project_giveups: int

    def to_canonical(self) -> Dict[str, Any]:
        """Every field, in a fixed key order: the record is hashed whole."""
        return {
            "experience_id": self.experience_id, "anchor": [int(self.anchor[0]), int(self.anchor[1])], "purpose": self.purpose.to_canonical(), "cause": self.cause.value,
            "ring_evidence": [e.value for e in self.ring_evidence], "from_position": [int(self.from_position[0]), int(self.from_position[1])],
            "target_tile": [int(self.target_tile[0]), int(self.target_tile[1])], "need_services": sorted(s.value for s in self.need_services), "project_id": self.project_id,
            "observed_tick": int(self.observed_tick), "cycle": int(self.cycle), "next_review_tick": self.next_review_tick, "status": self.status.value,
            "reviewed_tick": self.reviewed_tick, "review_reason": None if self.review_reason is None else self.review_reason.value, "project_giveups": int(self.project_giveups),
        }


@dataclass(frozen=True, slots=True)
class NavigationExperienceMemory:
    """The subject's navigation experiences (``MemoryModel.navigation``), sorted by id. Empty by default; an older state loads empty."""
    records: Tuple[NavigationExperience, ...] = ()

    def to_canonical_dict(self) -> Dict[str, Any]:
        """The canonical dict: the records in id order."""
        return {"records": [r.to_canonical() for r in self.records]}


@dataclass(frozen=True, slots=True)
class ExperienceReview:
    """A review the consume step recorded: applies only to the stored record of that cycle while it is ACTIVE (idempotent)."""
    experience_id: str
    cycle: int
    reviewed_tick: int
    reason: ReviewReason


@dataclass(frozen=True, slots=True)
class NavigationExperienceUpdate:
    """The one typed update of the experience memory, written only by the subject's strategic consume step: reviews, upserts (a record at a NEW cycle replaces the stored one) and the ids evicted at the cap."""
    reviews: Tuple[ExperienceReview, ...] = ()
    upserts: Tuple[NavigationExperience, ...] = ()
    evictions: Tuple[str, ...] = ()

    def is_noop(self) -> bool:
        """True when the update carries no review, upsert or eviction."""
        return not (self.reviews or self.upserts or self.evictions)

    def merge(self, other: "NavigationExperienceUpdate") -> "NavigationExperienceUpdate":
        """This update merged under ``other`` (reviews and upserts concatenated, evictions a sorted union)."""
        if other is None or other.is_noop():
            return self
        return NavigationExperienceUpdate(self.reviews + other.reviews, self.upserts + other.upserts, tuple(sorted(set(self.evictions) | set(other.evictions))))


def apply_experience_update(memory: NavigationExperienceMemory, update: NavigationExperienceUpdate) -> NavigationExperienceMemory:
    """The memory after ``update``, pure and deterministic: evictions first, then reviews (only of the stored cycle, only while ACTIVE), then upserts (only over a lower stored cycle, so an upsert of cycle n + 1
    supersedes a review of cycle n in the same update). Records come out sorted by id."""
    records = {r.experience_id: r for r in memory.records if r.experience_id not in update.evictions}
    for review in update.reviews:
        stored = records.get(review.experience_id)
        if stored is not None and stored.cycle == review.cycle and stored.status == NavExperienceStatus.ACTIVE:
            records[review.experience_id] = replace(stored, status=NavExperienceStatus.REVIEWED, reviewed_tick=review.reviewed_tick, review_reason=review.reason)
    for record in sorted(update.upserts, key=lambda r: r.experience_id):
        stored = records.get(record.experience_id)
        if stored is None or stored.cycle < record.cycle:
            records[record.experience_id] = record
    return NavigationExperienceMemory(tuple(records[k] for k in sorted(records)))


def with_navigation_experience(cognition: Any, update: NavigationExperienceUpdate) -> Any:
    """The cognition model with its memory's navigation experiences after ``update`` (the navigation patch's apply). Duck-typed on the cognition model so this module does not import it (the memory model imports this one)."""
    return replace(cognition, memory=replace(cognition.memory, navigation=apply_experience_update(cognition.memory.navigation, update)))


class NavigationExperienceCounts:
    """Counts of what the consume step skipped or ended: OBSERVABILITY ONLY, never durable state; written only by the consume step, read and reset only by the run ledger (it lives in this core module because
    the layer contract allows systems -> core and observability -> core). Nothing in the simulation reads it."""

    _no_purpose: int = 0
    _live_evictions: int = 0

    @classmethod
    def note_no_purpose(cls) -> None:
        """A give-up whose stored purpose was None (a target restored from an old checkpoint) filed no experience."""
        cls._no_purpose += 1

    @classmethod
    def note_live_eviction(cls) -> None:
        """An ACTIVE record that was not yet due was evicted at the cap (it ended a live refusal)."""
        cls._live_evictions += 1

    @classmethod
    def no_purpose(cls) -> int:
        """How many give-ups were not filed because the pursuit had no stored purpose."""
        return cls._no_purpose

    @classmethod
    def live_evictions(cls) -> int:
        """How many records the cap evicted while still ACTIVE and not due."""
        return cls._live_evictions

    @classmethod
    def reset(cls) -> None:
        """Clear both counts (run start, test teardown)."""
        cls._no_purpose = 0
        cls._live_evictions = 0
