"""TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (decision 73, divergence 2.218): a held EAT that FAILS ends its task, like a failed ATTACK, INTERACT or REST.

Found by the forced-60 control at the D73 head: a broke subject beside an inn that refuses it re-issued the same refused EAT on all 60 ticks (INSUFFICIENT_GOLD, payload kept non-empty, so the scheduler never
re-ran the brain). The reasons that end it are SOURCE_MISSING, SOURCE_DEPLETED and INSUFFICIENT_GOLD (`actions._ENDS_HELD_EAT_REASONS`); TARGET_LOCKED (transient) and the resolver reasons do not. Every case runs
through the real `ActionRoutingPhase.route`."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState, BuildingState, CorpseState, InventoryComponent
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.pipeline_phases.actions import ActionRoutingPhase, _ENDS_HELD_EAT_REASONS, _is_unrecoverable_action_failure

INN_ID = 1
CORPSE_ID = 1000007


def _subject(gold=0, items=()):
    ent = V2EntityBuilder(1).kind("human").location(11.0, 10.0).combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).biological(hunger=90.0).inventory(gold=gold).build()
    return replace(ent, inventory=replace(ent.inventory, items=list(items)))


def _state(ent, *, inn=True, corpses=None):
    buildings = {INN_ID: BuildingState(id=INN_ID, kind="inn", position=(10, 10), functional=True, inventory=InventoryComponent(gold=0))} if inn else {}
    return AuthoritativeState(tick=1, seed=1, entities={1: ent}, buildings=buildings, building_tiles={(10, 10): "inn"} if inn else {}, town_tiles={(11, 10), (10, 10)}, corpses=corpses or {})


def _eat(**payload):
    return StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT", **payload}))})


def _route(state, **payload):
    refined = ActionRoutingPhase.route(state, _eat(**payload))
    return refined, refined.entity_updates[1]


@pytest.mark.parametrize("case,reason", [("nothing_carried_no_inn", ReasonCode.SOURCE_MISSING), ("broke_beside_a_serving_inn", ReasonCode.INSUFFICIENT_GOLD),
                                         ("carcass_gone", ReasonCode.SOURCE_MISSING), ("carcass_with_no_meal", ReasonCode.SOURCE_DEPLETED)])
def test_a_held_eat_failing_with_each_ending_reason_ends_the_task_with_an_empty_payload(case, reason):
    ent = _subject(gold=0)
    if case == "nothing_carried_no_inn":
        refined, upd = _route(_state(ent, inn=False), target_id=INN_ID)
    elif case == "broke_beside_a_serving_inn":
        refined, upd = _route(_state(ent), target_id=INN_ID)
    elif case == "carcass_gone":
        refined, upd = _route(_state(ent, inn=False), corpse_id=CORPSE_ID)
    else:
        corpse = CorpseState(id=CORPSE_ID, original_entity_id=7, position=(11.0, 11.0), items=[], decay_tick=105)
        refined, upd = _route(_state(ent, inn=False, corpses={CORPSE_ID: corpse}), corpse_id=CORPSE_ID)
    assert upd.task.payload_set == {}  # an empty payload hands the subject back to the brain (scheduler is_idle_act)
    assert [(e.actor_id, e.action_kind, e.reason) for e in refined.rejection_events] == [(1, "EAT", reason.value)]


def test_the_ending_reasons_are_exactly_the_three_and_target_locked_does_not_end_a_held_eat():
    assert _ENDS_HELD_EAT_REASONS == frozenset({ReasonCode.SOURCE_MISSING.value, ReasonCode.SOURCE_DEPLETED.value, ReasonCode.INSUFFICIENT_GOLD.value})
    for reason in (ReasonCode.TARGET_LOCKED, ReasonCode.PAYEE_MISSING, ReasonCode.INVENTORY_FULL):
        assert not _is_unrecoverable_action_failure("EAT", "FAILURE", reason.value if hasattr(reason, "value") else reason)
    for reason in _ENDS_HELD_EAT_REASONS:
        assert _is_unrecoverable_action_failure("EAT", "FAILURE", reason)
    assert not _is_unrecoverable_action_failure("EAT", "SUCCESS", ReasonCode.INSUFFICIENT_GOLD.value)  # a success is never an unrecoverable failure


def test_a_successful_paid_inn_meal_ends_its_task_exactly_as_before():
    refined, upd = _route(_state(_subject(gold=5)), target_id=INN_ID)
    assert upd.task.payload_set == {} and not refined.rejection_events and len(upd.resource_transfers) == 1


def test_a_carried_food_eat_is_unchanged_and_ends_on_success():
    from src.core.items import food_hunger_recovery
    food = next(i for i in ("bread", "cooked_meat", "meal", "wild_berries", "berries") if food_hunger_recovery(i) > 0.0)
    refined, upd = _route(_state(_subject(gold=0, items=[ItemStack(item_id=food, quantity=1)]), inn=False), reason="EAT_CARRIED")
    assert upd.task.payload_set == {} and not refined.rejection_events
    assert any(t.source_kind == "CARRIED_FOOD" for t in upd.resource_transfers)


def test_an_eat_at_an_atomic_inn_that_is_gone_at_resolve_ends_its_task_and_the_resolver_refuses_it_payee_missing():
    """Pins 'refused at resolve -> no loop': the EAT carries a paid transfer, so the action is a SUCCESS in this phase and ends its task (payload {}); the payee is gone by resolve time (a building removed between the
    action and the town resolution), so the resolver refuses the transfer with PAYEE_MISSING (ATOMIC: the full price to somebody, or no service) and delivers no meal."""
    from src.engine.economy import ResourceTransactionSystem
    state = _state(_subject(gold=5))
    refined, upd = _route(state, target_id=INN_ID)
    (meal,) = upd.resource_transfers
    assert upd.task.payload_set == {} and not refined.rejection_events and meal.requires_payee is True
    gone = replace(state, buildings={}, building_tiles={})
    out = ResourceTransactionSystem.resolve_all(gone, StateUpdate(entity_updates={1: upd})).entity_updates[1]
    assert [r.accepted for r in out.intent_results] == [False] and out.intent_results[0].reason == ReasonCode.PAYEE_MISSING
    assert out.biological is None and out.inventory is None  # no meal, no debit
