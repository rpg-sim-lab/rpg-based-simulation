"""#995 case (c) through the real kernel (trace v6 ruling; TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1): a broke hungry worker whose paid work is at a building that is NOT the inn
earns one wage and then goes to the inn and eats; it does not start a second shift with the price of a meal in hand.

The live pass is what this proves: the re-point lives in `live_record_route.route_live_record` and is reached through `intelligence.py` with the state; the arrival guard (`work_shift.meal_in_reach`)
keeps a NEW shift from starting while a meal is affordable, whichever of the two acts first. Staged on urban_political like the earn-and-eat scene (read-only here): the town hall hires (it is the only
workplace), the inn does not, the subject starts beside the hall with no gold."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.engine import service_admission
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.service_prices import EAT_PRICE_GOLD
from src.engine.work_shift import WAGE_GOLD
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world

WHO = 2
INN_ID, HALL_ID = 20003, 20000


def _staged():
    state = compile_world("urban_political", seed=46)
    inn, hall = state.buildings[INN_ID], state.buildings[HALL_ID]
    e = state.entities[WHO]
    e = replace(e, navigation=replace(e.navigation, position=(hall.position[0], hall.position[1] + 1.0)),
                biological=replace(e.biological, hunger=60.0, sleep_debt=0.0), inventory=replace(e.inventory, gold=0, items=[]))
    object.__setattr__(state, "entities", {WHO: e})
    hall = replace(hall, functional=True, hires_for_pay=True, maintenance_shifts_needed=0, maintenance_shifts_done=0, inventory=replace(hall.inventory, gold=100))
    inn = replace(inn, hires_for_pay=False, maintenance_shifts_needed=0, maintenance_shifts_done=0)
    object.__setattr__(state, "buildings", {INN_ID: inn, HALL_ID: hall})  # the hall is the only workplace; no shop to sell to
    object.__setattr__(state, "resource_nodes", {})
    object.__setattr__(state, "corpses", {})
    return state


def test_a_worker_that_earned_at_the_hall_goes_to_the_inn_and_starts_no_second_shift_with_the_price_in_hand(monkeypatch):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", service_admission.PaymentLaw.ATOMIC)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=_staged(), rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    shift_starts_before_wage, shift_starts_after_wage, wage_tick, meal_tick, peak = set(), set(), None, None, 0
    try:
        for _ in range(900):
            kernel.tick_once()
            ent = kernel._state.entities[WHO]
            if not ent.combat.alive:
                break
            if ent.task.payload.get("action") == "WORK":
                (shift_starts_after_wage if wage_tick is not None else shift_starts_before_wage).add(ent.task.payload.get("shift_start"))
            peak = max(peak, ent.inventory.gold)
            if wage_tick is None and ent.inventory.gold >= WAGE_GOLD:
                wage_tick = kernel._state.tick
            if wage_tick is not None and meal_tick is None and ent.inventory.gold < peak and ent.inventory.gold >= peak - EAT_PRICE_GOLD:
                meal_tick = kernel._state.tick
            if meal_tick is not None:
                break
    finally:
        kernel.shutdown()
    assert shift_starts_before_wage, "the staging is wrong: the broke worker never started a shift at the hall"
    assert wage_tick is not None, "the worker never earned a wage"
    assert meal_tick is not None and meal_tick > wage_tick, "having earned, it never paid for a meal"
    new_after = {s for s in shift_starts_after_wage if s not in shift_starts_before_wage}
    assert not new_after, f"a NEW shift started after the wage with the price of a meal in hand (shift_start ticks {sorted(new_after)})"
