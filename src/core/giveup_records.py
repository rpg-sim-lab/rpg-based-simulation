"""The typed record of a way-round give-up (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; rpg-designer FINAL v2).

A give-up (the oscillation replan that drops the target, divergence 2.213) is a tactical FINDING: "I cannot get there from here now". The destination belongs to strategy, so the finding reaches
the layer that owns it as this typed record on the subject's navigation. Two writers, one owner each: movement APPENDS one (`NavigationUpdate.giveup_record_add`, applied by the navigation
patch) and the strategic pass CLEARS them (`NavigationUpdate.giveup_records_clear`) after it has filed the matching blockers. At most `GIVEUP_RECORDS_CAP` are kept, newest last; one dropped at the cap is
counted in `GiveUpDropCounts` (observability only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from src.core.navigation_experience import NavCause, RingEvidence
from src.core.navigation_purpose import TargetPurpose

# The designer's structural bound on unconsumed records (FINAL v2, OBJ-2): the strategic pass consumes them every pass, so more than this means the strategic pass is not running for the subject.
GIVEUP_RECORDS_CAP = 4

# The "near" of a give-up anchor (rpg-designer F2 v2.2a A''): a tile within this Chebyshev distance of an anchor is the anchor for suppression (destination_suppression, the consume step's held-target count) and for
# the navigation patch's same-update rule (a give-up's clear beats a target_set near its own anchor). Written here ONCE; the +-1 covers the task layer's one-tile jitter of an objective's target.
GIVEUP_NEAR_RADIUS = 1


def near_anchor(tile: Tuple[float, float], anchor: Tuple[float, float]) -> bool:
    """True when ``tile`` is within `GIVEUP_NEAR_RADIUS` (Chebyshev, integer tiles) of ``anchor``. Pure geometry: no policy, no state."""
    return max(abs(int(tile[0]) - int(anchor[0])), abs(int(tile[1]) - int(anchor[1]))) <= GIVEUP_NEAR_RADIUS


@dataclass(frozen=True, slots=True)
class GiveUpRecord:
    """One give-up: ``anchor`` is the tile the pursuit's way-round count opened on (the tile the subject could not get to), ``tick`` the tick of the give-up.

    The #996 rework adds the producer's EVIDENCE (design section 3), each written by `MovementSystem._oscillation_replan` from facts it already holds: ``cause`` (RING_BLOCKED when the one-ring check found no legal
    tile, else OSCILLATION), ``ring_evidence`` (the legality refusal of each ring tile, mapped to BODIES / STATIC / OTHER), ``from_position`` (the subject's tile), ``target_tile`` (the tile it was walking to) and
    ``purpose`` (the STORED purpose of the pursuit that failed; None for a target restored from an old checkpoint). A record built with only an anchor and a tick (``from_position`` None) carries none of it."""
    anchor: Tuple[int, int]
    tick: int
    cause: NavCause = NavCause.OSCILLATION
    ring_evidence: Tuple[RingEvidence, ...] = ()
    from_position: Optional[Tuple[int, int]] = None
    target_tile: Optional[Tuple[int, int]] = None
    purpose: Optional[TargetPurpose] = None

    def to_canonical(self) -> Dict[str, object]:
        """The canonical-dict form: the anchor as a list and the tick; the evidence only on a record that carries it (``from_position`` set), so a bare record keeps its older form."""
        res: Dict[str, object] = {"anchor": [int(self.anchor[0]), int(self.anchor[1])], "tick": int(self.tick)}
        if self.from_position is not None:
            res["cause"] = self.cause.value
            res["ring_evidence"] = [e.value for e in self.ring_evidence]
            res["from_position"] = [int(self.from_position[0]), int(self.from_position[1])]
            res["target_tile"] = None if self.target_tile is None else [int(self.target_tile[0]), int(self.target_tile[1])]
            res["purpose"] = None if self.purpose is None else self.purpose.to_canonical()
        return res


def giveup_canonical(records: Tuple[GiveUpRecord, ...]) -> Dict[str, object]:
    """The canonical-dict entry of a navigation's held records: ``{"giveup_records": [...]}`` while any is held, ``{}`` while none (the form of a subject that never gave up is unchanged)."""
    return {"giveup_records": [r.to_canonical() for r in records]} if records else {}


class GiveUpDropCounts:
    """A count of give-up records dropped at `GIVEUP_RECORDS_CAP`. OBSERVABILITY ONLY, never durable state; written only by the navigation patch's append, read and reset only by the run ledger
    (it lives in this core module because the layer contract allows engine -> core and observability -> core, not engine -> observability). Nothing in the simulation reads it."""

    _dropped: int = 0

    @classmethod
    def note(cls) -> None:
        """Count one record dropped at the cap."""
        cls._dropped += 1

    @classmethod
    def dropped(cls) -> int:
        """How many records were dropped at the cap since the last reset."""
        return cls._dropped

    @classmethod
    def reset(cls) -> None:
        """Clear the count (run start, and test teardown)."""
        cls._dropped = 0


class HeldTargetAtAnchorCounts:
    """A count of the times the consume step found the subject's STORED target within Chebyshev 1 of a consumed give-up anchor (rpg-designer v2.1c: report only; consume does NOT clear it). OBSERVABILITY ONLY, never durable
    state, read and reset only by the run ledger. With every target writer routed through `destination_suppressed` it should read 0; a nonzero count names a writer that skips the helper."""

    _held: int = 0

    @classmethod
    def note(cls) -> None:
        """Count one held target at a consumed anchor."""
        cls._held += 1

    @classmethod
    def held(cls) -> int:
        """How many were seen since the last reset."""
        return cls._held

    @classmethod
    def reset(cls) -> None:
        """Clear the count (run start, and test teardown)."""
        cls._held = 0



def anchored_target(target_set: Optional[Tuple[float, float]], explicit_clear: bool, stored: Optional[Tuple[float, float]], record: Optional[GiveUpRecord], clear_anchors: Tuple[Tuple[int, int], ...]) -> Tuple[Optional[Tuple[float, float]], bool]:
    """The navigation patch's ONE anchor rule (rpg-designer, F2 v2.2a A'' and its pairing-run generalisation): the target a merged update leaves stored and whether the stored path goes with it. Two anchors may ride one update, each
    decides only for itself: the give-up record's (``record``) and the strategic pass's (``clear_anchors``: set with a refusal clear, or alone when the pass files or extends a suppression). (1) a ``target_set`` within `GIVEUP_NEAR_RADIUS` of
    an anchor is dropped; (2) with no set left, a STORED target within the radius of an anchor is cleared; (3) any other target, set or stored, stands. With no anchor this is today's precedence: the set wins, else an explicit clear
    clears, else the stored target stays. Pure geometry on the update and the patched entity's own stored target: no other entity, no world, no suppression policy. Returns (target, drop_path)."""
    anchors = ((record.anchor,) if record is not None else ()) + tuple(clear_anchors)
    dropped = target_set is not None and any(near_anchor(target_set, a) for a in anchors)
    kept = None if dropped else target_set
    stored_near = kept is None and stored is not None and any(near_anchor(stored, a) for a in anchors)
    if kept is not None:
        return kept, False
    if explicit_clear or stored_near:
        return None, dropped or stored_near
    return stored, dropped
