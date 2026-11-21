"""The typed record of a way-round give-up (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; rpg-designer FINAL v2).

A give-up (the oscillation replan that drops the target, divergence 2.213) is a tactical FINDING: "I cannot get there from here now". The destination belongs to strategy, so the finding reaches
the layer that owns it as this typed record on the subject's navigation. Two writers, one owner each: movement APPENDS one (`NavigationUpdate.giveup_record_add`, applied by the navigation
patch) and the strategic pass CLEARS them (`NavigationUpdate.giveup_records_clear`) after it has filed the matching blockers. At most `GIVEUP_RECORDS_CAP` are kept, newest last; one dropped at the cap is
counted in `GiveUpDropCounts` (observability only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

# The designer's structural bound on unconsumed records (FINAL v2, OBJ-2): the strategic pass consumes them every pass, so more than this means the strategic pass is not running for the subject.
GIVEUP_RECORDS_CAP = 4


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
