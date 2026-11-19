"""TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (owner decisions 44 and 73): nothing is free.

A meal at the inn gives 60 hunger for 5 gold, a bed gives hp +5 and readiness +10 for 10 gold, each applied with the payment or not at all, with no
clamp to what the subject holds. Every case runs through the real path: `ActionRouter.execute_action`, then `ResourceTransactionSystem.resolve_all`.
"""
from __future__ import annotations

import pickle
from dataclasses import asdict, replace

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent
from src.core.updates import EntityUpdate, ResourceTransferIntent, StateUpdate
from src.engine.domain.action_router import ActionRouter
from src.engine.economy import ResourceTransactionSystem
from src.engine.service_prices import EAT_PRICE_GOLD, INN_MEAL_HUNGER, REST_PRICE_GOLD


def _world(gold: int, *, hunger: float = 80.0, items=(), species: str = "human"):
    """One subject of a real species (``kind`` is the only species field), standing beside the inn. A human keeps coin and eats a prepared meal."""
    ent = (V2EntityBuilder(1).kind(species).location(11.0, 10.0).biological(hunger=hunger).inventory(gold=gold).build())
    ent = replace(ent, inventory=replace(ent.inventory, items=list(items)))
    inn = BuildingState(id=1, kind="inn", position=(10, 10), functional=True, inventory=InventoryComponent(gold=0))
    return ent, AuthoritativeState(tick=1, seed=1, entities={1: ent}, buildings={1: inn}, building_tiles={(10, 10): "inn"}, town_tiles={(11, 10), (10, 10)})


def _act(action: str, gold: int, **kw):
    ent, state = _world(gold, **kw)
    upd = ActionRouter.execute_action(ent, {"action": action, "target_id": 1}, state.tick, None, state)[1]
    return ent, state, upd


def _resolve(state, upd):
    return ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={1: upd})).entity_updates[1]


def _purse_change(state, upd):
    out = ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={1: upd}))
    building = out.building_updates.get(1)
    return (building.inventory.gold_delta if building is not None and building.inventory else 0), (out.entity_updates[1].inventory.gold_delta if out.entity_updates[1].inventory else 0)


# ---- the meal -------------------------------------------------------------------------------------------------------------------------------------

def test_a_broke_subject_beside_the_inn_is_not_fed_and_the_task_ends_with_the_typed_payment_refusal():
    """Ruling (i): a serving inn that refused the payment gives the task its own typed reason, not SOURCE_MISSING."""
    _, state, upd = _act("EAT", EAT_PRICE_GOLD - 1)
    assert not upd.resource_transfers and upd.biological is None
    assert upd.navigation.failure_reason == ReasonCode.INSUFFICIENT_GOLD and upd.readiness_delta == 0.0


def test_the_same_broke_subject_with_no_inn_in_reach_keeps_source_missing():
    ent, state = _world(0)
    state = replace(state, buildings={}, building_tiles={})
    upd = ActionRouter.execute_action(ent, {"action": "EAT"}, state.tick, None, state)[1]
    assert upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING and upd.biological is None and not upd.resource_transfers


def test_an_inn_whose_meal_the_body_cannot_eat_is_no_food_source_so_source_missing_stands(monkeypatch):
    """The diet edge with a real species: a wolf's diet has no prepared food. A wolf does not keep coin, so the inn would not serve it for that reason first; the coin trait is
    forced on here so the DIET is the one thing refusing the meal. Broke, so a payment refusal would be INSUFFICIENT_GOLD: the typed reason must stay SOURCE_MISSING."""
    monkeypatch.setattr("src.engine.building_services.keeps_coin", lambda entity: True)
    from src.engine.appraisal import can_use_inn_meal
    ent, state = _world(0, species="wolf")
    assert not can_use_inn_meal(ent)
    upd = ActionRouter.execute_action(ent, {"action": "EAT", "target_id": 1}, state.tick, None, state)[1]
    assert upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING and upd.biological is None and not upd.resource_transfers


def test_the_free_meal_is_gone_under_clamp_too(monkeypatch):
    """The removal is unconditional (designer ruling): the payment law governs how a SERVICE is paid; EAT with nothing carried is not a service."""
    from src.engine import service_admission
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", service_admission.PaymentLaw.CLAMP)
    ent, state = _world(50)
    state = replace(state, buildings={}, building_tiles={})
    upd = ActionRouter.execute_action(ent, {"action": "EAT"}, state.tick, None, state)[1]
    assert upd.biological is None and not upd.resource_transfers and upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING


def test_a_subject_holding_exactly_the_price_pays_in_full_and_is_fed_in_one_accepted_transfer():
    _, state, upd = _act("EAT", EAT_PRICE_GOLD)
    (meal,) = upd.resource_transfers
    assert meal.gold_cost == EAT_PRICE_GOLD and meal.gold_delta == 0 and meal.biological_upd.hunger_delta == -INN_MEAL_HUNGER == -60.0
    out = _resolve(state, upd)
    assert [r.accepted for r in out.intent_results] == [True]
    assert out.biological.hunger_delta == -60.0 and out.biological.last_meal_tick_set is None  # the stamp is its own ticket, after #781
    assert out.inventory.gold_delta == -EAT_PRICE_GOLD
    assert _purse_change(state, upd) == (EAT_PRICE_GOLD, -EAT_PRICE_GOLD)  # coin is conserved: the building gets what the subject paid


def test_a_meal_rejected_at_apply_time_gives_no_hunger_relief_and_moves_no_coin():
    """The race the up-front check cannot close: the purse is empty when the transfer resolves. The relief rides on the transfer, so it is refused with it."""
    _, state, upd = _act("EAT", EAT_PRICE_GOLD)
    ent = state.entities[1]
    broke_state = replace(state, entities={1: replace(ent, inventory=replace(ent.inventory, gold=0))})
    out = _resolve(broke_state, upd)
    assert [r.accepted for r in out.intent_results] == [False] and out.intent_results[0].reason == ReasonCode.ACTION_EXHAUSTION
    assert out.biological is None and out.inventory is None


def test_carried_food_is_eaten_without_the_inn_and_without_gold():
    from src.core.models.inventory import ItemStack
    from src.core.items import food_hunger_recovery

    ent, state = _world(0)
    food = next(i for i in ("bread", "cooked_meat", "meal", "wild_berries", "berries") if food_hunger_recovery(i) > 0.0)
    ent = replace(ent, inventory=replace(ent.inventory, items=[ItemStack(item_id=food, quantity=1)]))
    state = replace(state, entities={1: ent})
    upd = ActionRouter.execute_action(ent, {"action": "EAT", "target_id": 1}, state.tick, None, state)[1]
    assert upd.navigation is None or upd.navigation.failure_reason is None
    assert any(t.items_remove for t in upd.resource_transfers)


def test_eat_with_nothing_carried_and_no_inn_fails_typed_and_does_not_burn_readiness():
    ent, state = _world(50)
    state = replace(state, buildings={}, building_tiles={})
    upd = ActionRouter.execute_action(ent, {"action": "EAT"}, state.tick, None, state)[1]
    assert upd.biological is None and not upd.resource_transfers and upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING


def test_a_meal_at_a_serving_inn_carries_the_requires_payee_flag_only_under_atomic(monkeypatch):
    from src.engine import service_admission
    _, _, upd = _act("EAT", 50)
    assert upd.resource_transfers[0].requires_payee is True
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", service_admission.PaymentLaw.CLAMP)
    _, _, upd = _act("EAT", 50)
    assert upd.resource_transfers[0].requires_payee is False


def test_the_typed_failure_does_not_fire_when_an_inn_serves_a_subject_that_can_pay():
    """The merge order: the failure is for nothing to eat, not for the plain EAT update the inn's transfer is merged into."""
    _, state, upd = _act("EAT", 50)
    assert upd.navigation is None or upd.navigation.failure_reason is None
    assert upd.readiness_delta == -100.0 and len(upd.resource_transfers) == 1


# ---- the bed --------------------------------------------------------------------------------------------------------------------------------------

def test_a_bed_is_refused_up_front_to_a_subject_without_the_price():
    _, state, upd = _act("REST", REST_PRICE_GOLD - 1)
    assert not upd.resource_transfers and upd.readiness_delta == 0.0 and upd.combat is None


def test_a_paid_bed_gives_hp_and_readiness_and_takes_the_full_price():
    _, state, upd = _act("REST", REST_PRICE_GOLD)
    assert upd.readiness_delta == 0.0  # the bed's effects ride on the transfer, none on the update itself
    out = _resolve(state, upd)
    assert out.inventory.gold_delta == -REST_PRICE_GOLD and out.combat.hp_delta == 5 and out.readiness_delta == 10.0
    assert _purse_change(state, upd) == (REST_PRICE_GOLD, -REST_PRICE_GOLD)


def test_a_bed_rejected_at_apply_time_gives_no_gold_hp_or_readiness():
    """The regression pin for the free rest: readiness used to sit on the update and survived a rejected payment."""
    _, state, upd = _act("REST", REST_PRICE_GOLD)
    ent = state.entities[1]
    out = _resolve(replace(state, entities={1: replace(ent, inventory=replace(ent.inventory, gold=0))}), upd)
    assert [r.accepted for r in out.intent_results] == [False]
    assert out.readiness_delta == 0.0 and out.combat is None and out.inventory is None


def test_a_bed_in_a_rolled_back_group_gives_nothing():
    _, state, upd = _act("REST", REST_PRICE_GOLD)
    (bed,) = upd.resource_transfers
    failing = ResourceTransferIntent(source_id=1, source_kind="TOWN_SERVICE", gold_cost=10_000, transfer_kind="REST", group_id="g")
    grouped = replace(upd, resource_transfers=[replace(bed, group_id="g"), failing])
    ent = state.entities[1]
    out = _resolve(replace(state, entities={1: replace(ent, inventory=replace(ent.inventory, gold=50))}), grouped)
    assert [r.accepted for r in out.intent_results] == [False, False]
    assert out.readiness_delta == 0.0 and out.combat is None and out.inventory is None


def test_the_intent_with_a_readiness_field_round_trips():
    intent = ResourceTransferIntent(source_id=1, source_kind="TOWN_SERVICE", gold_cost=10, transfer_kind="REST", readiness_delta=10.0)
    assert ResourceTransferIntent(**asdict(intent)) == intent and pickle.loads(pickle.dumps(intent)) == intent
    assert ResourceTransferIntent(source_id=1, source_kind="X").readiness_delta == 0.0  # the default leaves every other transfer unchanged


# ---- no payee under ATOMIC ------------------------------------------------------------------------------------------------------------------------

def _no_payee_state():
    ent, state = _world(50)
    return state


def _resolve_intent(state, intent):
    return _resolve(state, EntityUpdate(entity_id=1, resource_transfers=[intent]))


def test_an_atomic_service_with_no_payee_is_refused_typed_with_no_debit_and_no_relief():
    from src.core.updates import BiologicalUpdate
    meal = ResourceTransferIntent(source_id=999, source_kind="TOWN_SERVICE", gold_cost=EAT_PRICE_GOLD, transfer_kind="EAT", requires_payee=True,
                                  biological_upd=BiologicalUpdate(hunger_delta=-INN_MEAL_HUNGER))
    out = _resolve_intent(_no_payee_state(), meal)
    assert [r.accepted for r in out.intent_results] == [False] and out.intent_results[0].reason == ReasonCode.PAYEE_MISSING
    assert out.biological is None and out.inventory is None


def test_a_repair_or_shop_fee_with_no_payee_is_unchanged_debited_zero_and_counted():
    """requires_payee defaults False: only the ATOMIC inn builders set it, so every other service or fee keeps the coin fix's behaviour."""
    from src.core.conservation import PayeeMissingCounts
    PayeeMissingCounts.reset()
    fee = ResourceTransferIntent(source_id=999, source_kind="TOWN_SERVICE", gold_cost=7, transfer_kind="REPAIR")
    assert fee.requires_payee is False
    out = _resolve_intent(_no_payee_state(), fee)
    assert [r.accepted for r in out.intent_results] == [True]
    assert out.inventory is None or out.inventory.gold_delta == 0


def test_requires_payee_round_trips_and_defaults_false():
    intent = ResourceTransferIntent(source_id=1, source_kind="TOWN_SERVICE", gold_cost=10, transfer_kind="REST", requires_payee=True)
    assert ResourceTransferIntent(**asdict(intent)) == intent and pickle.loads(pickle.dumps(intent)) == intent
    assert ResourceTransferIntent(source_id=1, source_kind="X").requires_payee is False


# ---- the granted bed ------------------------------------------------------------------------------------------------------------------------------

def test_a_claim_admitted_then_the_purse_emptied_before_the_grant_delivers_nothing():
    """The grant does not ask admission again (the claim did). With the bed riding the paid transfer, the resolver's own `gold < gold_cost` test refuses it atomically."""
    from src.core.updates import StateUpdate
    from src.engine.lodging import grant_beds, lodge_claim
    from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        ent = st.entities[1]
        assert ent.inventory.gold >= REST_PRICE_GOLD  # admitted at claim time
        granted = grant_beds(st, StateUpdate(entity_updates={1: lodge_claim(ent, st.buildings[INN_ID])}))
        broke = replace(st, entities={**st.entities, 1: replace(ent, inventory=replace(ent.inventory, gold=0))})
        out = ResourceTransactionSystem.resolve_all(broke, granted).entity_updates[1]
        assert [r.accepted for r in out.intent_results] == [False]
        assert out.readiness_delta == 0.0 and out.combat is None and (out.inventory is None or out.inventory.gold_delta == 0)
    finally:
        k.shutdown()


def test_grant_beds_stamps_the_payee_requirement_on_a_granted_bed_only_when_the_law_asks():
    from src.core.updates import StateUpdate
    from src.engine.lodging import grant_beds, lodge_claim
    from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        st = k._state
        claim = StateUpdate(entity_updates={1: lodge_claim(st.entities[1], st.buildings[INN_ID])})
        assert [t.requires_payee for t in grant_beds(st, claim, True).entity_updates[1].resource_transfers] == [True]
        assert [t.requires_payee for t in grant_beds(st, claim).entity_updates[1].resource_transfers] == [False]
    finally:
        k.shutdown()
