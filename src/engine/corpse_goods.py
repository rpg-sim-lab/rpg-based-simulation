"""What a corpse's goods become when the body leaves the world (ch03 conservation): coin to a purse, raw meat to the typed sink, every other stack to a ground item."""
# Compliance IDs: ECON-001
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from src.core.state import GroundItemState
from src.engine.carcass import RAW_MEAT_ITEM

if TYPE_CHECKING:
    from src.core.models.world_records import CorpseState


@dataclass(frozen=True)
class CorpseRemains:
    """The goods of one corpse as records: the purse, the ground items, the raw meat that goes out through the typed sink, and the next free item id."""

    purse: Optional[GroundItemState]
    ground_items: tuple[GroundItemState, ...]
    meat_left: float
    next_item_id: int


def corpse_remains(corpse: CorpseState, tick: int, next_item_id: int) -> CorpseRemains:
    """The remains of `corpse` leaving at `tick`: nothing is lost.

    Coin becomes a purse that takes the corpse's id (the body is gone, so its id is free) and carries whose body it fell from and when; raw meat is
    returned as `meat_left` for the caller to send out through the MEAT_DECAYED sink; every other stack becomes a ground item at the corpse tile with ids
    from `next_item_id` on. Pure: it reads the corpse and changes nothing, and it must only be called for a corpse that leaves by the APPLIED outcome of
    the tick (never at world_dynamics time, where a loot or meal may still undo the decay)."""
    dropped_tick = tick + 1
    purse = None
    if corpse.gold > 0:
        purse = GroundItemState(id=corpse.id, item_id="", quantity=0, position=corpse.position, gold=corpse.gold,
                                source_entity_id=corpse.original_entity_id, dropped_tick=dropped_tick)
    items: List[GroundItemState] = []
    meat = 0.0
    item_id = next_item_id
    for stack in sorted(corpse.items, key=lambda s: s.item_id):
        if stack.item_id == RAW_MEAT_ITEM:
            meat += stack.quantity
        elif stack.quantity > 0:
            items.append(GroundItemState(id=item_id, item_id=stack.item_id, quantity=stack.quantity, position=corpse.position,
                                         source_entity_id=corpse.original_entity_id, dropped_tick=dropped_tick))
            item_id += 1
    return CorpseRemains(purse=purse, ground_items=tuple(items), meat_left=float(meat), next_item_id=item_id)
