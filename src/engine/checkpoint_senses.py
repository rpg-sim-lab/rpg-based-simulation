"""The restore-time sense check (PERC-02a, STRAT-352): a checkpoint is read under the CURRENT catalog, so a body saved under older content can belong to a species that has since lost its sense profile.

Restore refuses it before any tick, with a typed error that is a checkpoint fact (a ``ValueError``, like the other restore refusals), and keeps the content error as its ``__cause__``."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from src.content.species_senses import require_species_sense_profile
from src.core.species import SenseProfileError, species_of


class RestoredBodySenseProfileError(ValueError):
    """A restored body's species has no usable sense profile under the current content. Names the checkpoint, the entity and the species; ``__cause__`` is the ``SenseProfileError``."""


def check_restored_body_senses(state: Any, path: "str | Path", catalog: Optional[Any] = None) -> None:
    """Refuse a checkpoint holding a body whose species resolves no usable sense profile (lowest entity id first)."""
    checked = set()
    for entity_id in sorted(state.entities):
        species_id = species_of(state.entities[entity_id])
        if species_id in checked:
            continue
        try:
            require_species_sense_profile(species_id, f"restored entity {entity_id}", catalog)
        except SenseProfileError as err:
            raise RestoredBodySenseProfileError(
                f"checkpoint {str(path)!r}: entity {entity_id} has species {species_id!r}, which has no usable sense profile under the current content"
            ) from err
        checked.add(species_id)
