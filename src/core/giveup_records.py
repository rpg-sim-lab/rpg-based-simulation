"""The typed record of a way-round give-up (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; rpg-designer FINAL v2).

A give-up (the oscillation replan that drops the target, divergence 2.213) is a tactical FINDING: "I cannot get there from here now". The destination belongs to strategy, so the finding reaches
the layer that owns it as this typed record on the subject's navigation. Two writers, one owner each: movement APPENDS one (`NavigationUpdate.giveup_record_add`, applied by the navigation
patch) and the strategic pass CLEARS them (`NavigationUpdate.giveup_records_clear`) after it has filed the matching blockers. At most `GIVEUP_RECORDS_CAP` are kept, newest last; one dropped at the cap is
counted in `GiveUpDropCounts` (observability only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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
    """One give-up: ``anchor`` is the tile the pursuit's way-round count opened on (the tile the subject could not get to), ``tick`` the tick of the give-up."""
    anchor: Tuple[int, int]
    tick: int

    def to_canonical(self) -> Dict[str, object]:
        """The canonical-dict form: the anchor as a list, the tick."""
        return {"anchor": [int(self.anchor[0]), int(self.anchor[1])], "tick": int(self.tick)}


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



def giveup_clear_beats_target(target_set: Optional[Tuple[float, float]], record: Optional[GiveUpRecord], clear_anchor: Optional[Tuple[int, int]] = None) -> bool:
    """The navigation patch's same-update rule (rpg-designer F2 v2.2a A''): True when ONE merged update carries a give-up record AND a ``target_set`` within `GIVEUP_NEAR_RADIUS` of THAT record's anchor, so
    the give-up's clear wins over the set. Generalised (rpg-designer, F2 pairing re-run): the same holds for ONE update that carries the strategic pass's suppression clear with its ``clear_anchor`` (the anchor of the
    suppression that made the pass clear the stored target): the clear wins over a same-update set within `GIVEUP_NEAR_RADIUS` of THAT anchor. A set elsewhere stands (a flee's retreat tile keeps its tick); no record and no
    anchor, no rule. Each anchor decides only for itself. Pure geometry: no world read, no suppression policy."""
    if target_set is None:
        return False
    return (record is not None and near_anchor(target_set, record.anchor)) or (clear_anchor is not None and near_anchor(target_set, clear_anchor))
