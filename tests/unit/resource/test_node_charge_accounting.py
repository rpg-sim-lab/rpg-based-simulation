"""Node-charge accounting in ``ResourceTransactionResolver`` (Mechanics Bible ch03 §3, §1).

Oracle: ``docs/mechanics/03_economic_laws.md`` §3 "Node Charges" (regular nodes lose exactly 1 charge
per harvest; loot nodes are fully consumed on the first successful interaction) and §1 Atomic
Conservation. Parity: ``TOWN-122`` (two actors completing the same node charge in one tick cannot
duplicate the yield).
"""

import pytest

from src.core.conservation import ResourceTransactionResolver
from src.core.models.inventory import ItemStack
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import ResourceNodeUpdate
from src.core.enums import ReasonCode
from tests.helpers.entities import make_entity
from tests.helpers.resources import make_resource_node, make_resource_state

pytestmark = [pytest.mark.domain("substrate"), pytest.mark.domain("economy"), pytest.mark.level("unit")]

_NODE_ID = 101
_KEY = ("NODE", _NODE_ID)


def _intent() -> ResourceTransferIntent:
    return ResourceTransferIntent(
        source_id=_NODE_ID,
        source_kind="NODE",
        items_add=[ItemStack("iron_ore", 1)],
        transfer_kind="HARVEST",
    )


def _resolve(node, *, node_overrides=None, reservations=None):
    actor = make_entity(1)
    state = make_resource_state(entities=[actor], nodes=[node])
    return ResourceTransactionResolver.resolve(
        state, actor, _intent(), node_overrides=node_overrides, reservations=reservations
    )


def test_regular_node_loses_exactly_one_charge_per_harvest():
    result = _resolve(make_resource_node(_NODE_ID, kind="IRON_NODE", remaining_charges=5))
    assert result.accepted
    assert result.node_update.charges_delta == -1
    assert result.inventory_update.items_add == [ItemStack("iron_ore", 1)]


def test_loot_node_is_fully_consumed_on_first_interaction():
    result = _resolve(make_resource_node(_NODE_ID, kind="LOOT", remaining_charges=4, max_charges=4))
    assert result.accepted
    assert result.node_update.charges_delta == -4


def test_last_charge_taken_earlier_in_the_tick_cannot_be_harvested_again():
    # The apply-path shape: an accepted harvest leaves charges_delta -1 in node_overrides and nothing else.
    node = make_resource_node(_NODE_ID, remaining_charges=1, max_charges=1)
    earlier = {_NODE_ID: ResourceNodeUpdate(node_id=_NODE_ID, charges_delta=-1)}
    result = _resolve(node, node_overrides=earlier)
    assert not result.accepted
    assert result.reason == ReasonCode.SOURCE_DEPLETED
    assert result.inventory_update is None and result.node_update is None


def test_second_harvest_of_a_two_charge_node_in_the_same_tick_is_accepted_and_takes_the_last_charge():
    node = make_resource_node(_NODE_ID, remaining_charges=2, max_charges=2)
    earlier = {_NODE_ID: ResourceNodeUpdate(node_id=_NODE_ID, charges_delta=-1)}
    result = _resolve(node, node_overrides=earlier)
    assert result.accepted
    assert result.node_update.charges_delta == -1
    assert result.inventory_update.items_add == [ItemStack("iron_ore", 1)]


def test_a_node_reservation_no_longer_counts_against_the_charges():
    # No NODE reservation is written or read: the in-tick charges_delta is the whole record.
    node = make_resource_node(_NODE_ID, remaining_charges=1, max_charges=1)
    result = _resolve(node, reservations={_KEY: 1})
    assert result.accepted


def test_sliding_charge_delta_from_earlier_update_is_counted_before_yield():
    node = make_resource_node(_NODE_ID, remaining_charges=1, max_charges=1)
    earlier = {_NODE_ID: ResourceNodeUpdate(node_id=_NODE_ID, charges_delta=-1)}
    result = _resolve(node, node_overrides=earlier)
    assert not result.accepted
    assert result.reason == ReasonCode.SOURCE_DEPLETED
    assert result.inventory_update is None and result.node_update is None

