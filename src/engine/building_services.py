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

from src.core.service_refusals import ServiceRefusal
from src.core.updates import (
    BiologicalUpdate,
    EntityUpdate,
    NavigationUpdate,
    ResourceTransferIntent,
)
from src.engine.lodging import bed_delta, lodge_claim, lodges, refuse_rest
from src.engine.serves import keeps_coin, serves
from src.engine.service_admission import (
    admits_at,
    no_bed_for,
    refusal_reason,
    service_terms,
)
from src.engine.service_prices import INN_MEAL_HUNGER
from src.engine.service_reach import service_building_where, service_tile
from src.engine.shop_sale import plan_sale
from src.engine.spatial_query import SpatialQueryService

# The building kinds that serve an action. WORK is not here: the work a building offers is declared by its state (content ``hires_for_pay`` and
# ``maintenance_shifts``, EXCH-02 ruling 66), see ``offers_work``; no building name is in code (D56).
SERVICE_KINDS = {"REST": frozenset({"inn", "home"}), "EAT": frozenset({"inn"}), "SELL": frozenset({"shop"}), "REPAIR": frozenset({"blacksmith"})}


def no_bed_in_reach(state: Any, entity: Any) -> Optional[Any]:
    """The building in whose reach the subject stands (the REST service reach) that declares beds and has none for it (none free, or the bed not payable: `service_admission.no_bed_for`), or None (F3, divergence 2.155)."""
    tile = service_tile(state, (int(entity.navigation.position[0]), int(entity.navigation.position[1])), SERVICE_KINDS["REST"])
    building = SpatialQueryService.get_building_at(state, tile) if tile is not None else None
    return building if no_bed_for(state, entity, building) else None


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


def service_delta(context: Any, entity: Any, action: str, tick: int) -> Optional[EntityUpdate]:
    """What the building service for `action` adds to the subject's update, or None (no such building in reach, or nothing to deliver).

    An inn meal and a bed are each ONE paid transfer (owner decision 73, ATOMIC): the full price (`gold_cost`) and the service (hunger relief, or hp and readiness) are
    applied together or not at all, so a refused payment delivers nothing, and the building's purse is credited with exactly what was debited. A service with no payee is
    refused (`requires_payee`, PAYEE_MISSING). The building is found only for a subject it serves (`service_building`)."""
    building = service_building(context, entity, action)
    if building is None or (action in ("EAT", "REST") and not admits_at(entity, building, action, context)):
        return None  # the one admission rule (service_admission): no meal to a diet without prepared food (decision 44), none the payment law refuses, no bed where none is free (F3)
    if action == "REST":
        if lodges(building):
            return lodge_claim(entity, building)  # grant before delivery (F3): the bed service is merged only into a GRANTED claim (`lodging.grant_beds`), never delivered and taken back
        return bed_delta(entity, building, terms=service_terms("REST"))
    if action == "EAT":
        meal = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", transfer_kind="EAT", is_group_required=True, **service_terms("EAT"),
                                      biological_upd=BiologicalUpdate(hunger_delta=-INN_MEAL_HUNGER))  # no last_meal_tick stamp: its own ticket, after #781
        return EntityUpdate(entity_id=entity.id, resource_transfers=[meal])
    sale = plan_sale(context, entity, building)
    return None if sale is None else EntityUpdate(entity_id=entity.id, resource_transfers=[sale])


def _rest_refusal(context: Any, entity: Any, tick: int) -> Optional[EntityUpdate]:
    """K2 fix B: the typed record of a REST that a serving building refused for PAYMENT (the same reason EAT carries, `refusal_reason`), or None. It COUNTS only: it sets no failure reason and does not end the REST."""
    building = service_building(context, entity, "REST")
    if building is None:
        return None
    reason = refusal_reason(entity, "REST")
    if reason is None:
        return None
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(service_refusal_add=ServiceRefusal("REST", building.id, int(tick), reason.value)))


def _refusal_clear(context: Any, entity: Any, action: str) -> EntityUpdate:
    """K2 fix B: the delivery of (action, building) ends the subject's held refusals of that way; an empty update when it holds none (so a subject never refused is not touched)."""
    building = service_building(context, entity, action)
    if building is None or not any(r.action == action and r.building == building.id for r in entity.navigation.service_refusals):
        return EntityUpdate(entity_id=entity.id)
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(service_refusal_clear=(action, building.id)))


def with_service(updates: dict, entity: Any, action: str, tick: int, context: Any) -> dict:
    """The action's updates with the building service for `action` merged into the subject's own update."""
    if context is None or entity.id not in updates or (action == "REST" and "outcome" in entity.task.payload):
        return updates  # (a held sleep repeats its action every tick; the bed is paid for, and heals, once)
    if action == "REST":
        if no_bed_in_reach(context, entity) is not None:
            return {**updates, entity.id: refuse_rest(entity, tick)}  # F3: a REST whose first execution is in reach of a full beds building does not run on that tile (the one 'no bed' predicate)
    delta = service_delta(context, entity, action, tick)
    if delta is None:
        refusal = _rest_refusal(context, entity, tick) if action == "REST" else None   # K2 fix B: a REST refused for PAYMENT is a typed, counted finding about the way (EAT stamps where `_survival_action` types its own refusal)
        return updates if refusal is None else {**updates, entity.id: updates[entity.id].merge(refusal)}
    served = delta.merge(_refusal_clear(context, entity, action))
    return {**updates, entity.id: updates[entity.id].merge(served)}
