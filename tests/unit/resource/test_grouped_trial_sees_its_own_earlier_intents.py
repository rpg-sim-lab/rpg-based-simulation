"""A grouped transfer is all or nothing, so its trial must see what the group's own earlier intents would take (Mechanics Bible ch03 §1, §3).

``ResourceTransactionSystem.resolve_all`` trial-resolves a group's intents one after another on group-local copies of the node charges,
reservations, treasury and building records; the live records change only when the whole group commits. Parity ``TOWN-122``.
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, RegionState
from src.core.treasury import treasury_key
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import BuildingUpdate, EntityUpdate, ResourceNodeUpdate, StateUpdate
from src.engine.economy import ResourceTransactionSystem
from src.engine.work_shift import WAGE_GOLD
from tests.helpers.entities import make_entity
from tests.helpers.resources import make_resource_node, make_resource_state

pytestmark = [pytest.mark.domain("substrate"), pytest.mark.domain("economy"), pytest.mark.level("unit")]

_NODE_ID = 101
_HERO = int(Faction.HERO_GUILD)
_KEY = treasury_key(_HERO)


def _harvest(txn):
    return ResourceTransferIntent(transaction_id=txn, source_id=_NODE_ID, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)],
                                  transfer_kind="HARVEST", group_id="G", is_group_required=True)


def _group_on_node(charges, intents=2):
    state = make_resource_state(entities=[make_entity(1)], nodes=[make_resource_node(_NODE_ID, remaining_charges=charges, max_charges=charges)])
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[_harvest(f"t{i}") for i in range(intents)])})
    return state, ResourceTransactionSystem.resolve_all(state, update)


def _accepted(out, entity_id=1):
    return [r.accepted for r in out.entity_updates[entity_id].intent_results]


def test_two_node_intents_in_a_group_on_a_one_charge_node_roll_back():
    _, out = _group_on_node(charges=1)
    assert _accepted(out) == [False, False]
    reasons = [r.reason for r in out.entity_updates[1].intent_results]
    assert reasons == [ReasonCode.GROUP_ROLLBACK, ReasonCode.SOURCE_DEPLETED]
    assert _NODE_ID not in out.node_updates
    assert out.entity_updates[1].inventory is None


def test_two_node_intents_in_a_group_on_a_two_charge_node_are_both_accepted():
    _, out = _group_on_node(charges=2)
    assert _accepted(out) == [True, True]
    assert out.node_updates[_NODE_ID].charges_delta == -2
    assert out.entity_updates[1].inventory.items_add == [ItemStack("iron_ore", 1), ItemStack("iron_ore", 1)]


def _wage_state(*, purse, treasury, needed=2):
    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=purse),
                        maintenance_shifts_needed=needed, maintenance_shifts_done=0)
    worker = V2EntityBuilder(1).kind("worker").location(5.0, 6.0).inventory(gold=0).build()
    region = RegionState(id="r", name="R", bounds=(0, 0, 50, 50), owner_faction_id=_HERO)
    return AuthoritativeState(tick=5, seed=1, entities={1: worker}, buildings={10: inn}, regions={"r": region}, global_resources={_KEY: treasury})


def _wage(txn, *, maintenance):
    return ResourceTransferIntent(source_id=10, source_kind="WAGE", gold_delta=WAGE_GOLD, transfer_kind="WAGE", transaction_id=txn, group_id="G",
                                  treasury_faction=_HERO, treasury_gold=0, treasury_pays=maintenance, maintenance_shift=maintenance)


def _wages(state, *, maintenance, base=None):
    base = base or StateUpdate()
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[_wage("w0", maintenance=maintenance), _wage("w1", maintenance=maintenance)])},
                         resource_updates=base.resource_updates, building_updates=base.building_updates)
    return ResourceTransactionSystem.resolve_all(state, update)


def test_a_treasury_funded_pair_that_exceeds_the_balance_rolls_back():
    out = _wages(_wage_state(purse=0, treasury=float(WAGE_GOLD)), maintenance=True)
    assert _accepted(out) == [False, False]
    assert out.entity_updates[1].intent_results[1].reason == ReasonCode.LIQUIDITY_EXHAUSTED
    assert out.resource_updates.get(_KEY, 0.0) == 0.0
    assert 10 not in out.building_updates


def test_a_purse_pair_that_exceeds_the_purse_rolls_back():
    out = _wages(_wage_state(purse=WAGE_GOLD, treasury=0.0), maintenance=False)
    assert _accepted(out) == [False, False]
    assert 10 not in out.building_updates


def test_a_treasury_funded_pair_within_the_balance_is_accepted_and_spends_the_treasury_twice():
    out = _wages(_wage_state(purse=0, treasury=float(2 * WAGE_GOLD)), maintenance=True)
    assert _accepted(out) == [True, True]
    assert out.resource_updates[_KEY] == -2 * WAGE_GOLD + 0.0
    assert out.building_updates[10].maintenance_shifts_done_delta == 2


def test_a_rejected_group_leaves_the_live_records_unchanged():
    state = _wage_state(purse=0, treasury=float(WAGE_GOLD))
    base = StateUpdate(resource_updates={_KEY: -1.0, "other": 3.0}, building_updates={10: BuildingUpdate(building_id=10, hp_delta=-1)})
    out = _wages(state, maintenance=True, base=base)
    assert _accepted(out) == [False, False]
    assert out.resource_updates == {_KEY: -1.0, "other": 3.0}
    assert out.building_updates == {10: BuildingUpdate(building_id=10, hp_delta=-1)}


def test_a_rejected_group_leaves_the_node_records_and_reservations_unchanged():
    # Group [harvest node, crafting that fails]: the harvest trial is accepted, the group is rolled back, then a later actor harvests the node.
    node = make_resource_node(_NODE_ID, remaining_charges=1, max_charges=1)
    state = make_resource_state(entities=[make_entity(1), make_entity(2)], nodes=[node])
    failing = ResourceTransferIntent(source_id="C1", source_kind="CRAFTING", items_add=[ItemStack("steel_sword", 1)],
                                     items_remove=[ItemStack("coal", 5)], group_id="G", is_group_required=True)
    later = ResourceTransferIntent(transaction_id="t-later", source_id=_NODE_ID, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)],
                                   transfer_kind="HARVEST")
    seeded = {7: ResourceNodeUpdate(node_id=7, charges_delta=-1)}
    update = StateUpdate(node_updates=dict(seeded), entity_updates={
        1: EntityUpdate(entity_id=1, resource_transfers=[_harvest("t0"), failing]),
        2: EntityUpdate(entity_id=2, resource_transfers=[later])})
    out = ResourceTransactionSystem.resolve_all(state, update)
    assert _accepted(out, 1) == [False, False]
    assert _accepted(out, 2) == [True]
    assert out.node_updates[7] == seeded[7]
    assert out.node_updates[_NODE_ID].charges_delta == -1
