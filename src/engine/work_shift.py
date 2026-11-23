"""A shift of work at a building for a wage (EXCH-02, owner decision 34: a wage for work at a shop, inn or smithy, paid from the payer's own purse).

A subject that cannot afford a meal and has nothing a shop would buy can work a shift at the inn: the WORK action, held tick after tick beside a
functional inn, counts up the interaction progress the node harvest already uses (``kind="work"``, no new state). Walking away, taking damage or
changing task resets it (``interaction.py``). After SHIFT_TICKS consecutive ticks the inn pays WAGE_GOLD out of its OWN purse as one typed ``WAGE``
transfer; a short purse pays nothing (the resolver rejects it) and the worker has worked unpaid. The inn's coin is credited by the meals and
beds it sells, so the loop closes through the inn's purse. The town (treasury) wage for public work is a separate path, not built here.

Values follow the fiction (owner decision 33): 200 ticks at 36 seconds a tick (Bible 05) is a two-hour kitchen and yard shift; its 6 gold is a
meal (5) and a coin.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.core.treasury import can_pay
from src.core.updates import EntityUpdate, InteractionUpdate, ResourceTransferIntent
from src.engine.biological_needs import need_rates
from src.engine.building_services import maintenance_open, offers_work, service_building
from src.engine.need_pull import TICKS_PER_TILE, step_travel_tiles
from src.engine.place_tax import building_holder, tax_on
from src.engine.serves import serves
from src.engine.starvation import STARVING_LINE, hp_loss_period
from src.engine.way_in_range import way_in_range
from src.engine.work_wake import held_work_is_threatened

SHIFT_TICKS = 200
WAGE_GOLD = 6
SHIFT_START = "shift_start"  # the tick the shift began, carried by the held WORK task's payload


def _can_pay_shift(state: Any, building: Any) -> bool:
    """Whether `building` can pay one wage now. Maintenance is paid first, from the purse and topped up from the holding treasury; commercial work
    from the purse alone (ruling 66)."""
    if building.inventory.gold >= WAGE_GOLD:
        return True
    holder = building_holder(state, building) if maintenance_open(building) else None
    return holder is not None and can_pay(state.global_resources, holder, WAGE_GOLD - building.inventory.gold)


def nearest_inn(state: Any, pos: Any) -> Optional[Any]:
    """The inn nearest to ``pos``, or None. The ONE selection of "the inn": the wage's meal (`meal_position_after`) and "an inn in reach" (`inn_in_reach`, read by the way set, the hunger scorer and the arrival)."""
    # A direct scan of ``state.buildings``, not `SpatialQueryService.nearest_building`: this is read from a tactical ENTITY_BRAIN worker (`building_arrival` -> `shift_takeable`) on a WorkerPacket,
    # which carries ``buildings`` but not the `world_indexes` the spatial query reads (an undeclared state read stops the run: docs/engine/contracts/bounded_concurrency_contract.md section 4).
    # The same answer as the index: Manhattan distance, the first strictly smaller wins, in ``state.buildings`` order (the order the index is built in).
    inn, best = None, float("inf")
    for building in state.buildings.values():
        if building.kind != "inn":
            continue
        dist = abs(building.position[0] - pos[0]) + abs(building.position[1] - pos[1])
        if dist < best:
            inn, best = building, dist
    return inn


def inn_in_reach(state: Any, entity: Any) -> Optional[Any]:
    """The nearest inn when it lies inside the subject's range (owner decision D57), else None: a farther inn in range does not stand in for a nearer one out of it."""
    inn = nearest_inn(state, entity.navigation.position)
    return inn if inn is not None and way_in_range(entity, inn.position) else None


def meal_in_reach(state: Any, entity: Any) -> bool:
    """True when the subject could buy a meal in reach now: the INN_MEAL way's own test (`ways.ways_in_reach`): the nearest inn is inside its range (`inn_in_reach`, one definition,
    read from ``state.buildings`` because a worker packet has no world index) and the one admission rule `admits(EAT)` holds (the coin trait, the diet, the full price). The ONE predicate for
    the arrival (`building_arrival`: a visit ends instead of starting a shift) and the re-point of a need project from its earn step to the meal (`live_record_route`)."""
    from src.engine.service_admission import admits
    return admits(entity, "EAT") and inn_in_reach(state, entity) is not None


def shift_held(entity: Any, state: Any) -> bool:
    """True while a shift is HELD in progress: the task is the WORK action carrying its start tick and fewer than SHIFT_TICKS ticks have passed since (the wage is paid on the last one). A task whose
    action is still WORK after the shift ended is not a held shift."""
    payload = entity.task.payload if isinstance(entity.task.payload, dict) else {}
    start = payload.get(SHIFT_START)
    return payload.get("action") == "WORK" and start is not None and int(state.tick) - int(start) + 1 < SHIFT_TICKS


def meal_position_after(state: Any, work_pos: Any) -> Optional[tuple]:
    """Where the wage is spent: the inn nearest to the place of work, or None when there is none."""
    inn = nearest_inn(state, work_pos)
    return None if inn is None else (inn.position[0], inn.position[1])


def shift_takeable(entity: Any, state: Any, work_pos: Any) -> bool:
    """True when a shift at ``work_pos`` can be taken now (row 27: a step is offered only if the subject can take it): the subject would reach the meal ALIVE and no
    present threat to life holds, by the same test that interrupts a held shift (``work_wake.held_work_is_threatened``).

    Hunger past the starvation line costs health slowly (decision 36, ``starvation.hp_loss_period``), so the line is not a veto: the ticks to the meal are the same
    whole-step sum the pull uses (``need_pull.step_travel_tiles``: the walk to the work, SHIFT_TICKS and the walk on to the meal); the ticks before the line are
    ``(STARVING_LINE - hunger) / rate`` (0 once past it); the health lost on the way is ``ticks_past_line / hp_loss_period``; the step is takeable while
    ``hp - that`` stays above 0. No new constant, no margin. One definition for the open step, the arrival action and the wake: a shift is never started that the
    next tick would interrupt."""
    ticks_to_meal = step_travel_tiles(entity.navigation.position, work_pos, float(SHIFT_TICKS), meal_position_after(state, work_pos)) * TICKS_PER_TILE
    rate = need_rates(entity)[0]
    ticks_before_line = max(0.0, (STARVING_LINE - entity.biological.hunger) / rate) if rate > 0 else float("inf")
    ticks_past_line = max(0.0, ticks_to_meal - ticks_before_line)
    if entity.combat.hp - ticks_past_line / hp_loss_period(entity.combat.max_hp) <= 0:
        return False
    return not held_work_is_threatened(entity, state)


def shift_startable(state: Any, entity: Any, building: Any) -> bool:
    """True when `entity` can start a paid shift at `building` now: it offers a shift, can pay one wage, serves the subject (owner decision 43) and the subject can finish the shift
    before the starvation line with no threat present (:func:`shift_takeable`). The ONE predicate for the open earn step (`work_in_reach`), the arrival action
    (`building_arrival`) and the held shift's own checks; no occupancy test, a tile in reach is a separate matter."""
    return offers_work(building) and _can_pay_shift(state, building) and serves(state, entity, building) and shift_takeable(entity, state, building.position)


def nearest_work(state: Any, entity: Any) -> Optional[Any]:
    """The nearest functional building that offers `entity` a shift (it serves it, owner decision 43) and can pay one wage, or None. Ties keep the lower id."""
    px, py = entity.navigation.position
    best, best_key = None, None
    for building in state.buildings.values():
        if not offers_work(building) or not _can_pay_shift(state, building) or not serves(state, entity, building):
            continue
        key = (abs(building.position[0] - px) + abs(building.position[1] - py), building.id)
        if best_key is None or key < best_key:
            best, best_key = building, key
    return best


def shift_done(update: Optional[EntityUpdate]) -> bool:
    """True when `update` ends a shift (completed, or no inn in reach): the held WORK task then ends."""
    return update is not None and update.interaction is not None and update.interaction.reset


def work_update(entity: Any, payload: Dict[str, Any], tick: int, context: Any) -> Dict[int, EntityUpdate]:
    """One tick of the shift: nothing until the SHIFT_TICKS-th tick since it began, then the inn's wage and the end of the shift."""
    inn = service_building(context, entity, "WORK") if context is not None else None
    if inn is None or not serves(context, entity, inn):
        return {entity.id: EntityUpdate(entity_id=entity.id, interaction=InteractionUpdate(reset=True))}
    if tick - int(payload.get(SHIFT_START, tick)) + 1 < SHIFT_TICKS:
        return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}
    # A held action runs twice a tick (the worker, then the routing phase); one shift is paid once, by its transaction id.
    shift = f"wage:{entity.id}:{inn.id}:{payload.get(SHIFT_START, tick)}"
    holder, tax = tax_on(context, inn, WAGE_GOLD)
    maintenance = maintenance_open(inn)  # maintenance first: the capped, counted, treasury-backed shift; else commercial, from the purse alone
    backer = building_holder(context, inn) if maintenance else None
    holder = backer if backer is not None else holder
    wage = ResourceTransferIntent(source_id=inn.id, source_kind="WAGE", gold_delta=WAGE_GOLD, transfer_kind="WAGE", transaction_id=shift,
                                  treasury_faction=holder, treasury_gold=tax, treasury_pays=backer is not None, maintenance_shift=maintenance)
    return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0, resource_transfers=[wage], interaction=InteractionUpdate(reset=True))}
