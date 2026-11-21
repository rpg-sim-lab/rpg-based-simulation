"""TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY: a way is open iff the inn would actually deliver the service now (AGENCY-03,
SURV-07 row 27). One admission function (``service_admission.admits``) is read by the service and by every "open" test; the payment law is one
constant. The ATOMIC law is exercised here by patching that constant; main keeps CLAMP."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.ways import WayKind, ways_in_reach
from src.ai.goals.scorers import EatScorer, SleepScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.engine import service_admission
from src.engine.appraisal import can_use_inn_meal
from src.engine.building_services import service_building, service_delta
from src.engine.domain.core_actions import eat_update
from src.engine.service_admission import PaymentLaw, admits
from src.engine.service_prices import EAT_PRICE_GOLD, REST_PRICE_GOLD

PRICES = {"EAT": EAT_PRICE_GOLD, "REST": REST_PRICE_GOLD}
GOLDS = (0, 1, EAT_PRICE_GOLD - 1, EAT_PRICE_GOLD, EAT_PRICE_GOLD + 1, REST_PRICE_GOLD - 1, REST_PRICE_GOLD, REST_PRICE_GOLD + 7)
TICKET = "TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT"


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _world(species_id="human", gold=20, kind="inn", at=(5.0, 5.0), **bio):
    ent = V2EntityBuilder(1).kind(species_id).properties({"species_id": species_id}).location(*at).inventory(gold=gold).build()
    ent = replace(ent, biological=replace(ent.biological, **bio))
    buildings = {10: BuildingState(id=10, kind=kind, position=(5.0, 5.0), functional=True)}
    state = AuthoritativeState(tick=1, seed=1, world_time=1000, entities={1: ent}, town_tiles={(5, 5)}, building_tiles={(5, 5): kind}, buildings=buildings)
    return state, ent


def _law(monkeypatch, law):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", law)


def test_main_keeps_the_clamp_law():  # [TAG (a)] the law constant this ticket exists to flip; the test pins the constant, not a behaviour; the both-laws parametrised tests are unchanged in what they cover
    assert service_admission.SERVICE_PAYMENT_LAW is PaymentLaw.ATOMIC


@pytest.mark.parametrize("law", list(PaymentLaw))
@pytest.mark.parametrize("action", ["EAT", "REST"])
@pytest.mark.parametrize("gold", GOLDS)
def test_admission_equals_what_the_service_really_delivers_for_a_coin_keeping_subject(monkeypatch, law, action, gold):
    _law(monkeypatch, law)
    state, ent = _world(gold=gold, hunger=60.0, sleep_debt=60.0)
    delivered = service_delta(state, ent, action, 1) is not None
    assert admits(ent, action) is delivered
    assert delivered is (law is PaymentLaw.CLAMP or gold >= PRICES[action])


@pytest.mark.parametrize("law", list(PaymentLaw))
@pytest.mark.parametrize("action", ["EAT", "REST"])
@pytest.mark.parametrize("gold", GOLDS)
def test_gold_is_never_debited_without_the_service_in_the_same_update(monkeypatch, law, action, gold):
    """Under CLAMP partial payment is the law; what must never happen is gold leaving a subject with no delivery (the N1 t587 shape)."""
    _law(monkeypatch, law)
    state, ent = _world(gold=gold)
    delta = service_delta(state, ent, action, 1)
    if delta is None:
        return  # nothing delivered and nothing charged: no transfer exists to debit
    # [TAG REWRITE] the property is unchanged ("no debit without the service in the SAME accepted transfer"); it is asserted on the transfer now: D73 puts the relief ON the paid transfer
    (charge,) = delta.resource_transfers
    assert charge.gold_delta < 0 or charge.gold_cost > 0  # the price rides the transfer: on gold_cost under ATOMIC, on a negative gold_delta under CLAMP (`service_admission.price_fields`)
    assert (charge.gold_cost > 0) is (law is PaymentLaw.ATOMIC) and (charge.gold_delta < 0) is (law is PaymentLaw.CLAMP)
    if action == "EAT":
        assert charge.biological_upd is not None and charge.biological_upd.hunger_delta < 0
        assert delta.biological is None  # nothing is delivered outside the paid transfer
    else:
        assert charge.readiness_delta > 0 and charge.combat_upd is not None and charge.combat_upd.hp_delta > 0
        assert delta.readiness_delta == 0 and delta.combat is None


@pytest.mark.parametrize("action", ["EAT", "REST"])
@pytest.mark.parametrize("gold", (0, 1, EAT_PRICE_GOLD - 1, EAT_PRICE_GOLD, REST_PRICE_GOLD - 1, REST_PRICE_GOLD))
def test_the_resolved_transfer_is_per_law_refused_with_nothing_or_served_with_debit_equal_to_credit(monkeypatch, action, gold):
    """[TAG REWRITE, new] Resolved through the real resolver, per law. ATOMIC, short purse: refused, no debit, no relief. CLAMP, any purse: served, the debit is min(gold, price) and equals the building's credit."""
    from src.core.updates import StateUpdate
    from src.engine.economy import ResourceTransactionSystem
    for law in PaymentLaw:
        _law(monkeypatch, law)
        state, ent = _world(gold=gold)
        delta = service_delta(state, ent, action, 1)
        if delta is None:
            assert law is PaymentLaw.ATOMIC and gold < PRICES[action]  # refused up front: nothing charged, nothing delivered
            continue
        out = ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={1: delta}))
        res = out.entity_updates[1]
        paid = min(gold, PRICES[action]) if law is PaymentLaw.CLAMP else PRICES[action]
        assert [r.accepted for r in res.intent_results] == [True]
        assert (res.inventory.gold_delta if res.inventory else 0) == -paid
        credit = out.building_updates[10].inventory.gold_delta if 10 in out.building_updates and out.building_updates[10].inventory else 0
        assert credit == paid  # debit == credit
        if action == "EAT":
            assert res.biological is not None and res.biological.hunger_delta < 0
        else:
            assert res.readiness_delta > 0


def test_a_diet_without_prepared_food_is_not_admitted_to_the_meal_whatever_it_holds():
    _, plant_eater = _world("small_plant_eater", gold=100)
    assert not can_use_inn_meal(plant_eater) and not admits(plant_eater, "EAT")
    _, person = _world("human", gold=EAT_PRICE_GOLD)  # [TAG A FUND] holds the price: the test is about the DIET, not payment
    assert can_use_inn_meal(person) and admits(person, "EAT")


def test_a_person_holding_nothing_is_not_admitted_to_the_meal_under_atomic(monkeypatch):
    """[TAG A, new ATOMIC gold-0 case for class 1] the diet is fine, the purse is empty: no way."""
    _law(monkeypatch, PaymentLaw.ATOMIC)
    _, person = _world("human", gold=0)
    assert can_use_inn_meal(person) and not admits(person, "EAT")


def test_the_action_side_gives_no_core_relief_to_any_diet_and_admission_keeps_the_diet_branch():
    """[TAG C REMOVED LAW] the core EAT relief is gone for every diet under either law (D73): eat_update with nothing carried is the typed SOURCE_MISSING failure. The diet branch of admission stays, and a plant eater is still not admitted."""
    from src.core.enums import ReasonCode
    for species in ("human", "small_plant_eater", "wolf"):
        _, ent = _world(species, gold=100)
        upd = eat_update(ent, 1)
        assert upd.biological is None and upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING
    assert admits(_world("human", gold=100)[1], "EAT", PaymentLaw.CLAMP) and not admits(_world("small_plant_eater", gold=100)[1], "EAT", PaymentLaw.CLAMP)


@pytest.mark.parametrize("law", list(PaymentLaw))
@pytest.mark.parametrize("gold", (0, EAT_PRICE_GOLD - 1, EAT_PRICE_GOLD))
def test_ways_in_reach_and_the_eat_scorer_agree_with_the_service_on_the_inn_meal(monkeypatch, law, gold):
    _law(monkeypatch, law)
    state, ent = _world(gold=gold, at=(2.0, 5.0), hunger=60.0)
    inn_open = WayKind.INN_MEAL in ways_in_reach(ent, state)
    on_the_inn_tile = replace(ent, navigation=replace(ent.navigation, position=(5.0, 5.0)))
    assert inn_open is admits(ent, "EAT") is (service_delta(state, on_the_inn_tile, "EAT", 1) is not None)
    score = EatScorer().score(ent, state)
    assert (score.target_id == "10") is inn_open


@pytest.mark.parametrize("law,walks", [(PaymentLaw.CLAMP, True), (PaymentLaw.ATOMIC, False)])
def test_a_broke_tired_subject_is_offered_the_inn_bed_iff_rest_would_deliver_it(monkeypatch, law, walks):
    """f400 (TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR): live on main (CLAMP: it walks to the bed); under the atomic law (D73) it rests in place."""
    _law(monkeypatch, law)
    state, ent = _world(gold=0, at=(2.0, 5.0), sleep_debt=60.0)
    score = SleepScorer().score(ent, state)
    on_the_inn_tile = replace(ent, navigation=replace(ent.navigation, position=(5.0, 5.0)))
    assert (score.target_id == "10") is walks is (service_delta(state, on_the_inn_tile, "REST", 1) is not None)
    if not walks:
        assert score.target_pos is None


def test_known_gap_admission_ignores_keeps_coin_while_the_service_refuses_a_non_coin_subject():
    """Pinned, not xfail (designer ruling A, 2026-10-29): ``admits`` is True for a non-coin subject that ``service_building`` refuses. Tracked in
    %s; when that ticket puts keeps_coin into admission this test is rewritten to assert agreement."""  % TICKET
    state, ent = _world("small_plant_eater", gold=100)
    assert admits(ent, "REST") is True
    assert service_building(state, ent, "REST") is None
