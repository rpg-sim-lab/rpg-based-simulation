"""When the resource_transactions phase also runs for a rise check: moved verbatim out of src/world/risen.py so the engine's phase graph can read it without importing the world layer
(import contract "Registry layer order"; TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.engine.cadence import SystemCadence, should_run

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState


def rise_triggers_phase(phase_name: str, state: AuthoritativeState, cadence: Optional[SystemCadence]) -> bool:
    """The resource_transactions phase also runs on a rise check when the world holds a corpse: the rise sub-step lives at its end and a clean dirty set must not skip it."""
    return phase_name == "resource_transactions" and bool(state.corpses) and should_run(state.tick, None, cadence.rises if cadence is not None else SystemCadence.model_fields["rises"].default)
