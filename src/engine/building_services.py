"""Building services land when their action executes (EXCH-02; bug fix of the cadence-gated town phase).

A bed (inn, home), a meal (inn) and a chosen sale (shop) used to be attached in ``TownResolutionSystem.resolve``, a phase that runs only on
ticks divisible by the profile's ``town_resolution`` cadence and that read the request from the entity's NEW task in that tick's update. A
subject's brain decides on its own offset, so for most subjects the request was never present when the phase ran. The service now lands in the
action itself: ``ActionRouter`` asks :func:`service_delta` when a REST, EAT or SELL action executes, and merges the result into the action's
update. The action runs wherever the subject is processed (the main thread or a worker); the lookup uses only what a ``WorkerPacket`` carries
(``SpatialQueryService.get_building_at``), and the building's purse and stock change only through the typed transfer the apply path resolves.
"""
from __future__ import annotations

from typing import Any, Optional

from src.core.updates import (
    BiologicalUpdate,
    CombatUpdate,
    EntityUpdate,
    ResourceTransferIntent,
)
from src.engine.serves import keeps_coin, serves
from src.engine.lodging import lodge_claim, lodges
from src.engine.service_admission import admits_at
from src.engine.service_prices import EAT_PRICE_GOLD, INN_MEAL_HUNGER, REST_PRICE_GOLD
from src.engine.service_reach import service_building_where, service_tile
from src.engine.shop_sale import plan_sale
from src.engine.spatial_query import SpatialQueryService

# The building kinds that serve an action. WORK is not here: the work a building offers is declared by its state (content ``hires_for_pay`` and
# ``maintenance_shifts``, EXCH-02 ruling 66), see ``offers_work``; no building name is in code (D56).
SERVICE_KINDS = {"REST": frozenset({"inn", "home"}), "EAT": frozenset({"inn"}), "SELL": frozenset({"shop"}), "REPAIR": frozenset({"blacksmith"})}


def maintenance_open(building: Any) -> bool:
    """True when `building` still needs maintenance shifts this upkeep period (EXCH-02, ruling 66)."""
    return bool(building.maintenance_shifts_done < building.maintenance_shifts_needed)


def offers_work(building: Any) -> bool:
    """True when `building` offers a shift now: maintenance it still needs, or commercial work it declares (``hires_for_pay``). No building name."""
    return bool(building.functional and (maintenance_open(building) or building.hires_for_pay))


def service_building(context: Any, entity: Any, action: str) -> Optional[Any]:
    """The functional building (of the kinds that serve `action`) the subject stands on or orthogonally beside, or None."""
    if action == "WORK":
        found = service_building_where(context, (int(entity.navigation.position[0]), int(entity.navigation.position[1])), offers_work)
        return found if found is not None and found.functional else None
    kinds = SERVICE_KINDS.get(action)
    if kinds is None:
        return None
    tile = service_tile(context, (int(entity.navigation.position[0]), int(entity.navigation.position[1])), kinds)
    building = SpatialQueryService.get_building_at(context, tile) if tile is not None else None
    if building is None or not building.functional or not (serves(context, entity, building) if action == "SELL" else keeps_coin(entity)):
        return None  # rest, meal, repair: the trait only (decision 43), never a kind name; the sale keeps its relationship rule as on main
    return building


def bed_delta(entity: Any, building: Any) -> EntityUpdate:
    """What a bed delivers: readiness, a little health and the charge for it (the bed is paid for, and heals, once per hold). The one definition, read by the rough-rest service
    (a building with no beds, on the reach tile) and by `lodging.grant_beds` (a granted lodging)."""
    charge = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", gold_delta=-REST_PRICE_GOLD, transfer_kind="REST", is_group_required=True)
    return EntityUpdate(entity_id=entity.id, readiness_delta=10.0, combat=CombatUpdate(hp_delta=5), resource_transfers=[charge])


def service_delta(context: Any, entity: Any, action: str, tick: int) -> Optional[EntityUpdate]:
    """What the building service for `action` adds to the subject's update, or None (no such building in reach, or nothing to deliver).

    A bed and an inn meal are as they were on main (free meals stay on until M0 step 4, owner decision 44): the effects are on the update, the price is a
    charge the resolver clamps at what the subject holds, and the building's purse is credited with what was actually paid. The building is found only
    for a subject it serves (`service_building`)."""
    building = service_building(context, entity, action)
    if building is None or (action in ("EAT", "REST") and not admits_at(entity, building, action, context)):
        return None  # the one admission rule (service_admission): no meal to a diet without prepared food (decision 44), none the payment law refuses, no bed where none is free (F3)
    if action == "REST":
        if lodges(building):
            return lodge_claim(entity, building)  # grant before delivery (F3): the bed service is merged only into a GRANTED claim (`lodging.grant_beds`), never delivered and taken back
        return bed_delta(entity, building)
    if action == "EAT":
        charge = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", gold_delta=-EAT_PRICE_GOLD, transfer_kind="EAT",
                                        is_group_required=True)
        return EntityUpdate(entity_id=entity.id, biological=BiologicalUpdate(hunger_delta=-INN_MEAL_HUNGER), resource_transfers=[charge])
    sale = plan_sale(context, entity, building)
    return None if sale is None else EntityUpdate(entity_id=entity.id, resource_transfers=[sale])


def with_service(updates: dict, entity: Any, action: str, tick: int, context: Any) -> dict:
    """The action's updates with the building service for `action` merged into the subject's own update."""
    if context is None or entity.id not in updates or (action == "REST" and "outcome" in entity.task.payload):
        return updates  # (a held sleep repeats its action every tick; the bed is paid for, and heals, once)
    delta = service_delta(context, entity, action, tick)
    if delta is None:
        return updates
    return {**updates, entity.id: updates[entity.id].merge(delta)}
