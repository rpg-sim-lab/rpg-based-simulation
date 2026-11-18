from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.engine.economy import ResourceTransactionSystem
from src.world.risen import RisenService

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.engine.cadence import SystemCadence


class ResourceTransactionPhase:
    """
    Resolves ResourceTransferIntent objects into inventory, identity, node,
    corpse, chest, or rejection updates.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate, cadence: Optional[SystemCadence] = None) -> StateUpdate:
        """
        Resolve all resource transactions, then the rise sub-step: a corpse a loot or meal took or shrank this tick does not rise, so it runs on the outcome.
        """
        return RisenService.process_rises(state, ResourceTransactionSystem.resolve_all(state, update), cadence)
