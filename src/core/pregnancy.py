"""The pregnancy of a mother (M1 reproduction): a typed, frozen record on her lifecycle from conception to the birth at term or her death."""
# Compliance IDs: WORLD-122
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from src.core.state import GeneticProfile  # re-exported there; importing it from systems here would add a core -> systems edge


@dataclass(frozen=True, slots=True)
class PregnancyState:
    """One pregnancy: who sired it, when it started and ends, the litter drawn at conception, and the father's genes as they were at conception.

    ``father_genetic_profile`` is a snapshot, so a father who dies before term still gives his genes; ``due_tick`` is always a births check tick
    (the profile's ``gestation_ticks`` is a multiple of the check interval). The mother's death clears it in the death's own update."""

    father_entity_id: int
    conceived_tick: int
    due_tick: int
    litter_size: int
    father_genetic_profile: GeneticProfile

    def to_canonical_dict(self) -> Dict[str, Any]:
        """The record as plain sorted-key data for hashing and checkpoints."""
        return {
            "father_entity_id": self.father_entity_id,
            "conceived_tick": self.conceived_tick,
            "due_tick": self.due_tick,
            "litter_size": self.litter_size,
            "father_genetic_profile": asdict(self.father_genetic_profile),
        }
